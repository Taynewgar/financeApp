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
  - `app/routers/` — CRUD de contas, categorias, subcategorias, caixinhas,
    transações (com parcelamento e fatura por ciclo de fechamento) e
    orçamento (versionado por mês de vigência, com itens por bucket:
    custos fixos/variáveis, sazonalidades, investimentos — modelo de
    envelope acumulativo via `POST /orcamentos/{id}/proximo-mes`, que
    fecha o mês e carrega a sobra/estouro de cada item para o mês seguinte).
    `GET /transacoes` aceita filtros (categoria, subcategoria, conta,
    caixinha, tipo de movimento, estrutura de custo, meio de pagamento,
    período, texto na descrição) — é a Busca de Lançamentos do app
    original; `GET /transacoes/resumo` calcula os mesmos cartões de resumo
    (as duas leituras financeiras) sobre o conjunto filtrado. `meio_pagamento`
    é só uma etiqueta (pix/cartao_debito/boleto/debito_automatico/dinheiro/
    transferencia/outro) — não tem saldo próprio nem gera transferência
    entre contas, é `conta` que continua sendo o ledger de verdade.
    Parcelamento (`POST /transacoes/parceladas`) não é exclusivo de cartão
    de crédito (ex: Pix parcelado numa conta corrente) — só "mover fatura"
    (`PATCH /transacoes/{id}/fatura`) exige conta do tipo `cartao_credito`,
    retornando 422 caso contrário.
    `GET /estrutura-custo/{vigencia_mes}` compara orçado x realizado do mês
    (por categoria/subcategoria, agrupado nos mesmos buckets do orçamento),
    lendo diretamente das transações — funciona mesmo sem orçamento
    configurado para o mês, e uma despesa sem `estrutura_custo` preenchida
    aparece no bucket `sem_estrutura` em vez de sumir da soma.

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
