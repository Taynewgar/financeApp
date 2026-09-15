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
| Intervalo (Todos os meses / mês específico) | ✅ | Tabs Mês/Intervalo/Todos os meses — Intervalo com 2 seletores de mês, Todos os meses calcula a partir de `GET /dashboard/primeiro-mes` |
| Base da média (Até o mês / Todos os meses) | 🟡 | Seletor existe e guarda o estado, mas ainda **sem nenhum cálculo pendurado nele** — combinado explicitamente com o usuário, é plumbing pra quando algum gráfico/KPI passar a consumir média |
| Alternância "Leitura de Caixa" / "Leitura de Saúde" | ✅ | Toggle troca só o hero e o par Receita/Despesa — Taxa de poupança, Reservas e Investimentos ficam sempre visíveis nas duas leituras (não mudam de valor entre elas) |
| KPI: Despesas Líquidas, Receita, Resultado de Saúde, Taxa de Poupança | ✅ | Cards + número principal (hero) |
| Delta de cada KPI vs mês anterior (ex: "6,2% vs mês anterior") | ✅ | Calculado no frontend a partir do próprio `/dashboard/evolucao` (penúltimo mês da janela) — só aparece no modo Mês (Intervalo/Todos os meses não têm um "mês anterior" único pra comparar) |
| Taxa de poupança acumulada no ano | ✅ | Busca à parte de `/dashboard/evolucao` (jan até o mês de referência), mostrada junto do card de Taxa de poupança |
| Patrimônio por conta (saldo de cada conta/caixinha/fatura) | 🟡 | Só caixinhas (`GET /dashboard/patrimonio/{mes}`) — contas seguem sem saldo próprio por decisão do usuário, a definir depois |
| Compromissos futuros (parcelas futuras, fixos recorrentes) | 🟡 | Só parcelas futuras (`GET /dashboard/compromissos-futuros`) — "fixo recorrente" (ex: aluguel todo dia 5) registrado como backlog (ver seção própria abaixo), não implementado |
| Evolução mensal — 3 séries (Receita/Despesa/Resultado) | ✅ | Combo: barras pra Receita/Despesa + linha de Resultado sobreposta, como no mockup (era só 3 linhas antes — corrigido) |
| Despesas por categoria do mês (% por categoria) | 🟡 | Implementado como **barra horizontal empilhada** + lista, não donut — a skill de dataviz do projeto marca donut/pizza como anti-pattern pra comparar valores próximos; mesma informação (categoria, valor, %), forma diferente. Ver nota abaixo |

**Sobre o donut:** o mockup e o app original (`gráficos de pizza por categoria/subcategoria`,
ver `plano-de-evolucao-original.md`) usavam pizza/donut. Optei por uma barra horizontal
empilhada porque é a forma recomendada pra "parte-do-todo" pela skill de dataviz usada
neste projeto (`references/choosing-a-form.md`: "Part-to-whole → stacked bar"; e
`anti-patterns.md` lista "donut/pie para comparar valores próximos" como erro comum).
O layout (barra + lista com cor, categoria, valor e %) reproduz a mesma leitura do
mockup. Se preferir o donut literal mesmo assim, é uma troca pontual no componente.

**Arquivo:** `frontend/src/routes/Dashboard.tsx`, `frontend/src/components/EvolucaoChart.tsx`,
`frontend/src/components/DespesasPorCategoria.tsx`, `backend/app/routers/dashboard.py`.

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

**Divisão de responsabilidade decidida depois do mockup** (ver
`sugestoes-e-decisoes-do-redesign.md`, seção 8): Planejamento é *só*
configuração dos valores-alvo (R$ por item/bucket) — nenhuma leitura de
realizado nem comparação com mês anterior aparece aqui. Essa leitura fica
inteira pra tela de Estrutura de Custo. Por isso as colunas "Realizado" e
"Mês anterior" do mockup **não foram implementadas por decisão**, não por
lacuna — o mockup ficou desatualizado nesse ponto específico depois da
conversa que fechou essa divisão.

| Proposto no mockup | Status | Observação |
|---|---|---|
| Tela de configuração (renda, % geral, limites por bucket) | ✅ | `frontend/src/routes/Planejamento.tsx` — cria/edita o orçamento do mês |
| Alocação por bucket (% limite) | ✅ | Barra de alocação total + card por bucket, com % do teto já usado pelos itens |
| Itens do orçamento por bucket (nome/categoria/subcategoria/conta, valor mensal) | ✅ | Aparecem sozinhos a partir do que é lançado (paridade com o app original — "categorias de custo derivadas automaticamente do CSV carregado") — você só ajusta o valor. CRUD manual (nome livre, conta vinculada) continua disponível pra casos sem transação ainda. Teto do bucket validado pelo backend |
| Orçado x Realizado por bucket | 🚫 | **Fora do escopo desta tela por decisão** — fica em Estrutura de Custo (`GET /estrutura-custo/{mes}` já calcula os dois no backend) |
| Comparação com mês anterior por bucket | 🚫 | Mesma decisão acima — é leitura de execução, não de configuração |
| Sobra do envelope acumulada | ✅ | Botão "Gerar orçamento do próximo mês" (`POST /orcamentos/{id}/proximo-mes`); cada item mostra sobra/disponível quando há saldo trazido |
| Ações manuais "Acumular"/"Transferir" sobre a sobra | ⬜ | Continua automático (todo o saldo rola pro item equivalente do mês seguinte) — sem escolha manual de acumular vs transferir pra outro bucket |
| Alternância de entrada R$/% | ⬜ | Itens são cadastrados só em R$; os limites por bucket já são em % |

