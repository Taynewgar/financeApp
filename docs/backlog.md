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

Reorganizado por prioridade em 2026-09-24 (a pedido do usuário — a
numeração em si não muda, cada item mantém o número que já tinha em
qualquer lugar que o referencie; só a ordem/agrupamento na lista muda,
pra separar o que ainda está pendente do que já foi entregue e não ficar
perdido em volta de itens concluídos).

### Alta prioridade

**Pendente:**

9. **Migração de dados do app antigo** (detalhe abaixo) — registrada
   2026-09-24. Passo do MVP original que ficou de fora do backlog quando
   ele foi consolidado em arquivo próprio (2026-09-15); ver detalhe
   abaixo pro porquê.
10. Exportação de relatório mensal/anual (detalhe abaixo) — próximo passo
    depois do MVP fechado (itens 1-8 abaixo).
29. **Menu "mais" da barra de navegação mobile: promover item mais usado
    por contador de uso** (detalhe abaixo) — sugestão minha (Claude),
    confirmada como alta prioridade pelo usuário em 2026-09-24, durante a
    discussão de mockups do item 21.

**Concluído:**

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
11. ~~Compromissos futuros no Dashboard~~ **feito por completo
    2026-09-22** — parcelas futuras (2026-09-13) + despesa fixa
    recorrente (item 7, 2026-09-22).
12. ~~Indicador visual de tooltip~~ **feito 2026-09-24** — componente
    `InfoIcon` único pro app inteiro (Dashboard, Lançamentos, Base da
    média), clicável (não depende de hover — não existe em touchscreen,
    corrigido na Rodada 22.1). Ver changelog Rodadas 22/22.1.

### Média prioridade confirmada pelo usuário

Registrados 2026-09-24, a partir do teste do seed novo e dos mockups de
cabeçalho fixo; depois da alta prioridade acima, antes da baixa
prioridade abaixo:

**Pendente:**

18. **Janela de meses pra trás × ano civil (jan-dez) nos gráficos** —
    hoje o modo "Mês" em `/graficos` mostra N meses pra trás contando do
    mês selecionado (12, ver Rodada 16.2). Repensar se um ano civil fixo
    (janeiro-dezembro) seria mais legível.
23. **Lançamentos recorrentes: aplicação/retirada com caixinha (reserva)**
    — registrado 2026-09-24. Escopo confirmado com o usuário depois da
    Rodada 25 (que estendeu recorrentes pra receita/despesa/aplicação/
    retirada, mas deixou caixinha de fora por decisão minha, não pedida —
    limitação de análise, o usuário esclareceu depois que aplicação/
    retirada recorrente PODE ser vinculada a caixinha, igual em Novo
    Lançamento). Ordem confirmada: item 22 (lentidão de Estrutura de
    Custo) vem imediatamente antes deste na fila.

**Concluído:**

13. ~~Persistir estado de filtros ao navegar entre features~~ **feito
    2026-09-24** — Detalhe na subseção própria abaixo, ver changelog
    Rodada 24.
14. ~~Filtro específico pra recorrentes~~ **feito 2026-09-24** — Detalhe
    na subseção própria abaixo, ver changelog Rodada 25.
15. ~~Lista de "meses pulados" muito grande~~ **feito 2026-09-24** —
    acordeão por ano, escolhido pelo usuário entre 2 mockups. Detalhe na
    subseção própria abaixo, ver changelog Rodada 26.
16. ~~Cabeçalho fixo/controles fixos por feature~~ **feito 2026-09-24** —
    decidido via mockups (Lançamentos, Gráficos, Estrutura de Custo,
    Planejamento, Dashboard). Ver changelog Rodada 23.
17. ~~Barra lateral não deve sumir ao rolar~~ **feito 2026-09-24** — Ver
    changelog Rodada 23.
21. ~~Botões inferiores (barra de navegação mobile) pequenos e colados~~
    **feito 2026-09-25** — decidido via 3 rodadas de mockups (Opção A/B/C,
    Opção C mesclada escolhida e refinada pelo usuário). Detalhe na
    subseção própria abaixo, ver changelog Rodada 28.
