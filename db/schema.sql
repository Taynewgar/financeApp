-- Finance App — schema inicial (Supabase/Postgres)
-- Reflete as decisões da fase de discovery:
--   * "conta" cobre corrente/cartão/carteira/caixinha-reserva, com dia de
--     fechamento/vencimento já previsto para a feature de fatura de cartão.
--   * subcategoria carrega uma sugestão de estrutura de custo (fixo/variável/
--     sazonal), não uma verdade fixa — o campo na transação é sempre editável
--     (categorias mistas como "Lazer" usam isso).
--   * parcelamento materializa cada parcela como uma transação própria,
--     ligada por compra_parcelada_id — espelha a fatura real do cartão.
--   * fatura_referencia é calculada a partir de data_compra + dia_fechamento
--     da conta; fatura_override permite mover manualmente sem alterar a
--     data real da compra (caso de liquidação atrasada pelo lojista/adquirente).
--   * orçamento é versionado por vigência mensal (não múltiplos templates).
--   * hash_dedup garante idempotência na migração e em importações futuras.

create extension if not exists "pgcrypto";

-- ── CONTAS ──────────────────────────────────────────────────────────────
create table contas (
    id uuid primary key default gen_random_uuid(),
    user_id uuid not null references auth.users(id) on delete cascade,
    nome text not null,
    tipo_conta text not null check (tipo_conta in (
        'corrente', 'cartao_credito', 'carteira', 'caixinha', 'investimento'
    )),
    banco text,
    saldo_inicial numeric(14,2) not null default 0,
    dia_fechamento smallint check (dia_fechamento between 1 and 31),
    dia_vencimento smallint check (dia_vencimento between 1 and 31),
    ativo boolean not null default true,
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now()
);

-- ── CATEGORIAS / SUBCATEGORIAS ──────────────────────────────────────────
create table categorias (
    id uuid primary key default gen_random_uuid(),
    user_id uuid not null references auth.users(id) on delete cascade,
    nome text not null,
    -- receita/investimento têm 1 categoria "pai" fixa por usuário (a
    -- escolha do lançamento fica só na subcategoria); despesa é onde mora
    -- a variedade real de categorias/subcategorias
    tipo text not null default 'despesa' check (tipo in ('receita', 'despesa', 'investimento')),
    ativo boolean not null default true,
    created_at timestamptz not null default now(),
    unique (user_id, nome)
);

create table subcategorias (
    id uuid primary key default gen_random_uuid(),
    user_id uuid not null references auth.users(id) on delete cascade,
    categoria_id uuid not null references categorias(id) on delete cascade,
    nome text not null,
    -- sugestão pré-preenchida no formulário; null = força escolha explícita
    -- (subcategorias sabidamente mistas, ex: Lazer > Viagens)
    estrutura_custo_padrao text check (estrutura_custo_padrao in ('fixo', 'variavel', 'sazonal', 'investimentos')),
    ativo boolean not null default true,
    created_at timestamptz not null default now(),
    unique (categoria_id, nome)
);

-- ── CAIXINHAS (reservas) ────────────────────────────────────────────────
create table caixinhas (
    id uuid primary key default gen_random_uuid(),
    user_id uuid not null references auth.users(id) on delete cascade,
    nome text not null,
    conta_id uuid references contas(id) on delete set null,
    ativo boolean not null default true,
    created_at timestamptz not null default now(),
    unique (user_id, nome)
);

-- ── COMPRAS PARCELADAS (cabeçalho do grupo de parcelas) ────────────────
create table compras_parceladas (
    id uuid primary key default gen_random_uuid(),
    user_id uuid not null references auth.users(id) on delete cascade,
    descricao text not null,
    valor_total numeric(14,2) not null check (valor_total >= 0),
    parcela_total smallint not null check (parcela_total >= 1),
    created_at timestamptz not null default now()
);

