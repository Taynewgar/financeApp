"""Reimplementação independente da cadeia de `saldo_anterior` do
Planejamento, pra comparar contra o que a API real retorna — mesmo
objetivo do `/financeapp-ref` (independência de implementação pra achar
bug), mas de um jeito diferente: não existe fonte externa pro Orçado (é
tudo digitado direto no Planejamento, nunca existiu num CSV histórico),
então não há "arquivo de origem" pra comparar — a única forma de validar
é recalcular a cadeia do zero, a partir do mesmo dado bruto (orçamento
mensal + realizado de cada mês), e ver se bate com o que a API já
retorna.

Por que `saldo_anterior` especificamente: é a parte mais arriscada da
regra de Planejamento — soma recursiva mês a mês (sobra/furo rolando via
"gerar próximo mês"), silenciosa quando quebra (nunca dá erro, só
devolve um número errado). Teto e percentuais são fórmula simples o
bastante pra conferir na mão. Ver docs/backlog.md e a conversa que gerou
este script pro racional completo.

Suspeita concreta sendo testada: `saldo_anterior_em_lote`
(app/services/orcamento_saldo.py) busca o "item equivalente" do mês
anterior só entre itens ATIVOS — se um item ficou inativo num mês e
voltou a ficar ativo depois, a cadeia não acha o antecessor e trata como
se não houvesse orçamento anterior nenhum (zera o saldo_anterior
silenciosamente, não é um 0 real). Este script roda a reimplementação
2x por item — uma restrita a itens ativos (igual o app faz hoje) e outra
sem essa restrição — pra isolar exatamente esse caso, se existir.

Roda contra o Supabase REAL (precisa de backend/.env preenchido) — não
roda nesta sessão remota, mesma limitação dos testes de integração e do
script de migração. Só GET: não cria, edita nem apaga nada em nenhuma
tabela.

Uso:
    cd backend
    source venv/bin/activate
    TEST_USER_EMAIL=voce@email.com TEST_USER_PASSWORD=sua_senha \\
        python scripts/referencia_saldo_anterior.py
"""
from __future__ import annotations

import os
import sys
from calendar import monthrange
from datetime import date
from typing import Any

import httpx
from fastapi.testclient import TestClient

sys.path.insert(0, ".")
from app.config import settings  # noqa: E402
from app.main import app  # noqa: E402

client = TestClient(app)

# mesmo sinal de orcamento_saldo.py — despesa conta a favor do gasto,
# estorno/ressarcimento reduz (dinheiro devolvido), aplicação soma e
# retirada subtrai (só entram pra item de investimento, via conta
# vinculada; reserva com caixinha não aparece aqui, não é item de
# orçamento possível hoje)
_SINAL_REALIZADO = {
    "despesa": 1,
    "estorno": -1,
    "ressarcimento": -1,
    "aplicacao": 1,
    "retirada": -1,
}


def sign_in(email: str, password: str) -> str:
    resp = httpx.post(
        f"{settings.supabase_url}/auth/v1/token?grant_type=password",
        headers={"apikey": settings.supabase_anon_key, "Content-Type": "application/json"},
        json={"email": email, "password": password},
        timeout=15,
    )
    resp.raise_for_status()
    return resp.json()["access_token"]


