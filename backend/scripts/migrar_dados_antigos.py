"""Migração de dados do histórico da planilha antiga pro Supabase — ver
docs/backlog.md, seção "Migração de dados do app antigo", pro desenho
técnico completo (por que cada decisão abaixo foi tomada).

Dois modos:

  dry-run (padrão, sem --executar): só análise local — carrega os 3
  CSVs, agrupa parcelas, resolve estrutura de custo (perguntando
  interativamente o que não dá pra resolver sozinho, salvando a
  resposta em migracao_overrides.json) e imprime um relatório. Não faz
  nenhuma chamada de rede, não grava nada.

  --executar: além do dry-run, cria de verdade contas/categorias/
  subcategorias/caixinhas/transações no Supabase (idempotente — rodar
  de novo não duplica). Só prossegue se não sobrar nenhum lançamento de
  despesa sem estrutura de custo resolvida.

Requer rede de saída pro Supabase e backend/.env preenchido — não roda
nesta sessão remota (mesma limitação dos testes de integração). Segue o
mesmo padrão de autenticação de tests/seed_dados_teste.py.

Uso:
    cd backend
    source venv/bin/activate

    # 1) dry-run — resolve as pendências de estrutura de custo aos poucos
    python scripts/migrar_dados_antigos.py \\
        --csv-lancamentos /caminho/Lancamentos.csv \\
        --csv-categorias /caminho/Categorias.csv \\
        --csv-caixinhas /caminho/Caixinhas.csv

    # 2) quando o relatório não apontar mais pendência, roda de verdade
    TEST_USER_EMAIL=voce@email.com TEST_USER_PASSWORD=sua_senha \\
        python scripts/migrar_dados_antigos.py \\
        --csv-lancamentos /caminho/Lancamentos.csv \\
        --csv-categorias /caminho/Categorias.csv \\
        --csv-caixinhas /caminho/Caixinhas.csv \\
        --executar
"""
from __future__ import annotations

import argparse
import calendar
import os
import sys
from collections import defaultdict
from dataclasses import dataclass
from datetime import date

import httpx
from fastapi import HTTPException
from fastapi.testclient import TestClient

sys.path.insert(0, ".")
from app.auth import get_user_client  # noqa: E402
from app.config import settings  # noqa: E402
from app.main import app  # noqa: E402
from app.services.dedup import compute_hash  # noqa: E402
from app.services.orcamento_sync import sincronizar_item_orcamento  # noqa: E402
from app.services.transacao_insercao import fatura_referencia_para, inserir_transacao  # noqa: E402
from scripts.migracao.contas import CONTAS, resolver_conta  # noqa: E402
from scripts.migracao.mapeamento import (  # noqa: E402
    aprender_estrutura_custo_por_subcategoria,
    resolver_estrutura_custo,
    resolver_meio_pagamento,
    resolver_tipo_movimento,
    resolver_valor,
)
from scripts.migracao.overrides import carregar as carregar_overrides  # noqa: E402
from scripts.migracao.overrides import chave_linha, perguntar_pendentes  # noqa: E402
from scripts.migracao.parcelas import GrupoParcela, agrupar_parcelas  # noqa: E402
from scripts.migracao.parsing import Lancamento, carregar_caixinhas, carregar_categorias, carregar_lancamentos  # noqa: E402

client = TestClient(app)


@dataclass
class Contexto:
    """Mapas nome-do-CSV -> id (real, vindos do Supabase, ou o próprio
    nome como placeholder no dry-run — serve só pra validar que todo
    lookup resolve sem KeyError antes de gravar qualquer coisa)."""

    contas: dict[str, str]
    categorias: dict[str, str]
    subcategorias: dict[tuple[str, str], str]
    caixinhas: dict[str, str]
    aprendido: dict[tuple[str, str], str]
    overrides: dict[str, str | None]


def contexto_local(
    categorias_csv: dict[str, list[str]],
    caixinhas_csv: dict[str, str],
    aprendido: dict[tuple[str, str], str],
    overrides: dict[str, str | None],
) -> Contexto:
    contas = {nome: nome for nome in CONTAS}
    categorias = {pai: pai for pai in categorias_csv}
    subcategorias = {(pai, sub): sub for pai, subs in categorias_csv.items() for sub in subs}
    caixinhas = {nome: nome for nome in caixinhas_csv}
    return Contexto(contas, categorias, subcategorias, caixinhas, aprendido, overrides)


