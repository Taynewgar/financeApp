# Backlog — próximos passos

**Este é o arquivo de backlog do projeto** — a lista viva de prioridades e
pendências registradas. É aqui que se olha pra saber "o que vem depois" e
"o que ficou combinado registrar pra decidir mais tarde". Os outros 3
documentos em `docs/` são histórico e racional de decisão de design, não
pauta de trabalho — ver `docs/README.md` pra saber qual é qual.

Até 2026-09-15 esse conteúdo vivia espalhado dentro de
`changelog-proposta-original-do-redesign.md` ("Resumo de prioridades" + "Backlog
registrado"). Consolidado aqui num arquivo próprio porque o backlog cresceu
o suficiente (Pareto, exportação de relatório, propostas de gráficos) pra
merecer não ficar misturado com a tabela proposto×implementado tela a tela.

---

## Ordem de prioridade atual

1. ~~Delta vs mês anterior nos KPIs do Dashboard~~ **feito 2026-09-13**
2. ~~Tela de Planejamento~~ **feito 2026-09-14** — só configuração
3. ~~Tela de Estrutura de Custo~~ **feito 2026-09-15** — tabela hierárquica
   com expand/collapse (bucket > categoria > subcategoria), fita de KPIs,
   vereditos de pool de despesas/piso de investimentos e drill-down pra
   Busca de Lançamentos. Backend não mudou (motor já existia).
4. ~~Categorias "mais usadas" + criação inline no Novo Lançamento~~ **feito
   2026-09-15** — chips de atalho (ranking por uso nos últimos 6 meses) +
   formulário inline de criação, sem sair da tela.
5. ~~Feature "Gráficos" nova~~ **feita 2026-09-16**, em 3 rodadas (A: tela
   + migração + sparkline, com 2 ajustes extras 16.1/16.2; B: Pareto de
   despesas por categoria/subcategoria; C: tendência de Orçado×Realizado
   em vários meses, linka pra Estrutura de Custo) — ver changelog pra
   detalhe completo de cada rodada.
6. ~~Dashboard — 3 KPIs novos~~ **feito 2026-09-16** (ordem invertida com o
   item 5 a pedido do usuário, entregue antes por não ter dependência real
   de Gráficos) — "Meses com resultado negativo", "Resultado acumulado"
   (R$, ao lado da taxa em % que já existia) e "Maior categoria de
   despesa" (mesmo recorte do gráfico "Despesas por Categoria", sem
   endpoint novo — os 3 vêm de dados já buscados na tela).
7. Despesa fixa recorrente — aluguel, assinaturas (detalhe abaixo).
8. Edição de compra parcelada (detalhe abaixo).
9. Exportação de relatório mensal/anual (detalhe abaixo) — próximo passo
   depois do MVP fechado (itens 3-6 acima).
10. ~~Compromissos futuros no Dashboard~~ **feito parcialmente 2026-09-13**
    — só parcelas futuras; "fixo recorrente" fica coberto pelo item 7.
11. **Indicador visual de tooltip** — registrado 2026-09-15, sugestão do
    usuário pra pós-MVP (não é baixa prioridade, só sequenciado depois do
    MVP fechado, igual ao item 9). Hoje o Dashboard tem tooltip explicando
    cada card de resumo (item 24 do histórico), mas nada na tela avisa que
    o card é "hover-ável" — só se descobre passando o mouse por acaso.
    Ideia: marcar com um ícone pequeno (círculo com "?", tipo os de
    formulário) ao lado do que tem explicação extra — o padrão atual
    (tooltip nativo via `title`) continua por trás, só falta o
    *sinalizador visual*. Escopo: acha todo lugar que já usa tooltip
    explicativo (Dashboard é o caso conhecido, mas vale auditar as outras
    telas) e decide um componente/ícone padrão único pro app inteiro, não
    um por tela.

**Baixa prioridade confirmada pelo usuário** — todo o resto acima (e o
item 11) é alta ou média prioridade, mesmo o que está sequenciado pra
depois do MVP:

12. Aba Bancos em Configurações — hoje resolvido como campo de texto em
    Conta, sem perda funcional real. *(2026-09-15)*
13. Saldo atual de contas — hoje só caixinhas têm saldo calculado
    (`GET /dashboard/patrimonio/{mes}`); dar saldo a `contas` também seria
    a extensão natural, mas não é urgente. *(2026-09-15)*
