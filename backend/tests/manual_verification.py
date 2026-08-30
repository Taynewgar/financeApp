"""Verificação manual de ponta a ponta contra o Supabase real.

Não faz parte da suíte automatizada (não roda em CI) — é uma ferramenta
para validar CRUD + isolamento por usuário (RLS) contra dados reais.
Cria um usuário descartável para o teste de isolamento e apaga tudo que
usa ao final (inclusive esse usuário).

Requer rede de saída para o Supabase — não roda em ambientes com egress
restrito (ex.: alguns sandboxes de CI). Rode localmente ou onde houver
acesso à internet normal.

Uso:
    TEST_USER_EMAIL=teste@teste.com TEST_USER_PASSWORD=teste \
        python tests/manual_verification.py
"""
from __future__ import annotations

import os
import sys
import uuid

import httpx
from fastapi.testclient import TestClient

sys.path.insert(0, ".")
from app.config import settings  # noqa: E402
from app.db import get_service_client  # noqa: E402
from app.main import app  # noqa: E402

client = TestClient(app)
results: list[tuple[str, bool, str]] = []


def check(label: str, condition: bool, detail: str = "") -> None:
    results.append((label, condition, detail))
    print(f"{'OK ' if condition else 'FALHOU'} - {label}" + (f" ({detail})" if detail and not condition else ""))


def sign_in(email: str, password: str) -> str:
    resp = httpx.post(
        f"{settings.supabase_url}/auth/v1/token?grant_type=password",
        headers={"apikey": settings.supabase_anon_key, "Content-Type": "application/json"},
        json={"email": email, "password": password},
        timeout=15,
    )
    resp.raise_for_status()
    return resp.json()["access_token"]


def create_throwaway_user() -> tuple[str, str, str]:
    email = f"verificacao-{uuid.uuid4().hex[:8]}@teste.local"
    password = "verificacao-temp-123"
    admin = get_service_client()
    result = admin.auth.admin.create_user(
        {"email": email, "password": password, "email_confirm": True}
    )
    return result.user.id, email, password


def delete_user(user_id: str) -> None:
    get_service_client().auth.admin.delete_user(user_id)


def main() -> None:
    email_a = os.environ.get("TEST_USER_EMAIL")
    password_a = os.environ.get("TEST_USER_PASSWORD")
    if not email_a or not password_a:
        sys.exit("Defina TEST_USER_EMAIL e TEST_USER_PASSWORD (usuário de teste já criado no Supabase).")

    print(f"== Autenticando usuário A ({email_a}) ==")
    token_a = sign_in(email_a, password_a)
    headers_a = {"Authorization": f"Bearer {token_a}"}

    print("== Criando usuário B descartável (para teste de isolamento) ==")
    user_b_id, email_b, password_b = create_throwaway_user()
    token_b = sign_in(email_b, password_b)
    headers_b = {"Authorization": f"Bearer {token_b}"}

    created_ids: dict[str, list[str]] = {"contas": [], "categorias": [], "subcategorias": [], "caixinhas": []}

    try:
        # --- CRUD básico como usuário A ---
        r = client.post("/contas", json={"nome": "Conta Verificação", "tipo_conta": "corrente", "saldo_inicial": 100}, headers=headers_a)
        check("POST /contas cria com 201", r.status_code == 201, f"status={r.status_code} body={r.text}")
        conta = r.json()
        created_ids["contas"].append(conta.get("id", ""))

        r = client.get("/contas", headers=headers_a)
        check("GET /contas lista a conta criada", r.status_code == 200 and any(c["id"] == conta["id"] for c in r.json()))

        r = client.patch(f"/contas/{conta['id']}", json={"nome": "Conta Verificação (editada)"}, headers=headers_a)
        check("PATCH /contas/{id} edita", r.status_code == 200 and r.json()["nome"] == "Conta Verificação (editada)")

        r = client.patch(f"/contas/{conta['id']}/ativo", params={"ativo": False}, headers=headers_a)
        check("PATCH /contas/{id}/ativo desativa", r.status_code == 200 and r.json()["ativo"] is False)

        r = client.post("/categorias", json={"nome": "Categoria Verificação"}, headers=headers_a)
        check("POST /categorias cria com 201", r.status_code == 201, f"status={r.status_code} body={r.text}")
        categoria = r.json()
        created_ids["categorias"].append(categoria.get("id", ""))

        r = client.post(
            "/subcategorias",
            json={"categoria_id": categoria["id"], "nome": "Subcategoria Verificação", "estrutura_custo_padrao": "variavel"},
            headers=headers_a,
        )
        check("POST /subcategorias cria com 201", r.status_code == 201, f"status={r.status_code} body={r.text}")
        subcategoria = r.json()
        created_ids["subcategorias"].append(subcategoria.get("id", ""))

        r = client.post("/subcategorias", json={"categoria_id": str(uuid.uuid4()), "nome": "Deve falhar"}, headers=headers_a)
        check("POST /subcategorias com categoria inexistente retorna 404", r.status_code == 404, f"status={r.status_code}")

        r = client.post("/caixinhas", json={"nome": "Caixinha Verificação"}, headers=headers_a)
        check("POST /caixinhas cria com 201", r.status_code == 201, f"status={r.status_code} body={r.text}")
        caixinha = r.json()
        created_ids["caixinhas"].append(caixinha.get("id", ""))

        # --- Isolamento entre usuários (RLS) ---
        r = client.get("/contas", headers=headers_b)
        check(
            "Usuário B NÃO enxerga a conta do usuário A (RLS)",
            r.status_code == 200 and not any(c["id"] == conta["id"] for c in r.json()),
        )

        r = client.patch(f"/contas/{conta['id']}", json={"nome": "Tentativa de invasão"}, headers=headers_b)
        check(
            "Usuário B NÃO consegue editar conta do usuário A (RLS)",
            r.status_code == 404,
            f"status={r.status_code}",
        )

        # --- Sem autenticação ---
        r = client.get("/contas")
        check("Sem token retorna 401", r.status_code == 401)

    finally:
        print("== Limpando dados de teste ==")
        admin = get_service_client()
        for table, ids in created_ids.items():
            for item_id in ids:
                if item_id:
                    admin.table(table).delete().eq("id", item_id).execute()
        delete_user(user_b_id)
        print("Limpeza concluída.")

    print("\n== Resumo ==")
    total = len(results)
    ok = sum(1 for _, passed, _ in results if passed)
    print(f"{ok}/{total} verificações passaram")
    if ok != total:
        sys.exit(1)


if __name__ == "__main__":
    main()