def montar_payload_avista(lancamento: Lancamento, contexto: Contexto) -> dict:
    tipo_mov = resolver_tipo_movimento(lancamento.movimentacao, lancamento.tipo_pag_movimento)
    conta_id = contexto.contas[resolver_conta(lancamento.banco, lancamento.meio_pagamento)]
    payload: dict = {
        "data_compra": lancamento.data.isoformat(),
        "valor": resolver_valor(lancamento.valor),
        "descricao": lancamento.descricao or None,
        "tipo_movimento": tipo_mov,
        "conta_id": conta_id,
    }
    if tipo_mov in ("aplicacao", "retirada"):
        payload["caixinha_id"] = contexto.caixinhas[lancamento.caixinha]
        return payload

    if lancamento.categoria:
        payload["categoria_id"] = contexto.categorias[lancamento.categoria]
    if lancamento.subcategoria:
        payload["subcategoria_id"] = contexto.subcategorias[(lancamento.categoria, lancamento.subcategoria)]
    meio = resolver_meio_pagamento(lancamento.meio_pagamento)
    if meio:
        payload["meio_pagamento"] = meio
    if lancamento.movimentacao == "Despesa":
        estrutura = resolver_estrutura_custo(lancamento, contexto.aprendido, contexto.overrides, chave_linha(lancamento))
        if estrutura:
            payload["estrutura_custo"] = estrutura
    return payload


def chave_hash_avista(lancamento: Lancamento, contexto: Contexto) -> tuple:
    """Os mesmos campos que `POST /transacoes` usa pro `hash_dedup`
    (ver `criar()` em app/routers/transacoes.py: user_id, data_compra,
    valor, descricao, conta_id, tipo_movimento — categoria/subcategoria
    não entram). 2 lançamentos com essa chave igual colidem na
    constraint UNIQUE do banco, mesmo sendo 2 transações reais
    diferentes (ex: 2 assinaturas de mesmo valor cobradas no mesmo
    dia) — achado rodando a migração de verdade (ver docs/backlog.md)."""
    tipo_mov = resolver_tipo_movimento(lancamento.movimentacao, lancamento.tipo_pag_movimento)
    conta_id = contexto.contas[resolver_conta(lancamento.banco, lancamento.meio_pagamento)]
    return (lancamento.data.isoformat(), resolver_valor(lancamento.valor), lancamento.descricao or None, conta_id, tipo_mov)


def agrupar_por_chave_hash(lancamentos: list[Lancamento], contexto: Contexto) -> dict[tuple, list[Lancamento]]:
    grupos: dict[tuple, list[Lancamento]] = defaultdict(list)
    for l in lancamentos:
        grupos[chave_hash_avista(l, contexto)].append(l)
    return grupos


def gravar_avista_duplicado(db, user_id: str, lancamento: Lancamento, contexto: Contexto, ocorrencia: int) -> dict:
    """Grava a 2ª+ ocorrência de um grupo com `chave_hash_avista` igual
    — não dá pra usar POST /transacoes (o hash padrão colidiria com a
    1ª ocorrência mesmo sendo uma transação real diferente). Grava
    direto, reaproveitando a mesma lógica de fatura/hash do endpoint,
    somando `ocorrencia` ao hash só pra desempatar — nunca é gravado na
    linha, o dado salvo fica idêntico ao que o endpoint criaria."""
    payload = montar_payload_avista(lancamento, contexto)
    conta_id = payload["conta_id"]
    row = {
        "user_id": user_id,
        **payload,
        "pagamento": "avista",
        "parcela_atual": None,
        "parcela_total": None,
        "compra_parcelada_id": None,
        "fatura_referencia": fatura_referencia_para(db, user_id, conta_id, lancamento.data),
        "fatura_override": False,
    }
    row["hash_dedup"] = compute_hash(
        user_id=user_id,
        data_compra=row["data_compra"],
        valor=row["valor"],
        descricao=row["descricao"],
        conta_id=row["conta_id"],
        tipo_movimento=row["tipo_movimento"],
        parcela_atual=None,
        parcela_total=None,
        compra_parcelada_id=None,
        ocorrencia=ocorrencia,
    )
    criada = inserir_transacao(db, row)
    sincronizar_item_orcamento(db, user_id, criada)
    return criada


