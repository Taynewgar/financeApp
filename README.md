# financeApp

Relatório financeiro pessoal — migrando de app desktop offline (Tkinter) para
PWA com backend hospedado (Render) e banco Supabase.

## Estrutura

- `backend/` — API FastAPI.
  - `app/main.py` — monta os routers. `/health` responde mesmo sem o
    Supabase configurado.
  - `app/db.py` — dois clientes Supabase: `get_service_client()` (só para
    tarefas administrativas, ignora RLS) e `get_user_client()` (autenticado
    como o usuário da requisição, respeita RLS).
  - `app/auth.py` — valida o token `Authorization: Bearer <token>` de cada
    requisição.
  - `app/routers/` — CRUD de contas, categorias, subcategorias e caixinhas.
    Transações e orçamento entram numa próxima entrega.
- `db/schema.sql` — schema inicial do Postgres (contas, categorias,
  subcategorias, caixinhas, transações, orçamento versionado por mês), com
  Row Level Security por usuário.
- `render.yaml` — blueprint de deploy no Render.

## Setup

1. Crie um projeto em [supabase.com](https://supabase.com) (sua própria conta).
2. Em *SQL Editor*, rode o conteúdo de `db/schema.sql`.
3. Em *Project Settings → API*: copie a **Project URL**, a **anon key** e a
   **service_role key**. Em *Project Settings → Database → Connection
   string*: copie a URI (pooler).
4. Copie `backend/.env.example` para `backend/.env` e preencha os quatro
   valores localmente (esse arquivo nunca é commitado).
5. No serviço do Render (criado via blueprint), confirme em *Environment*
   que as 4 variáveis estão preenchidas: `SUPABASE_URL`,
   `SUPABASE_ANON_KEY`, `SUPABASE_SERVICE_ROLE_KEY`, `DATABASE_URL` — cole
   os valores direto no painel do Render, nunca em texto de chat ou commit.

## Desenvolvimento local

```bash
cd backend
pip install -r requirements-dev.txt
uvicorn app.main:app --reload
```

Com o servidor no ar, `http://localhost:8000/docs` abre a documentação
interativa (Swagger) — dá para testar cada endpoint ali sem escrever código,
desde que informe um token de usuário válido no botão "Authorize".

## Testes

```bash
cd backend
pip install -r requirements-dev.txt
pytest -q
```
