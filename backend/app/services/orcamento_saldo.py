"""Cálculo de realizado e saldo_anterior de um item de orçamento — usado
tanto por routers/orcamentos.py (validação de teto, envelope de cada item)
quanto por routers/estrutura_custo.py (saldo acumulado por bucket, teto do
pool/piso).

saldo_anterior nunca é confiável direto da coluna gravada: ela só é
atualizada no momento em que "gerar próximo mês" roda, então editar ou
lançar algo no mês anterior DEPOIS de já ter gerado o mês seguinte deixa
esse valor congelado (era o bug reportado: item de agosto mudou, setembro
continuava com o saldo antigo até alguém clicar "gerar" de novo). Em vez
de gravar-e-confiar, cada leitura recalcula subindo a cadeia de meses
anteriores até achar o primeiro mês (sem orçamento anterior) ou um item
sem vínculo (categoria/subcategoria/conta — aí não tem como achar o
equivalente do mês anterior, mantém o valor gravado como estava).

Só existe a versão "em lote" (100% em memória sobre dados pré-carregados
por `carregar_dados_periodo`) — a versão que consultava o banco a cada
passo da cadeia (`saldo_anterior_ao_vivo`) foi removida em 2026-09-25
(Rodada 29): era o último lugar do código ainda com essa classe de bug de
N+1 requisições (mesma raiz já corrigida em `/graficos`, Rodada
2026-09-22, e em Estrutura de Custo, Rodada 27) — cada item de orçamento
em `routers/orcamentos.py` subia sua própria cadeia de meses anteriores
direto no banco, 3 SELECTs por mês subido."""
from __future__ import annotations

from datetime import date

from supabase import Client

from .fatura import somar_meses

ITENS_TABLE = "orcamento_itens"
ORCAMENTOS_TABLE = "orcamentos"

# mesmo sinal de orcamentos.py — despesa conta a favor do gasto,
# estorno/ressarcimento reduz (é dinheiro devolvido); aplicacao/retirada só
# entram para itens de investimento (via conta_vinculada_id)
_SINAL_REALIZADO = {
    "despesa": 1,
    "estorno": -1,
    "ressarcimento": -1,
    "aplicacao": 1,
    "retirada": -1,
}


def calcular_realizado_item(db: Client, user_id: str, item: dict, mes_inicio: date, mes_fim: date) -> float:
    """Soma as transações do período que contam para este item — por
    subcategoria/categoria para os buckets de custo, ou pela conta vinculada
    para itens de investimento. Sem nenhum dos três vínculos, não há como
    calcular realizado (o item é só uma linha de planejamento livre).

    Checa subcategoria antes de categoria: um item criado a partir da tela
    de Planejamento pode ter os dois campos preenchidos ao mesmo tempo
    (formulário sempre manda a categoria pai junto quando escolhe
    subcategoria), e filtrar por categoria primeiro puxaria transações de
    outras subcategorias da mesma categoria pai — mesma lógica de
    estrutura_custo._chave. A exclusão de subcategoria no caso "só
    categoria" é feita em Python (não com .is_() do postgrest) — mesmo
    filtro final, sem depender de mais um operador da query builder."""
    if item.get("subcategoria_id"):
        linhas = (
            db.table("transacoes")
            .select("valor,tipo_movimento")
            .eq("user_id", user_id)
            .gte("data_compra", mes_inicio.isoformat())
            .lt("data_compra", mes_fim.isoformat())
            .eq("subcategoria_id", item["subcategoria_id"])
            .execute()
            .data
        )
    elif item.get("categoria_id"):
        candidatas = (
            db.table("transacoes")
            .select("valor,tipo_movimento,subcategoria_id")
            .eq("user_id", user_id)
            .gte("data_compra", mes_inicio.isoformat())
            .lt("data_compra", mes_fim.isoformat())
            .eq("categoria_id", item["categoria_id"])
            .execute()
            .data
        )
        linhas = [t for t in candidatas if not t.get("subcategoria_id")]
    elif item.get("conta_vinculada_id"):
        linhas = (
            db.table("transacoes")
            .select("valor,tipo_movimento")
            .eq("user_id", user_id)
            .gte("data_compra", mes_inicio.isoformat())
            .lt("data_compra", mes_fim.isoformat())
            .eq("conta_id", item["conta_vinculada_id"])
            .execute()
            .data
        )
    else:
        return 0.0

    total = sum(_SINAL_REALIZADO.get(t["tipo_movimento"], 0) * t["valor"] for t in linhas)
    return round(total, 2)


