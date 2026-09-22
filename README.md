# financeApp

Relatório financeiro pessoal — migrando de app desktop offline (Tkinter) para
PWA com backend hospedado (Render) e banco Supabase.

## Estrutura

- `backend/` — API FastAPI.
  - `app/main.py` — monta os routers. `/health` responde mesmo sem o
    Supabase configurado.
  - `app/db.py` — dois clientes Supabase: `get_service_client()` (só para
    tarefas administrativas, ignora RLS) e `get_user_client()` (autenticado
    como o usuário da requisição, respeita RLS). Os dois compartilham um
    único `httpx.Client` (conexão TCP/TLS reaproveitada entre requisições)
    — criar um novo a cada chamada, como o SDK faz por padrão, paga o
    handshake inteiro toda vez, o maior fator por trás da lentidão notável
    em cada troca de tela. O token de autenticação continua isolado por
    requisição (nunca é escrito no `httpx.Client` compartilhado), então
    não há risco de misturar sessão entre usuários concorrentes.
  - `app/auth.py` — valida o token `Authorization: Bearer <token>` de cada
    requisição. Local, via a chave pública do projeto (JWKS, buscada a
    partir da `SUPABASE_URL` e cacheada — sem segredo pra configurar);
    se o projeto ainda usa assinatura simétrica (HS256) legada, sem chave
    pública pra publicar, cai automaticamente pra validar direto contra o
    endpoint do Supabase (mais lento — uma chamada de rede a mais por
    request — mas funciona sem exigir nada a mais do usuário).
  - `app/routers/` — CRUD de contas, categorias (cada uma com um `tipo`:
    `receita`/`despesa`/`investimento` — receita e investimento podem ter
    mais de uma categoria cada, despesa é onde mora a maior variedade),
    subcategorias, caixinhas, transações (com parcelamento e fatura por
    ciclo de fechamento) e
    orçamento (versionado por mês de vigência, com itens por bucket:
    custos fixos/variáveis, sazonalidades, investimentos — modelo de
    envelope acumulativo via `POST /orcamentos/{id}/proximo-mes`, que
    fecha o mês e carrega a sobra/estouro de cada item para o mês seguinte).
    `GET /transacoes` aceita filtros (categoria, subcategoria, conta,
    caixinha, tipo de movimento, estrutura de custo, meio de pagamento,
    período, texto na descrição) — é a Busca de Lançamentos do app
    original; `GET /transacoes/resumo` calcula os mesmos cartões de resumo
    (as duas leituras financeiras) sobre o conjunto filtrado. `meio_pagamento`
    é só uma etiqueta (pix/cartao_debito/cartao_credito/boleto/
    debito_automatico/dinheiro/transferencia/outro) — não tem saldo próprio
    nem gera transferência entre contas, é `conta` que continua sendo o
    ledger de verdade. Parcelamento (`POST /transacoes/parceladas`) não é
    exclusivo de cartão de crédito (ex: Pix parcelado numa conta corrente)
    — só "mover fatura" (`PATCH /transacoes/{id}/fatura`) exige conta do
    tipo `cartao_credito`, retornando 422 caso contrário. `PATCH
    /transacoes/{id}` edita um lançamento à vista por completo (mesmas
    validações do `POST`) — parcela de compra parcelada retorna 422 (edite
    excluindo e lançando de novo, pra não quebrar a consistência do grupo);
    se a fatura já tinha sido movida manualmente, a edição preserva essa
    referência em vez de recalcular pelo dia de fechamento. Caixinha é
    reserva, não despesa nem investimento: só pode ser vinculada a uma
    transação de `aplicacao`/`retirada`, e uma categoria vinculada precisa
    ter o `tipo` compatível com o tipo de movimento (receita/despesa/
    investimento) — qualquer uma dessas combinações erradas retorna 422.
    Caixinha vinculada a uma conta "mora" nessa conta: a transação
    precisa usar a mesma `conta_id` da caixinha (422 se não bater) — a
    conta vinculada da caixinha em si pode ser trocada livremente via
    `PATCH /caixinhas/{id}`.
    Despesa exige `categoria_id`, `estrutura_custo` e `meio_pagamento`
    preenchidos (422 se faltar algum — vale pra `POST /transacoes` e
    `POST /transacoes/parceladas`); aplicação/retirada sem `caixinha_id`
    (ou seja, investimento de verdade, não reserva) exige `estrutura_custo`
    preenchido pelo mesmo motivo. Os demais tipos de movimento (receita,
    estorno, ressarcimento, e aplicação/retirada COM caixinha) continuam
    sem exigir nenhum desses três campos.

    **Despesa fixa recorrente** (`lancamentos_recorrentes` — aluguel,
    assinaturas) usa **projeção virtual**: cadastrar um recorrente não
    grava nada em `transacoes` — só quando um mês específico é confirmado
    (`POST /lancamentos-recorrentes/{id}/confirmar`) é que a transação real
    nasce (`tipo_movimento='despesa'`, vinculada de volta via
    `lancamento_recorrente_id`). Decisão contra a alternativa óbvia
    (materializar parcelas futuras de uma vez, como compra parcelada):
    materializar exigiria um job periódico pra ir "abastecendo" mais meses
    conforme o tempo passa — o projeto não tem nenhum cron — e deixaria
    `transacoes` com linhas "no futuro" numa tabela pensada como histórico
    do que já aconteceu. `GET /dashboard/compromissos-futuros` mistura a
    próxima parcela de cada compra parcelada com a próxima ocorrência
    PENDENTE de cada recorrente ativo (pode ser um mês já vencido, se
    ficou sem confirmar — some da lista só quando confirmado ou o
    recorrente é desativado). Confirmar o mesmo mês duas vezes retorna 409;
    apagar o molde não apaga meses já confirmados (`ON DELETE SET NULL`).

    `GET /estrutura-custo/{vigencia_mes}` compara orçado x realizado do mês
    (por categoria/subcategoria, agrupado nos mesmos buckets do orçamento),
    lendo diretamente das transações — funciona mesmo sem orçamento
    configurado para o mês, e uma despesa sem `estrutura_custo` preenchida
    aparece no bucket `sem_estrutura` em vez de sumir da soma. Aplicação/
    retirada vinculada a uma categoria de investimento cai no bucket
    `investimentos` (com teto/piso); vinculada a uma caixinha cai no bucket
    `reservas` (só informativo, sem teto nem piso — reserva não é meta de
    investimento).

    **Orçamento: macro em %, micro em R$.** O orçamento define percentuais
    (`percentual_geral` e `limite_*` por bucket) sobre `receita_base` — isso
    gera um teto em R$ por bucket (`receita_base × percentual_geral% ×
    limite_bucket%`). Dentro de cada bucket, os itens são cadastrados em R$
    (`orcamento_mensal`), e a API calcula e devolve as duas leituras de
    percentual de cada item (`percentual_da_renda` = sobre a renda total;
    `percentual_do_teto` = sobre o teto do próprio bucket) — nenhuma delas é
    aceita como entrada, são sempre calculadas. Criar/editar/reativar um
    item que faria a soma do bucket ultrapassar o teto retorna `422` (você
    digita livre, mas não salva estourado). O teto usado nessa validação já
    é o efetivo: teto puro + a soma do `saldo_anterior` de todos os itens
    ativos daquele bucket (a sobra acumulada do envelope) — se Custos Fixos
    sobrou R$200 no total do mês passado, o teto pra alocar itens novos
    esse mês já nasce R$200 maior. Essa mesma soma por bucket (sem misturar
    com os outros) também aparece em `GET /estrutura-custo/{vigencia_mes}`,
    campo `saldo_anterior_acumulado` de cada bucket — o detalhe por item
    continua disponível em `GET /orcamentos/{id}/itens`, isso é só a visão
    agregada.

    **Pool de despesas e piso de investimentos** (`GET
    /estrutura-custo/{vigencia_mes}`, campos `pool_despesas` e
    `piso_investimentos`): `custos_fixos` + `custos_variaveis` +
    `sazonalidades` são tratados como um teto agregado único — estourar um
    deles não compromete o mês se sobrar nos outros dois, e só o total dos
    três é comparado contra a soma dos três tetos (mais o `saldo_anterior`
    acumulado dos itens desses buckets). `investimentos` é o oposto: não é
    teto, é piso — a meta é bater pelo menos aquele valor.
    `GET /dashboard/mensal/{vigencia_mes}` e `GET /dashboard/evolucao` dão
    as duas leituras financeiras herdadas do app original — fluxo de caixa
    (bruto) e saúde financeira (líquida de estornos/ressarcimentos
    vinculados a uma despesa, que não contam como receita nova) — com taxa
    de poupança e resultado acumulado mês a mês.