**Arquivo:** `frontend/src/routes/Planejamento.tsx`, `frontend/src/components/planejamento.css`.

---

## Estrutura de Custo

Não fazia parte dos 4 mockups originais (não foi desenhada como tela própria
naquele momento) — surgiu como conceito só no backend, e virou tela em
2026-09-15 depois da avaliação dos 6 mockups de referência (ver changelog
"rodada 3"/"rodada 4" abaixo), com design hierárquico escolhido pelo usuário
depois de testar um mockup interativo comparando as duas opções.

| Entregue | Status | Observação |
|---|---|---|
| Leitura orçado × realizado por bucket do mês | ✅ | `GET /estrutura-custo/{mes}`; 6 buckets — os 4 do orçamento mais `reservas` e `sem_estrutura`, que só existem aqui (nunca recebem item de orçamento) |
| Hierarquia bucket > categoria pai > subcategoria, expand/collapse | ✅ | Agrupamento client-side (`agruparPorCategoria`) — o backend devolve itens "achatados" por categoria/subcategoria/conta |
| Fita de KPIs (Orçado/Realizado/Diferença/Execução %) | ✅ | Soma só os 4 buckets que aceitam orçamento (reservas/sem_estrutura ficam de fora, já que orçado é sempre 0 neles) |
| Vereditos de pool de despesas (teto) e piso de investimentos | ✅ | `pool_despesas` (fixos+variáveis+sazonalidades tratados como 1 teto agregado) e `piso_investimentos` (mínimo, não teto) |
| Badge Dentro/Excedido por subcategoria | ✅ | "—" quando o item não tem orçado (nada a comparar) |
| Drill-down pra Busca de Lançamentos | ✅ | Seta "→" no item leva a `/lancamentos?categoria_id=...&mes=...` (ou `subcategoria_id`), que já vem com os filtros pré-aplicados |
| Aviso quando o mês não tem orçamento configurado | ✅ | Tela funciona sem orçamento (todo orçado fica 0), com aviso linkando pra Planejamento |
| Modo privacidade | ✅ | Valores em R$ ocultáveis; percentuais (ex.: "Execução: 98,1%") ficam sempre visíveis, mesmo padrão do resto do app |
| Responsivo mobile | ✅ | Colunas Status/drill-down somem <480px; cabeçalho de bucket/categoria quebra em 2 linhas pra não estourar largura |

**Arquivo:** `frontend/src/routes/EstruturaCusto.tsx`, `frontend/src/components/estruturaCusto.css`.

---

## Gráficos / Análise

Não fazia parte dos 4 mockups originais, e diferente de Estrutura de Custo
(que pelo menos virou um conceito citado explicitamente nas fases do plano),
a aba **Gráficos** do app antigo ficou sem menção nenhuma no redesign depois
do `plano-de-evolucao-original.md` — não virou mockup, não virou tela
planejada, não entrou no backlog. Registrado aqui em 2026-09-15 depois do
usuário apontar a lacuna e pedir reavaliação direto do código-fonte do ZIP
(`features/graficos/graficos_html.py` + `assets/report_scripts.js`).

A aba original tinha 4 blocos. Comparado feature a feature com o que existe
hoje:

| Bloco / item do original | Status | Observação |
|---|---|---|
| Reading strip de saúde (receita de caixa, despesa bruta, ajustes, despesa líquida, resultado de caixa) | ✅ | Coberto pelo Dashboard atual (resumo cards + hero) |
| KPI: Taxa de poupança do período | ✅ | Dashboard |
| KPI: Taxa de poupança acumulada | ✅ | Dashboard ("Acumulado no ano") |
| KPI: Meses com resultado negativo | ⬜ | Não existe em nenhuma tela |
| KPI: Maior categoria de despesa | 🟡 | Coberto indiretamente pelo gráfico "Despesas por Categoria" do Dashboard — dá pra ver visualmente, mas não como um KPI numérico dedicado ("Mercado — R$ 850") |
| KPI: Desvio do orçamento | ⬜ | Depende de Estrutura de Custo ter orçado×realizado calculado numa tela, o que ainda não existe |
| KPI: Completude dos dados | ⬜ | Ver "Qualidade dos dados" abaixo |
| Seletor local "Escopo da evolução" (Ano até o mês / Só o mês / Período global) — independente do filtro de período da página inteira | ⬜ | O Dashboard novo tem um seletor de período **global** (Mês/Intervalo/Todos os meses) que cobre parte do mesmo objetivo; um segundo escopo *local* só para este gráfico pode ser redundante agora — ver recomendação abaixo |
| Gráfico de evolução mensal da saúde financeira | ✅ | `EvolucaoChart` do Dashboard |
| **Pareto de despesas por categoria e subcategoria** (ordenado por valor, % acumulado, filtro de categoria pai para o Pareto de subcategoria) | ⬜ | **Não existe em lugar nenhum do app novo.** Não é a mesma coisa que "Despesas por Categoria" do Dashboard — aquele é uma barra empilhada por categoria/%, sem ordenação nem % acumulado; Pareto responde uma pergunta diferente ("quais poucas categorias concentram a maior parte do gasto"). É o gap mais real desta lista |
| Orçado × Realizado — **tendência de vários meses** (barra Orçado/Realizado + linha % executado, resumo sem detalhe por categoria) | ⬜ | Diferente do que está planejado para Estrutura de Custo, que hoje é uma leitura de **1 mês só** (orçado×realizado por bucket do mês selecionado), não uma série temporal. Os dois são complementares, não substitutos |
| Qualidade dos dados (diagnóstico de campos ausentes/pendências, painel sempre disponível, com gráfico e cards) | 🟡 | Já registrado em `sugestoes-e-decisoes-do-redesign.md` seção 5, mas reenquadrado especificamente para o fluxo de **importação de CSV** ("tela de revisão de importação"), não como painel geral sempre visível como no original. O formulário guiado do app novo já **exige** categoria/estrutura de custo/meio de pagamento na entrada de despesas — o cenário de "lançamento incompleto" que esse painel diagnosticava no app antigo é bem mais raro agora, exceto justamente na importação, onde a decisão de manter esse painel já foi tomada |
| Gasto mensal no cartão de crédito | 🚫 | Conferido no código-fonte: era um dado **calculado mas nunca renderizado** em nenhum gráfico do app original (`data_json["cartao"]` sem consumidor em `report_scripts.js`) — código morto, não uma funcionalidade perdida. Corrigida a menção equivocada em `plano-de-evolucao-original.md` |

**Minha avaliação, não uma decisão já tomada:**

- **Recomendo registrar como prioridade real**: o Pareto por categoria/subcategoria é a única peça desta lista que é uma capacidade analítica genuinamente ausente hoje, sem equivalente parcial em nenhuma tela. Adicionar como backlog concreto (ver seção "Backlog registrado" abaixo).
- **Recomendo registrar como extensão futura de Estrutura de Custo**, não como feature nova separada: a visão de tendência de Orçado×Realizado ao longo de vários meses — faz mais sentido morar ali (mesma divisão de responsabilidade já decidida: Planejamento configura, Estrutura de Custo lê o realizado) do que reviver uma aba "Gráficos" à parte.
- **Recomendo baixa prioridade, mas registro**: os 3 KPIs que faltam (meses negativos, maior categoria como número, desvio do orçamento) — baratos de adicionar ao Dashboard quando Estrutura de Custo existir (desvio do orçamento depende disso).
- **Recomendo não adotar como estava**: o seletor local "Escopo da evolução" — o Dashboard já resolve boa parte do mesmo problema com o seletor de período global (Mês/Intervalo/Todos os meses), que não existia no app antigo. Replicar os dois pode ser complexidade duplicada sem ganho real; melhor avaliar de novo se, na prática, alguém sentir falta de comparar um escopo diferente do que está selecionado na página.
- **Qualidade dos dados**: mantenho a decisão já registrada (ligado à importação) — o formulário guiado do app novo já cobre a maior parte do problema original na entrada manual.

---

## Prioridades e backlog

Movido para `docs/backlog.md` em 2026-09-15 — esse conteúdo (ordem de
prioridade + itens detalhados registrados pra decidir depois) cresceu o
suficiente pra merecer arquivo próprio, separado da tabela proposto ×
implementado tela a tela que é o foco deste documento.

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

### 2026-09-13 (rodada 2) — correção do gráfico, KPIs sempre visíveis, seletor de período, categoria

Pedido do usuário: revisão em cima da entrega anterior, corrigindo 2 decisões
minhas que se afastaram do que foi combinado e fechando mais gaps do plano.
Entregue nesta rodada:

- **Gráfico de evolução corrigido para combo barra+linha** (Receita/Despesa em
  barra, Resultado em linha sobreposta), como estava no mockup — a versão
  anterior (3 linhas) foi uma escolha minha não avisada, corrigida aqui.
- **Gráfico "Despesas por Categoria"** (categoria pai, mês de referência) —
  não existia antes. Implementado como barra horizontal empilhada + lista, não
  donut (ver nota na tabela do Dashboard acima) — restaura uma leitura que o
  app original tinha (`gráficos de pizza por categoria/subcategoria`) usando a
  forma que a skill de dataviz do projeto recomenda pra parte-do-todo.
