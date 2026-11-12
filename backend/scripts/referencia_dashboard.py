"""Calcula, a partir do CSV histórico ("Lançamentos Calculado"), os
mesmos parâmetros que o Dashboard do app mostra — pra servir de
referência independente na hora de testar a aplicação de verdade.
Desde 2026-10-01 também calcula o REALIZADO por bucket (Estrutura de
Custo/Planejamento) — ver "Limitação importante" abaixo.

Importante: os cálculos aqui são uma reimplementação DELIBERADAMENTE
independente das regras de negócio (fluxo de caixa vs saúde financeira,
reserva vs investimento, bucket de estrutura de custo, etc. — ver
README.md/docs/backlog.md pro racional de cada uma), não uma cópia do
código de `app/services/resumo_financeiro.py`,
`app/routers/estrutura_custo.py` ou dos demais routers. O objetivo é
ter um segundo cálculo, feito do zero a partir da regra escrita, pra
comparar contra o que a aplicação responde de verdade — se os dois
baterem, tanto a regra quanto a implementação estão alinhadas; se não
baterem, aponta pra revisar um dos dois lados.

Reaproveita só a camada de PARSING/interpretação do CSV
(scripts/migracao/parsing.py, mapeamento.py, parcelas.py, overrides.py)
— já validada durante a migração real (reconciliação bateu, ver
docs/backlog.md) — porque "ler a linha do CSV corretamente" (incluindo
resolver qual bucket de estrutura de custo uma linha de despesa tinha)
não é a regra de negócio que este script quer conferir, é só leitura de
dado. A regra de NEGÓCIO (como agregar isso em "realizado por bucket",
com que sinal cada tipo de movimento entra) é reimplementada aqui do
zero, à parte.

**Limitação importante — o que este script NÃO consegue validar:**
ele só calcula o lado REALIZADO (o que de fato foi gasto/investido,
derivado 100% do histórico de transações do CSV). O lado ORÇADO —
teto por bucket (`receita_base × percentual_geral% × limite_bucket%`),
`orcamento_mensal` de cada item, e a cadeia de `saldo_anterior` do
modo envelope — não existe no CSV histórico: é configuração que o
usuário digita direto no Planejamento do app (vive só no Supabase).
Então este script serve pra conferir a coluna "Realizado" de Estrutura
de Custo/Planejamento, não a coluna "Orçado" nem o `saldo_anterior`
acumulado — essas duas precisam de verificação manual (ver
`docs/backlog.md`, item relacionado ao racional de testes com esta
skill).

Não lê nem grava nenhum arquivo do repositório além do CSV passado por
--csv e, opcionalmente, do arquivo de overrides de estrutura de custo
(ambos dado financeiro pessoal, nunca devem ser commitados — ver
`docs/backlog.md`, "Migração de dados do app antigo"). A saída (JSON)
também não deve ser commitada — é resultado, não código.

Uso:
    cd backend
    source venv/bin/activate
    python scripts/referencia_dashboard.py --csv /caminho/Lancamentos.csv > referencia.json

Opções:
    --hoje AAAA-MM-DD   data de referência pra "Compromissos Futuros"
                        (default: hoje real do sistema)
    --overrides CAMINHO arquivo de respostas da estrutura de custo
                        ambígua (mesmo formato/arquivo usado na migração
                        real, `scripts/migracao_overrides.json` por
                        padrão, se existir). Sem ele, despesas cuja
                        estrutura de custo não vinha no CSV nem tinha
                        um valor único aprendido por subcategoria caem
                        em "sem_estrutura" na referência, mesmo que o
                        app real (que usou os overrides na migração)
                        mostre um bucket concreto pra elas — isso
                        aparece num aviso no stderr, não é bug do
                        script.
"""
from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict
from dataclasses import dataclass
from datetime import date
from pathlib import Path

sys.path.insert(0, ".")
from scripts.migracao.mapeamento import (  # noqa: E402
    aprender_estrutura_custo_por_subcategoria,
    resolver_estrutura_custo,
    resolver_tipo_movimento,
    resolver_valor,
)
from scripts.migracao.overrides import CAMINHO_PADRAO as CAMINHO_OVERRIDES_PADRAO  # noqa: E402
from scripts.migracao.overrides import carregar as carregar_overrides  # noqa: E402
from scripts.migracao.overrides import chave_linha  # noqa: E402
from scripts.migracao.parcelas import agrupar_parcelas  # noqa: E402
from scripts.migracao.parsing import Lancamento, carregar_lancamentos  # noqa: E402