- `db/schema.sql` — schema inicial do Postgres (contas, categorias,
  subcategorias, caixinhas, transações, lançamentos recorrentes, orçamento
  versionado por mês), com Row Level Security por usuário.
- `frontend/` — PWA em React + Vite + TypeScript, consome a API do
  `backend/`. Login (Supabase Auth), rotas protegidas, casca de navegação
  (sidebar no desktop, barra inferior no mobile, botão flutuante de Novo
  Lançamento). Telas com dados reais: Dashboard (KPIs do mês + gráfico de
  evolução), Lançamentos (lista/busca/edição), Novo Lançamento, e
  Configurações (CRUDs de Contas/Categorias/Caixinhas/Despesas Fixas
  Recorrentes), e Planejamento
  (configuração do orçamento por mês — renda, % por bucket, itens reativos
  a partir dos lançamentos, modo envelope). Estruturas de Custo ainda é
  placeholder — próxima tela da fila (motor já pronto no backend).
  Decisões de escopo e changelog tela a tela em
  `docs/changelog-proposta-original-do-redesign.md`. Detalhes técnicos em
  `frontend/README.md`.
- `render.yaml` — blueprint de deploy no Render (backend).
- `vercel.json` — build do frontend no Vercel a partir da raiz do repo
  (entra em `frontend/` sozinho — evita depender do campo Root Directory
  na tela de import do Vercel). Detalhes em `frontend/README.md`.