def calcular_realizado_item_em_lote(item: dict, transacoes_do_mes: list[dict]) -> float:
    """Mesma regra de calcular_realizado_item (subcategoria > categoria >
    conta vinculada, excluindo de "só categoria" o que já tem subcategoria
    própria), mas filtrando em memória sobre uma lista de transações do mês
    JÁ CARREGADA, em vez de consultar o banco — usado por
    /estrutura-custo/evolucao/tendencia, que pré-carrega o período inteiro
    de uma vez (ver saldo_anterior_em_lote)."""
    if item.get("subcategoria_id"):
        linhas = [t for t in transacoes_do_mes if t.get("subcategoria_id") == item["subcategoria_id"]]
    elif item.get("categoria_id"):
        linhas = [
            t
            for t in transacoes_do_mes
            if t.get("categoria_id") == item["categoria_id"] and not t.get("subcategoria_id")
        ]
    elif item.get("conta_vinculada_id"):
        linhas = [t for t in transacoes_do_mes if t.get("conta_id") == item["conta_vinculada_id"]]
    else:
        return 0.0

    total = sum(_SINAL_REALIZADO.get(t["tipo_movimento"], 0) * t["valor"] for t in linhas)
    return round(total, 2)


def _item_equivalente_no_mes_em_lote(itens_do_orcamento: list[dict], item: dict) -> dict | None:
    """Acha, dentro dos itens de um orçamento de outro mês (já carregados
    em memória), o item do mesmo bucket com a mesma categoria/subcategoria/
    conta vinculada — o "mesmo envelope" em outro mês. Sem nenhum vínculo
    (item nome-livre) não há como achar, retorna None."""
    if item.get("subcategoria_id"):
        chave = ("subcategoria_id", item["subcategoria_id"])
    elif item.get("categoria_id"):
        chave = ("categoria_id", item["categoria_id"])
    elif item.get("conta_vinculada_id"):
        chave = ("conta_vinculada_id", item["conta_vinculada_id"])
    else:
        return None

    campo, valor = chave
    for candidato in itens_do_orcamento:
        if candidato.get("bucket") == item["bucket"] and candidato.get(campo) == valor:
            return candidato
    return None


def saldo_anterior_em_lote(
    item: dict,
    vigencia_mes_item: date,
    orcamento_por_mes: dict[str, dict],
    itens_por_orcamento_id: dict[str, list[dict]],
    transacoes_por_mes: dict[str, list[dict]],
    cache: dict[tuple, float],
) -> float:
    """Cálculo recursivo de saldo_anterior (mesma regra, mesmo racional —
    ver docstring do módulo), 100% em memória sobre dados pré-carregados em
    lote pra um período inteiro (`carregar_dados_periodo`), sem nenhuma
    consulta ao banco aqui dentro. Usada por `routers/estrutura_custo.py`
    e `routers/orcamentos.py` — pedir vários itens/meses de uma vez não
    pode custar 1 ida-e-volta ao Supabase por item×mês (era o gargalo real
    de "Gráficos", depois de Estrutura de Custo, depois de Planejamento —
    ver Rodadas 2026-09-22, 27 e 29)."""
    sem_vinculo = not (item.get("subcategoria_id") or item.get("categoria_id") or item.get("conta_vinculada_id"))
    if sem_vinculo:
        return item.get("saldo_anterior", 0)

    chave_cache = (
        item.get("bucket"),
        item.get("categoria_id"),
        item.get("subcategoria_id"),
        item.get("conta_vinculada_id"),
        vigencia_mes_item.isoformat(),
    )
    if chave_cache in cache:
        return cache[chave_cache]

    mes_anterior = somar_meses(vigencia_mes_item, -1)
    orcamento_anterior = orcamento_por_mes.get(mes_anterior.isoformat())
    if orcamento_anterior is None:
        cache[chave_cache] = 0.0
        return 0.0

    item_anterior = _item_equivalente_no_mes_em_lote(itens_por_orcamento_id.get(orcamento_anterior["id"], []), item)
    if item_anterior is None:
        cache[chave_cache] = 0.0
        return 0.0

    saldo_do_anterior = saldo_anterior_em_lote(
        item_anterior, mes_anterior, orcamento_por_mes, itens_por_orcamento_id, transacoes_por_mes, cache
    )
    disponivel_anterior = round(item_anterior["orcamento_mensal"] + saldo_do_anterior, 2)
    realizado_anterior = calcular_realizado_item_em_lote(
        item_anterior, transacoes_por_mes.get(mes_anterior.isoformat(), [])
    )
    resultado = round(disponivel_anterior - realizado_anterior, 2)
    cache[chave_cache] = resultado
    return resultado


