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
- `src/lib/types.ts` — tipos TS espelhando os schemas Pydantic do backend
  (mesmos nomes de campo, pra não precisar traduzir mentalmente).
- `src/routes/` — uma tela por seção. `Dashboard` e `Configuracoes` já
  fazem chamada real à API (a segunda lista as contas de verdade, prova
  que autenticação + API estão conectadas ponta a ponta); `NovoLancamento`
  é o formulário completo de lançamento (ver abaixo); as demais ainda são
  placeholders.

## Setup

Requer **Node 22+** (o `vite-plugin-pwa`/`workbox-build` exige 20+, e os
pacotes `@supabase/*` pedem 22+). Se usa `nvm`, o `.nvmrc` já fixa a
versão certa:

```bash
cd frontend
nvm use          # troca pro Node 22 automaticamente, lendo o .nvmrc
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
- **Novo Lançamento** (`/lancamentos/novo`), formulário completo:
  - Tipo: Receita / Despesa / Aplicação / Retirada / Estorno-Ressarcimento
    (segmentado, não é um select cru com os 6 valores do banco).
  - Despesa ganha o sub-toggle À vista / Parcelado — parcelado troca pros
    campos de `POST /transacoes/parceladas` (valor total, nº de parcelas,
    data da 1ª); à vista usa `POST /transacoes` normal.
  - Estorno/Ressarcimento mostra um seletor com as despesas recentes pra
    vincular (`ajuste_de_transacao_id`), alimentado pelo filtro
    `GET /transacoes?tipo_movimento=despesa` que a Busca já expõe.
  - Categoria → Subcategoria (dependente) → ao escolher a subcategoria, a
    Estrutura de Custo é pré-preenchida com `estrutura_custo_padrao` dela,
    mas continua editável manualmente.
  - Conta, Caixinha (só aparece se você tiver alguma) e Meio de Pagamento.
  - Ao salvar, tela de confirmação com atalho pra lançar outro ou voltar
    ao Dashboard.

## O que falta (próximas entregas)

Lançamentos (lista/busca), Planejamento (orçamento) e Estruturas de Custo
ainda são placeholders. Configurações só lista contas — falta criar/editar
contas/categorias/subcategorias/caixinhas.