## Setup

1. Crie um projeto em [supabase.com](https://supabase.com) (sua própria conta).
2. Em *SQL Editor*, rode o conteúdo de `db/schema.sql`.
3. Em *Project Settings → API*: copie a **Project URL**, a **anon key** (ou
   **publishable key**, no formato novo) e a **service_role key** (ou
   **secret key**). Em *Project Settings → Database → Connection string*:
   copie a URI (pooler).
4. Copie `backend/.env.example` para `backend/.env` e preencha os quatro
   valores localmente (esse arquivo nunca é commitado).
5. No serviço do Render (criado via blueprint), confirme em *Environment*
   que as 4 variáveis estão preenchidas: `SUPABASE_URL`,
   `SUPABASE_ANON_KEY`, `SUPABASE_SERVICE_ROLE_KEY`, `DATABASE_URL` — cole
   os valores direto no painel do Render, nunca em texto de chat ou commit.
   (Não precisa de nenhum segredo de JWT: a validação de token usa a
   chave pública do projeto via JWKS, buscada automaticamente a partir da
   `SUPABASE_URL` — funciona tanto com o par anon/service_role legado
   quanto com o publishable/secret novo, e não depende do JWT Secret que
   o Supabase está descontinuando.)
6. Ainda no Render, defina `FRONTEND_ORIGINS` com a URL do frontend
   publicado (ex: `https://seu-app.vercel.app`) — sem isso, o navegador
   bloqueia por CORS toda chamada do frontend em produção pro backend,
   mesmo com tudo certo (dá pra confirmar isso no DevTools do navegador:
   erro de CORS no console, não erro de rede). Em dev local não precisa
   configurar nada — `http://localhost:5173` (porta padrão do Vite) já
   vem liberado por padrão.

### Migração pendente no seu Supabase: `orcamento_itens.saldo_anterior`

Se o seu projeto Supabase já existia antes desta entrega (envelope
acumulativo no orçamento), rode isto uma vez no *SQL Editor* antes de usar
`POST /orcamentos/{id}/proximo-mes` ou os testes de integração de orçamento
— sem essa coluna, a API responde 500 nesse endpoint:

```sql
alter table orcamento_itens
  add column if not exists saldo_anterior numeric(14,2) not null default 0;
```

Um projeto novo, criado rodando `db/schema.sql` já com esta versão, não
precisa desse passo — a coluna já nasce criada.

### Migração pendente no seu Supabase: `transacoes.meio_pagamento`

Mesma situação para a etiqueta de meio de pagamento — se o projeto já
existia antes desta entrega, rode uma vez no *SQL Editor*:

```sql
alter table transacoes
  add column if not exists meio_pagamento text
    check (meio_pagamento in ('pix', 'cartao_debito', 'boleto', 'debito_automatico', 'dinheiro', 'transferencia', 'outro'));
```

### Migração pendente no seu Supabase: `categorias.tipo` + estrutura "investimentos" + "cartão de crédito"

Categoria agora sabe se é receita/despesa/investimento (receita e
investimento têm 1 categoria "pai" fixa; despesa é onde mora a variedade),
estrutura de custo ganhou o valor `investimentos` (fixo pra transações de
investimento) e meio de pagamento ganhou `cartao_credito`. Se o projeto já
existia antes desta entrega, rode uma vez no *SQL Editor* (os nomes de
constraint abaixo são os que o Postgres gera por padrão — confira com `\d
transacoes` / `\d subcategorias` se algum `drop constraint` der erro de
"does not exist"):

```sql
alter table categorias
  add column if not exists tipo text not null default 'despesa'
    check (tipo in ('receita', 'despesa', 'investimento'));

alter table subcategorias drop constraint if exists subcategorias_estrutura_custo_padrao_check;
alter table subcategorias
  add constraint subcategorias_estrutura_custo_padrao_check
  check (estrutura_custo_padrao in ('fixo', 'variavel', 'sazonal', 'investimentos'));

alter table transacoes drop constraint if exists transacoes_estrutura_custo_check;
alter table transacoes
  add constraint transacoes_estrutura_custo_check
  check (estrutura_custo in ('fixo', 'variavel', 'sazonal', 'investimentos'));

alter table transacoes drop constraint if exists transacoes_meio_pagamento_check;
alter table transacoes
  add constraint transacoes_meio_pagamento_check
  check (meio_pagamento in ('pix', 'cartao_debito', 'cartao_credito', 'boleto', 'debito_automatico', 'dinheiro', 'transferencia', 'outro'));
```

Depois de rodar isso, todas as categorias existentes ficam com
`tipo = 'despesa'` — use a nova tela de Categorias (Configurações no
frontend, ou `PATCH /categorias/{id}`) pra marcar qual categoria é a de
Receita e qual é a de Investimentos (o Novo Lançamento usa essas duas
automaticamente).

### Migração pendente no seu Supabase: `lancamentos_recorrentes`

Despesa fixa recorrente (aluguel, assinaturas) ganhou tabela própria —
projeção virtual, nada é gravado em `transacoes` até o mês ser confirmado
em "Compromissos Futuros" (ver seção "Transações" abaixo). Se o projeto já
existia antes desta entrega, rode uma vez no *SQL Editor*:

```sql
create table if not exists lancamentos_recorrentes (
    id uuid primary key default gen_random_uuid(),
    user_id uuid not null references auth.users(id) on delete cascade,
    descricao text not null,
    valor numeric(14,2) not null check (valor >= 0),
    dia_mes smallint not null check (dia_mes between 1 and 31),
    conta_id uuid not null references contas(id),
    categoria_id uuid not null references categorias(id),
    subcategoria_id uuid references subcategorias(id),
    estrutura_custo text not null check (estrutura_custo in ('fixo', 'variavel', 'sazonal')),
    meio_pagamento text not null check (meio_pagamento in (
        'pix', 'cartao_debito', 'cartao_credito', 'boleto', 'debito_automatico', 'dinheiro', 'transferencia', 'outro'
    )),
    data_inicio date not null,
    data_fim date,
    ativo boolean not null default true,
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now()
);

create index if not exists idx_lancamentos_recorrentes_user on lancamentos_recorrentes (user_id);

alter table lancamentos_recorrentes enable row level security;
create policy "lancamentos_recorrentes: dono" on lancamentos_recorrentes for all
  using (auth.uid() = user_id) with check (auth.uid() = user_id);

alter table transacoes
  add column if not exists lancamento_recorrente_id uuid references lancamentos_recorrentes(id) on delete set null;

create index if not exists idx_transacoes_lancamento_recorrente on transacoes (lancamento_recorrente_id);
```

Um projeto novo, criado rodando `db/schema.sql` já com esta versão, não
precisa desse passo — tabela e coluna já nascem criadas.

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

Se uma rodada anterior for interrompida no meio (Ctrl+C, timeout de rede)
antes da fixture de limpeza terminar, sobra lixo no banco — sintoma típico:
`duplicate key value violates unique constraint "categorias_user_id_nome_key"`
ou um `orcamento["id"]` faltando porque já existe orçamento pro mesmo mês.
Rode `tests/limpar_dados_integracao.py` (ver seção abaixo) pra zerar a
conta de teste e destravar.

O script `tests/manual_verification.py` (anterior a essa suíte) continua
funcionando como um roteiro único de fumaça, mas os testes de integração
acima são mais completos e específicos — prefira-os.

### Popular dados de teste (`tests/seed_dados_teste.py`)

Pra testar telas manualmente (Lançamentos, Dashboard, Estrutura de Custo)
com uma massa de dados mais coerente do que uns poucos lançamentos soltos,
sem digitar cada um na mão: cria contas/categorias/caixinhas (reaproveita se
já existirem, pelo nome) e alguns meses de lançamentos variados — salário,
aluguel, mercado, lazer, aporte, reserva, uma compra parcelada. Também cria
um orçamento encadeado (um por mês, sobra rolando) pros últimos 3 meses + o
atual, pra testar Planejamento/Estrutura de Custo já com sobra acumulada —
reaproveita se já existir orçamento pro mês (idempotente). Lançamentos com
descrição prefixada `[seed]`, pra dar pra identificar e remover depois:

```bash
cd backend
source venv/bin/activate
TEST_USER_EMAIL=teste@teste.com TEST_USER_PASSWORD=teste python tests/seed_dados_teste.py

# pra remover depois (só o que tem o prefixo [seed], nunca lançamentos seus):
TEST_USER_EMAIL=teste@teste.com TEST_USER_PASSWORD=teste python tests/seed_dados_teste.py --limpar
```

Roda contra o Supabase de verdade (mesmo usuário dos testes de integração)
— não é ambiente de CI.

### Resetar a conta de teste (`tests/limpar_dados_integracao.py`)

Apaga (DELETE de verdade, não desativa) tudo que a conta `TEST_USER_EMAIL`
tem em transações/orçamentos/caixinhas/compras parceladas/categorias/
contas — pra destravar os testes de integração quando uma rodada anterior
deixou dados presos (ver nota acima). Pede confirmação antes, mostrando
quantas linhas existem em cada tabela; só mexe no `user_id` dessa conta de
teste, nunca no seu usuário pessoal:

```bash
cd backend
source venv/bin/activate
TEST_USER_EMAIL=teste@teste.com TEST_USER_PASSWORD=teste python tests/limpar_dados_integracao.py
```