-- ── TRANSAÇÕES ───────────────────────────────────────────────────────────
create table transacoes (
    id uuid primary key default gen_random_uuid(),
    user_id uuid not null references auth.users(id) on delete cascade,

    data_compra date not null,
    valor numeric(14,2) not null check (valor >= 0),
    descricao text,

    tipo_movimento text not null check (tipo_movimento in (
        'receita', 'despesa', 'aplicacao', 'retirada', 'estorno', 'ressarcimento'
    )),
    pagamento text not null default 'avista' check (pagamento in ('avista', 'parcelado')),
    parcela_atual smallint,
    parcela_total smallint,
    compra_parcelada_id uuid references compras_parceladas(id) on delete cascade,

    conta_id uuid not null references contas(id),
    categoria_id uuid references categorias(id),
    subcategoria_id uuid references subcategorias(id),
    -- editável por transação mesmo quando a subcategoria sugere um valor
    estrutura_custo text check (estrutura_custo in ('fixo', 'variavel', 'sazonal', 'investimentos')),
    caixinha_id uuid references caixinhas(id),

    -- etiqueta descritiva de como a transação saiu da conta — não tem
    -- saldo próprio nem vira transferência entre contas, é só metadado
    -- pra filtro/análise (ex: distinguir Pix de boleto numa conta corrente)
    meio_pagamento text check (meio_pagamento in (
        'pix', 'cartao_debito', 'cartao_credito', 'boleto', 'debito_automatico', 'dinheiro', 'transferencia', 'outro'
    )),

    -- fatura de cartão: calculada por padrão (data_compra + dia_fechamento
    -- da conta), com override manual para o caso de liquidação atrasada
    fatura_referencia date,
    fatura_override boolean not null default false,

    -- vincula estorno/ressarcimento à despesa original
    ajuste_de_transacao_id uuid references transacoes(id),

    -- garante idempotência na migração inicial e em importações futuras
    hash_dedup text not null unique,

    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now()
);

create index idx_transacoes_user_data on transacoes (user_id, data_compra);
create index idx_transacoes_conta on transacoes (conta_id);
create index idx_transacoes_fatura on transacoes (conta_id, fatura_referencia);
create index idx_transacoes_compra_parcelada on transacoes (compra_parcelada_id);

-- ── ORÇAMENTO (versionado por mês de vigência) ──────────────────────────
create table orcamentos (
    id uuid primary key default gen_random_uuid(),
    user_id uuid not null references auth.users(id) on delete cascade,
    vigencia_mes date not null, -- primeiro dia do mês a partir do qual vale

    receita_base numeric(14,2) not null default 0,
    percentual_geral numeric(5,2) not null default 0 check (percentual_geral between 0 and 100),

    limite_custos_fixos numeric(5,2) not null default 40,
    limite_custos_variaveis numeric(5,2) not null default 25,
    limite_sazonalidades numeric(5,2) not null default 10,
    limite_investimentos numeric(5,2) not null default 25,

    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now(),
    unique (user_id, vigencia_mes)
);

create table orcamento_itens (
    id uuid primary key default gen_random_uuid(),
    orcamento_id uuid not null references orcamentos(id) on delete cascade,
    bucket text not null check (bucket in (
        'custos_fixos', 'custos_variaveis', 'sazonalidades', 'investimentos'
    )),
    categoria_id uuid references categorias(id),
    subcategoria_id uuid references subcategorias(id),
    nome text, -- usado por itens de investimentos sem subcategoria (ex: "Liberdade Financeira")
    -- liga um item de investimento/reserva à conta real que guarda o saldo
    conta_vinculada_id uuid references contas(id),

    orcamento_mensal numeric(14,2) not null default 0,
    percentual numeric(5,2) not null default 0 check (percentual between 0 and 100),
    -- modelo de envelope acumulativo: sobra (ou estouro, se negativo) trazida
    -- do mês anterior para este item, gerada por POST /orcamentos/{id}/proximo-mes;
    -- "disponível neste mês" = orcamento_mensal + saldo_anterior
    saldo_anterior numeric(14,2) not null default 0,
    ativo boolean not null default true,

    created_at timestamptz not null default now()
);

-- ── RLS: cada usuário só vê seus próprios dados ─────────────────────────
alter table contas enable row level security;
alter table categorias enable row level security;
alter table subcategorias enable row level security;
alter table caixinhas enable row level security;
alter table compras_parceladas enable row level security;
alter table transacoes enable row level security;
alter table orcamentos enable row level security;
alter table orcamento_itens enable row level security;

create policy "contas: dono" on contas for all using (auth.uid() = user_id) with check (auth.uid() = user_id);
create policy "categorias: dono" on categorias for all using (auth.uid() = user_id) with check (auth.uid() = user_id);
create policy "subcategorias: dono" on subcategorias for all using (auth.uid() = user_id) with check (auth.uid() = user_id);
create policy "caixinhas: dono" on caixinhas for all using (auth.uid() = user_id) with check (auth.uid() = user_id);
create policy "compras_parceladas: dono" on compras_parceladas for all using (auth.uid() = user_id) with check (auth.uid() = user_id);
create policy "transacoes: dono" on transacoes for all using (auth.uid() = user_id) with check (auth.uid() = user_id);
create policy "orcamentos: dono" on orcamentos for all using (auth.uid() = user_id) with check (auth.uid() = user_id);
create policy "orcamento_itens: dono via orcamento" on orcamento_itens for all
    using (exists (select 1 from orcamentos o where o.id = orcamento_id and o.user_id = auth.uid()))
    with check (exists (select 1 from orcamentos o where o.id = orcamento_id and o.user_id = auth.uid()));
