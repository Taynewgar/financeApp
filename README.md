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
  - `app/routers/` — CRUD de contas, categorias, subcategorias, caixinhas e
    transações (com parcelamento e fatura por ciclo de fechamento).
    Orçamento entra numa próxima entrega.
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

Duas suítes, com propósitos diferentes:

**Testes offline** (`tests/*.py`, exceto `tests/integration/`) — não tocam
rede nem Supabase. Usam um dublê do cliente do banco (`tests/fakes.py`) que
reproduz o mesmo encadeamento de chamadas, então validam a lógica da API de
verdade (validação de campos, cálculo de fatura por ciclo, deduplicação,
checagem de posse entre recursos) de forma instantânea, em qualquer máquina
Linux, sem precisar de `.env`:

```bash
cd backend
pip install -r requirements-dev.txt
pytest -q
```

**Testes de integração** (`tests/integration/`) — tocam o Supabase real.
Validam o que o dublê não pode provar: que o RLS do Postgres isola os dados
entre usuários de verdade, e que a constraint UNIQUE de `hash_dedup` existe
no banco. São pulados automaticamente (com uma mensagem explicando por quê)
se `backend/.env` não estiver preenchido ou as variáveis abaixo não
existirem — não quebram em CI nem numa máquina sem rede:

```bash
cd backend
cp .env.example .env   # preencha os 4 valores do seu Supabase
TEST_USER_EMAIL=teste@teste.com TEST_USER_PASSWORD=teste pytest -q
```

Rodar `pytest -q` sozinho, sem essas variáveis, executa só a suíte offline
e pula a de integração — é seguro rodar sempre o mesmo comando.

O script `tests/manual_verification.py` (anterior a essa suíte) continua
funcionando como um roteiro único de fumaça, mas os testes de integração
acima são mais completos e específicos — prefira-os.