def validar_localmente(lancamentos_avista: list[Lancamento], grupos: list[GrupoParcela], contexto: Contexto) -> list[str]:
    """Tenta montar o payload de cada lançamento contra o contexto local
    (ids placeholder) — qualquer KeyError vira um erro no relatório em
    vez de estourar no meio da execução real."""
    erros = []
    for l in lancamentos_avista:
        try:
            montar_payload_avista(l, contexto)
        except KeyError as exc:
            erros.append(f"{l.data:%d/%m/%Y} {l.descricao!r}: referência não encontrada {exc}")
    for grupo in grupos:
        try:
            _ = contexto.contas[resolver_conta(grupo.banco, grupo.itens[0][1].meio_pagamento)]
            if grupo.categoria:
                _ = contexto.categorias[grupo.categoria]
            if grupo.subcategoria:
                _ = contexto.subcategorias[(grupo.categoria, grupo.subcategoria)]
        except KeyError as exc:
            erros.append(f"grupo de parcela {grupo.descricao!r}: referência não encontrada {exc}")
    return erros


def sign_in(email: str, password: str) -> str:
    resp = httpx.post(
        f"{settings.supabase_url}/auth/v1/token?grant_type=password",
        headers={"apikey": settings.supabase_anon_key, "Content-Type": "application/json"},
        json={"email": email, "password": password},
        timeout=15,
    )
    resp.raise_for_status()
    return resp.json()["access_token"]


def obter_user_id(token: str) -> str:
    resp = httpx.get(
        f"{settings.supabase_url}/auth/v1/user",
        headers={"apikey": settings.supabase_anon_key, "Authorization": f"Bearer {token}"},
        timeout=10,
    )
    resp.raise_for_status()
    return resp.json()["id"]


def get_ou_criar(headers: dict, listar_path: str, nome: str, extra: dict | None = None) -> dict:
    """Idempotente — reaproveita se já existir um registro com esse
    nome, mesma técnica de tests/seed_dados_teste.py."""
    existentes = client.get(listar_path, headers=headers).json()
    achado = next((x for x in existentes if x["nome"] == nome), None)
    if achado:
        return achado
    resposta = client.post(listar_path, json={"nome": nome, **(extra or {})}, headers=headers)
    resposta.raise_for_status()
    return resposta.json()


def preparar_contas(headers: dict) -> dict[str, str]:
    return {nome: get_ou_criar(headers, "/contas", nome, payload)["id"] for nome, payload in CONTAS.items()}


def preparar_categorias(
    headers: dict, categorias_csv: dict[str, list[str]]
) -> tuple[dict[str, str], dict[tuple[str, str], str]]:
    ids_categoria: dict[str, str] = {}
    ids_subcategoria: dict[tuple[str, str], str] = {}
    for pai, subs in categorias_csv.items():
        tipo = "receita" if pai == "Receitas" else "despesa"
        categoria = get_ou_criar(headers, "/categorias", pai, {"tipo": tipo})
        ids_categoria[pai] = categoria["id"]
        for sub in subs:
            subcategoria = get_ou_criar(headers, "/subcategorias", sub, {"categoria_id": categoria["id"]})
            ids_subcategoria[(pai, sub)] = subcategoria["id"]
    return ids_categoria, ids_subcategoria


def preparar_caixinhas(headers: dict, caixinhas_csv: dict[str, str], ids_conta: dict[str, str]) -> dict[str, str]:
    ids: dict[str, str] = {}
    for nome, banco in caixinhas_csv.items():
        conta_id = ids_conta[resolver_conta(banco, "")]
        ids[nome] = get_ou_criar(headers, "/caixinhas", nome, {"conta_id": conta_id})["id"]
    return ids


def grupo_ja_migrado(db, user_id: str, grupo: GrupoParcela) -> bool:
    """Idempotência pro caminho de parcelas: como esse caminho não passa
    pelo endpoint (e portanto não esbarra sozinho no hash_dedup — o hash
    do endpoint inclui `compra_parcelada_id`, que é gerado de novo a
    cada inserção de cabeçalho, então nunca bateria com uma rodada
    anterior mesmo pra dados idênticos), a checagem aqui é por
    igualdade direta: se a 1ª parcela do grupo já existe (mesma
    descrição, parcela_atual, parcela_total e data), o grupo inteiro já
    foi migrado antes."""
    primeiro_n, primeiro = grupo.itens[0]
    resultado = (
        db.table("transacoes")
        .select("id")
        .eq("user_id", user_id)
        .eq("descricao", primeiro.descricao)
        .eq("parcela_atual", primeiro_n)
        .eq("parcela_total", grupo.parcela_total)
        .eq("data_compra", primeiro.data.isoformat())
        .limit(1)
        .execute()
    )
    return bool(resultado.data)


