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
   em vários meses, linka pra Estrutura de Custo), mais uma Rodada D de
   refinamento em 2026-09-22 (Base da média sempre visível e com efeito
   garantido em todo modo, reordenação por tema, curva de % acumulado no
   Pareto) — ver changelog pra detalhe completo de cada rodada.
6. ~~Dashboard — 3 KPIs novos~~ **feito 2026-09-16** (ordem invertida com o
   item 5 a pedido do usuário, entregue antes por não ter dependência real
   de Gráficos) — "Meses com resultado negativo", "Resultado acumulado"
   (R$, ao lado da taxa em % que já existia) e "Maior categoria de
   despesa" (mesmo recorte do gráfico "Despesas por Categoria", sem
   endpoint novo — os 3 vêm de dados já buscados na tela).
7. ~~Despesa fixa recorrente — aluguel, assinaturas~~ **feito 2026-09-22**
   — projeção virtual (decisão discutida e aprovada nesta rodada, ver
   detalhe abaixo): `lancamentos_recorrentes` (tela em Configurações),
   `POST /lancamentos-recorrentes/{id}/confirmar` materializa a transação
   real só quando o mês é confirmado, `GET /dashboard/compromissos-futuros`
   mistura parcelas + ocorrências pendentes.
8. ~~Edição de compra parcelada~~ **feito 2026-09-24** — níveis 1
   (metadado) + 3 (exclusão em grupo); nível 2 (recriar o grupo) fica pra
   decisão futura (detalhe abaixo).
9. **Migração de dados do app antigo** (detalhe abaixo) — alta
   prioridade, registrada 2026-09-24. Passo do MVP original que ficou de
   fora do backlog quando ele foi consolidado em arquivo próprio
   (2026-09-15); ver detalhe abaixo pro porquê.
10. Exportação de relatório mensal/anual (detalhe abaixo) — próximo passo
    depois do MVP fechado (itens 3-6 acima).
11. ~~Compromissos futuros no Dashboard~~ **feito por completo
    2026-09-22** — parcelas futuras (2026-09-13) + despesa fixa
    recorrente (item 7, 2026-09-22).
12. ~~Indicador visual de tooltip~~ **feito 2026-09-24** — componente
    `InfoIcon` único pro app inteiro (Dashboard, Lançamentos, Base da
    média), clicável (não depende de hover — não existe em touchscreen,
    corrigido na Rodada 22.1). Ver changelog Rodadas 22/22.1.

**Média prioridade confirmada pelo usuário** — registrados 2026-09-24, a
partir do teste do seed novo e dos mockups de cabeçalho fixo; depois do
que está acima, antes da baixa prioridade abaixo:

13. ~~Persistir estado de filtros ao navegar entre features~~ **feito
    2026-09-24** — Detalhe na subseção própria abaixo, ver changelog
    Rodada 24.
14. **Filtro específico pra recorrentes** — Detalhe na subseção própria
    abaixo.
15. **Lista de "meses pulados" muito grande** — com sugestão de
    abordagem. Detalhe na subseção própria abaixo.
16. ~~Cabeçalho fixo/controles fixos por feature~~ **feito 2026-09-24** —
    decidido via mockups (Lançamentos, Gráficos, Estrutura de Custo,
    Planejamento, Dashboard). Ver changelog Rodada 23.
17. ~~Barra lateral não deve sumir ao rolar~~ **feito 2026-09-24** — Ver
    changelog Rodada 23.
18. **Janela de meses pra trás × ano civil (jan-dez) nos gráficos** —
    hoje o modo "Mês" em `/graficos` mostra N meses pra trás contando do
    mês selecionado (12, ver Rodada 16.2). Repensar se um ano civil fixo
    (janeiro-dezembro) seria mais legível.
19. **Tooltip: balão abre perto da borda/canto no mobile aumentando a
    área que precisa ser rolada** — reportado 2026-09-24, testando a
    Rodada 22.1. O balão (`position:absolute`) pode extrapolar o
    viewport perto das bordas, ampliando o scroll da página. Fix
    provável: clampar a posição do balão dentro do viewport (ou usar
    `position:fixed` com coordenadas calculadas via
    `getBoundingClientRect`).
