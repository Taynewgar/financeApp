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
- `src/routes/` — uma tela por seção. `Dashboard` faz chamada real à API;
  `Configuracoes` tem os CRUDs de Contas/Categorias/Caixinhas (ver abaixo);
  `NovoLancamento` é o formulário completo de lançamento (ver abaixo);
  Lançamentos, Planejamento e Estruturas de Custo ainda são placeholders.
- `src/routes/configuracoes/` — uma seção por aba de Configurações
  (`ContasSection`, `CategoriasSection`, `CaixinhasSection`), cada uma com
  seu próprio listar/criar/editar/ativar-desativar.

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
- Chamada real e autenticada à API.
- **Configurações**: CRUD completo (criar/editar/ativar/desativar) de
  Contas, Categorias (com subcategorias aninhadas, expansíveis por
  categoria) e Caixinhas, em abas.
- **Novo Lançamento** (`/lancamentos/novo`), formulário completo:
  - Tipo: Receita / Despesa / Investimento / Reserva / Estorno-Ressarcimento
    (segmentado, não é um select cru com os 6 valores do banco). Cada tipo
    só mostra os campos que fazem sentido pra ele:
    - **Despesa**: categoria/subcategoria (só categorias tipo despesa),
      estrutura de custo, meio de pagamento, sub-toggle À vista/Parcelado
      (parcelado usa `POST /transacoes/parceladas`).
    - **Receita**: categoria é fixa (a única categoria tipo `receita` do
      usuário) — só escolhe a subcategoria. Sem estrutura de custo, sem
      meio de pagamento, sem caixinha.
    - **Investimento**: categoria fixa (tipo `investimento`) e estrutura
      de custo fixa (`investimentos`) — só escolhe subcategoria e a
      direção (Aplicação/Retirada). Sem meio de pagamento, sem caixinha.
    - **Reserva**: escolhe a caixinha (obrigatório) e a direção
      (Aplicação/Retirada). Sem categoria, sem estrutura de custo, sem
      meio de pagamento — caixinha é reserva, não despesa nem investimento.
    - **Estorno/Ressarcimento**: busca a despesa original por descrição
      (`GET /transacoes?tipo_movimento=despesa&descricao=...`, com debounce
      — não carrega o histórico inteiro de despesas na abertura do
      formulário) e pré-preenche conta/categoria/subcategoria/estrutura a
      partir dela.
  - Ao salvar, tela de confirmação com atalho pra lançar outro ou voltar
    ao Dashboard.

## O que falta (próximas entregas)

Lançamentos (lista/busca), Planejamento (orçamento) e Estruturas de Custo
ainda são placeholders.
