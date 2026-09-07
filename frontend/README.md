# financeApp — frontend

PWA em React + Vite + TypeScript, consumindo a API do `backend/`.

## Estrutura

- `src/lib/supabase.ts` — cliente Supabase (auth).
- `src/lib/api.ts` — `apiFetch()`, wrapper de `fetch` que anexa o token da
  sessão Supabase atual como `Authorization: Bearer` em toda chamada à API;
  `checkHealth()` chama `/health` sem autenticação.
- `src/auth/AuthContext.tsx` — sessão atual, `signIn`/`signOut`, escuta
  `onAuthStateChange`.
- `src/auth/ProtectedRoute.tsx` — redireciona para `/login` sem sessão.
- `src/components/AppShell.tsx` — casca do app: navegação lateral no
  desktop, barra inferior no mobile (troca por CSS em 720px), botão
  flutuante de "+" pra Novo Lançamento a partir de qualquer tela.
- `src/routes/` — uma tela por seção. `Dashboard` e `Configuracoes` já
  fazem chamada real à API (a segunda lista as contas de verdade, prova
  que autenticação + API estão conectadas ponta a ponta); as demais são
  placeholders — chegam nas próximas entregas.

## Setup

Requer **Node 20+** (o `vite-plugin-pwa` depende do `workbox-build`, que
exige isso). Se usa `nvm`, o `.nvmrc` já fixa a versão certa:

```bash
cd frontend
nvm use          # troca pro Node 20 automaticamente, lendo o .nvmrc
npm install
cp .env.example .env.local   # preencha com o mesmo Supabase do backend
npm run dev
```

As 3 variáveis em `.env.local`:
- `VITE_SUPABASE_URL` / `VITE_SUPABASE_ANON_KEY` — mesmas do `backend/.env`.
- `VITE_API_BASE_URL` — `http://localhost:8000` rodando o backend local
  (`cd backend && uvicorn app.main:app --reload`), ou a URL do serviço no
  Render em produção.

`npm run build` gera a versão de produção em `dist/` (com manifest e
service worker do PWA já embutidos via `vite-plugin-pwa`).

## O que já funciona nesta entrega

- Login (Supabase Auth, e-mail/senha) e logout.
- Rotas protegidas — sem sessão, qualquer URL redireciona pra `/login`.
- Navegação entre as 5 seções (Dashboard, Lançamentos, Planejamento,
  Estruturas de Custo, Configurações), responsiva (sidebar ↔ barra
  inferior).
- Tema claro/escuro automático (`prefers-color-scheme`, sem toggle manual
  ainda).
- Chamada real e autenticada à API (`Configurações` lista as contas).

## O que falta (próximas entregas)

Cada tela hoje é um placeholder, exceto Dashboard (só status de conexão)
e Configurações (só lista contas, sem criar/editar). Formulários de
lançamento, orçamento, estruturas de custo com gráficos, e CRUD completo
de contas/categorias/subcategorias/caixinhas ainda não existem.