def carregar_dados_periodo(
    db: Client, user_id: str, mes_inicio: date, mes_fim: date
) -> tuple[dict[str, dict], dict[str, list[dict]], dict[str, list[dict]]]:
    """Busca em lote (3 SELECTs fixos, não 1 grupo de 3 por mês) tudo que
    `saldo_anterior_em_lote`/`calcular_realizado_item_em_lote` precisam pra
    montar qualquer mês do intervalo — incluindo a cadeia de
    `saldo_anterior` recursiva, que pode subir arbitrariamente antes de
    `mes_inicio`. Compartilhada por `routers/estrutura_custo.py` (`obter()`,
    1 mês, e `evolucao_orcamento()`, vários) e `routers/orcamentos.py`
    (`_enriquecer_item`/`_validar_teto_bucket`) — movida pra cá em
    2026-09-25 (Rodada 29) quando o mesmo fix de perf (Rodada 27, Estrutura
    de Custo) foi portado pra Planejamento: antes disso, cada leitura de
    item de orçamento em `orcamentos.py` subia a cadeia de meses anteriores
    DIRETO NO BANCO (`saldo_anterior_ao_vivo`, removida), 3 SELECTs por mês
    subido × N itens da lista — `GET /orcamentos/{id}/itens` virava dezenas
    de idas e voltas sequenciais ao Supabase por requisição."""
    todos_orcamentos = db.table(ORCAMENTOS_TABLE).select("*").eq("user_id", user_id).execute().data
    orcamento_por_mes = {o["vigencia_mes"]: o for o in todos_orcamentos}

    itens_por_orcamento_id: dict[str, list[dict]] = {}
    orcamento_ids = [o["id"] for o in todos_orcamentos]
    if orcamento_ids:
        todos_itens = (
            db.table(ITENS_TABLE).select("*").in_("orcamento_id", orcamento_ids).eq("ativo", True).execute().data
        )
        for item in todos_itens:
            itens_por_orcamento_id.setdefault(item["orcamento_id"], []).append(item)

    # transações: do mais antigo entre `mes_inicio` e o orçamento mais
    # antigo (a cadeia de saldo_anterior de um mês do período pode
    # precisar do realizado de um mês ANTES de `mes_inicio`) até `mes_fim`
    transacoes_inicio = mes_inicio
    if todos_orcamentos:
        mes_orcamento_mais_antigo = min(date.fromisoformat(o["vigencia_mes"]) for o in todos_orcamentos)
        transacoes_inicio = min(transacoes_inicio, mes_orcamento_mais_antigo)
    mes_fim_exclusivo = somar_meses(mes_fim, 1)
    todas_transacoes = (
        db.table("transacoes")
        .select("valor,tipo_movimento,estrutura_custo,categoria_id,subcategoria_id,conta_id,caixinha_id,data_compra")
        .eq("user_id", user_id)
        .gte("data_compra", transacoes_inicio.isoformat())
        .lt("data_compra", mes_fim_exclusivo.isoformat())
        .execute()
        .data
    )
    transacoes_por_mes: dict[str, list[dict]] = {}
    for t in todas_transacoes:
        chave_mes = f"{t['data_compra'][:7]}-01"
        transacoes_por_mes.setdefault(chave_mes, []).append(t)

    return orcamento_por_mes, itens_por_orcamento_id, transacoes_por_mes
