# Backlog — próximos passos

**Este é o arquivo de backlog do projeto** — a lista viva de prioridades e
pendências registradas. É aqui que se olha pra saber "o que vem depois" e
"o que ficou combinado registrar pra decidir mais tarde". Os outros 3
documentos em `docs/` são histórico e racional de decisão de design, não
pauta de trabalho — ver `docs/README.md` pra saber qual é qual.

Até 2026-09-15 esse conteúdo vivia espalhado dentro de
`redesign-proposta-original.md` ("Resumo de prioridades" + "Backlog
registrado"). Consolidado aqui num arquivo próprio porque o backlog cresceu
o suficiente (Pareto, exportação de relatório, propostas de gráficos) pra
merecer não ficar misturado com a tabela proposto×implementado tela a tela.

---

## Ordem de prioridade atual

1. ~~Delta vs mês anterior nos KPIs do Dashboard~~ **feito 2026-09-13**
2. ~~Tela de Planejamento~~ **feito 2026-09-14** — só configuração
3. **Tela de Estrutura de Custo — próxima entrega.** Motor já pronto no
   backend (`GET /estrutura-custo/{vigencia_mes}`); só falta a tela.
4. Categorias "mais usadas" + criação inline no Novo Lançamento.
5. Pareto de despesas por categoria/subcategoria (detalhe abaixo).
6. Despesa fixa recorrente — aluguel, assinaturas (detalhe abaixo).
7. Edição de compra parcelada (detalhe abaixo).
8. Exportação de relatório mensal/anual (detalhe abaixo) — próximo passo
   depois do MVP fechado (Estrutura de Custo + os itens acima).
9. ~~Compromissos futuros no Dashboard~~ **feito parcialmente 2026-09-13**
   — só parcelas futuras; "fixo recorrente" fica coberto pelo item 6.

**Baixa prioridade confirmada pelo usuário (2026-09-15)** — ficam por
último de propósito, sem previsão:

10. Aba Bancos em Configurações — hoje resolvido como campo de texto em
    Conta, sem perda funcional real.
11. Saldo atual de contas — hoje só caixinhas têm saldo calculado
    (`GET /dashboard/patrimonio/{mes}`); dar saldo a `contas` também seria
    a extensão natural, mas não é urgente.

Este arquivo não substitui o `README.md` da raiz (que descreve o que
existe) nem o `/status-projeto` (relatório de andamento) — é o registro do
que falta, não do que já foi entregue.

---

## Detalhamento dos itens maiores

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

**Status:** registrado, sem decisão de estratégia ainda.

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

### Pareto de despesas por categoria/subcategoria

**O que é:** ordenar as despesas líquidas do período (decrescente por valor)
e mostrar o percentual acumulado sobre o total — responde "quantas
categorias concentram 80% do meu gasto", uma leitura que "Despesas por
Categoria" (Dashboard) não dá, porque essa é ordenada alfabeticamente/por
cor fixa e não acumula percentual.

**Por que ficou de fora até agora:** não fazia parte dos 4 mockups originais
do redesign — só foi percebido ao reler o código-fonte do app antigo
(`features/graficos/graficos_html.py`) depois de já estar quase tudo
implementado.

**O que precisaria:**
- Nenhum endpoint novo de dados brutos — `GET /transacoes` já retorna
  despesas com categoria/subcategoria e valor; a agregação (ordenar +
  acumular %) pode ser feita no frontend a partir do que `/dashboard/
  despesas-por-categoria/{mes}` já calcula (ou um endpoint irmão dele, se
  o agregado por subcategoria precisar vir pronto do backend).
- Um componente de gráfico novo (barra + linha de % acumulado sobre eixo
  secundário — igual ao padrão já usado no `EvolucaoChart`), reaproveitando
  a paleta categórica validada pela skill de dataviz do projeto.
- Filtro de categoria pai pro Pareto de subcategoria, igual ao original
  (select simples, mesmo padrão dos filtros já usados em Lançamentos).

**Onde morar:** ver seção "Feature Gráficos" abaixo — proposta em avaliação
inclui o Pareto como um dos 2 blocos da tela nova.

**Status:** registrado 2026-09-15, sem decisão de prioridade de execução.

### Exportação de relatório mensal/anual

**Pedido pelo usuário em 2026-09-15**, como próximo passo depois do MVP
(depois de Estrutura de Custo + os itens 4-7 acima estarem prontos).

**Objetivo declarado pelo usuário:** exportar os dados de um mês ou um ano
de um jeito que dê pra entregar pra uma análise (a mim, Claude, ou qualquer
outra ferramenta) — não é primariamente um relatório bonito pra imprimir,
é dado estruturado pra ser interpretado depois.

**Proposta de duas camadas, prioridade na primeira:**

1. **Export de dados estruturados (prioridade)** — JSON (ou CSV, mas JSON
   preserva melhor a estrutura aninhada) com: resumo financeiro do
   período (as duas leituras, taxa de poupança), lançamentos individuais
   do período, agregado por categoria/subcategoria, agregado por bucket
   (Estrutura de Custo: orçado × realizado, se houver orçamento no
   período), evolução mês a mês (se escopo = ano). Pensado pra ser colado
   numa conversa ou anexado a um prompt pra análise — não precisa ser
   bonito, precisa ser completo e sem ambiguidade (nomes de campo claros,
   valores já formatados como número, não string com "R$").
2. **Relatório legível (extensão futura, menor prioridade)** — PDF ou HTML
   pra impressão/leitura humana direta, reaproveitando os mesmos dados do
   item 1. Só vale a pena depois do item 1 existir, já que os dados são
   os mesmos.

**O que precisaria (para o item 1):**
- Escopo: mês específico ou ano inteiro (reaproveita os mesmos endpoints já
  existentes — `/dashboard/mensal`, `/dashboard/evolucao`,
  `/dashboard/despesas-por-categoria`, `/estrutura-custo/{mes}` — ou um
  endpoint agregador novo que já monta o JSON pronto pra download,
  evitando várias chamadas no frontend).
- Onde disparar o download: em aberto — um botão em Dashboard/Estrutura de
  Custo, ou uma tela própria "Relatórios" (ver seção "Feature Gráficos"
  abaixo, um dos mockups analisados tinha exatamente essa aba na
  navegação) — decisão de produto a tomar quando for priorizado.

**Status:** registrado 2026-09-15 a pedido explícito do usuário, como
próximo passo pós-MVP. Sem decisão de onde mora na navegação nem do
formato exato do JSON.

---

## Propostas em avaliação — aguardando aprovação

Itens sugeridos em 2026-09-15 a partir de mockups de referência trazidos
pelo usuário (não são screenshots do app antigo — são conceitos visuais
avaliados por mérito). **Nada aqui foi aprovado ainda** — a avaliação
completa, com o que eu recomendo adotar/adaptar/descartar de cada peça,
está na conversa; aqui só o resumo do que está em aberto:

- **Feature "Gráficos" dedicada** (nova tela na navegação): Pareto de
  despesas (item já no backlog acima) + tendência de Orçado×Realizado em
  vários meses (extensão de Estrutura de Custo, não duplicação). Em
  aberto: se a "Visão de Saúde Financeira" (evolução com taxa de poupança)
  merece uma segunda instância aqui ou só um reforço no Dashboard.
- **Reforço no `EvolucaoChart` do Dashboard**: adicionar taxa de poupança
  mensal (não só acumulada) como linha extra.
- **3 KPIs novos no Dashboard**: "Meses com resultado negativo",
  "Resultado acumulado" (R$, complementa a taxa em %), "Maior categoria de
  despesa" (KPI textual, hoje só visível no gráfico).
- **Estrutura de Custo**: adotar do mockup o resumo (Orçado/Realizado/
  Diferença/Execução %) e badges de status (Excedido/Dentro) por
  categoria — mas agrupando por **bucket** (fixo/variável/sazonal/
  investimentos), não por "categoria pai" solta como no mockup, pra bater
  com o schema real do app.

Ver a conversa de 2026-09-15 (ou o changelog em
`redesign-proposta-original.md`, quando isso for fechado) para o
raciocínio completo por trás de cada recomendação.