20. **Lançamentos: cards quebrando no layout mobile** — reportado
    2026-09-24.
21. **Botões inferiores (barra de navegação mobile) pequenos e colados**
    — reportado 2026-09-24.
22. **Estrutura de Custo carregando devagar — investigar excesso de
    requisições** — reportado 2026-09-24, suspeita de padrão parecido com
    o bug já corrigido em Gráficos.

**Baixa prioridade confirmada pelo usuário** — todo o resto acima (itens
1-22) é alta ou média prioridade, mesmo o que está sequenciado pra depois
do MVP:

23. Aba Bancos em Configurações — hoje resolvido como campo de texto em
    Conta, sem perda funcional real. *(2026-09-15)*
24. Saldo atual de contas — hoje só caixinhas têm saldo calculado
    (`GET /dashboard/patrimonio/{mes}`); dar saldo a `contas` também seria
    a extensão natural, mas não é urgente. *(2026-09-15)*
25. **Changelog estruturado** — trocar a prosa narrativa de
    `changelog-proposta-original-do-redesign.md` pelo formato [Keep a
    Changelog](https://keepachangelog.com) (seções `Added/Changed/Fixed/
    Removed` por versão datada, amarrada a tag git). Ganho: escaneável e
    diffável, pronto pra virar release notes se o app for a público. Custo:
    perde o espaço pro "porquê" narrativo que o formato atual dá — por
    isso fica de baixa prioridade enquanto o projeto for de um usuário só.
    Sugestão minha (Claude), confirmada como baixa prioridade pelo usuário.
    *(2026-09-16)*
26. **ADRs (Architecture Decision Records)** — trocar o Q&A único de
    `sugestoes-e-decisoes-do-redesign.md` por um arquivo curto e imutável
    por decisão relevante (formato Nygard: contexto/decisão/consequências).
    Decisão revista vira um ADR novo que supersede o antigo, em vez de
    editar o `> Status:` por cima como hoje — histórico fica honesto, mas
    com mais arquivos pra navegar. Mesma origem e confirmação do item 25.
    *(2026-09-16)*

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

**Status:** implementado em 2026-09-22 — projeção virtual (opção 2),
confirmação manual (escolha do usuário pro MVP, dado que o projeto não tem
job/cron agendado nenhum hoje). Escopo já integra "Compromissos Futuros"
(mescla parcelas + ocorrências pendentes, escolha do usuário — a
alternativa seria isolar num "só cadastro + confirmação", sem tocar em
Compromissos Futuros nesta rodada). Ver changelog pro detalhe completo:
schema (`lancamentos_recorrentes` + `transacoes.lancamento_recorrente_id`),
endpoints (`/lancamentos-recorrentes` CRUD + `/confirmar`), tela de gestão
em Configurações, botão "Confirmar" no Dashboard. Criação inline de
categoria/subcategoria no formulário (mesmo padrão do Novo Lançamento,
conta continua só por dropdown) e ação de **pular um mês** (`/pular` —
ex: viajou, não teve a despesa naquele mês; não vira transação, só faz o
mês parar de reaparecer como pendente) adicionadas no mesmo dia, a partir
de feedback do usuário testando a entrega original. Em 2026-09-24, bug
real reportado em uso (clique acidental em "Pular" confundido com
"Confirmar" + mensagem de erro apagada por uma ação subsequente antes de
ser lida) motivou 3 fixes: tela de ver/desfazer meses pulados em
Configurações (`GET /pulados`), erro só limpo no sucesso da própria ação
(com contexto do item/mês na mensagem), e separação visual dos botões
"Confirmar"/"Pular este mês" no Dashboard. Ver changelog Rodada 20.3.

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
   *(Revisto na Rodada 21.1: valor saiu desse grupo travado — ver Status
   abaixo.)*

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

**Status:** implementado 2026-09-24 — níveis 1 e 3. `PATCH /transacoes/
parceladas/{id}` (metadado) e `DELETE /transacoes/parceladas/
{compra_parcelada_id}` (grupo inteiro). Nível 1 estendido no mesmo dia
(Rodada 21.1) pra incluir **valor** — motivo real do pedido original:
não existe padrão bancário único de arredondamento de centavos entre
parcelas, então a fatura real do emissor pode divergir do calculado na
criação, e `valor_total` do grupo nunca foi conferido em lugar nenhum do
código depois da criação (só serviu pra calcular o valor inicial) — não
havia inconsistência real a proteger. Nível 2 (editar o grupo recriando
com novo valor total/quantidade de parcelas) segue sem decisão — o ponto
difícil descrito acima (parcelas já vencidas / `fatura_override`) não
mudou. Ver changelog pro detalhe técnico completo e o checklist de teste
manual.

### Migração de dados do app antigo (CSV/JSON → Supabase)

**Origem:** fase 2.e do plano original de evolução
(`docs/plano-de-evolucao-original.md`, seção "2.e — Migrar dados
existentes sem conflito") — script único, rodado uma vez, que importa o
histórico consolidado do app desktop antigo (`historico_lancamentos.csv`
+ `orcamentos.json`, não o CSV bruto de extrato bancário) pras tabelas do
Supabase.

**Por que ficou de fora do backlog até agora:** quando o backlog foi
consolidado num arquivo próprio (2026-09-15), esse item não foi trazido
junto — só existia documentado dentro do plano de evolução original, que
descreve o racional de decisão, não é pauta de trabalho. Achado e
corrigido em 2026-09-24, a pedido do usuário.

**O que o script precisa fazer** (detalhado no plano original):
1. Rodar sobre o histórico consolidado/deduplicado, não sobre CSVs brutos
   de banco.
2. Normalizar texto (reaproveitando `_normalize_text` do app antigo) pra
   agrupar variações e gerar `categorias`/`subcategorias`/`contas`/
   `caixinhas` a partir dos valores distintos encontrados.
3. Manter o texto original bruto numa coluna de auditoria
   (`categoria_raw`) durante a transição, pra conferência.
4. Reaproveitar `hash_dedup` (unique constraint já implementado desde a
   Entrega 1, pronto exatamente pra isso) — rodar o script de novo não
   duplica nada.
5. Gerar um relatório de dry-run antes de gravar de vez (quantas
   categorias novas, quantas transações, quantos itens não mapeados) pra
   validação antes do commit definitivo.
6. Checagem de reconciliação pós-migração: soma de receita/despesa por
   mês no CSV antigo tem que bater exatamente com a soma no banco novo
   (`docs/sugestoes-e-decisoes-do-redesign.md`, seção 4).

**Depois da migração:** importação de CSV vira opcional (import assistido
de extrato bancário, mapeando pras categorias já existentes) — não é mais
o único caminho de entrada, já que o formulário guiado já cobre o uso do
dia a dia.

**Status:** registrado 2026-09-24, alta prioridade — nenhum trabalho
iniciado ainda.

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

**Status:** implementado por completo em 2026-09-22 — tabela (Rodada B,
2026-09-16) + `ParetoTendenciaChart` complementar (curva de % acumulado,
eixo Y fixo 0-100%, linha tracejada em 80%, sem duplicar a leitura por
categoria que a tabela já dá).

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
feature Gráficos. As 3 primeiras já resolvidas; a 4ª (item 18 da lista de
prioridade) segue pendente.

1. ~~**Layout e posicionamento dos gráficos na página**~~ **feito
   2026-09-22** — `/graficos` reorganizada por tema: Evolução Mensal (+
   Taxa de Poupança) → Orçado×Realizado (+ % executado) → Pareto de
   Despesas → Despesas por Categoria fica por último (composição, não
   tendência). Ver changelog pro detalhe completo desta rodada.
2. ~~**Cabeçalho fixo por feature**~~ **feito 2026-09-24** (item 16) —
   decidido via mockups: controles (período/mês/KPIs-resumo) fixos no
   topo, não um botão de ciclar (essa alternativa foi descartada — não
   resolvia o objetivo real do usuário, que era não precisar rolar de
   volta pra usar um controle). Ver "Cabeçalho fixo — detalhe da decisão"
   abaixo e changelog Rodada 23.
3. **Janela de meses pra trás × ano civil (jan-dez) nos gráficos** (item
   18 da lista de prioridade) — hoje o modo "Mês" em `/graficos` mostra N
   meses pra trás contando do mês selecionado (12, ver Rodada 16.2).
   Repensar se um ano civil fixo (janeiro-dezembro) seria mais legível —
   decidir quando esta fase de melhoria chegar.
4. ~~**Barra lateral de navegação não deve sumir ao rolar**~~ **feito
   2026-09-24** (item 17) — `position: sticky` em `.shell-nav`
   (`AppShell.css`). Ver changelog Rodada 23.

### Cabeçalho fixo — detalhe da decisão

Processo: usuário pediu mockups (Artifact tipo Design/canvas) antes de
decidir. 1ª rodada comparou 2 alternativas genéricas — cabeçalho com
título de seção vs. botão de ciclar topo↔ponto anterior — usando Gráficos
como exemplo. Usuário esclareceu a intenção real: não é sobre "saber em
que seção estou", é sobre **não precisar rolar de volta pra usar um
controle** (filtro de Lançamentos, período de Gráficos, mês de Estrutura
de Custo/Planejamento/Dashboard). Isso descartou o botão de ciclar (não
resolve esse problema) e redirecionou a 1ª opção pra fixar os controles
de verdade, não um título ilustrativo.

2ª rodada de mockups, um por tela, com o controle real de cada uma:
- **Lançamentos** — comportamento diferente por tamanho de tela: no
  desktop tem espaço pra fixar o painel de filtro completo (12 campos,
  elementos reduzidos); no mobile o painel sozinho já ocupa a tela toda
  hoje, então vira uma barra resumida fixa ("N filtros ativos ▾") que
  expande o painel completo por cima da lista ao tocar.
- **Gráficos** — seletor de período (Mês/Intervalo/Todos + Base da
  média) fixo.
- **Estrutura de Custo** — navegador de mês + fita de KPIs (Orçado/
  Realizado/Diferença/Execução) fixos, versão compacta da fita que já
  existe abaixo (não substitui, duplica reduzido).
- **Planejamento** — navegador de mês fixo; usuário pediu pra também
  manter a alocação por bucket visível (mesmo que reduzida) — versão
  final tem 4 barrinhas de progresso compactas (uma por bucket) abaixo
  do navegador.
- **Dashboard** — toggle Leitura de Caixa/Saúde + seletor de período
  fixos; usuário pediu pra também manter alguns KPIs visíveis — versão
  final acrescenta uma linha com 3 KPIs (Resultado/Despesas líquidas/
  Taxa de poupança).

Todas as 5 aprovadas e implementadas na Rodada 23. Componente/CSS
compartilhado: `components/cabecalhoFixo.css` (`.cabecalho-fixo` — só a
mecânica sticky; `.cabecalho-fixo-card` — visual de card pras telas sem
um card próprio pra encaixar; `.cabecalho-fixo-grid`/`-stat`/`-barra` —
grade compacta de estatísticas/barrinhas de progresso reaproveitada em
Estrutura de Custo/Planejamento/Dashboard).

### Persistir estado de filtros ao navegar entre features

**Motivo de não existir hoje:** cada tela guarda seus filtros em estado
local do componente React (`useState`), que é descartado ao desmontar —
sair de Lançamentos pra Planejamento e voltar reseta o formulário de
filtro pro padrão. Exemplo trazido pelo usuário: aplicar filtros em
Lançamentos, ir pra Planejamento, voltar — os filtros deveriam continuar
aplicados.

**O que precisaria:** mover o estado de filtro pra fora do componente de
tela (contexto React, ou persistência em `sessionStorage`/`localStorage`
por feature) pra sobreviver à navegação. Escopo real depende de quantas
telas têm filtro hoje (Lançamentos é a mais rica; Gráficos e Estrutura de
Custo também têm seletor de período) — decidir se é um mecanismo genérico
(1 hook reaproveitado por tela) ou feito tela a tela quando aparecer o
próximo pedido.

**Status:** implementado 2026-09-24 — escolhido o mecanismo genérico:
Context React por tela, montado no `AppShell` (que fica montado o tempo
todo — só o `<Outlet/>` troca entre rotas), sem `sessionStorage`/
`localStorage` (não precisa sobreviver a fechar a aba, só à navegação
dentro do app). Escopo final: **5 telas** — Lançamentos, Gráficos,
Estrutura de Custo, Planejamento e Dashboard (Dashboard ficou de fora do
escopo confirmado inicialmente por engano meu, corrigido no mesmo dia —
Rodada 24.1). Bug real achado e corrigido no mesmo dia (Rodada 24.1):
o efeito que aplica `?mes=` (drill-down vindo de Gráficos) em Estrutura
de Custo dependia do objeto `searchParams` inteiro, que o react-router
recria a cada render mesmo sem navegação — sobrescrevia cliques nas
setas de mês sempre que a URL ainda carregava o `?mes=` antigo; corrigido
pra depender só do valor (string). Comportamento confirmado com o
usuário: entrar de novo pelo link de drill-down deve mesmo levar ao mês
indicado — não é bug, é o esperado. Toggle "Leitura de Caixa/Saúde" do
Dashboard também entrou no escopo (Rodada 24.2) — era `useState` local,
resetava pra "saúde" a cada troca de tela; passou a viver no mesmo
Context de período do Dashboard. Ver changelog Rodadas 24/24.1/24.2 pro
detalhe técnico completo.

### Filtro específico pra recorrentes

**Contexto:** a tela de gestão de recorrentes (Configurações →
Lançamentos Recorrentes) hoje lista tudo sem filtro — pedido do usuário
depois de usar a tela com o seed novo (2 recorrentes já deixa a lista
maior que o caminho feliz original previa).

**O que precisaria:** decidir os eixos de filtro fazem sentido aqui —
candidatos óbvios são status (ativo/inativo), categoria e tipo de
movimento, no mesmo padrão visual dos filtros já usados em Lançamentos.

**Status:** registrado 2026-09-24, a pedido do usuário, sem decisão de
escopo/prioridade ainda.

### Lista de "meses pulados" muito grande

**Contexto:** a tela de "Meses pulados"/desfazer por recorrente (Rodada
20.3) lista todos os meses pulados sem paginação nem agrupamento —
funciona bem com poucos itens, mas um recorrente de longa duração pode
acumular muitos pulados ao longo dos anos. Usuário pediu explicitamente
uma sugestão de tratamento visual, não só o registro do problema.

**Sugestão (Claude):** agrupar por ano com o ano corrente expandido e
anos anteriores colapsados por padrão (acordeão) — cobre o caso comum
(poucos pulados, tudo visível de cara) sem esconder o histórico, e evita
paginação (mais complexa de implementar e pior UX numa lista pequena por
natureza — "pular um mês" é uma ação ocasional, não constante). Alternativa
mais simples, se o acordeão for exagero pro volume real: limitar a lista a
"últimos 12 meses" com um link "ver todos" que expande o resto.

**Status:** registrado 2026-09-24, a pedido do usuário, com sugestão de
abordagem; decisão de qual variante (acordeão por ano vs. "últimos 12 +
ver todos") fica pra quando esta melhoria for priorizada.

---

Todas as propostas trazidas em 2026-09-15 (6 mockups de referência) foram
decididas nesta mesma rodada — nenhuma pendência de aprovação restante. Ver
o changelog em `changelog-proposta-original-do-redesign.md` pro raciocínio completo por
trás de cada recomendação.
