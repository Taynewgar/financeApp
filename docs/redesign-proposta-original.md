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

## Backlog registrado — não implementado

Itens discutidos e combinados como "registrar pra decidir depois", não como
trabalho desta rodada.

### Despesa fixa recorrente (aluguel, assinaturas)

**Motivo de não existir hoje:** não há cadastro de "lançamento recorrente" —
cada linha em `transacoes` é um evento já acontecido (ou uma parcela já
materializada). Um aluguel que se repete todo mês precisaria de um molde
que gera lançamentos futuros sozinho, e isso não existe no schema.

**Por que é maior que parece:** a maioria dos lançamentos de custo fixo do
dia a dia se encaixaria nessa lógica, então não é um recurso de nicho — é
usado toda vez que alguém cadastra "Aluguel" ou "Internet". Precisa de:

- Tabela nova (`lancamentos_recorrentes`: descrição, valor, dia do mês,
  conta, categoria, subcategoria, estrutura de custo, meio de pagamento,
  data de início, data de fim opcional, ativo).
- Uma tela de gestão em Configurações (parcela nunca precisou disso — só se
  cria e se apaga; um recorrente precisa poder ser editado/desativado).
- Uma das duas estratégias de geração, que levam a desenhos bem diferentes:

  1. **Materialização antecipada** — igual compra parcelada: ao criar o
     recorrente, gera de uma vez linhas reais em `transacoes` pra N meses
     futuros. Simples de consultar (mesmo caminho de código que já existe
     pra "Compromissos Futuros"), mas precisa de um job periódico rodando
     de tempos em tempos pra ir "abastecendo" mais meses conforme o tempo
     passa, e fica em aberto o que fazer com uma edição de valor (ex:
     aluguel reajustou) — afeta só as parcelas futuras ainda não geradas, ou
     também as já materializadas que ainda não venceram?
  2. **Projeção virtual** — a tabela nova é só um molde; nada é escrito em
     `transacoes` até o mês realmente acontecer. "Compromissos Futuros"
     passa a mesclar parcelas reais + recorrentes projetados (calculados na
     hora, não guardados). Mantém `transacoes` 100% "coisas que realmente
     aconteceram", mas exige uma lógica de "confirmar o mês" — manual (o
     usuário confirma que o aluguel de outubro realmente saiu) ou automática
     (um job cria a transação real na data configurada).

**Recomendação, se/quando for priorizado:** projeção virtual (opção 2) —
mantém a tabela `transacoes` como fonte da verdade só do que já aconteceu de
fato, evita o job de "abastecimento" contínuo da opção 1, e o custo de
construir a confirmação (manual ou automática) é comparável ao da opção 1
de qualquer forma.

**Status:** registrado, sem decisão de prioridade nem de estratégia ainda.

### Edição de compra parcelada

**Motivo de não ser editável:** uma parcela é 1 linha em `transacoes`
(`parcela_atual`/`parcela_total`/`compra_parcelada_id` apontando pro grupo
em `compras_parceladas`, que guarda `valor_total`). Editar valor/data/conta
de só uma parcela quebra três coisas ao mesmo tempo: a soma das parcelas
para de bater com `valor_total` do grupo; o hash de dedup (que inclui esses
campos) dessincroniza; e trocar a conta de só uma parcela divide a mesma
compra entre dois cartões sem sentido nenhum.

**As 3 opções, o que cada uma faz de verdade:**

1. **Nível barato — editar só metadado que não afeta o grupo.** Descrição,
   categoria, subcategoria, estrutura de custo e meio de pagamento passam a
   ser editáveis parcela a parcela (são só classificação, não mexem em
   dinheiro nem em identidade da compra). Valor, data e conta continuam
   travados — é exatamente a mesma trava de hoje, só que mais restrita
   (hoje a parcela é 100% travada; passaria a estar parcialmente aberta).
   Não mexe em `compras_parceladas`, não precisa recalcular nada.

2. **Nível médio — editar o grupo inteiro.** A ação apaga todas as parcelas
   da compra e recria com os novos parâmetros (novo valor total, nova
   quantidade de parcelas, nova data etc.), preservando o mesmo
   `compra_parcelada_id` ou gerando um novo — decisão de produto em aberto.
   O ponto difícil: parcelas que já venceram (já apareceram numa fatura
   passada) ou que tiveram a fatura movida manualmente
   (`fatura_override=true`) entram nessa recriação ou ficam de fora? Editar
   o passado financeiro já fechado é diferente de editar o que ainda não
   aconteceu, e a resposta muda o desenho da operação.

3. **Grátis, ganho imediato — excluir o grupo inteiro numa ação só.** Hoje
   `DELETE /transacoes/{id}` já existe, mas só apaga 1 parcela por vez — pra
   cancelar uma compra parcelada de 10x é preciso repetir a chamada 10
   vezes. Um endpoint `DELETE /transacoes/parceladas/{compra_parcelada_id}`
   (ou equivalente) resolve metade da dor de "errei o lançamento, vou
   refazer" (exclui tudo de uma vez, relança do zero) sem tocar em nenhuma
   lógica de edição — é só estender o `DELETE` que já existe pra apagar
   pelo grupo em vez de pelo id da parcela.

**Recomendação, se/quando for priorizado:** nível barato (1) primeiro —
resolve a reclamação mais comum (corrigir a categoria de uma parcela) sem
nenhum risco de inconsistência — e exclusão em grupo (3) junto, por ser
praticamente grátis e já cobrir metade do caso de uso do nível médio (2).

**Status:** registrado, sem decisão de prioridade ainda.

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
