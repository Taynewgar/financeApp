"""Sincroniza itens de orçamento com o que está sendo lançado de verdade —
paridade com o app original (que derivava categorias de custo
automaticamente do CSV carregado, ver docs/plano-de-evolucao-original.md).

Reativo: assim que uma despesa (ou aplicação/retirada sem caixinha, que é
investimento) usa uma categoria/subcategoria ainda sem item no orçamento do
mês daquela transação, cria um item novo com orcamento_mensal=0 — você só
ajusta o valor, em vez de cadastrar o item do zero. Não cria orçamento
nenhum (só entra se já existir um pro mês da transação) e nunca mexe no
valor de um item já existente.
"""
from datetime import date

from supabase import Client

_BUCKET_POR_ESTRUTURA = {
    "fixo": "custos_fixos",
    "variavel": "custos_variaveis",
    "sazonal": "sazonalidades",
    "investimentos": "investimentos",
}


def sincronizar_item_orcamento(db: Client, user_id: str, transacao: dict) -> None:
    tipo = transacao["tipo_movimento"]
    # receita, estorno/ressarcimento e reserva (aplicação/retirada COM
    # caixinha) não alimentam orçamento — só despesa e investimento têm
    # bucket/teto pra fazer sentido virar item
    eh_investimento_sem_caixinha = tipo in ("aplicacao", "retirada") and not transacao.get("caixinha_id")
    if tipo != "despesa" and not eh_investimento_sem_caixinha:
        return

    bucket = _BUCKET_POR_ESTRUTURA.get(transacao.get("estrutura_custo"))
    if not bucket:
        return

    subcategoria_id = transacao.get("subcategoria_id")
    categoria_id = transacao.get("categoria_id")
    if not subcategoria_id and not categoria_id:
        return

    mes_inicio = date.fromisoformat(str(transacao["data_compra"])[:10]).replace(day=1)
    orcamentos = (
        db.table("orcamentos")
        .select("id")
        .eq("user_id", user_id)
        .eq("vigencia_mes", mes_inicio.isoformat())
        .execute()
        .data
    )
    if not orcamentos:
        return  # sincronização só entra dentro de um orçamento que já existe, nunca cria um
    orcamento_id = orcamentos[0]["id"]

    itens_existentes = (
        db.table("orcamento_itens")
        .select("categoria_id,subcategoria_id")
        .eq("orcamento_id", orcamento_id)
        .execute()
        .data
    )
    if subcategoria_id:
        ja_existe = any(i.get("subcategoria_id") == subcategoria_id for i in itens_existentes)
    else:
        ja_existe = any(
            i.get("categoria_id") == categoria_id and not i.get("subcategoria_id") for i in itens_existentes
        )
    if ja_existe:
        return

    db.table("orcamento_itens").insert(
        {
            "orcamento_id": orcamento_id,
            "bucket": bucket,
            "categoria_id": None if subcategoria_id else categoria_id,
            "subcategoria_id": subcategoria_id,
            "orcamento_mensal": 0,
        }
    ).execute()
