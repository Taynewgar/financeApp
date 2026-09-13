# Proposta original do redesign — o que foi combinado x o que existe hoje

Este documento existe pra não perder o que foi desenhado no início do projeto,
quando o ZIP do app antigo (`v6_Estrutura_de_custos.zip`, Tkinter + relatório
HTML local) foi analisado e viraram 4 mockups de tela. Serve de referência pra
continuar o trabalho sem precisar redescobrir o que já foi decidido.

**Fonte:** artifact de design "Finance App Redesign", publicado a partir da
análise do ZIP original —
[ver mockups interativos](https://claude.ai/code/artifact/aca7d916-7ef2-4b93-b482-bce337d343ed).
As 4 telas também estão exportadas como PNG em `docs/mockups/` (abaixo, uma
por seção) — versionado, sem depender de login nem do artifact continuar no
ar. O ZIP em si não está neste repositório (foi um anexo de conversa, não um
arquivo versionado) — se quiser preservá-lo de forma durável, vale anexar de
novo e commitar num lugar como `docs/app-original/`. Ver também
`plano-de-evolucao-original.md` (a auditoria do ZIP e o plano de fases que
vieram antes destes mockups) e `sugestoes-e-decisoes-do-redesign.md` (a
rodada de perguntas e respostas que veio logo depois deles).

Cada seção abaixo lista o que o mockup propôs, o que existe hoje (código real,
não memória — conferido nos routers/telas na data deste documento) e o que
falta. Legenda: ✅ implementado · 🟡 parcial · ⬜ não implementado.

---

## Dashboard

![Mockup do Dashboard](mockups/dashboard.png)

Mockup: número de patrimônio no topo, seletor de mês com opções de intervalo,
alternância entre as duas leituras financeiras, KPIs com variação percentual
vs mês anterior, saldo por conta, compromissos futuros, evolução de 3 séries,
e despesas por categoria do mês.

| Proposto no mockup | Status | Observação |
|---|---|---|
| Saldo histórico / patrimônio total (topo, "desde jan/2019") | ⬜ | Ainda não existe — depende de contas terem saldo, e isso ficou de fora por decisão explícita (ver changelog 2026-09-13) |
| Seletor de mês | ✅ | `<input type="month">` |
| Intervalo (Todos os meses / mês específico) | ⬜ | Só dá pra ver 1 mês por vez |
| Base da média (Até o mês / Todos os meses) | ⬜ | Não existe esse conceito na tela |
| Alternância "Leitura de Caixa" / "Leitura de Saúde" | ✅ | Toggle segmentado troca o hero e os 3 cards de KPI exibidos |
| KPI: Despesas Líquidas, Receita, Resultado de Saúde, Taxa de Poupança | ✅ | Cards + número principal (hero), divididos entre as duas leituras |
| Delta de cada KPI vs mês anterior (ex: "6,2% vs mês anterior") | ✅ | Calculado no frontend a partir do próprio `/dashboard/evolucao` (penúltimo mês da janela), sem endpoint novo |
| Taxa de poupança acumulada no ano | ⬜ | Backend calcula acumulado em `/dashboard/evolucao` (`taxa_poupanca_acumulada`), mas o Dashboard não expõe isso ainda |
| Patrimônio por conta (saldo de cada conta/caixinha/fatura) | 🟡 | Só caixinhas (`GET /dashboard/patrimonio/{mes}`) — contas seguem sem saldo próprio por decisão do usuário, a definir depois |
| Compromissos futuros (parcelas futuras, fixos recorrentes) | 🟡 | Só parcelas futuras (`GET /dashboard/compromissos-futuros`) — "fixo recorrente" (ex: aluguel todo dia 5) não existe como conceito no app, não tem cadastro próprio, então ficou de fora |
| Evolução mensal — 3 linhas (Receita/Despesa/Resultado) | ✅ | 3ª série (Resultado) adicionada ao `EvolucaoChart`, cor slot 3 (aqua) da paleta validada |
| Despesas por categoria do mês (% por categoria) | ⬜ | Existe conceito parecido na Estrutura de Custo (por bucket, não por categoria), que também não tem frontend ainda |

**Arquivo:** `frontend/src/routes/Dashboard.tsx`, `frontend/src/components/EvolucaoChart.tsx`,
`backend/app/routers/dashboard.py`.

---

## Novo Lançamento

![Mockup do Novo Lançamento](mockups/novo-lancamento.png)

Mockup: tipo em 4 segmentos (Receita/Despesa/Aplicação/Retirada) + checkbox de
estorno/ressarcimento, categorias "mais usadas" com atalho de criação inline,
estrutura de custo sugerida pela subcategoria.

| Proposto no mockup | Status | Observação |
|---|---|---|
| Tipo: Receita/Despesa/Aplicação/Retirada | 🟡 | Evoluiu pra 5 tipos (Receita/Despesa/Investimento/Reserva/Estorno-Ressarcimento) — Aplicação/Retirada do mockup viraram dois tipos "pai" (Investimento e Reserva) distinguidos por ter ou não caixinha vinculada, decidido depois em conversa com base em uso real |
| Toggle À vista/Parcelado | ✅ | |
| Checkbox "É estorno/ressarcimento" | 🟡 | Virou um tipo de movimento próprio (mais estruturado que um checkbox modificador — decisão posterior, não regressão) |
| Valor, data, conta | ✅ | |
| Categoria "mais usadas" (atalho) | ⬜ | Formulário usa select simples com todas as categorias do tipo, sem destaque pras mais usadas |
| "+ Nova" categoria inline, sem sair do formulário | ⬜ | Categoria só pode ser criada em Configurações |
| Subcategoria | ✅ | |
| Estrutura de custo sugerida pela subcategoria | ✅ | `estrutura_custo_padrao` da subcategoria pré-preenche o campo |
| Descrição opcional | ✅ | |

**Arquivo:** `frontend/src/routes/NovoLancamento.tsx` (e `EditarLancamento.tsx`,
que não existia no mockup — feature adicionada depois por pedido direto).

---

## Configurações (Contas/Categorias/Bancos/Caixinhas)

![Mockup de Configurações](mockups/contas-categorias.png)

Mockup: 4 abas incluindo uma aba "Bancos" separada, tabela de contas com
saldo calculado e status ativo.

| Proposto no mockup | Status | Observação |
|---|---|---|
| Aba Contas | ✅ | CRUD completo |
| Aba Categorias (pai expansível + subcategorias) | ✅ | Implementado exatamente como desenhado |
| Aba Bancos (separada de Conta) | ⬜ | `banco` é só um campo de texto livre em `Conta`, não uma entidade própria gerenciável |
| Aba Caixinhas | ✅ | Não estava desenhada no mockup original (só apareciam como um tipo de conta), acabou implementada como aba própria — decisão do meio do projeto quando caixinha virou conceito de "reserva" separado de conta |
| Coluna de saldo calculado na tabela de contas | ⬜ | Mesma dependência do saldo atual (Dashboard) |

**Arquivo:** `frontend/src/routes/Configuracoes.tsx` e
`frontend/src/routes/configuracoes/*Section.tsx`.

---

## Planejamento (Orçamento)

![Mockup do Planejamento](mockups/planejamento.png)

Mockup: alocação percentual visual por bucket, comparação orçado x realizado
x mês anterior por bucket, ações explícitas "Acumular/Transferir" sobre a
sobra do envelope, alternância R$/%.

| Proposto no mockup | Status | Observação |
|---|---|---|
| **Tela inteira** | ⬜ | `/planejamento` ainda é um placeholder — nenhuma UI existe, só a API |
| Renda base + % destinado ao orçamento | ✅ (backend) | `receita_base` + `percentual_geral` em `POST /orcamentos` |
| Alocação por bucket (% limite) | ✅ (backend) | `limite_fixos/variaveis/sazonalidades/investimentos` |
| Orçado x Realizado por bucket | ✅ (backend) | `GET /estrutura-custo/{mes}` já calcula os dois |
| Comparação com mês anterior por bucket | ⬜ | Não existe no backend nem no frontend |
| Sobra do envelope acumulada | ✅ (backend) | `saldo_anterior_acumulado`, carregado via `POST /orcamentos/{id}/proximo-mes` |
| Ações manuais "Acumular"/"Transferir" sobre a sobra | ⬜ | Hoje é automático (todo o saldo rola pro mês seguinte via `próximo-mes`) — não existe escolha manual de acumular vs transferir pra outro bucket |
| Alternância de entrada R$/% | ⬜ | Itens são cadastrados só em R$ hoje |

**Conclusão da seção:** o motor de cálculo do orçamento (backend) está
praticamente alinhado com o que foi desenhado — o que falta inteiro é a tela.

---

## Estrutura de Custo

Não fazia parte dos 4 mockups originais (não foi desenhada como tela própria
naquele momento), mas existe como conceito no backend e é mencionada aqui por
ser outro placeholder de frontend: `/estruturas-de-custo` ainda não tem UI,
só a API (`GET /estrutura-custo/{vigencia_mes}`).

---

## Resumo de prioridades sugerido

~~1. Delta vs mês anterior nos KPIs do Dashboard (dado já existe, é reprocessar).~~ **feito 2026-09-13**
2. Tela de Planejamento (motor de orçamento já pronto no backend).
3. Tela de Estrutura de Custo (motor já pronto no backend).
~~4. Endpoint + UI de saldo atual por conta/caixinha...~~ **feito parcialmente 2026-09-13** — só caixinhas; conta segue sem saldo (decisão do usuário, em aberto)
~~5. Linha de Resultado na Evolução Mensal...~~ **feito 2026-09-13**
6. Categorias "mais usadas" + criação inline no Novo Lançamento.
~~7. Compromissos futuros no Dashboard...~~ **feito parcialmente 2026-09-13** — só parcelas futuras; "fixo recorrente" não existe como conceito no app
8. Aba Bancos em Configurações (baixa prioridade — hoje resolvido como campo
   de texto em Conta, sem perda funcional real).

Este documento não substitui o `README.md` (que descreve o que existe) nem o
`/status-projeto` (relatório de andamento) — é o registro do que foi
*proposto*, pra comparar contra o que foi *decidido mudar* ao longo do
desenvolvimento real.

---

## Changelog deste documento

Registro de rodadas de mudança pedidas diretamente sobre o que já tinha sido
entregue — pra não perder o histórico de decisão ao reescrever as tabelas
acima a cada entrega.

### 2026-09-13 — Dashboard: caixa/saúde, delta, patrimônio, compromissos, 3ª linha

Pedido do usuário: o Dashboard entregue antes (só evolução + KPIs simples)
ficou bem diferente do mockup original, então foi pedido explicitamente para
fechar mais gaps daquela tabela. Entregue nesta rodada:

- Toggle "Leitura de Caixa" / "Leitura de Saúde" trocando hero + KPIs.
- Delta vs mês anterior em todo KPI e no hero (reaproveitando `/dashboard/evolucao`,
  sem endpoint novo).
- Seção **Patrimônio em Caixinhas** — novo endpoint `GET /dashboard/patrimonio/{mes}`
  (aplicações menos retiradas, acumulado até o fim do mês selecionado). Título
  deixa explícito que é só caixinhas: **decisão do usuário nesta rodada foi
  não dar saldo a contas por enquanto** ("contas decidirei futuramente se
  terão saldo ou não") — então o "Patrimônio por Conta" do mockup original
  não pode ser replicado por inteiro ainda.
- Seção **Compromissos Futuros** — novo endpoint `GET /dashboard/compromissos-futuros`
  (próxima parcela em aberto de cada compra parcelada, já que parcelas futuras
  já são materializadas na tabela desde a Entrega 4). **Não inclui despesas
  fixas recorrentes** (ex: "Aluguel · Fixo · todo dia 05" do mockup) — esse
  conceito não existe no app: não há cadastro de "lançamento recorrente"
  separado de uma transação já lançada, só compra parcelada tem data futura
  conhecida de antemão. Implementar isso é feature nova (schema + tela), não
  coberta nesta rodada.
- 3ª linha "Resultado" (resultado_saude) no `EvolucaoChart`, cor slot 3 (aqua,
  `#1baf7a`/`#199e70`) da paleta categórica validada pela skill de dataviz —
  mantém a mesma paleta usada nas 2 séries já existentes.

**O que ficou de fora, mesmo estando no mockup do Dashboard** (não foi pedido
nesta rodada): saldo histórico/patrimônio total no topo, seletor de
intervalo/"todos os meses", "base da média", taxa de poupança acumulada
exposta na tela, e o donut de despesas por categoria.