def gravar_grupo_parcela(db, user_id: str, grupo: GrupoParcela, contexto: Contexto) -> list[dict]:
    """Não usa POST /transacoes/parceladas (ver docs/backlog.md pro
    porquê) — grava o cabeçalho direto e cada parcela com o valor/data
    reais do CSV, reaproveitando as mesmas funções de serviço que o
    endpoint usa por baixo dos panos. Chame `grupo_ja_migrado` antes
    (não faz a checagem sozinha) — ver docstring de lá pro porquê de
    não dar pra confiar só no hash_dedup aqui."""
    meio_pagamento_grupo = grupo.itens[0][1].meio_pagamento
    conta_id = contexto.contas[resolver_conta(grupo.banco, meio_pagamento_grupo)]
    categoria_id = contexto.categorias.get(grupo.categoria) if grupo.categoria else None
    subcategoria_id = contexto.subcategorias.get((grupo.categoria, grupo.subcategoria)) if grupo.subcategoria else None
    meio_pagamento = resolver_meio_pagamento(meio_pagamento_grupo)

    cabecalho = (
        db.table("compras_parceladas")
        .insert(
            {
                "user_id": user_id,
                "descricao": grupo.descricao,
                "valor_total": grupo.valor_total,
                "parcela_total": grupo.parcela_total,
            }
        )
        .execute()
        .data[0]
    )

    criadas = []
    for n, lancamento in grupo.itens:
        estrutura = resolver_estrutura_custo(lancamento, contexto.aprendido, contexto.overrides, chave_linha(lancamento))
        row = {
            "user_id": user_id,
            "data_compra": lancamento.data.isoformat(),
            "valor": resolver_valor(lancamento.valor),
            "descricao": lancamento.descricao,
            "tipo_movimento": "despesa",
            "pagamento": "parcelado",
            "parcela_atual": n,
            "parcela_total": grupo.parcela_total,
            "compra_parcelada_id": cabecalho["id"],
            "conta_id": conta_id,
            "categoria_id": categoria_id,
            "subcategoria_id": subcategoria_id,
            "estrutura_custo": estrutura,
            "meio_pagamento": meio_pagamento,
            "fatura_referencia": fatura_referencia_para(db, user_id, conta_id, lancamento.data),
            "fatura_override": False,
        }
        row["hash_dedup"] = compute_hash(
            user_id=user_id,
            data_compra=row["data_compra"],
            valor=row["valor"],
            descricao=row["descricao"],
            conta_id=row["conta_id"],
            tipo_movimento=row["tipo_movimento"],
            parcela_atual=row["parcela_atual"],
            parcela_total=row["parcela_total"],
            compra_parcelada_id=row["compra_parcelada_id"],
        )
        criada = inserir_transacao(db, row)
        sincronizar_item_orcamento(db, user_id, criada)
        criadas.append(criada)
    return criadas


def somar_do_csv(lancamentos: list[Lancamento]) -> dict[tuple[int, int, str], float]:
    somas: dict[tuple[int, int, str], float] = defaultdict(float)
    for l in lancamentos:
        tipo_mov = resolver_tipo_movimento(l.movimentacao, l.tipo_pag_movimento)
        chave = (l.data.year, l.data.month, tipo_mov)
        somas[chave] = round(somas[chave] + resolver_valor(l.valor), 2)
    return somas


def somar_do_banco(headers: dict, ano: int, mes: int) -> dict[str, float]:
    inicio = date(ano, mes, 1)
    fim = date(ano, mes, calendar.monthrange(ano, mes)[1])
    resposta = client.get(
        "/transacoes",
        params={"data_inicio": inicio.isoformat(), "data_fim": fim.isoformat()},
        headers=headers,
    )
    resposta.raise_for_status()
    somas: dict[str, float] = defaultdict(float)
    for transacao in resposta.json():
        somas[transacao["tipo_movimento"]] = round(somas[transacao["tipo_movimento"]] + transacao["valor"], 2)
    return somas


