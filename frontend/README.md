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
  flutuante de "+" pra Novo Lançamento a partir de qualquer tela. A
  navegação lateral (`.shell-nav`) é `position: sticky` — fica fixa no
  viewport ao rolar o conteúdo (antes acompanhava o scroll do corpo da
  página, comportamento não intencional corrigido 2026-09-24, `docs/
  backlog.md` item 17).
- `src/lib/types.ts` — tipos TS espelhando os schemas Pydantic do backend
  (mesmos nomes de campo, pra não precisar traduzir mentalmente).
- `src/lib/rotulos.ts` — rótulos/mapeamentos compartilhados entre
  `NovoLancamento`, `EditarLancamento` e `Lancamentos` (estrutura de custo,
  meio de pagamento, tipo de movimento).
- `src/lib/formatar.ts` — `formatarMoeda`/`formatarData` (pt-BR);
  `formatarMoedaCompacta` (`"1,8 mil"`, sem `R$`/centavos) pra espaços
  apertados onde o formato completo não cabe.
- `src/lib/LancamentosFiltrosContext.tsx`, `GraficosPeriodoContext.tsx`,
  `EstruturaCustoContext.tsx`, `PlanejamentoContext.tsx` — estado de
  filtro/período de cada tela sobrevivendo à navegação (`docs/
  backlog.md`, item 13, decidido 2026-09-24): Context React montado no
  `AppShell` (que fica montado o tempo todo — só o `<Outlet/>` troca
  entre rotas), não `sessionStorage`/`localStorage` — não precisa
  sobreviver a fechar a aba, só à navegação dentro do app. Cada tela usa
  seu hook (`useLancamentosFiltros`/`useGraficosPeriodo`/
  `useEstruturaCustoMes`/`usePlanejamentoMes`) no lugar do `useState`
  local que tinha antes; o resto do componente não muda.
- `src/lib/escala.ts` — marcações "redondas" (1/2/5 × potência de 10) pro
  eixo Y do gráfico de evolução.
- `src/components/EvolucaoChart.tsx` — gráfico de linha (SVG puro) usado no
  Dashboard, com hover/crosshair/tooltip e alternância pra tabela.
- `src/components/InfoIcon.tsx` — círculo pequeno com "?", usado ao lado
  de rótulos que têm explicação extra. Recebe o texto via prop `texto` e
  mostra num balão próprio ao ser clicado/tocado — não depende de
  `title`/hover nativo, que não existe em touchscreen (bug reportado
  2026-09-24: no mobile, tocar não mostrava nada). Fecha ao clicar fora ou
  Esc. Componente único pro app inteiro (Dashboard, Lançamentos, Base da
  média em `SeletorPeriodo`), em vez de um ícone por tela.
- `src/components/cabecalhoFixo.css` — controles fixos no topo do
  conteúdo ao rolar (`docs/backlog.md`, item 16, decidido via mockups
  2026-09-24): `.cabecalho-fixo` é só a mecânica (`position: sticky`);
  `.cabecalho-fixo-card` dá o visual de card pra tela que não tem um card
  próprio pra encaixar (Dashboard/Estrutura de Custo/Planejamento —
  Gráficos reaproveita o card que `SeletorPeriodo` já desenha, então
  não usa essa classe); `.cabecalho-fixo-grid`/`-stat`/`-barra` são a
  grade compacta de estatísticas/barrinhas de progresso (KPIs no
  Dashboard, alocação por bucket no Planejamento, fita de KPIs na
  Estrutura de Custo) — sempre um resumo **reduzido** do que já existe
  em detalhe mais abaixo na página, não uma fonte de dado própria.
  Lançamentos é a exceção: no mobile o painel de filtro completo não
  cabe fixo (ocupa a tela toda sozinho hoje), então vira uma barra
  resumida ("N filtros ativos ▾") que expande o painel completo por
  cima da lista ao tocar; no desktop o painel completo fica sempre
  fixo, sem colapsar (espaço horizontal sobra).
- `src/routes/` — uma tela por seção. `Dashboard` mostra os KPIs do mês e a
  evolução (ver abaixo); `Configuracoes` tem os CRUDs de Contas/Categorias/
  Caixinhas (ver abaixo);
  `NovoLancamento` é o formulário completo de lançamento (ver abaixo);
  `Lancamentos` é a lista/busca (ver abaixo); `EditarLancamento` edita um
  lançamento à vista existente; Planejamento e Estruturas de Custo ainda
  são placeholders.
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
  inatividade) antes que a primeira tela realmente precise de dados. Se
  isso demorar mais que ~1,5s, um banner no topo avisa que o servidor pode
  estar "acordando" e mostra um contador de segundos, em vez de deixar a
  tela parecendo travada sem explicação; se falhar, o banner vira um aviso
  de erro com botão "Tentar novamente".
- **Dashboard** (`/dashboard`):
  - Seletor de mês (`<input type="month">`), busca `GET /dashboard/mensal/
    {vigencia_mes}` e `GET /dashboard/evolucao` (janela dos últimos 6 meses
    terminando no mês selecionado).
  - Número principal ("Resultado do mês" — a leitura de saúde financeira)
    em destaque, seguido de uma fileira de cartões (Receitas, Despesas
    líquidas, Fluxo de caixa, Taxa de poupança, Reservas no mês), cada um
    com tooltip explicando o cálculo.
  - Gráfico de linha (Receitas x Despesas líquidas ao longo dos 6 meses),
    em SVG puro (sem biblioteca de gráficos): crosshair + tooltip ao passar
    o mouse (ou focar via teclado), legenda, alternância "Ver como tabela"
    (a mesma leitura em `<table>`, sem depender do gráfico pra enxergar os
    números). Cores da paleta categórica validada (azul/laranja — ver skill
    `dataviz`), não o par verde/vermelho usado pra receita/despesa em
    outras telas (esse par falha em daltonismo quando é a única forma de
    diferenciar duas linhas no mesmo gráfico).
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
  - Filtros: tipo de movimento, texto na descrição (com debounce), mês+ano
    rápido (preenche período automaticamente, mas o período personalizado
    continua editável à parte) ou período customizado, conta, categoria,
    subcategoria (dependente da categoria), caixinha, estrutura de custo e
    meio de pagamento — mesmos filtros de `GET /transacoes` no backend. Uma
    resposta de um filtro antigo que chegue depois de um filtro mais novo é
    descartada (guarda contra corrida de requisições), pra nunca mostrar um
    resultado que não bate com os filtros atuais na tela.
  - Cartões de resumo (total de lançamentos, receitas, despesas líquidas,
    fluxo de caixa, taxa de poupança) vindos de `GET /transacoes/resumo`,
    recalculados sobre exatamente o mesmo conjunto filtrado — cada cartão
    tem um tooltip (passar o mouse) explicando o que o número significa.
  - Cada lançamento mostra data, descrição, valor (colorido por tipo —
    verde receita/ajuste, vermelho despesa, azul aplicação/retirada),
    conta/categoria/subcategoria/caixinha/estrutura de custo/meio de
    pagamento e parcela (se parcelado). Edição direta na lista
    (`/lancamentos/:id/editar`, `PATCH /transacoes/{id}`) pra lançamentos à
    vista — parcela de compra parcelada não é editável (exclua e lance de
    novo). Exclusão direta (`DELETE /transacoes/{id}`, com confirmação).

## O que falta (próximas entregas)

Planejamento (orçamento) e Estruturas de Custo ainda são placeholders.