# mesmo vocabulário de bucket de app/routers/estrutura_custo.py — a
# aplicação/retirada decide o bucket pela presença de caixinha, nunca
# por `estrutura_custo` (esse campo só importa pra despesa)
_BUCKET_POR_ESTRUTURA_CUSTO: dict[str, str] = {
    "fixo": "custos_fixos",
    "variavel": "custos_variaveis",
    "sazonal": "sazonalidades",
}
_BUCKETS_ESTRUTURA_CUSTO = (
    "custos_fixos",
    "custos_variaveis",
    "sazonalidades",
    "investimentos",
    "reservas",
    "sem_estrutura",
)
_SINAL_REALIZADO_ESTRUTURA_CUSTO: dict[str, int] = {
    "despesa": 1,
    "estorno": -1,
    "ressarcimento": -1,
    "aplicacao": 1,
    "retirada": -1,
}


@dataclass
class Movimento:
    """Uma transação já traduzida pro vocabulário do app — só os campos
    que as fórmulas do Dashboard usam. Nada aqui depende de conta_id,
    banco ou meio de pagamento (o Dashboard não agrupa por isso)."""

    data: date
    valor: float
    tipo_movimento: str  # receita | despesa | estorno | ressarcimento | aplicacao | retirada
    categoria: str
    caixinha: str  # "" = sem caixinha (investimento, não reserva)
    # a migração nunca vincula estorno/ressarcimento a uma despesa
    # específica (o CSV antigo não guardava esse vínculo) — todo ajuste
    # migrado é "solto". Ver docs/backlog.md.
    tem_ajuste_vinculado: bool = False
    # só preenchido pra despesa — aplicação/retirada decide o bucket pela
    # caixinha, nunca por isso (ver _BUCKET_POR_ESTRUTURA_CUSTO). `None` =
    # despesa sem estrutura resolvida (nem literal do CSV, nem aprendida
    # por subcategoria, nem em overrides) — vira bucket "sem_estrutura".
    estrutura_custo: str | None = None

    @property
    def tem_caixinha(self) -> bool:
        return bool(self.caixinha)


def bucket_da_transacao(m: Movimento) -> str:
    """Mesma regra de app/routers/estrutura_custo.py::_bucket_da_transacao
    — reimplementada do zero, não importada de lá."""
    if m.tipo_movimento in ("aplicacao", "retirada"):
        return "reservas" if m.tem_caixinha else "investimentos"
    if m.estrutura_custo:
        return _BUCKET_POR_ESTRUTURA_CUSTO[m.estrutura_custo]
    return "sem_estrutura"


def realizado_por_bucket_e_mes(movimentos: list[Movimento]) -> dict[str, dict[str, float]]:
    """Soma de sinal×valor por bucket, por mês — mesma regra de
    app/routers/estrutura_custo.py::_agregar_estrutura_custo (sem o lado
    orçado, que não existe no CSV — ver limitação no topo do arquivo).
    Receita não entra em bucket nenhum (mesmo filtro do app real)."""
    totais: dict[date, dict[str, float]] = defaultdict(lambda: defaultdict(float))
    for m in movimentos:
        if m.tipo_movimento == "receita":
            continue
        sinal = _SINAL_REALIZADO_ESTRUTURA_CUSTO.get(m.tipo_movimento, 0)
        totais[_mes(m.data)][bucket_da_transacao(m)] += sinal * m.valor
    return {
        mes.isoformat(): {b: round(buckets.get(b, 0.0), 2) for b in _BUCKETS_ESTRUTURA_CUSTO}
        for mes, buckets in totais.items()
    }


def _mes(d: date) -> date:
    return date(d.year, d.month, 1)