def reconciliar(headers: dict, lancamentos: list[Lancamento]) -> None:
    print("\n=== Reconciliação pós-migração ===")
    esperado = somar_do_csv(lancamentos)
    meses = sorted({(ano, mes) for ano, mes, _ in esperado})
    divergencias = 0
    for ano, mes in meses:
        real = somar_do_banco(headers, ano, mes)
        for tipo in ("despesa", "receita", "aplicacao", "retirada", "estorno", "ressarcimento"):
            valor_csv = esperado.get((ano, mes, tipo), 0.0)
            valor_banco = real.get(tipo, 0.0)
            if abs(valor_csv - valor_banco) > 0.01:
                divergencias += 1
                print(
                    f"  {ano}-{mes:02d} {tipo}: CSV={valor_csv:.2f}  banco={valor_banco:.2f}  "
                    f"(diferença {valor_csv - valor_banco:+.2f})"
                )
    if divergencias == 0:
        print("  Nenhuma divergência — soma por mês/tipo bate exatamente com o CSV.")
    else:
        print(f"  {divergencias} divergência(s) encontrada(s) — revisar acima antes de confiar nos relatórios do app.")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--csv-lancamentos", required=True)
    parser.add_argument("--csv-categorias", required=True)
    parser.add_argument("--csv-caixinhas", required=True)
    parser.add_argument("--executar", action="store_true", help="Grava de verdade (padrão: só dry-run)")
    args = parser.parse_args()

    lancamentos, linhas_puladas = carregar_lancamentos(args.csv_lancamentos)
    categorias_csv = carregar_categorias(args.csv_categorias)
    caixinhas_csv = carregar_caixinhas(args.csv_caixinhas)

    grupos_parcela, sem_padrao = agrupar_parcelas(lancamentos)
    ids_em_grupo = {id(l) for grupo in grupos_parcela for _, l in grupo.itens}
    ids_sem_padrao = {id(l) for l in sem_padrao}
    lancamentos_avista = [l for l in lancamentos if id(l) not in ids_em_grupo and id(l) not in ids_sem_padrao]

    aprendido = aprender_estrutura_custo_por_subcategoria(lancamentos)
    overrides = carregar_overrides()
    candidatos_despesa = [l for l in lancamentos if l.movimentacao == "Despesa"]
    pendentes = [l for l in candidatos_despesa if not l.custo and (l.categoria, l.subcategoria) not in aprendido]
    overrides = perguntar_pendentes(pendentes, overrides)

    contexto = contexto_local(categorias_csv, caixinhas_csv, aprendido, overrides)
    erros = validar_localmente(lancamentos_avista, grupos_parcela, contexto)
    grupos_hash = agrupar_por_chave_hash(lancamentos_avista, contexto)
    duplicatas_reais = sum(len(itens) - 1 for itens in grupos_hash.values() if len(itens) > 1)

    bloqueantes = []
    for l in candidatos_despesa:
        if resolver_tipo_movimento(l.movimentacao, l.tipo_pag_movimento) != "despesa":
            continue
        if resolver_estrutura_custo(l, aprendido, overrides, chave_linha(l)) is None:
            bloqueantes.append(l)

    total_parcelas = sum(len(g.itens) for g in grupos_parcela)
    completos = sum(1 for g in grupos_parcela if g.completo)
    print("\n=== Relatório (dry-run) ===")
    print(f"Lançamentos válidos no CSV: {len(lancamentos)}")
    print(f"  Contas (fixas): {len(CONTAS)}")
    print(f"  Categorias: {len(categorias_csv)}  |  Subcategorias: {sum(len(v) for v in categorias_csv.values())}")
    print(f"  Caixinhas: {len(caixinhas_csv)}")
    print(f"  Grupos de compra parcelada: {len(grupos_parcela)} ({completos} completos, {len(grupos_parcela) - completos} truncados nas bordas do arquivo — esperado)")
    print(f"  Transações em grupos de parcela: {total_parcelas}")
    print(f"  Transações avista/receita/reserva: {len(lancamentos_avista)}")
    print(f"  Total de transações a criar: {len(lancamentos_avista) + total_parcelas}")
    if duplicatas_reais:
        print(
            f"  Transações com mesma data/valor/descrição/conta/tipo de outra (ex: 2 assinaturas "
            f"cobradas no mesmo dia) — gravadas com desambiguador pra não colidir no hash_dedup: {duplicatas_reais}"
        )
    if linhas_puladas:
        print(f"  Linhas do CSV ignoradas: {len(linhas_puladas)} (sem a coluna Data preenchida — sobra de template da planilha, não é lançamento)")
        exemplos = linhas_puladas[:5]
        for p in exemplos:
            resumo = {k: v for k, v in p.linha_bruta.items() if v and v.strip()}
            print(f"    linha {p.numero}: {resumo or '(completamente vazia)'}")
        if len(linhas_puladas) > len(exemplos):
            print(f"    ... e mais {len(linhas_puladas) - len(exemplos)} linha(s) igual(is)")
    if sem_padrao:
        print(f"  ATENÇÃO: {len(sem_padrao)} linha(s) 'Parcela sem juros' sem padrão (N/M) reconhecido — não serão migradas:")
        for l in sem_padrao:
            print(f"    {l.data:%d/%m/%Y} {l.descricao!r}")
    if erros:
        print(f"  ERRO: {len(erros)} referência(s) que não resolvem:")
        for erro in erros:
            print(f"    {erro}")
    print(f"  Estrutura de custo ainda pendente (bloqueia --executar): {len(bloqueantes)}")

    if not args.executar:
        print("\nDry-run concluído — nada foi gravado. Rode de novo com --executar quando o relatório não apontar mais pendência.")
        return

    if erros:
        print("\nHá referências que não resolvem — corrija o CSV antes de executar.")
        sys.exit(1)
    if bloqueantes:
        print(f"\n{len(bloqueantes)} lançamento(s) de despesa ainda sem estrutura de custo — rode sem --executar pra resolver.")
        sys.exit(1)

    email = os.environ.get("TEST_USER_EMAIL")
    senha = os.environ.get("TEST_USER_PASSWORD")
    if not email or not senha:
        print("\nDefina TEST_USER_EMAIL e TEST_USER_PASSWORD (a conta real do Supabase) pra executar de verdade.")
        sys.exit(1)

    token = sign_in(email, senha)
    user_id = obter_user_id(token)
    headers = {"Authorization": f"Bearer {token}"}
    db = get_user_client(token)

    print("\nCriando contas...")
    ids_conta = preparar_contas(headers)
    print("Criando categorias/subcategorias...")
    ids_categoria, ids_subcategoria = preparar_categorias(headers, categorias_csv)
    print("Criando caixinhas...")
    ids_caixinha = preparar_caixinhas(headers, caixinhas_csv, ids_conta)
    contexto = Contexto(ids_conta, ids_categoria, ids_subcategoria, ids_caixinha, aprendido, overrides)

    print(f"\nCriando {len(lancamentos_avista)} transações avista/receita/reserva...")
    criadas, puladas = 0, 0
    # grupos_hash já foi calculado antes (contexto placeholder do dry-run) —
    # o agrupamento em si (quais lançamentos colidem) não muda com o
    # contexto, só os ids; reaproveita em vez de recalcular
    for itens in grupos_hash.values():
        for ocorrencia, l in enumerate(itens):
            if ocorrencia == 0:
                payload = montar_payload_avista(l, contexto)
                resposta = client.post("/transacoes", json=payload, headers=headers)
                if resposta.status_code == 409:
                    puladas += 1
                    continue
                resposta.raise_for_status()
                criadas += 1
            else:
                # 2ª+ ocorrência de uma transação real repetida (mesma
                # data/valor/descrição/conta/tipo) — POST /transacoes
                # colidiria com a 1ª no hash_dedup padrão, ver
                # gravar_avista_duplicado
                try:
                    gravar_avista_duplicado(db, user_id, l, contexto, ocorrencia)
                    criadas += 1
                except HTTPException as exc:
                    if exc.status_code != 409:
                        raise
                    puladas += 1
    print(f"  {criadas} criadas, {puladas} já existiam (puladas — idempotente)")

    print(f"\nCriando {len(grupos_parcela)} grupos de compra parcelada...")
    total_parcelas_criadas, grupos_pulados = 0, 0
    for grupo in grupos_parcela:
        if grupo_ja_migrado(db, user_id, grupo):
            grupos_pulados += 1
            continue
        total_parcelas_criadas += len(gravar_grupo_parcela(db, user_id, grupo, contexto))
    print(f"  {total_parcelas_criadas} parcelas criadas, {grupos_pulados} grupo(s) já existiam (pulados — idempotente)")

    reconciliar(headers, lancamentos)


if __name__ == "__main__":
    main()