- **Taxa de poupança e Reservas passam a ficar sempre visíveis**, nas duas
  leituras (antes cada uma "pertencia" só a uma leitura e sumia na outra —
  decisão minha que escondia informação sem necessidade real, já que nenhum
  dos dois valores muda entre as leituras). O toggle Caixa/Saúde agora só
  troca o hero e o par Receita/Despesa, que são os únicos valores que
  realmente mudam entre as duas leituras.
- **Novo KPI "Investimentos", separado de "Reservas"** — o usuário notou que
  aplicação/retirada estava sendo tratado como um conceito só ("reservas"),
  mas são dois diferentes: reserva é aplicação/retirada COM caixinha
  vinculada (guardar dinheiro numa Reserva de Emergência, por exemplo);
  investimento é SEM caixinha. É a mesma distinção que `estrutura_custo.py`
  já usava pros buckets da Estrutura de Custo — só não estava replicada no
  resumo do Dashboard. Correção feita na função compartilhada
  `calcular_resumo()` (afeta também `/transacoes/resumo`, usado pela busca de
  Lançamentos, de forma aditiva — campo novo, nada quebrou).
- **Seletor de período Mês / Intervalo / Todos os meses** — implementado com
  tabs; Intervalo com 2 seletores de mês, Todos os meses calculado a partir
  de `GET /dashboard/primeiro-mes` (mês do lançamento mais antigo). Novo
  endpoint `GET /dashboard/resumo-periodo` soma as transações do período
  inteiro de uma vez (não é a soma dos resumos mensais — taxa de poupança
  precisa ser recalculada sobre o total, não a média das taxas mensais).
  Delta vs mês anterior só aparece no modo Mês (não existe um "mês anterior"
  único pra comparar num intervalo).
- **"Base da média"** — seletor implementado (Até o mês / Todos os meses),
  visível só fora do modo Mês, mas **sem nenhum cálculo pendurado nele
  ainda** — combinado explicitamente com o usuário como plumbing pra uma
  funcionalidade futura, não uma entrega funcional completa.
- **Taxa de poupança acumulada no ano** — exposta junto do card de Taxa de
  poupança, calculada com uma busca à parte de `/dashboard/evolucao` (janeiro
  até o mês de referência).
- **Backlog registrado, não implementado:** despesa fixa recorrente e edição
  de compra parcelada — ambos com o motivo técnico e as opções de
  implementação detalhadas na seção "Backlog registrado" acima, sem decisão
  de prioridade ainda.

### 2026-09-14 — Tela de Planejamento

Pedido do usuário: seguir o plano de desenvolvimento — próximo item da lista
de prioridades era a tela de Planejamento, cujo motor de orçamento já
estava pronto no backend. Antes de implementar, o usuário pediu pra
confirmar a divisão de responsabilidade entre Planejamento e Estrutura de
Custo (ele lembrava que Planejamento seria só configuração, sem
orçado×realizado) — recuperei a seção 8 de
`sugestoes-e-decisoes-do-redesign.md`, que confirmou exatamente isso sem
nenhuma mudança necessária no que já estava registrado.

Entregue:

- Tela `frontend/src/routes/Planejamento.tsx` (substituiu o placeholder).
- Seletor de mês; criação de orçamento do zero ou a partir do mês anterior
  (`POST /orcamentos/{id}/proximo-mes`, traz a sobra do envelope); edição da
  configuração geral (renda base, % destinado, limite de cada bucket).
- Barra de alocação total dos 4 buckets (cor fixa por bucket, mesma paleta
  categórica validada) + aviso de % ainda não alocado.
- Card por bucket com barra de "% do teto já alocado em itens" (fica
  vermelha se os itens somarem mais que o teto) — isso é sobre o *plano*
  (quanto dos R$ disponíveis já foi distribuído entre itens), não sobre
  execução real, então não conflita com a divisão de responsabilidade.
- CRUD completo de itens do orçamento por bucket (categoria, subcategoria,
  nome livre, ou conta vinculada pra investimentos) — reaproveita as
  validações já existentes no backend (teto do bucket, referências).
- Item mostra sobra do envelope trazida do mês anterior e o disponível
  total, quando existir.
- **Não incluído, por decisão de escopo confirmada nesta rodada:** orçado ×
  realizado e comparação com mês anterior por bucket — ficam pra Estrutura
  de Custo. Também não incluído (não fazia parte do pedido): ações manuais
  de acumular/transferir a sobra (continua automático) e alternância de
  entrada R$/%.
- tsc + build limpos, suíte de backend (190 testes, sem mudança nesta
  rodada) verde, QA visual via Playwright (claro/escuro/mobile) antes de
  fechar.

### 2026-09-14 (rodada 2) — modo privacidade, correções no Planejamento

