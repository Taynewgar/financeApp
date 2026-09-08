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
  `Lancamentos` é a lista/busca de lançamentos (ver abaixo); Planejamento e
  Estruturas de Custo ainda são placeholders.
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

## Deploy (Vercel)

O `vercel.json` fica na **raiz do repositório** (não dentro de `frontend/`)
de propósito: em vez de exigir que você mude o campo *Root Directory* na
tela de import do Vercel (esse campo às vezes nem aparece editável até o
projeto já existir), o `buildCommand` já entra na pasta `frontend` sozinho
— zero configuração manual de diretório. Ele também cuida do rewrite pra
`index.html` (necessário porque as rotas são client-side via
`react-router-dom`; sem isso, abrir `/dashboard` direto ou dar F5 numa
rota interna retorna 404).

1. Em [vercel.com](https://vercel.com), *Add New → Project*, importe este
   repositório (GitHub). Não precisa mexer em Root Directory nem em build
   command/output — o `vercel.json` da raiz já resolve isso.
2. Em *Environment Variables*, adicione as 3 mesmas variáveis do
   `.env.local`: `VITE_SUPABASE_URL`, `VITE_SUPABASE_ANON_KEY` (mesmas do
   backend), `VITE_API_BASE_URL` (a URL do backend no Render — algo como
   `https://financeapp-api.onrender.com`, sem barra no final).
3. Deploy. O Vercel dá uma URL (`https://seu-projeto.vercel.app`).
4. **Passo final, no Render**: defina `FRONTEND_ORIGINS` com essa URL do
   Vercel (ver `README.md` da raiz, passo 6 do Setup do backend) — sem
   isso o navegador bloqueia por CORS toda chamada do frontend publicado
   pro backend, mesmo com tudo certo.

Se em algum momento preferir usar o campo *Root Directory* do Vercel em
vez do `vercel.json` da raiz (ex: outro projeto for adicionado depois
neste mesmo monorepo), é só apontar Root Directory pra `frontend` e
apagar o `vercel.json` da raiz — o projeto Vite continua funcionando do
mesmo jeito, é só uma forma alternativa de configurar a mesma coisa.

Depois de configurado, todo `git push` nesta branch redeploya sozinho —
sem precisar rodar nada manualmente.

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
  categoria, também editáveis) e Caixinhas, em abas. Listas sempre
  ordenadas por nome, mesmo logo após criar/editar (sem precisar
  recarregar a página). A conta vinculada de uma caixinha pode ser
  trocada livremente aqui — quem trava é o Novo Lançamento (ver abaixo).
- Ao entrar no app, dispara um `GET /health` em segundo plano pra começar
  a "acordar" o backend (planos free do Render hibernam após
  inatividade) antes que a primeira tela realmente precise de dados.
- **Novo Lançamento** (`/lancamentos/novo`), formulário completo:
  - Tipo: Receita / Despesa / Investimento / Reserva / Estorno-Ressarcimento
    (segmentado, não é um select cru com os 6 valores do banco). Cada tipo
    só mostra os campos que fazem sentido pra ele:
    - **Despesa**: categoria, estrutura de custo e meio de pagamento são
      **obrigatórios** (o backend também recusa com 422 se faltar algum —
      ver `_check_campos_obrigatorios` em `backend/app/routers/
      transacoes.py`); subcategoria continua opcional. Sub-toggle À
      vista/Parcelado (parcelado usa `POST /transacoes/parceladas`, mesma
      obrigatoriedade). Se a conta escolhida é do tipo `cartao_credito`, o
      meio de pagamento trava automaticamente em "Cartão de crédito" (não
      faz sentido pagar uma despesa lançada no cartão de outra forma).
    - **Receita**: escolhe entre as categorias do tipo `receita` (pode ter
      mais de uma — ex: "Salário", "Freelance") + subcategoria. Sem
      estrutura de custo, sem meio de pagamento, sem caixinha.
    - **Investimento**: escolhe entre as categorias do tipo `investimento`
      + subcategoria; estrutura de custo sempre fixa em `investimentos`,
      qualquer que seja a categoria. Sem meio de pagamento, sem caixinha.
    - **Reserva**: escolhe a caixinha (obrigatório) e a direção
      (Aplicação/Retirada). Sem categoria, sem estrutura de custo, sem
      meio de pagamento — caixinha é reserva, não despesa nem investimento.
      Se a caixinha escolhida tem uma conta vinculada, o campo Conta trava
      nela automaticamente (mesmo princípio do cartão de crédito travando
      o meio de pagamento) — a reserva "mora" numa conta específica, não
      faz sentido lançar a movimentação em outra. Backend também recusa
      (422) se a conta enviada não bater com a da caixinha.
    - **Estorno/Ressarcimento**: busca a despesa original por descrição
      (`GET /transacoes?tipo_movimento=despesa&descricao=...`, com debounce
      — não carrega o histórico inteiro de despesas na abertura do
      formulário) e pré-preenche conta/categoria/subcategoria/estrutura a
      partir dela.
  - Ao salvar, tela de confirmação com atalho pra lançar outro ou voltar
    ao Dashboard.

- **Lançamentos** (`/lancamentos`), lista/busca:
  - Filtros: tipo de movimento, texto na descrição (com debounce), período,
    conta, categoria, subcategoria (dependente da categoria), caixinha,
    estrutura de custo e meio de pagamento — mesmos filtros de
    `GET /transacoes` no backend.
  - Cartões de resumo (total de lançamentos, receitas, despesas líquidas,
    fluxo de caixa, taxa de poupança) vindos de `GET /transacoes/resumo`,
    recalculados sobre exatamente o mesmo conjunto filtrado.
  - Cada lançamento mostra data, descrição, valor (colorido por tipo),
    conta/categoria/subcategoria/caixinha/meio de pagamento e parcela (se
    parcelado). Exclusão direta na lista (`DELETE /transacoes/{id}`, com
    confirmação) — útil pra corrigir um lançamento de teste.

## O que falta (próximas entregas)

Planejamento (orçamento) e Estruturas de Custo ainda são placeholders.