22. ~~Estrutura de Custo carregando devagar~~ **feito 2026-09-24** —
    causa raiz era a mesma classe de bug já corrigida em Gráficos (Rodada
    19.2/19.3), só que ainda não tinha sido aplicada em `obter()` (a
    tela de 1 mês). Detalhe na subseção própria abaixo, ver changelog
    Rodada 27.
24. ~~Planejamento com o mesmo padrão de lentidão de Estrutura de Custo~~
    **feito 2026-09-25** — mesmo fix portado pra `routers/orcamentos.py`.
    Detalhe na subseção própria abaixo, ver changelog Rodada 29.
19. ~~Tooltip: balão abre perto da borda/canto no mobile aumentando a
    área que precisa ser rolada~~ **feito 2026-09-25** — `InfoIcon` passou
    a `position:fixed` com coordenadas calculadas via
    `getBoundingClientRect`, clampadas dentro do viewport. Detalhe na
    subseção própria abaixo, ver changelog Rodada 30.
20. ~~Lançamentos: cards quebrando no layout mobile~~ **feito 2026-09-25**
    — causa era compartilhada com Contas/Categorias/Caixinhas/Recorrentes
    (mesmo componente de lista, `crud.css`), não só Lançamentos. Detalhe
    na subseção própria abaixo, ver changelog Rodada 30.

### Baixa prioridade confirmada pelo usuário

Todo o resto acima é alta ou média prioridade, mesmo o que está
sequenciado pra depois do MVP. Nenhum destes 4 está em andamento:

25. Saldo atual de contas — hoje só caixinhas têm saldo calculado
    (`GET /dashboard/patrimonio/{mes}`); dar saldo a `contas` também seria
    a extensão natural, mas não é urgente. *(2026-09-15)*