Pedido do usuário logo após usar a tela de Planejamento: 1 correção de
paridade que ficou faltando, 1 melhoria de usabilidade, e 1 feature nova
restaurando algo que o app original já tinha. Entregue:

- **Modo privacidade** (`👁 Ocultar valores` no AppShell, sidebar desktop +
  nav inferior mobile) — o app original tinha isso no relatório HTML
  ("Modo privacidade (ocultar/mostrar valores)", ver
  `plano-de-evolucao-original.md`). Estado persistido em localStorage,
  aplicado em todo display de R$ do app (Dashboard, gráficos, Lançamentos,
  Planejamento).
- **Destaque de estouro na soma dos limites dos buckets do Planejamento**
  (vermelho quando passa de 100%) — confirmado como paridade: o app
  original já tinha "indicadores visuais de alocação/estouro" pra essa
  soma. Só faltava replicar (o destaque por item individual acima do teto
  do bucket já existia desde a entrega da tela).
- **Botão "Editar configuração" do Planejamento** trocado de link discreto
  pra botão de verdade — ficava escondido demais.

**Em aberto na época, decidido e implementado na rodada seguinte** (ver
changelog 2026-09-14 rodada 3 abaixo): itens reativos a partir de
lançamentos (decisão: reativo, não só na criação do orçamento) e
confirmação antes de substituir orçamento existente.

### 2026-09-14 (rodada 3) — itens de orçamento reativos, substituir orçamento existente, botão de privacidade reposicionado

Resolve os 2 pontos que ficaram em aberto na rodada anterior, mais 1 ajuste
de posição pedido depois de usar o botão de privacidade pela primeira vez.

- **Itens do orçamento reativos** — decisão: reativo (não só na criação do
  orçamento). Novo `services/orcamento_sync.py`: toda vez que uma despesa
  ou um investimento (aplicação/retirada sem caixinha) é lançado ou editado,
  se já existe orçamento pro mês daquela transação e a categoria/subcategoria
  usada ainda não tem item nele, um item novo é criado sozinho com
  `orcamento_mensal=0` — você só ajusta o valor, nunca precisa criar o item
  do zero. Bucket vem direto do `estrutura_custo` da transação (mesmo mapa
  usado em Estrutura de Custo). Reserva (aplicação/retirada com caixinha),
  receita e estorno/ressarcimento não alimentam orçamento, não criam item.
  Item já existente nunca é tocado (nem o valor, nem removido). 8 testes
  novos cobrindo os casos (categoria nova, subcategoria em vez de categoria,
  não duplica, sem orçamento não cria nada, investimento, reserva não cria,
  estorno não cria, edição sincroniza a categoria nova).
- **Substituir orçamento existente ao gerar o próximo mês** —
  `POST /orcamentos/{id}/proximo-mes?substituir=true` agora apaga o
  orçamento (e itens) que já existe pro mês seguinte antes de recriar, em
  vez de só recusar com 409. Sem o parâmetro, comportamento antigo mantido
  (409). Frontend: ao tentar gerar e receber 409, mostra
  `window.confirm()` perguntando se quer substituir; se sim, repete a
  chamada com `substituir=true`.
- **Botão de privacidade reposicionado** — tirado do rodapé da barra
  lateral (ficava embaixo de tudo, fora da vista sem rolar) e virou uma
  barrinha fixa no topo da página, acima de tudo, sempre visível em
  qualquer tela — desktop e mobile, com ou sem o aviso de "acordando o
  servidor" no topo (motivo da mudança: a primeira versão usava um botão
  flutuante fixo que ficava embaixo desse aviso quando ele aparecia).
- tsc + build limpos; suíte de backend (199 testes) verde; QA visual via
  Playwright (claro/escuro/mobile, com e sem o banner do backend) antes de
  fechar.

### 2026-09-14 (rodada 4) — botão de privacidade: de barrinha no topo pra ícone quadrado ao lado do seletor de mês

A barrinha fixa no topo (rodada 3) ainda incomodava — posição genérica,
desconectada do conteúdo da tela. Trocado por um botão quadrado com ícone
de olho, pequeno, ao lado do controle de mês em cada tela — mais perto de
onde o olhar já passa.

- Novo `components/BotaoPrivacidade.tsx` — botão 38×38px reutilizável, com
  SVG de olho (aberto) / olho riscado (fechado) inline, `aria-pressed` pra
  indicar estado ativo. Some o `.shell-topbar` do `AppShell.tsx` (e o CSS
  correspondente) — o toggle não é mais um elemento global da casca do
  app, e sim posicionado por tela.
- Colocado ao lado do seletor de mês/segmentado em **Dashboard** (dentro
  de `.dashboard-seletor`) e **Planejamento** (ao lado do campo Mês);
  colocado ao lado do título em **Lançamentos** (o filtro rápido de
  mês/ano ali fica dentro da linha de filtros, menos em destaque que um
  cabeçalho). Configurações, Novo/Editar Lançamento seguem sem o botão —
  não mostram valores agregados relevantes.