14. **Changelog estruturado** — trocar a prosa narrativa de
    `changelog-proposta-original-do-redesign.md` pelo formato [Keep a
    Changelog](https://keepachangelog.com) (seções `Added/Changed/Fixed/
    Removed` por versão datada, amarrada a tag git). Ganho: escaneável e
    diffável, pronto pra virar release notes se o app for a público. Custo:
    perde o espaço pro "porquê" narrativo que o formato atual dá — por
    isso fica de baixa prioridade enquanto o projeto for de um usuário só.
    Sugestão minha (Claude), confirmada como baixa prioridade pelo usuário.
    *(2026-09-16)*
15. **ADRs (Architecture Decision Records)** — trocar o Q&A único de
    `sugestoes-e-decisoes-do-redesign.md` por um arquivo curto e imutável
    por decisão relevante (formato Nygard: contexto/decisão/consequências).
    Decisão revista vira um ADR novo que supersede o antigo, em vez de
    editar o `> Status:` por cima como hoje — histórico fica honesto, mas
    com mais arquivos pra navegar. Mesma origem e confirmação do item 14.
    *(2026-09-16)*
16. **Melhorias pós-MVP na tela Gráficos e na casca do app** — registradas
    2026-09-22, a pedido do usuário, pra decidir quando essa fase chegar
    (não agora). Detalhe de cada uma na subseção própria abaixo.

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

**Onde morar:** dentro da nova Feature Gráficos (ver subseção abaixo).

**Status:** registrado 2026-09-15, sem decisão de prioridade de execução.

### Feature "Gráficos" — tela nova na navegação

**Origem:** a aba Gráficos existia no app antigo (ver
`changelog-proposta-original-do-redesign.md`, seção "Gráficos / Análise") mas nunca virou
mockup nem backlog no redesign. Em 2026-09-15 o usuário trouxe mockups de
referência e pediu explicitamente uma feature de gráficos própria — decisão
tomada de destinar toda visualização gráfica do app pra cá, tirando gráfico
nenhum do Dashboard (que fica só com informação sintética — números, KPIs,
listas). Ver `changelog-proposta-original-do-redesign.md` pro racional completo por trás
de cada peça avaliada.

**O que entra nesta tela (v1):**
1. **Pareto de despesas** por categoria e subcategoria, com filtro de
   categoria pai — detalhe técnico na subseção própria acima.
2. **Tendência de Orçado × Realizado em vários meses** (barra Orçado/
   Realizado + linha % executado, por mês) — resumo que linka pra Estrutura
   de Custo pro detalhe por bucket/categoria de 1 mês específico. Não
   duplica o que Estrutura de Custo faz (que é uma leitura de 1 mês só),
   complementa com a visão de tendência.
3. **`EvolucaoChart`** (Receita/Despesa/Resultado, hoje no Dashboard) —
   move pra cá, não duplica.
4. **"Despesas por Categoria"** (barra empilhada, hoje no Dashboard) — move
   pra cá, não duplica.
5. Reforço no `EvolucaoChart` ao mover: adicionar taxa de poupança mensal
   (não só acumulada) como linha extra — dado computável a partir do que
   `/dashboard/evolucao` já retorna por mês.

**Dashboard ganha, em troca (aprovado 2026-09-15):** um **sparkline**
compacto (sem eixos, sem legendas, sem tooltip — só a forma dos últimos 6
meses) ao lado do resultado principal, pra manter a leitura rápida de
tendência mesmo com os gráficos completos morando só em Gráficos. Mitigação
proposta por mim depois de avaliar ganhos/perdas da divisão, aprovada pelo
usuário.

**O que fica de fora, por decisão já tomada antes desta rodada:** painel de
qualidade dos dados (ligado ao fluxo de importação de CSV, não a esta tela)
e o seletor local "Escopo da evolução" (redundante com o seletor de
período — Mês/Intervalo/Todos os meses — que a tela reaproveita do
Dashboard, mesmo componente, em vez de reinventar um 3º modelo de filtro).

**Status:** decidido por completo 2026-09-15 — feature Gráficos (Pareto +
tendência), migração dos 2 gráficos do Dashboard, e o sparkline de
mitigação. Sem trabalho iniciado ainda (Estrutura de Custo é a prioridade
imediata).

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
- Onde disparar o download: **decidido 2026-09-15 — botão/link numa tela
  existente** (Estrutura de Custo, a definir se também em Dashboard),
  confirmado pelo usuário. Nada de tela "Relatórios" própria na navegação
  por enquanto — só reconsiderar se o export ganhar mais capacidade real
  que justifique um destino próprio (histórico de exports, PDF/HTML,
  agendamento).

**Status:** registrado 2026-09-15 a pedido explícito do usuário, como
próximo passo pós-MVP, local de disparo já decidido. Falta só o formato
exato do JSON quando for priorizado.

### Melhorias pós-MVP na tela Gráficos e na casca do app

Registradas 2026-09-22, a partir do teste do usuário nas Rodadas B e C da
feature Gráficos. Nenhuma priorizada ainda — só documentadas pra não se
perder.

1. **Layout e posicionamento dos gráficos na página** — reorganizar
   `/graficos` por tema (tendência: Evolução Mensal + Taxa de Poupança +
   Orçado×Realizado + % executado; composição: Pareto + Despesas por
   Categoria), em vez da ordem atual intercalada. Ver também os itens 2 e
   3 do detalhamento da Feature Gráficos acima, que já apontam pra essa
   reordenação.
2. **Cabeçalho fixo por feature, ou botão de ciclar topo↔ponto anterior**
   — qual é melhor pra UX numa página que cresceu (Gráficos já tem 4
   seções). **Só responder quando esta melhoria for implementada** —
   pedido explícito do usuário pra não decidir prematuramente.
3. **Janela de meses pra trás × ano civil (jan-dez) nos gráficos** —
   hoje o modo "Mês" em `/graficos` mostra N meses pra trás contando do
   mês selecionado (12, ver Rodada 16.2). Repensar se um ano civil fixo
   (janeiro-dezembro) seria mais legível — decidir quando esta fase de
   melhoria chegar.
4. **Barra lateral de navegação não deve sumir ao rolar** — hoje
   acompanha o scroll do corpo da página (comportamento não intencional,
   a confirmar onde exatamente isso acontece antes de corrigir).

---

Todas as propostas trazidas em 2026-09-15 (6 mockups de referência) foram
decididas nesta mesma rodada — nenhuma pendência de aprovação restante. Ver
o changelog em `changelog-proposta-original-do-redesign.md` pro raciocínio completo por
trás de cada recomendação.
