# financeApp

Relatório financeiro pessoal, migrando de app desktop (Tkinter) para PWA
(React) + API (FastAPI) + Supabase (Postgres com RLS por usuário).

Documentação de verdade já vive no repo — este arquivo é só o ponto de
entrada pra não repetir contexto a cada sessão:

- `README.md` (raiz) — arquitetura e regras de negócio de cada domínio
  (transações, orçamento envelope, caixinhas, estrutura de custo). **Leia
  antes de mexer em regra de negócio** — as regras são finas e já estão
  documentadas lá com o porquê de cada uma.
- `frontend/README.md` — estrutura do frontend, setup, deploy (Vercel).
- `docs/README.md` — qual documento em `docs/` é o quê.
- `docs/backlog.md` — lista viva de prioridades. Consultar antes de sugerir
  "próximo passo" — pode já estar decidido (ou descartado) ali.

## Stack

- **Backend** (`backend/`): FastAPI + Supabase, Python, pytest. venv local
  em `backend/venv`.
- **Frontend** (`frontend/`): React 19 + Vite + TypeScript, Node 22+
  (`.nvmrc`), lint com `oxlint`.
- **Banco**: Postgres via Supabase, schema em `db/schema.sql`, RLS por
  usuário.
- Deploy: backend no Render (`render.yaml`), frontend na Vercel
  (`vercel.json` fica na raiz do repo, não em `frontend/` — de propósito).

## Rodando localmente

```bash
# backend
cd backend && source venv/bin/activate && uvicorn app.main:app --reload

# frontend
cd frontend && nvm use && npm run dev
```

## Testes

- Backend: `venv/bin/python -m pytest -q` dentro de `backend/` (não
  `pytest` direto — evita erro de "externally-managed-environment").
- **Nesta sessão remota não há `backend/.env` com credenciais reais do
  Supabase** — os testes de integração (`backend/tests/integration/`)
  sempre aparecem como skip aqui; isso é esperado, não uma falha pra
  investigar. Rodar de novo não muda o resultado. Só o usuário, no
  terminal dele, roda a integração real.
- Use a skill `/rodar-testes` — ela já sabe reportar certo e imprimir os
  comandos de integração pro usuário copiar.
- Frontend: `npm run lint` (oxlint) e `npm run build` (tsc + vite) como
  verificação de tipo.

## Convenções

- Domínio e nomes de campo em **português** em todas as camadas (banco,
  API, frontend) — `categoria`, `subcategoria`, `estrutura_custo`,
  `meio_pagamento`, etc. Não traduzir para inglês em código novo.
- `frontend/src/lib/types.ts` espelha os schemas Pydantic do backend com
  os mesmos nomes de campo — ao mudar um schema no backend, atualizar os
  tipos no frontend junto.
- Nunca commitar `.env`/`.env.local` (já no `.gitignore`) nem colar
  segredos do Supabase em texto de chat — eles vão direto no painel do
  Render/Vercel.
- Regra de negócio nova ou alterada: documentar na mesma seção do domínio
  no `README.md` raiz, seguindo o padrão "regra + porquê" já usado lá.