- Estado continua global (mesmo `PrivacyContext`/localStorage de antes) —
  só a posição de cada botão é por tela.
- tsc + build limpos; suíte de backend (199 testes, sem mudança) verde; QA
  visual via Playwright (claro/escuro) confirmando o botão ao lado do
  seletor de mês e o toggle funcionando.

### 2026-09-15 — botão de privacidade: de posição por tela pra global na casca do app

Correção sobre a rodada anterior: o usuário apontou que o botão *tem* que
ser global — acessível em qualquer tela, não só nas 3 que tinham seletor
de mês/título em destaque (ficava ausente em Configurações e nos
formulários de lançamento). Pedi sugestão de posição, propus a casca do
app (`AppShell`) em vez de por tela, mostrei um mockup com screenshot
antes de mexer no código de verdade — a primeira tentativa no mockup
(6º item na barra inferior mobile) quebrou visualmente (rótulos
colidindo: "Lançamentos"/"Planejamento" sobrepostos, "Estruturas de
Custo" invadindo "Configurações"), corrigida ainda no mockup antes de ir
para aprovação.

- **Desktop**: `<BotaoPrivacidade />` (mesmo componente da rodada
  anterior, sem mudança nele) movido para dentro de `.shell-nav-header`,
  ao lado do texto "Finance App", topo da barra lateral — sempre visível
  sem rolar, em fluxo normal (não `position: fixed`), então sem risco de
  colidir com o banner de "acordando o servidor" (o mesmo tipo de bug que
  a versão flutuante da rodada 3 teve).
- **Mobile**: nova faixa `.shell-topo-mobile` (só visível abaixo de
  720px, escondida no desktop), com "Finance App" + o botão — a barra de
  navegação inferior continua com os 5 itens originais, sem o 6º item que
  quebrou no mockup.
- Removido de **Dashboard**, **Planejamento** e **Lançamentos** (import e
  uso de `<BotaoPrivacidade />` por tela, da rodada anterior) — agora é
  um único ponto de verdade na casca do app, cobrindo todas as telas
  (inclusive Configurações e os formulários de lançamento, que antes
  ficavam sem o toggle).
- `components/BotaoPrivacidade.tsx` e `botaoPrivacidade.css` continuam os
  mesmos (SVG de olho, `aria-pressed`) — só o lugar onde são montados
  mudou.
- tsc + build limpos; suíte de backend (199 testes, sem mudança) verde; QA
  visual via Playwright (claro/escuro, desktop/mobile) no mockup antes de
  aprovar, e de novo na implementação final antes de commitar.

### 2026-09-15 (rodada 2) — registro da aba "Gráficos" do app original, ausente do redesign

Pedido do usuário: o ZIP original ainda estava disponível na conversa, e ele
notou que a aba **Gráficos** do app antigo nunca foi mencionada em nenhum
documento do redesign — nem virou mockup, nem virou backlog. Pediu pra
avaliar as funcionalidades e, se eu concordasse com todas, registrar como
parte do redesign.

Reli o código-fonte do ZIP (`features/graficos/graficos_html.py` +
`assets/report_scripts.js`, não só a memória documentada) pra levantar
exatamente o que a aba fazia. Resultado: **não concordei com adoção 1:1 de
tudo** — ver a nova seção "Gráficos / Análise" acima pra comparação completa
feature a feature. Resumo do que mudou nesta rodada:

- Nova seção **"Gráficos / Análise"** neste documento, com a tabela completa
  (11 itens do original × status atual) e minha avaliação item a item.
- **Achado principal**: o **Pareto de despesas por categoria/subcategoria**
  é uma capacidade real, hoje totalmente ausente, sem equivalente parcial —
  registrado como novo item no backlog (seção própria, com o que precisaria
  pra construir).
- **Achado secundário (correção, não gap)**: "Gasto mensal no cartão de
  crédito", listado em `plano-de-evolucao-original.md` como funcionalidade
  do app antigo, na verdade era um dado calculado mas nunca renderizado em
  nenhum gráfico — código morto no próprio original. Corrigido lá.
- **Recomendação de não adotar como estava**: o seletor local "Escopo da
  evolução" (Ano até o mês / Só o mês / Período global), por sobrepor boa
  parte do que o seletor de período global do Dashboard novo já resolve —
  registrado, mas não como pendência a construir.
- Item 9 adicionado ao "Resumo de prioridades sugerido" (o Pareto).
- Nenhuma linha de código mudou nesta rodada — só documentação.

### 2026-09-15 (rodada 3) — avaliação de 6 mockups de referência, feature Gráficos aprovada, backlog vira arquivo próprio

Usuário trouxe 6 mockups visuais de referência (conceitos, não screenshots
do app antigo) mostrando ideias de tela pra Gráficos, Estrutura de Custo e
Pareto, pediu avaliação honesta ("se discordar, me fale"), sugestões pra
deixar o Dashboard mais robusto, e reorganização da documentação de
backlog. Resultado, ponto a ponto:

- **Feature "Gráficos" aprovada como tela própria** — o usuário confirmou
  querer essa feature dedicada (revertendo minha recomendação anterior de
  só distribuir peças pelo Dashboard/Estrutura de Custo). Escopo v1: Pareto
  de despesas + tendência de Orçado×Realizado em vários meses. Detalhe
  completo em `backlog.md`.
- **Dashboard proposto para ficar 100% sintético** (números/KPIs/listas,
  sem gráfico nenhum) — ideia do próprio usuário, que eu recomendei adotar:
  `EvolucaoChart` e "Despesas por Categoria" migram pra Gráficos (mudam de
  lugar, não duplicam). Aguardando confirmação final antes de virar
  trabalho committed.
- **3 KPIs novos aprovados pro Dashboard**: "Meses com resultado negativo",
  "Resultado acumulado" (R$), "Maior categoria de despesa" (textual).
- **Discordâncias registradas, não adotadas como estavam nos mockups**:
  o seletor local "Escopo da evolução" (redundante com o seletor de
  período que a tela nova vai reaproveitar do Dashboard); o botão "Ocultar
  valores" embutido no toolbar de um dos mockups (já resolvido globalmente
  no `AppShell` desde a rodada de 2026-09-15 anterior); o agrupamento por
  "categoria pai" solta da tela de Estrutura de Custo no mockup (não bate
  com o schema real — buckets fixo/variável/sazonal/investimentos vêm
  primeiro).
