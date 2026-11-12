from datetime import date, timedelta

from fastapi import APIRouter, Depends
from supabase import Client

from ..auth import get_current_user_id, get_db
from ..schemas.relatorios import LancamentoExportado, RelatorioAnual, RelatorioMensal
from ..services.fatura import somar_meses
from ..services.orcamento_saldo import carregar_dados_periodo
from . import dashboard, estrutura_custo, transacoes

router = APIRouter(prefix="/relatorios", tags=["relatorios"])

# item 10 do backlog: export de dados estruturados (JSON) de um mês/ano,
# pensado pra ser colado numa conversa ou anexado a um prompt de análise —
# não precisa ser bonito, precisa ser completo e sem ambiguidade. Compõe
# dados que já existem em outros endpoints (nenhuma agregação nova aqui),
# só resolve nomes e empacota numa resposta só.

_ESTRUTURA_LABEL = {"fixo": "Fixo", "variavel": "Variável", "sazonal": "Sazonal", "investimentos": "Investimentos"}


def _mapas_de_nomes(db: Client, user_id: str) -> dict[str, dict[str, str]]:
    categorias = db.table("categorias").select("id,nome").eq("user_id", user_id).execute().data
    subcategorias = db.table("subcategorias").select("id,nome").eq("user_id", user_id).execute().data
    contas = db.table("contas").select("id,nome").eq("user_id", user_id).execute().data
    caixinhas = db.table("caixinhas").select("id,nome").eq("user_id", user_id).execute().data
    return {
        "categoria": {c["id"]: c["nome"] for c in categorias},
        "subcategoria": {s["id"]: s["nome"] for s in subcategorias},
        "conta": {c["id"]: c["nome"] for c in contas},
        "caixinha": {c["id"]: c["nome"] for c in caixinhas},
    }


def _lancamentos_exportados(
    db: Client, user_id: str, data_inicio: date, data_fim: date, nomes: dict[str, dict[str, str]]
) -> list[LancamentoExportado]:
    linhas = transacoes.listar(db=db, user_id=user_id, data_inicio=data_inicio, data_fim=data_fim)
    resultado = []
    for linha in linhas:
        resultado.append(
            {
                **linha,
                "categoria_nome": nomes["categoria"].get(linha.get("categoria_id") or "") if linha.get("categoria_id") else None,
                "subcategoria_nome": nomes["subcategoria"].get(linha.get("subcategoria_id") or "")
                if linha.get("subcategoria_id")
                else None,
                "conta_nome": nomes["conta"].get(linha.get("conta_id") or "") if linha.get("conta_id") else None,
                "caixinha_nome": nomes["caixinha"].get(linha.get("caixinha_id") or "") if linha.get("caixinha_id") else None,
                "caixinha_origem_nome": nomes["caixinha"].get(linha.get("caixinha_origem_id") or "")
                if linha.get("caixinha_origem_id")
                else None,
            }
        )
    return resultado


@router.get("/mes/{vigencia_mes}", response_model=RelatorioMensal)
def relatorio_mensal(vigencia_mes: date, db: Client = Depends(get_db), user_id: str = Depends(get_current_user_id)):
    mes_inicio = date(vigencia_mes.year, vigencia_mes.month, 1)
    mes_fim_exclusiva = somar_meses(mes_inicio, 1)
    ultimo_dia = mes_fim_exclusiva - timedelta(days=1)
    nomes = _mapas_de_nomes(db, user_id)

    resumo = dashboard.resumo_mensal(vigencia_mes=mes_inicio, db=db, user_id=user_id)
    retiradas = [t for t in transacoes.retiradas_pendentes(db=db, user_id=user_id) if mes_inicio <= date.fromisoformat(t["data_compra"]) <= ultimo_dia]

    return {
        "periodo": {"tipo": "mes", "inicio": mes_inicio, "fim": ultimo_dia},
        "resumo": resumo,
        "lancamentos": _lancamentos_exportados(db, user_id, mes_inicio, ultimo_dia, nomes),
        "despesas_por_categoria": dashboard.despesas_por_categoria(vigencia_mes=mes_inicio, db=db, user_id=user_id),
        "despesas_por_subcategoria": dashboard.despesas_por_subcategoria(vigencia_mes=mes_inicio, db=db, user_id=user_id),
        "estrutura_custo": estrutura_custo.obter(vigencia_mes=mes_inicio, db=db, user_id=user_id),
        "caixinhas_patrimonio": dashboard.patrimonio_caixinhas(vigencia_mes=mes_inicio, db=db, user_id=user_id),
        "retiradas_pendentes": retiradas,
    }


@router.get("/ano/{ano}", response_model=RelatorioAnual)
def relatorio_anual(ano: int, db: Client = Depends(get_db), user_id: str = Depends(get_current_user_id)):
    inicio = date(ano, 1, 1)
    fim = date(ano, 12, 1)
    ultimo_dia = date(ano, 12, 31)
    nomes = _mapas_de_nomes(db, user_id)

    evolucao = dashboard.evolucao_mensal(inicio=inicio, fim=fim, db=db, user_id=user_id)

    # mesmo padrão de perf de evolucao_orcamento() (estrutura_custo.py,
    # Rodada 2026-09-22/27) — 1 busca em lote pro ano inteiro, não 12
    # chamadas sequenciais de obter() (3 idas ao banco cada). Achado
    # 2026-10-21: usuário notou lentidão real gerando o export "Ano
    # inteiro". cache_saldo compartilhado entre os 12 meses, mesma razão.
    orcamento_por_mes, itens_por_orcamento_id, transacoes_por_mes = carregar_dados_periodo(db, user_id, inicio, fim)
    cache_saldo: dict = {}
    estrutura_mensal = []
    for mes in range(1, 13):
        mes_inicio_do_bucket = date(ano, mes, 1)
        estrutura = estrutura_custo._estrutura_custo_do_mes_em_lote(
            mes_inicio_do_bucket, orcamento_por_mes, itens_por_orcamento_id, transacoes_por_mes, cache_saldo
        )
        estrutura_custo._enriquecer_saldo_reservas(db, user_id, mes_inicio_do_bucket, estrutura)
        estrutura_mensal.append(estrutura)

    retiradas = [t for t in transacoes.retiradas_pendentes(db=db, user_id=user_id) if inicio <= date.fromisoformat(t["data_compra"]) <= ultimo_dia]

    return {
        "periodo": {"tipo": "ano", "inicio": inicio, "fim": ultimo_dia},
        "resumo": dashboard.resumo_periodo(inicio=inicio, fim=fim, db=db, user_id=user_id),
        "evolucao_mensal": evolucao["meses"],
        "lancamentos": _lancamentos_exportados(db, user_id, inicio, ultimo_dia, nomes),
        "despesas_por_categoria": dashboard.despesas_por_categoria_periodo(inicio=inicio, fim=fim, db=db, user_id=user_id),
        "despesas_por_subcategoria": dashboard.despesas_por_subcategoria_periodo(inicio=inicio, fim=fim, db=db, user_id=user_id),
        "estrutura_custo_mensal": estrutura_mensal,
        "caixinhas_patrimonio": dashboard.patrimonio_caixinhas(vigencia_mes=date(ano, 12, 1), db=db, user_id=user_id),
        "retiradas_pendentes": retiradas,
    }