26. **Changelog estruturado** — trocar a prosa narrativa de
    `changelog-proposta-original-do-redesign.md` pelo formato [Keep a
    Changelog](https://keepachangelog.com) (seções `Added/Changed/Fixed/
    Removed` por versão datada, amarrada a tag git). Ganho: escaneável e
    diffável, pronto pra virar release notes se o app for a público. Custo:
    perde o espaço pro "porquê" narrativo que o formato atual dá — por
    isso fica de baixa prioridade enquanto o projeto for de um usuário só.
    Sugestão minha (Claude), confirmada como baixa prioridade pelo usuário.
    *(2026-09-16)*
27. **ADRs (Architecture Decision Records)** — trocar o Q&A único de
    `sugestoes-e-decisoes-do-redesign.md` por um arquivo curto e imutável
    por decisão relevante (formato Nygard: contexto/decisão/consequências).
    Decisão revista vira um ADR novo que supersede o antigo, em vez de
    editar o `> Status:` por cima como hoje — histórico fica honesto, mas
    com mais arquivos pra navegar. Mesma origem e confirmação do item 26.
    *(2026-09-16)*
28. Aba Bancos em Configurações — hoje resolvido como campo de texto em
    Conta, sem perda funcional real. *(2026-09-15, renumerado de 24 pra 28
    em 2026-09-24 nesta reorganização — colidia com o item 24 de média
    prioridade acima)*

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

**Contexto:** a tela de gestão de recorrentes (então em Configurações →
Despesas Fixas Recorrentes) listava tudo sem filtro — pedido do usuário
depois de usar a tela com o seed novo (2 recorrentes já deixa a lista
maior que o caminho feliz original previa). Ao discutir os eixos
("tipo de movimento" fazia sentido?), veio à luz que "recorrente" tinha
sido modelado só como despesa fixa por engano de análise meu — o usuário
esclareceu que tem receitas e aplicações recorrentes também (salário
mensal, aporte mensal), então o item virou dois: estender o cadastro
pra cobrir receita/aplicação/retirada, e mover a tela de Configurações
pra dentro de Lançamentos (nova aba "Recorrentes" — "tipo de movimento"
só faz sentido como filtro real depois dessa extensão).

**Status:** implementado 2026-09-24 (Rodada 25) — `lancamentos_recorrentes`
ganhou `tipo_movimento` (receita/despesa/aplicacao/retirada); cada tipo
usa o mesmo subconjunto de campos do Novo Lançamento, forçado pelo
backend (despesa exige categoria/estrutura_custo/meio_pagamento;
aplicação/retirada é sempre `estrutura_custo='investimentos'`; receita
não usa nenhum dos dois). Sem suporte a caixinha/reserva recorrente por
enquanto (fica pra um próximo item, se pedido). A tela saiu de
Configurações e ganhou aba própria em Lançamentos, com filtro por
status/categoria/tipo de movimento (os 3 eixos do pedido original). Ver
changelog Rodada 25 pro detalhe técnico completo.

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

**Status:** implementado 2026-09-24 (Rodada 26) — as 2 variantes viraram
mockups interativos (Artifact Design) pro usuário comparar lado a lado;
escolhida a **Opção A (acordeão por ano)**. `RecorrentesSection.tsx`
agrupa `pulados[r.id]` por ano (`agruparPuladosPorAno`), ano corrente
sempre aberto ao abrir "Meses pulados", anos anteriores começam
fechados — clique no ano alterna (`anosAbertos`, um `Set` de chaves
`recorrenteId:ano`). Ver changelog Rodada 26 pro detalhe técnico.

### Estrutura de Custo carregando devagar

**Contexto:** reportado pelo usuário testando a tela — "provável excesso
de requisições", mesma suspeita já confirmada e corrigida em `/graficos`
(Rodada 19.2/19.3).

**Causa raiz:** confirmada igual à suspeita. `GET /estrutura-custo/{mes}`
(`obter()`) montava o resultado chamando `saldo_anterior_ao_vivo()` uma
vez por item do orçamento do mês — função recursiva que sobe a cadeia de
orçamentos anteriores no banco, mês a mês, até achar o primeiro mês sem
orçamento anterior (3 SELECTs por mês subido: `orcamentos`,
`orcamento_itens` do mês anterior, `transacoes` do mês anterior). Pra um
orçamento com histórico de N meses e M itens, isso é até `3×N×M`
requisições sequenciais numa tela que só mostra 1 mês. A Rodada 19.3 já
tinha resolvido exatamente essa classe de bug pra `/graficos`
(`evolucao_orcamento()`, que busca vários meses) via `saldo_anterior_em_lote()`
— carrega todo o histórico em 3 queries fixas e recalcula a cadeia
inteira em memória — mas não tinha sido portada pra `obter()` (só 1 mês,
"parecia" não precisar).

**Status:** implementado 2026-09-24 (Rodada 27) — `obter()` passou a usar
o mesmo mecanismo de carregamento em lote de `evolucao_orcamento()`
(`_carregar_dados_periodo()`, extraído como função compartilhada) +
`_estrutura_custo_do_mes_em_lote()`, no lugar da função antiga
`_estrutura_custo_do_mes()` (removida). Toda requisição a
`/estrutura-custo/{mes}` agora faz exatamente 3 SELECTs, não importa o
tamanho do histórico de orçamento nem o número de itens. Teste de
regressão conta as chamadas reais (`db.table(...)`) — confirmado
manualmente que falha contra o código antigo (13 chamadas a `orcamentos`
num cenário de 2 itens × 5 meses de cadeia, onde deveria ser 1). Ver
changelog Rodada 27 pro detalhe técnico completo. Achado de passagem
registrado como novo item 24 (Planejamento tem o mesmo padrão, ainda não
corrigido).

### Lançamentos recorrentes: aplicação/retirada com caixinha (reserva)

**Contexto:** a Rodada 25 estendeu `lancamentos_recorrentes` pra cobrir
receita/despesa/aplicação/retirada (antes só despesa fixa), mas deixou
caixinha/reserva de fora — decisão minha de escopo na hora, não um "não"
do usuário. Testando, o usuário esclareceu: aplicação/retirada
recorrente PODE ser vinculada a uma caixinha (reserva), mesma
possibilidade que já existe em Novo Lançamento — a limitação foi só
falta de eu ter perguntado, não uma regra de negócio real.

**O que precisaria:** `lancamentos_recorrentes` ganhar `caixinha_id`
(nullable), mesma regra de `transacoes`/Novo Lançamento — caixinha só em
aplicação/retirada, e a conta do recorrente precisa bater com a conta
vinculada da caixinha. `confirmar()` passa `caixinha_id` pra transação
real gerada. No formulário (`RecorrentesSection.tsx`), aplicação/
retirada ganha a mesma escolha "Investimento × Reserva" que Novo
Lançamento já tem (`direcao`/tipo `reserva` vs `investimento`), com
seleção de caixinha quando for reserva.

**Ordem confirmada com o usuário:** o item 22 (Estrutura de Custo
carregando devagar) é o item anterior a este na fila — corrigir a
lentidão primeiro, esta extensão de recorrentes depois.

**Status:** registrado 2026-09-24, a pedido do usuário, sem
implementação ainda.

### Planejamento com o mesmo padrão de lentidão de Estrutura de Custo

**Contexto:** achado de passagem corrigindo o item 22 (Rodada 27) —
não reportado pelo usuário ainda, então não corrigido junto (fora do
escopo pedido: "seguir para o 22, lentidão estrutura de custo").

`GET /orcamentos/{id}/itens` (a tela de Planejamento) monta cada item da
lista chamando `_enriquecer_item()` (`routers/orcamentos.py`), que
recalcula `saldo_anterior` via `saldo_anterior_ao_vivo()` — a mesma
função recursiva que causava o N+1 de requisições em Estrutura de Custo,
subindo a cadeia de orçamentos anteriores direto no banco, mês a mês, a
cada item. `_validar_teto_bucket()` (chamada ao criar/editar um item)
tem o mesmo padrão, numa escala menor (só os itens do bucket sendo
validado, não a lista inteira).

**O que precisaria:** portar o mesmo mecanismo que já resolveu Estrutura
de Custo — carregar o histórico de orçamentos/itens/transações em lote
(`_carregar_dados_periodo`, hoje em `estrutura_custo.py`) e recalcular a
cadeia de `saldo_anterior` em memória (`saldo_anterior_em_lote`, já
existe em `services/orcamento_saldo.py`) em vez de item a item no banco.
Como as duas funções (`saldo_anterior_em_lote`/`saldo_anterior_ao_vivo`)
já vivem no mesmo módulo de serviço, a troca deveria ser direta — o
trabalho principal é decidir se `_carregar_dados_periodo` migra pra
`services/` (compartilhada entre os dois routers) ou se `orcamentos.py`
ganha sua própria versão.

**Fix:** `_carregar_dados_periodo` migrou pra `services/orcamento_saldo.py`
como `carregar_dados_periodo` (função pública, sem `_`) — compartilhada
por `estrutura_custo.py` (que passou a importá-la de lá, sem duplicar) e
`orcamentos.py`. `_enriquecer_item()`/`_validar_teto_bucket()` passaram a
receber um `contexto_saldo` (tupla `orcamento_por_mes`/
`itens_por_orcamento_id`/`transacoes_por_mes`/`cache`) carregado 1 vez por
requisição (`_carregar_contexto_saldo`) e reaproveitado entre a validação
de teto e o enriquecimento do item, e entre todos os itens de
`listar_itens` — a lista inteira agora recalcula a cadeia de
`saldo_anterior` de todo item em memória, sem voltar ao banco por item.
`_validar_teto_bucket` também parou de fazer sua própria consulta de
itens do bucket — já vêm prontos (filtrados por `ativo=True`) do mesmo
lote. `saldo_anterior_ao_vivo`/`_item_equivalente_no_mes` (a versão que
consultava o banco a cada passo da cadeia) foram removidas de
`services/orcamento_saldo.py` — ficaram sem nenhum chamador depois da
troca, único lugar do código que ainda tinha essa classe de bug.

**Status:** implementado 2026-09-25 (Rodada 29). Teste de regressão
(`test_listar_itens_busca_dados_em_lote_nao_recalcula_cadeia_item_a_item`)
conta as chamadas reais a `db.table(...)` num cenário de 2 itens × 5
meses de cadeia encadeada de verdade, pedindo os itens do último mês —
confirmado manualmente que falha contra o código antigo (13 chamadas a
`orcamentos`, não 2 — revertido o fix isoladamente via `git stash` pra
provar). `GET /orcamentos/{id}/itens` fica em 5 chamadas fixas por
requisição (não 3 como Estrutura de Custo — a tela também precisa da
lista completa de itens, incluindo inativos, separada do lote
ativos-only usado pra recalcular a cadeia; ver docstring do teste), mas
não cresce mais com o histórico nem com o número de itens. Suíte
offline: **299 passed** (298 + 1), 33 skipped.

### Botões inferiores (barra de navegação mobile) pequenos e colados

**Contexto:** reportado pelo usuário testando a barra inferior mobile — os
6 itens dividiam o mesmo `font-size: 10px` entre ícone e rótulo, com
`padding: 4px 2px` e sem `gap` entre eles, o que apertava o toque.

**Processo:** usuário pediu mockups pra escolher a abordagem (Artifact
Design). 1ª rodada comparou Opção A (ícone maior, mantém os 6 itens) e
Opção B (4 itens diretos + botão "Mais" abrindo um cartão pequeno com os
outros 2). Usuário pediu pra mesclar as duas: 4 itens diretos + botão de
menu à direita, no máximo 5 slots — viraram Opção C. 3 rodadas de
refinamento sobre a Opção C, a partir de feedback do usuário a cada
volta:
- ícone do botão trocado de hambúrguer (`☰`) pra pontos (`•••`, mesmo
  símbolo do `⋯`/"more" já convencional em iOS/Android);
- indicador de ativo no botão "Menu" quando a tela atual é uma das
  escondidas (não só quando o menu está aberto) — senão o usuário perderia
  a noção de onde está ao navegar pra Planejamento ou Configurações;
- pergunta do usuário sobre mover o FAB ("+") pra esquerda, respondida com
  recomendação contrária (FAB e barra ocupam zonas verticais diferentes,
  não colidem de fato; mover quebra a convenção forte de FAB no canto
  inferior direito por um ganho só estético) — em vez disso, o FAB
  desaparece (fade) enquanto o menu está aberto;
- o cartão pequeno ancorado (`210px`, 2 linhas soltas) virou uma **sheet**
  de largura total, agrupada por seção com rótulo (ex: "Planejamento"),
  pensada pra crescer bem conforme mais telas entrarem no menu no futuro
  — ver item 29, sugestão de promover o item mais usado dentro dela;
- última ressalva do usuário: a sheet cobria a barra de navegação ao
  abrir — ajustada pra nascer colada **acima** da barra (`bottom` do
  tamanho da barra, não `0`), assim os 4 ícones diretos continuam visíveis
  e clicáveis com o menu aberto, só o conteúdo acima escurece.

**O que entrou na implementação real** (`AppShell.tsx`/`AppShell.css`):
- Barra mobile reduzida a 4 itens diretos (Dashboard, Lançamentos,
  Estruturas de Custo, Gráficos) + divisor + botão "Menu" (`•••`/`✕`),
  ícone (22px) desacoplado do rótulo (11px), pílula de fundo
  (`color-mix` com `--cor-acento`, mesmo padrão já usado em
  `estruturaCusto.css`/`pareto.css`) no item ativo.
- Planejamento e Configurações saíram da barra e foram pro menu, cada um
  na sua seção ("Planejamento"/"Conta") — únicos 2 itens reais hoje;
  estrutura já pronta pra crescer sem redesenho quando mais telas
  entrarem (ex: item 10, Exportação de relatório).
- `menuMobileAberto` fecha sozinho a cada troca de rota (`useEffect` em
  `location.pathname`) — `AppShell` não desmonta ao navegar (só o
  `<Outlet/>` troca), então sem isso o menu ficaria aberto por cima da
  tela seguinte.
- Indicador de ativo do botão "Menu": `menuMobileAtivo` é `true` se o
  menu está aberto OU se a rota atual começa com `/planejamento` ou
  `/configuracoes`.
- FAB ganhou `transition: opacity` e a classe `.escondido`
  (`opacity: 0; pointer-events: none`) aplicada enquanto o menu está
  aberto.

**Status:** implementado 2026-09-25 — aprovado pelo usuário depois de 3
rodadas de mockup (Artifact Design, canvas
`https://claude.ai/artifact/Px2ZERDHXK3ZGy1uyc5v5S`). Verificado com
`tsc`/`vite build`, `oxlint`, e QA visual via Playwright (mobile light e
dark, indicador de ativo em `/configuracoes`, menu aberto/fechado,
desktop sem regressão na sidebar) — sem Supabase real nesta sessão, então
sem teste de navegação de ponta a ponta contra dados reais. Ver checklist
de teste manual no changelog.

### Tooltip: balão abre perto da borda/canto no mobile

**Contexto:** reportado 2026-09-24, testando a Rodada 22.1 (ícone de
info clicável do `InfoIcon`). O balão (`.info-icone-balao`) era
`position: absolute; top: calc(100% + 6px); left: 0;`, ancorado sem
noção nenhuma de onde estava na tela — perto da borda direita do
viewport ele estourava (o `body` já tinha `overflow-x: hidden` desde a
Rodada 23.2, então não alargava a página, mas o texto ficava cortado/
ilegível); perto do fundo, como só `overflow-x` é escondido (não
`overflow-y`), o balão empurrava a altura rolável do documento pra baixo
do necessário.

**Fix:** balão trocou de `position: absolute` (ancorado no ícone via
CSS) pra `position: fixed` com coordenadas calculadas em JS
(`getBoundingClientRect()` do botão) e clampadas dentro do viewport (8px
de margem): `left` nunca deixa o balão passar da borda direita nem da
esquerda; se não coubesse embaixo do ícone (estimativa de altura de
90px — suficiente pros textos reais, todos curtos), abre em cima dele
em vez de embaixo. Fecha também ao rolar a página (um balão `fixed`
"gruda" no lugar errado assim que qualquer container rolável se move) —
antes só fechava por clique fora ou Escape.

- `frontend/src/components/InfoIcon.tsx`: `useLayoutEffect` novo calcula
  `{top, left}` sempre que o balão abre; listener de `scroll` (capture)
  adicionado ao efeito que já fechava por clique fora/Escape.
- `frontend/src/components/infoIcon.css`: `.info-icone-balao` de
  `position: absolute` pra `position: fixed`, sem `top`/`left` fixos no
  CSS (vêm inline, calculados).

**Status:** implementado 2026-09-25 (Rodada 30). QA visual via
Playwright (harness de auth mockada) nos 8 `InfoIcon` do Dashboard, a
390px de largura: todos os balões ficam dentro do viewport (horizontal e
vertical) ao abrir, incluindo o mais próximo da borda direita (que
precisou do clamp de verdade pra não estourar); `document.
documentElement.scrollHeight` não muda antes/depois de abrir nenhum
deles — o sintoma original ("amplia a área que precisa ser rolada")
confirmado resolvido.

**Checklist de teste manual:**
- [ ] Num celular de verdade (não só emulação), abrir um InfoIcon perto
      da borda direita da tela (ex: KPI "Investimentos" no Dashboard) —
      o balão deve aparecer inteiro, sem cortar.
- [ ] Abrir um InfoIcon perto do fim da tela (rolar até o fim antes) —
      o balão deve abrir em cima do ícone em vez de embaixo, sem cortar
      nem exigir rolar mais.
- [ ] Rolar a página com um balão aberto — ele deve fechar (em vez de
      ficar desalinhado do ícone).

### Lançamentos: cards quebrando no layout mobile

**Contexto:** reportado 2026-09-24. Ao investigar, a causa não era
específica de Lançamentos — é o componente de lista compartilhado
(`.lista-crud`/`.item-linha`/`.item-info`/`.item-acoes`, `crud.css`),
usado também em Contas/Categorias/Caixinhas (Configurações),
Recorrentes e Compromissos Futuros (Dashboard). `.item-acoes` tinha
`flex-shrink: 0` — em uma parcela com "Editar", "Excluir" e "Excluir
compra inteira" (label longo, só aparece em compra parcelada), a soma
dos botões passava da largura da tela e vazava pra fora do card. O
`flex-wrap: wrap` que parecia a correção óbvia não bastava sozinho:
`flex-shrink: 0` impede o container de encolher, então mesmo numa linha
própria (`.item-linha` já quebrando linha) ele nunca ficava menor que o
próprio conteúdo — precisava de `min-width: 0` pra que o `flex-wrap`
interno dele (os botões entre si) tivesse chance de agir.

**Fix:** `crud.css` — `.item-linha` ganhou `flex-wrap: wrap`;
`.item-acoes` trocou `flex-shrink: 0` por `min-width: 0` (mantendo
`flex-wrap: wrap` nele também, mais `justify-content: flex-end` pra
manter os botões alinhados à direita quando cabem numa linha só).

**Status:** implementado 2026-09-25 (Rodada 30). QA visual via
Playwright (harness de auth mockada) em `/lancamentos` a 360px e 320px
de largura com uma transação parcelada de descrição longa (pior caso:
"Excluir compra inteira" + valor + "Editar" + "Excluir" não cabem numa
linha só) — `document.documentElement.scrollWidth` bate exatamente com
a largura do viewport nos dois tamanhos (sem overflow), varredura por
`getBoundingClientRect()` de todos os elementos da página não encontrou
nenhum passando da borda. `/configuracoes` (mesmo componente
compartilhado) testado a 320px também sem overflow.

**Checklist de teste manual:**
- [ ] Lançamentos, mobile, um item de compra parcelada com descrição
      longa: os botões ("Editar"/"Excluir"/"Excluir compra inteira")
      quebram linha dentro do card em vez de vazar pra fora dele.
- [ ] Configurações → Contas/Categorias/Caixinhas e Lançamentos →
      Recorrentes, mobile: nenhuma lista com esse mesmo layout deve ter
      regressão visual (o fix é no componente compartilhado).

### Menu "mais" da barra de navegação mobile: promover item mais usado

**Contexto:** surgiu na discussão de mockups do item 21 (barra de
navegação mobile). A Opção C (escolhida pelo usuário) reduz a barra a 4
itens diretos + um botão "•••" que abre uma sheet com o resto
(Planejamento, Exportar relatório, Configurações, e o que mais entrar
aqui). Sugeri destacar o item mais usado dentro da sheet num atalho no
topo, fora dos grupos — pensando que a lista de itens escondidos só vai
crescer conforme o app ganha features, então "mais usado" vira cada vez
mais valioso lá dentro. O usuário gostou e perguntou de volta: como
saber qual é o mais usado? Um contador?

**Resposta (Claude):** sim — um contador simples, incrementado a cada
navegação pra uma das rotas escondidas no menu, sem endpoint novo:

- **Onde guardar:** `localStorage`, por dispositivo — não precisa de
  tabela nova nem de chamada ao backend. Custo real: o contador não
  sincroniza entre dispositivos (usar o app no celular e no desktop conta
  como dois contadores separados). Se isso incomodar na prática, a
  extensão natural é uma coluna por usuário no backend (mais uma
  chamada, mas sincroniza) — não vale o custo agora, pra um usuário só
  com poucos dispositivos.
- **O que contar:** 1 incremento por navegação bem-sucedida pra uma rota
  que hoje vive dentro do menu (Planejamento, Configurações, e o que mais
  entrar). Não precisa de janela deslizante nem decaimento no MVP —
  "total de cliques desde sempre" já resolve o caso de uso (item usado
  muito mais que os outros sobe pro topo); revisitar se o padrão de uso
  mudar radicalmente algum dia (ex: parou de usar Planejamento, passou a
  usar muito Exportar relatório).
- **Como promover sem "piscar":** só destacar um item se ele tiver, por
  exemplo, o dobro de cliques do 2º colocado — evita promover/despromover
  a cada clique quando dois itens estão empatados, o que ficaria
  bagunçado visualmente.

**Status:** registrado 2026-09-24, sugestão minha confirmada como alta
prioridade pelo usuário. Depende do item 21 (barra de navegação mobile)
estar implementado primeiro, já que é uma melhoria de dentro do menu que
o item 21 cria.

---

Todas as propostas trazidas em 2026-09-15 (6 mockups de referência) foram
decididas nesta mesma rodada — nenhuma pendência de aprovação restante. Ver
o changelog em `changelog-proposta-original-do-redesign.md` pro raciocínio completo por
trás de cada recomendação.