- **Estrutura de Custo — decisão de tabela em aberto**: publicado mockup
  interativo (artifact) comparando tabela hierárquica com expand/collapse
  (minha sugestão, mais fiel ao app original — drill-down direto pra Busca
  de Lançamentos) × duas listas separadas (estilo do mockup trazido) —
  aguardando o usuário escolher.
- **Exportação de relatório mensal/anual** — novo item de backlog, pedido
  explícito do usuário como próximo passo pós-MVP. Prioriza dado
  estruturado (JSON) pensado pra ser usado numa análise depois, sobre um
  relatório "bonito" pra imprimir. Recomendação de onde morar: começa como
  link numa tela existente, não uma tela "Relatórios" própria — só cresce
  pra isso se ganhar mais capacidade real.
- **Backlog extraído pra `docs/backlog.md`** — pedido do usuário
  ("qual arquivo é o backlog? organize") — ver commit próprio dessa
  reorganização; esta entrada de changelog documenta as decisões de
  conteúdo desta rodada, não a reorganização de arquivo em si.
- Nenhuma linha de código de produto mudou nesta rodada — só documentação e
  um artifact de mockup (fora do repositório).

### 2026-09-15 (rodada 4) — fecha as 2 decisões pendentes da rodada anterior

Usuário testou o mockup interativo, pediu avaliação de ganhos/perdas da
divisão Dashboard×Gráficos, e fechou tudo que tinha ficado em aberto:

- **Estrutura de Custo: tabela hierárquica escolhida** — depois de testar
  o mockup interativo (expand/collapse de verdade), decidiu pela hierarquia
  bucket > categoria > subcategoria em vez das duas listas separadas.
- **Dashboard 100% sintético, confirmado, com 1 adição** — perguntei
  explicitamente sobre ganhos/perdas antes do usuário confirmar: ganho é
  foco e velocidade de leitura + tela mais leve; perda real é a leitura
  imediata da *forma* da tendência, que um número sozinho não dá. Sugeri
  mitigar com um **sparkline** compacto (sem eixos/legendas/tooltip) ao
  lado do resultado principal — aprovado. Passa a fazer parte do escopo da
  migração de gráficos pro Dashboard/Gráficos.
- **Export de relatório: botão confirmado**, sem tela "Relatórios" própria.
- Com isso, nenhuma proposta da rodada anterior ficou pendente — próxima
  entrega de código é Estrutura de Custo (tabela hierárquica).
- Nenhuma linha de código mudou nesta rodada — só documentação.

### 2026-09-15 (rodada 5) — Estrutura de Custo entregue

- Tela nova `frontend/src/routes/EstruturaCusto.tsx`, hierárquica
  (bucket > categoria pai > subcategoria) com expand/collapse, fita de
  KPIs, vereditos de pool de despesas/piso de investimentos, badges
  Dentro/Excedido, drill-down pra Busca de Lançamentos via
  `useSearchParams` (novo em `Lancamentos.tsx`) e aviso de "sem orçamento
  configurado" quando o mês não tem `Orcamento`. Backend não mudou — o
  endpoint `GET /estrutura-custo/{mes}` já existia pronto.
- Verificação: `tsc --noEmit` e `npm run build` limpos; suíte de backend
  offline (199 passed, 33 skipped — integração fica pra rodar local);
  QA visual via Playwright (light/dark/mobile/privacidade/badges/
  drill-down), que encontrou e corrigiu 1 bug real de CSS (estouro de
  largura em 390px nos cabeçalhos de bucket/categoria).