def _somar_mes(d: date, n: int) -> date:
    mes_total = (d.year * 12 + (d.month - 1)) + n
    return date(mes_total // 12, mes_total % 12 + 1, 1)


def traduzir(lancamentos: list[Lancamento], overrides: dict[str, str | None] | None = None) -> list[Movimento]:
    """`overrides` (opcional) é o mesmo arquivo usado na migração real
    pra resolver estrutura de custo ambígua — sem ele, linhas ambíguas
    ficam com `estrutura_custo=None` (bucket "sem_estrutura" na
    referência, mesmo que o app real já tenha resolvido via override na
    migração — ver aviso impresso por `main()`)."""
    overrides = overrides or {}
    aprendido = aprender_estrutura_custo_por_subcategoria(lancamentos)
    movimentos = []
    for l in lancamentos:
        tipo = resolver_tipo_movimento(l.movimentacao, l.tipo_pag_movimento)
        estrutura_custo = resolver_estrutura_custo(l, aprendido, overrides, chave_linha(l))
        movimentos.append(
            Movimento(
                data=l.data,
                valor=resolver_valor(l.valor),
                tipo_movimento=tipo,
                categoria=l.categoria,
                caixinha=l.caixinha.strip(),
                estrutura_custo=estrutura_custo,
            )
        )
    return movimentos


def calcular_resumo(movimentos: list[Movimento]) -> dict:
    """Reimplementação independente da regra "fluxo de caixa vs saúde
    financeira":

    - Fluxo de caixa (bruto): o que de fato entrou/saiu, sem ajuste
      nenhum. resultado_fluxo_caixa = receitas - despesas_brutas.
    - Saúde financeira (líquida): um estorno/ressarcimento VINCULADO a
      uma despesa desfaz parte daquela despesa (reduz despesas_liquidas,
      não é receita nova); um ajuste SOLTO não desfaz nada específico,
      então conta como receita extra (receita_ajustada).
    - Reserva = aplicação/retirada COM caixinha; investimento = SEM
      caixinha — mesmo tipo_movimento, propósito diferente.
    """
    receitas = despesas_brutas = 0.0
    ajustes_vinculados = ajustes_nao_vinculados = 0.0
    aplicacoes = retiradas = 0.0
    aplicacoes_reserva = retiradas_reserva = 0.0
    aplicacoes_investimento = retiradas_investimento = 0.0

    for m in movimentos:
        if m.tipo_movimento == "receita":
            receitas += m.valor
        elif m.tipo_movimento == "despesa":
            despesas_brutas += m.valor
        elif m.tipo_movimento in ("estorno", "ressarcimento"):
            if m.tem_ajuste_vinculado:
                ajustes_vinculados += m.valor
            else:
                ajustes_nao_vinculados += m.valor
        elif m.tipo_movimento == "aplicacao":
            aplicacoes += m.valor
            if m.tem_caixinha:
                aplicacoes_reserva += m.valor
            else:
                aplicacoes_investimento += m.valor
        elif m.tipo_movimento == "retirada":
            retiradas += m.valor
            if m.tem_caixinha:
                retiradas_reserva += m.valor
            else:
                retiradas_investimento += m.valor

    despesas_liquidas = round(despesas_brutas - ajustes_vinculados, 2)
    receita_ajustada = round(receitas + ajustes_nao_vinculados, 2)
    resultado_saude = round(receita_ajustada - despesas_liquidas, 2)

    return {
        "receitas": round(receitas, 2),
        "despesas_brutas": round(despesas_brutas, 2),
        "despesas_liquidas": despesas_liquidas,
        "ajustes_vinculados": round(ajustes_vinculados, 2),
        "ajustes_nao_vinculados": round(ajustes_nao_vinculados, 2),
        "aplicacoes": round(aplicacoes, 2),
        "retiradas": round(retiradas, 2),
        "reservas": round(aplicacoes_reserva - retiradas_reserva, 2),
        "investimentos": round(aplicacoes_investimento - retiradas_investimento, 2),
        "resultado_fluxo_caixa": round(receitas - despesas_brutas, 2),
        "resultado_saude": resultado_saude,
        "taxa_poupanca": round(resultado_saude / receita_ajustada * 100, 2) if receita_ajustada else None,
        "_receita_ajustada": receita_ajustada,
    }


def despesas_por_categoria(movimentos: list[Movimento]) -> list[dict]:
    totais: dict[str, float] = defaultdict(float)
    for m in movimentos:
        if m.tipo_movimento == "despesa":
            totais[m.categoria or "Sem categoria"] += m.valor
    total_geral = sum(totais.values())
    resultado = [
        {
            "categoria_nome": nome,
            "valor": round(valor, 2),
            "percentual": round(valor / total_geral * 100, 2) if total_geral else 0.0,
        }
        for nome, valor in totais.items()
    ]
    resultado.sort(key=lambda r: r["valor"], reverse=True)
    return resultado


def patrimonio_caixinhas_por_mes(movimentos: list[Movimento], meses: list[date]) -> dict[str, dict[str, float]]:
    """Saldo de cada caixinha (aplicação - retirada, "desde sempre") ao
    fim de cada mês da lista — mesma regra de
    app/routers/dashboard.py:patrimonio_caixinhas (RPC saldo_caixinhas).
    `meses` já ordenados; o saldo de cada mês inclui tudo até o fim
    dele, então basta acumular andando em ordem cronológica."""
    saldo_atual: dict[str, float] = defaultdict(float)
    resultado: dict[str, dict[str, float]] = {}
    por_mes: dict[date, list[Movimento]] = defaultdict(list)
    for m in movimentos:
        if m.tem_caixinha and m.tipo_movimento in ("aplicacao", "retirada"):
            por_mes[_mes(m.data)].append(m)

    for mes in meses:
        for m in por_mes.get(mes, []):
            saldo_atual[m.caixinha] += m.valor if m.tipo_movimento == "aplicacao" else -m.valor
        resultado[mes.isoformat()] = {nome: round(saldo, 2) for nome, saldo in saldo_atual.items()}
    return resultado


def montar_referencia(movimentos: list[Movimento]) -> dict:
    if not movimentos:
        return {"meses": {}, "primeiro_mes": None, "ultimo_mes": None}

    por_mes: dict[date, list[Movimento]] = defaultdict(list)
    for m in movimentos:
        por_mes[_mes(m.data)].append(m)

    primeiro_mes = min(por_mes)
    ultimo_mes = max(por_mes)

    # acumulado "no ano" — mesma janela usada por /dashboard/evolucao no
    # card de taxa/resultado acumulado e "meses com resultado negativo":
    # sempre janeiro do ano do mês até o próprio mês, contando TODO mês
    # calendário do intervalo (mesmo sem transação nenhuma nele), não só
    # os meses com dado.
    resultado_acumulado_ano: dict[int, float] = defaultdict(float)
    receita_ajustada_acumulada_ano: dict[int, float] = defaultdict(float)
    negativos_ano: dict[int, int] = defaultdict(int)
    meses_no_ano_contados: dict[int, int] = defaultdict(int)

    meses_saida: dict[str, dict] = {}
    todos_os_meses: list[date] = []
    # o loop andando desde janeiro do ano (não desde primeiro_mes) é só
    # pra "total_meses_no_ano_até_aqui" bater com o app real — /dashboard/
    # evolucao sempre varre de janeiro, então dezembro/2025 (1º mês real
    # do CSV) mostra "12 meses no ano" mesmo sem ter existido antes disso.
    # Só NÃO expõe meses anteriores a primeiro_mes como entrada de saída
    # (não existiram, não faz sentido aparecer no seletor do mock).
    mes_atual = date(primeiro_mes.year, 1, 1)
    while mes_atual <= ultimo_mes:
        resumo = calcular_resumo(por_mes.get(mes_atual, []))
        receita_ajustada = resumo.pop("_receita_ajustada")

        ano = mes_atual.year
        resultado_acumulado_ano[ano] = round(resultado_acumulado_ano[ano] + resumo["resultado_saude"], 2)
        receita_ajustada_acumulada_ano[ano] = round(receita_ajustada_acumulada_ano[ano] + receita_ajustada, 2)
        if resumo["resultado_saude"] < 0:
            negativos_ano[ano] += 1
        meses_no_ano_contados[ano] += 1

        if mes_atual >= primeiro_mes:
            todos_os_meses.append(mes_atual)
            despesas_cat = despesas_por_categoria(por_mes.get(mes_atual, []))
            meses_saida[mes_atual.isoformat()] = {
                **resumo,
                "resultado_saude_acumulado_no_ano": resultado_acumulado_ano[ano],
                "taxa_poupanca_acumulada_no_ano": (
                    round(resultado_acumulado_ano[ano] / receita_ajustada_acumulada_ano[ano] * 100, 2)
                    if receita_ajustada_acumulada_ano[ano]
                    else None
                ),
                "meses_negativos_no_ano_até_aqui": negativos_ano[ano],
                "total_meses_no_ano_até_aqui": meses_no_ano_contados[ano],
                "despesas_por_categoria": despesas_cat,
                "maior_categoria_despesa": despesas_cat[0] if despesas_cat else None,
            }
        mes_atual = _somar_mes(mes_atual, 1)

    caixinhas_por_mes = patrimonio_caixinhas_por_mes(movimentos, todos_os_meses)
    for chave_mes, saldos in caixinhas_por_mes.items():
        meses_saida[chave_mes]["patrimonio_caixinhas"] = saldos

    # realizado por bucket (Estrutura de Custo/Planejamento) — só o lado
    # realizado, ver limitação no topo do arquivo (orçado/saldo_anterior
    # não existem no CSV)
    realizado_bucket_por_mes = realizado_por_bucket_e_mes(movimentos)
    for chave_mes in meses_saida:
        meses_saida[chave_mes]["realizado_por_bucket"] = realizado_bucket_por_mes.get(
            chave_mes, dict.fromkeys(_BUCKETS_ESTRUTURA_CUSTO, 0.0)
        )

    return {
        "meses": meses_saida,
        "primeiro_mes": primeiro_mes.isoformat(),
        "ultimo_mes": ultimo_mes.isoformat(),
    }


def compromissos_futuros(lancamentos: list[Lancamento], hoje: date) -> list[dict]:
    """Mesma regra de app/routers/dashboard.py:compromissos_futuros:
    olha só as parcelas com data > hoje (ainda não venceram), agrupadas
    por compra parcelada (agrupar_parcelas reconstrói esse vínculo, que
    o CSV original não guarda), e mostra só a PRÓXIMA parcela em aberto
    de cada grupo — não a lista inteira do que falta pagar."""
    grupos, _ = agrupar_parcelas(lancamentos)
    compromissos = []
    for grupo in grupos:
        futuras = [(n, l) for n, l in grupo.itens if l.data > hoje]
        if not futuras:
            continue
        n, proxima = min(futuras, key=lambda par: par[1].data)
        compromissos.append(
            {
                "descricao": proxima.descricao,
                "valor": resolver_valor(proxima.valor),
                "data_compra": proxima.data.isoformat(),
                "parcela_atual": n,
                "parcela_total": grupo.parcela_total,
            }
        )
    compromissos.sort(key=lambda c: c["data_compra"])
    return compromissos


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--csv", required=True, help="Caminho do CSV 'Lançamentos Calculado'")
    parser.add_argument("--hoje", default=None, help="AAAA-MM-DD — default: hoje real")
    parser.add_argument(
        "--overrides",
        default=str(CAMINHO_OVERRIDES_PADRAO),
        help=(
            "Caminho do arquivo de overrides de estrutura de custo "
            f"(default: {CAMINHO_OVERRIDES_PADRAO}, mesmo usado na migração real; "
            "se não existir, segue sem — ver aviso no stderr)"
        ),
    )
    args = parser.parse_args()

    hoje = date.fromisoformat(args.hoje) if args.hoje else date.today()

    lancamentos, puladas = carregar_lancamentos(args.csv)
    overrides = carregar_overrides(Path(args.overrides))
    movimentos = traduzir(lancamentos, overrides)

    despesas_sem_estrutura = sum(
        1 for m in movimentos if m.tipo_movimento == "despesa" and m.estrutura_custo is None
    )
    if despesas_sem_estrutura:
        print(
            f"[aviso] {despesas_sem_estrutura} despesa(s) sem estrutura de custo resolvida "
            f"(nem literal, nem aprendida, nem em '{args.overrides}') — entram como "
            "'sem_estrutura' na referência, mas o app real pode já ter resolvido isso via "
            "overrides na migração. Passe --overrides com o arquivo correto se a comparação "
            "não bater nesse bucket.",
            file=sys.stderr,
        )

    referencia = montar_referencia(movimentos)
    referencia["linhas_csv_ignoradas"] = len(puladas)
    referencia["total_lancamentos"] = len(lancamentos)
    referencia["hoje_referencia"] = hoje.isoformat()
    referencia["compromissos_futuros"] = compromissos_futuros(lancamentos, hoje)

    # "Todos os meses" do seletor do Dashboard = do 1º lançamento até o
    # mês de referência (hoje) — soma tudo de uma vez, não é a soma dos
    # resumos mensais (taxa_poupanca é recalculada sobre o total).
    if movimentos:
        mes_fim_exclusivo = _somar_mes(_mes(hoje), 1)
        ate_hoje = [m for m in movimentos if m.data < mes_fim_exclusivo]
        resumo_todos_os_meses = calcular_resumo(ate_hoje)
        resumo_todos_os_meses.pop("_receita_ajustada")
        resumo_todos_os_meses["despesas_por_categoria"] = despesas_por_categoria(ate_hoje)
        referencia["todos_os_meses_ate_hoje"] = resumo_todos_os_meses

    print(json.dumps(referencia, ensure_ascii=False, indent=2, default=str))


if __name__ == "__main__":
    main()