def somar_meses(d: date, n: int) -> date:
    total = d.year * 12 + (d.month - 1) + n
    return date(total // 12, total % 12 + 1, 1)


def ultimo_dia_do_mes(d: date) -> date:
    return date(d.year, d.month, monthrange(d.year, d.month)[1])


def chave_vinculo(item: dict) -> tuple[str, str] | None:
    """Mesma prioridade de orcamento_saldo.py: subcategoria > categoria >
    conta vinculada. None = item "nome livre", sem vínculo — não tem como
    achar o equivalente em outro mês nem recalcular realizado."""
    if item.get("subcategoria_id"):
        return ("subcategoria_id", item["subcategoria_id"])
    if item.get("categoria_id"):
        return ("categoria_id", item["categoria_id"])
    if item.get("conta_vinculada_id"):
        return ("conta_vinculada_id", item["conta_vinculada_id"])
    return None


def realizado_independente(headers: dict, item: dict, mes_inicio: date) -> float:
    """Reimplementação própria de calcular_realizado_item — soma via
    GET /transacoes (filtro + período), não consulta o banco direto.
    "Só categoria" exclui em Python o que já tem subcategoria própria,
    mesma regra documentada em orcamento_saldo.py (um item com
    subcategoria sempre carrega a categoria pai junto; checar categoria
    primeiro pegaria transação de outra subcategoria da mesma pai)."""
    mes_fim = ultimo_dia_do_mes(mes_inicio)
    params = {"data_inicio": mes_inicio.isoformat(), "data_fim": mes_fim.isoformat()}
    if item.get("subcategoria_id"):
        linhas = client.get(
            "/transacoes", params={**params, "subcategoria_id": item["subcategoria_id"]}, headers=headers
        ).json()
    elif item.get("categoria_id"):
        candidatas = client.get(
            "/transacoes", params={**params, "categoria_id": item["categoria_id"]}, headers=headers
        ).json()
        linhas = [t for t in candidatas if not t.get("subcategoria_id")]
    elif item.get("conta_vinculada_id"):
        linhas = client.get(
            "/transacoes", params={**params, "conta_id": item["conta_vinculada_id"]}, headers=headers
        ).json()
    else:
        return 0.0
    return round(sum(_SINAL_REALIZADO.get(t["tipo_movimento"], 0) * t["valor"] for t in linhas), 2)


def achar_candidatos(itens_mes_anterior: list[dict], item: dict, restringir_ativos: bool) -> list[dict]:
    """Todos os itens do mês anterior que batem (bucket, vínculo) — não só
    o 1º. Mais de 1 candidato é ambiguidade real (2 itens de orçamento
    pro mesmo bucket/categoria no mesmo mês) — quem desempata é a ordem
    de retorno da query, que pode não ser a mesma entre este script (via
    GET /orcamentos/{id}/itens, ordenado por bucket) e o cálculo ao vivo
    do app (sem ordenação explícita) — ver achado 2026-10-10."""
    chave = chave_vinculo(item)
    if chave is None:
        return []
    campo, valor = chave
    candidatos = []
    for candidato in itens_mes_anterior:
        if restringir_ativos and not candidato.get("ativo", True):
            continue
        if candidato.get("bucket") == item["bucket"] and candidato.get(campo) == valor:
            candidatos.append(candidato)
    return candidatos


def achar_equivalente(itens_mes_anterior: list[dict], item: dict, restringir_ativos: bool) -> dict | None:
    candidatos = achar_candidatos(itens_mes_anterior, item, restringir_ativos)
    return candidatos[0] if candidatos else None


def saldo_anterior_independente(
    headers: dict,
    item: dict,
    vigencia_mes: date,
    itens_por_mes: dict[str, list[dict]],
    cache: dict[tuple, float],
    restringir_ativos: bool,
) -> float | None:
    """None = item sem vínculo, não recalculável (mesma limitação do app:
    saldo_anterior gravado direto na criação, sem cadeia pra conferir).
    `restringir_ativos` controla se a busca do item equivalente no mês
    anterior ignora itens inativos (True = replica o comportamento atual
    do app; False = testa a hipótese de que isso quebra a cadeia)."""
    if chave_vinculo(item) is None:
        return None

    chave_cache = (chave_vinculo(item), vigencia_mes.isoformat(), restringir_ativos)
    if chave_cache in cache:
        return cache[chave_cache]

    mes_anterior = somar_meses(vigencia_mes, -1)
    itens_mes_anterior = itens_por_mes.get(mes_anterior.isoformat())
    if itens_mes_anterior is None:
        cache[chave_cache] = 0.0
        return 0.0

    item_anterior = achar_equivalente(itens_mes_anterior, item, restringir_ativos)
    if item_anterior is None:
        cache[chave_cache] = 0.0
        return 0.0

    saldo_do_anterior = (
        saldo_anterior_independente(headers, item_anterior, mes_anterior, itens_por_mes, cache, restringir_ativos)
        or 0.0
    )
    disponivel_anterior = round(item_anterior["orcamento_mensal"] + saldo_do_anterior, 2)
    realizado_anterior = realizado_independente(headers, item_anterior, mes_anterior)
    resultado = round(disponivel_anterior - realizado_anterior, 2)
    cache[chave_cache] = resultado
    return resultado


def tracar_cadeia(
    headers: dict,
    item: dict,
    vigencia_mes: date,
    itens_por_mes: dict[str, list[dict]],
    restringir_ativos: bool,
) -> list[dict]:
    """Mesma recursão de saldo_anterior_independente, mas em vez de só
    devolver o número final, devolve 1 registro por mês andado pra trás —
    pra inspecionar visualmente onde a cadeia diverge do esperado (qual
    item foi achado como equivalente, se havia mais de 1 candidato, se
    estava ativo, orçamento mensal e realizado usados em cada passo)."""
    passos: list[dict] = []
    atual = item
    mes_atual = vigencia_mes
    while True:
        chave = chave_vinculo(atual)
        if chave is None:
            passos.append({"mes": mes_atual.isoformat()[:7], "motivo": "item sem vínculo — fim da cadeia"})
            break

        mes_anterior = somar_meses(mes_atual, -1)
        itens_mes_anterior = itens_por_mes.get(mes_anterior.isoformat())
        if itens_mes_anterior is None:
            passos.append(
                {"mes": mes_anterior.isoformat()[:7], "motivo": "sem orçamento neste mês — cadeia termina aqui (0.0)"}
            )
            break

        candidatos = achar_candidatos(itens_mes_anterior, atual, restringir_ativos)
        if not candidatos:
            passos.append(
                {
                    "mes": mes_anterior.isoformat()[:7],
                    "motivo": "nenhum item equivalente achado — cadeia termina aqui (0.0)",
                    "restringindo_a_ativos": restringir_ativos,
                }
            )
            break

        item_anterior = candidatos[0]
        realizado = realizado_independente(headers, item_anterior, mes_anterior)
        passos.append(
            {
                "mes": mes_anterior.isoformat()[:7],
                "ambiguo": len(candidatos) > 1,
                "n_candidatos": len(candidatos),
                "item_id": item_anterior.get("id"),
                "ativo": item_anterior.get("ativo"),
                "orcamento_mensal": item_anterior.get("orcamento_mensal"),
                "realizado_recalculado": realizado,
                "saldo_anterior_do_app_nesse_item": item_anterior.get("saldo_anterior"),
            }
        )
        atual = item_anterior
        mes_atual = mes_anterior
    return passos


def nome_do_item(item: dict, categorias: dict, subcategorias: dict, contas: dict) -> str:
    if item.get("subcategoria_id"):
        sub = subcategorias.get(item["subcategoria_id"], {})
        cat = categorias.get(sub.get("categoria_id"), {}).get("nome", "?")
        return f"{cat} / {sub.get('nome', '?')}"
    if item.get("categoria_id"):
        return categorias.get(item["categoria_id"], {}).get("nome", "?")
    if item.get("conta_vinculada_id"):
        return f"conta: {contas.get(item['conta_vinculada_id'], {}).get('nome', '?')}"
    return item.get("nome") or "(sem nome)"


def main() -> None:
    email = os.environ.get("TEST_USER_EMAIL")
    senha = os.environ.get("TEST_USER_PASSWORD")
    if not email or not senha:
        print("Defina TEST_USER_EMAIL e TEST_USER_PASSWORD (sua conta real do Supabase) antes de rodar.")
        sys.exit(1)

    token = sign_in(email, senha)
    headers = {"Authorization": f"Bearer {token}"}

    orcamentos = sorted(client.get("/orcamentos", headers=headers).json(), key=lambda o: o["vigencia_mes"])
    if not orcamentos:
        print("Nenhum orçamento encontrado nessa conta — nada pra verificar.")
        return

    categorias = {c["id"]: c for c in client.get("/categorias", headers=headers).json()}
    subcategorias = {s["id"]: s for s in client.get("/subcategorias", headers=headers).json()}
    contas = {c["id"]: c for c in client.get("/contas", headers=headers).json()}

    itens_por_mes: dict[str, list[dict]] = {}
    for orc in orcamentos:
        itens_por_mes[orc["vigencia_mes"][:7] + "-01"] = client.get(
            f"/orcamentos/{orc['id']}/itens", headers=headers
        ).json()

    print(f"{len(orcamentos)} orçamento(s), de {orcamentos[0]['vigencia_mes'][:7]} a {orcamentos[-1]['vigencia_mes'][:7]}.\n")

    divergencias: list[dict[str, Any]] = []
    so_sem_restricao: list[dict[str, Any]] = []
    sem_vinculo = 0
    total_verificado = 0

    cache_restrito: dict[tuple, float] = {}
    cache_livre: dict[tuple, float] = {}

    for mes_str in sorted(itens_por_mes):
        mes = date.fromisoformat(mes_str)
        for item in itens_por_mes[mes_str]:
            nome = nome_do_item(item, categorias, subcategorias, contas)
            if chave_vinculo(item) is None:
                sem_vinculo += 1
                continue

            total_verificado += 1
            meu_restrito = saldo_anterior_independente(headers, item, mes, itens_por_mes, cache_restrito, True)
            app_valor = item["saldo_anterior"]

            if round(meu_restrito, 2) == round(app_valor, 2):
                continue

            meu_livre = saldo_anterior_independente(headers, item, mes, itens_por_mes, cache_livre, False)
            achado = {
                "mes": mes_str[:7],
                "item": nome,
                "bucket": item["bucket"],
                "app": app_valor,
                "recalculado_restrito": meu_restrito,
                "recalculado_livre": meu_livre,
                "_item": item,
            }
            if round(meu_livre, 2) == round(app_valor, 2):
                # recalculado SEM restrição bate com o app — raro, indicaria
                # que a restrição do app por algum motivo não se aplicou aqui
                so_sem_restricao.append(achado)
            else:
                divergencias.append(achado)

    print(f"Itens com vínculo verificados: {total_verificado}")
    print(f"Itens sem vínculo (nome livre, não verificável): {sem_vinculo}\n")

    if not divergencias and not so_sem_restricao:
        print("Nenhuma divergência — saldo_anterior recalculado bate com o que a API retorna em todos os itens.")
        return

    def _imprimir_rastro(d: dict) -> None:
        mes = date.fromisoformat(d["mes"] + "-01")
        print("    rastro (restrito a ativos, mês a mês pra trás):")
        for passo in tracar_cadeia(headers, d["_item"], mes, itens_por_mes, True):
            if "motivo" in passo:
                print(f"      {passo['mes']}: {passo['motivo']}")
                continue
            marca = " <<< AMBÍGUO, " + str(passo["n_candidatos"]) + " candidatos" if passo["ambiguo"] else ""
            print(
                f"      {passo['mes']}: item {passo['item_id']} "
                f"(ativo={passo['ativo']}) orçamento_mensal={passo['orcamento_mensal']:.2f} "
                f"realizado_recalc={passo['realizado_recalculado']:.2f} "
                f"saldo_anterior_do_app_nesse_item={passo['saldo_anterior_do_app_nesse_item']:.2f}{marca}"
            )

    if divergencias:
        print(f"=== {len(divergencias)} divergência(s) real(is) (recalculado ≠ app, com ou sem restrição) ===")
        for d in divergencias:
            print(
                f"  {d['mes']} — {d['bucket']} / {d['item']}: "
                f"app={d['app']:.2f} | recalc(restrito)={d['recalculado_restrito']:.2f} | "
                f"recalc(livre)={d['recalculado_livre']:.2f}"
            )
            _imprimir_rastro(d)
        print()

    if so_sem_restricao:
        print(
            f"=== {len(so_sem_restricao)} item(ns) onde a restrição a itens ATIVOS explica a diferença ==="
        )
        print("(recalculado sem essa restrição bate com o app — aponta pro caso de item desativado/reativado)")
        for d in so_sem_restricao:
            print(
                f"  {d['mes']} — {d['bucket']} / {d['item']}: "
                f"app={d['app']:.2f} | recalc(restrito)={d['recalculado_restrito']:.2f} | "
                f"recalc(livre)={d['recalculado_livre']:.2f}"
            )
            _imprimir_rastro(d)


if __name__ == "__main__":
    main()