- Removida `frontend/src/routes/Placeholder.tsx` (última tela que a usava
  virou tela própria).

### 2026-09-15 (rodada 6) — 2 correções de backend reportadas pelo usuário testando a tela

- **Subcategoria nunca aparecia como item próprio em Estrutura de Custo** —
  `_chave()` (`backend/app/routers/estrutura_custo.py`) checava
  `categoria_id` antes de `subcategoria_id`. Num lançamento real os dois
  vêm preenchidos juntos (escolher subcategoria grava a categoria pai
  também, `NovoLancamento.tsx`), então todo item com subcategoria caía
  agrupado só na categoria como "Geral (sem subcategoria)" — o frontend já
  sabia desenhar a subcategoria como folha própria, só nunca recebia o
  dado. Ordem invertida pra subcategoria > categoria > conta. Mesmo bug
  existia em `orcamentos._calcular_realizado` (usado no rollover de
  "próximo mês") — corrigido junto, senão um item de subcategoria somava
  o realizado de todas as subcategorias-irmãs da mesma categoria pai.
- **Planejamento não nascia com as categorias já lançadas no mês** —
  `sincronizar_item_orcamento` só reage a transação nova (criada/editada
  depois de o orçamento existir); lançar antes de planejar — fluxo normal
  — nunca alimentava a tela retroativamente. `POST /orcamentos` e
  `POST /orcamentos/{id}/proximo-mes` agora rodam a mesma sincronização
  contra as transações que já existem no mês, criando os itens com
  `orcamento_mensal=0`.
- 5 testes novos cobrindo os dois casos (offline, 204 passed no total).
  Nenhuma mudança de frontend — os dois bugs eram só backend.

### 2026-09-15 (rodada 7) — botão "Expandir tudo" / "Recolher tudo"

Sugestão minha, aprovada pelo usuário na hora: acha os buckets/categorias
abertos individualmente lento pra auditar o mês inteiro. Estado de
categoria aberta, que antes vivia local dentro de cada `BucketBloco`, subiu
pra `EstruturaCusto` (chave composta `bucket|categoria` — evita qualquer
ambiguidade entre buckets) pra um botão único conseguir expandir/recolher
os dois níveis juntos. Botão mostra "Expandir tudo" ou "Recolher tudo"
conforme o estado atual (calculado, não guardado à parte) e só aparece
quando existe algum bucket com lançamento. De brinde, corrigida a seta da
linha de categoria, que nunca rotacionava ao abrir (só a do bucket tinha
essa regra de CSS) — mesmo bug de UI, mesmo lugar, custo zero corrigir
junto. QA visual via Playwright (preview temporário, revertido depois).

### 2026-09-15 (rodada 8) — fix: fixture `cleanup` dos testes de integração vazava categoria/orçamento

Usuário reportou (com print da tela real de Categorias) várias categorias
"... Integração" travadas, e colou o log de 18 falhas — a maioria
`KeyError: 'id'` em `orcamento["id"]` (orçamento duplicado pro mesmo mês,
porque um anterior nunca foi apagado) e `duplicate key ... categorias_user_id_nome_key`.

**Causa raiz**: `tests/integration/conftest.py::cleanup` apagava na ordem
inversa da criação (LIFO), assumindo que "reverso de criação = seguro".
Isso é falso pro grafo de FK real — vários testes criam o **orçamento**
antes da **categoria** e só depois um **item** que referencia os dois
(`POST /orcamentos/{id}/itens`). LIFO então tentava apagar a categoria
*antes* do orçamento (e do item, que ainda a referenciava), a FK sem
cascade bloqueava, o erro caía num `except: pass` silencioso, e a
categoria ficava presa pra sempre. Bug latente desde que a fixture foi
escrita — a rodada 6 (retroalimentar Planejamento a partir de transações
já lançadas) tornou o gatilho muito mais frequente, porque agora até
criar um orçamento sozinho pode criar um item reativo na hora, sem o
teste saber.

**Fix**: `cleanup` agora apaga numa ordem fixa que respeita as FKs de
verdade (mesma lista de `tests/limpar_dados_integracao.py`:
`orcamento_itens → transacoes → orcamentos → caixinhas →
compras_parceladas → subcategorias → categorias → contas`), não mais a
ordem reversa de criação. De brinde: zera `ajuste_de_transacao_id`
(auto-referência de estorno) antes de apagar transações, mesma defesa do
script de limpeza; e troca o `except: pass` silencioso por um print —
uma falha de limpeza não pode mais passar despercebida até virar
"duplicate key" numa rodada futura.

**Ação pro usuário**: a conta de teste já está suja (é o que aparece no
print) — rode `python tests/limpar_dados_integracao.py` uma vez pra
zerar antes da próxima rodada de testes de integração (comando completo
no README, seção "Resetar a conta de teste"). O fix evita que aconteça
de novo, não desfaz o que já está preso.
