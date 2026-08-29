# financeApp

Relatório financeiro pessoal — migrando de app desktop offline (Tkinter) para
PWA com backend hospedado (Render) e banco Supabase.

## Estrutura

- `backend/` — API FastAPI (`app/main.py`). `/health` responde mesmo sem o
  Supabase configurado.
- `db/schema.sql` — schema inicial do Postgres (contas, categorias,
  subcategorias, caixinhas, transações, orçamento versionado por mês), com
  Row Level Security por usuário.
- `render.yaml` — blueprint de deploy no Render.

## Setup (Entrega 1 — infraestrutura)

1. Crie um projeto em [supabase.com](https://supabase.com) (sua própria conta).
2. Em *SQL Editor*, rode o conteúdo de `db/schema.sql`.
3. Em *Project Settings → API*, copie a URL e a `service_role key`; em
   *Project Settings → Database*, copie a connection string.
4. Copie `backend/.env.example` para `backend/.env` e preencha os três
   valores localmente (esse arquivo nunca é commitado).
5. Crie um serviço em [render.com](https://render.com) conectado a este
   repositório (Render detecta o `render.yaml` automaticamente) e cole os
   mesmos três valores nas *Environment Variables* do serviço, diretamente
   no painel do Render — nunca em texto de chat ou commit.

## Desenvolvimento local

```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload
```
