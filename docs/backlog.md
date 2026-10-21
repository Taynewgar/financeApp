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

Reorganizado por área em 2026-10-01 (a pedido do usuário, a partir da
reorganização por prioridade de 2026-09-24): agora a área é o agrupamento
de fora e, dentro de cada área, os itens pendentes aparecem por
prioridade (Alta/Média/Baixa). A numeração em si não muda — cada item
mantém o número que já tinha em qualquer lugar que o referencie. Os 20
itens novos trazidos em CSV em 2026-09-30 foram incorporados aqui,
numerados 41-60 na sequência. Itens concluídos saíram da divisão por
área/prioridade — ver "Concluído" abaixo, em ordem numérica simples (o
changelog já documenta quando e como cada um foi entregue).

> **Nota de status (2026-10-12):** essa regra (item concluído sai da
> divisão por área e vai pra "Concluído") vale pra TODO item marcado
> ✅ por completo — não só pros que existiam em 2026-10-01. Entre essa
> data e agora acumulou um desvio (itens concluídos ficando inline
> com ✅ em vez de ir pra lá), corrigido nesta rodada. Exceção: um item
> com ✅ só numa PARTE dele (ex: itens 59/60, onde só a ordenação
> alfabética está feita, a manual/drag-and-drop não) continua inline —
> só muda pra "Concluído" quando TODAS as partes estiverem prontas.
> "Ordem numérica simples" na prática é ordem de conclusão (cada item
> novo entra no fim da lista, não ordenado por número).

> **Nota de formatação (2026-09-25):** os itens abaixo usam `- **N.**`
> (marcador de lista solto + número em negrito), não `N.` como item de
> lista numerada nativa do Markdown. Motivo: como a numeração aqui não é
> sequencial dentro de cada bloco, uma lista numerada nativa é renumerada
> automaticamente pelo renderizador (GitHub etc.) a partir do primeiro
> item. `- **N.**` exibe sempre o número literal do texto-fonte, imune a
> isso.

### Pendente, por área

#### Dashboard

**Alta**

- **83.** **Somatório dos lançamentos que faltam ser retirados das
  caixinhas** `tipo: Implementação` — valor total das retiradas
  pendentes de caixinha, junto do card "Retiradas Pendentes de
  Caixinha" (hoje só lista os itens, sem um total agregado).
  *(trazido em CSV, 2026-10-21)*

**Baixa**

- **25.** **Saldo atual de contas** `tipo: Implementação` — hoje só
  caixinhas têm saldo calculado (`GET /dashboard/patrimonio/{mes}`); dar
  saldo a `contas` também seria a extensão natural, mas não é urgente.
  *(2026-09-15)*
- **73.** **Título do card "Retiradas pendentes de caixinha" em
  minúsculas** `tipo: Melhoria` — os outros títulos de card do Dashboard
  usam Title Case ("Compromissos Futuros", "Patrimônio em Caixinhas");
  esse ficou em sentence case. Corrigir pra "Retiradas Pendentes de
  Caixinha". Achado testando a Rodada 86/87 — a pedido do usuário, não
  implementar isolado, agrupar com os próximos itens do backlog.
  *(2026-10-12)*

#### Lançamentos

**Alta**

- **74.** **Excluir categoria/subcategoria sem transação associada**
  `tipo: Implementação` (detalhe abaixo) — hoje só existe desativar
  (`PATCH .../ativo`), nenhum DELETE real. *(2026-10-14)*
- **69.** **Excluir transações em massa** `tipo: Implementação`
  (detalhe abaixo) — **repriorizado de Baixa pra Alta a pedido do
  usuário 2026-10-14**; escopo reduzido ao de exclusão só (o pedido foi
  especificamente "excluir em massa" — criar/editar em lote, do escopo
  original do item, segue registrado separado como item 76, Baixa, sem
  caso de uso concreto que justifique agora). *(originalmente
  2026-10-11, desmembrado do item 44)*
- **77.** **Chips de "mais usadas" (categoria/subcategoria/descrição)
  em todos os formulários de criação/edição, não só Novo Lançamento**
  `tipo: Melhoria` (detalhe abaixo) — hoje só existe em Novo Lançamento;
  faltam em Editar Lançamento e no formulário de Lançamento Recorrente.
  *(2026-10-21)*
- **82.** **Campo de valor com formatação de moeda** `tipo: Melhoria` —
  input de Valor hoje é texto livre, sem máscara/formatação (R$,
  separador de milhar/decimal) enquanto digita. *(trazido em CSV,
  2026-10-21)*
- **84.** **Seletor de subcategoria liberado sem categoria preenchida**
  `tipo: Melhoria` — hoje a subcategoria só fica disponível depois de
  escolher a categoria; permitir escolher a subcategoria primeiro e
  preencher a categoria automaticamente a partir dela. *(trazido em
  CSV, 2026-10-21)*
- **86.** **Melhorar carregamento dos chips** `tipo: Melhoria` —
  performance/percepção de carregamento dos chips de "mais usadas"
  (categoria/subcategoria/descrição) em Novo Lançamento. *(trazido em
  CSV, 2026-10-21)*
- **87.** **Categorias desativadas aparecem no dropdown de escolha de
  categoria** `tipo: Bug` — select de categoria deveria listar só
  `ativo: true`, igual já é feito em outras listas do app. *(trazido em
  CSV, 2026-10-21)*
- **88.** **Aviso de retirada pendente de caixinha não aparece pra
  transações parceladas** `tipo: Bug` — o aviso/fluxo de "falta
  retirar da caixinha" (item 58) parece cobrir só transação à vista;
  conferir o caminho de compra parcelada. *(trazido em CSV, 2026-10-21)*
- **89.** **"Últimos lançamentos por conta" não atualiza ao CRIAR uma
  transação nova** `tipo: Bug` — relacionado ao item 66 (reatividade
  entre telas, Rodada 89): aquela rodada corrigiu o caso de EXCLUIR um
  lançamento (`excluir()`/`excluirCompraParcelada()` passaram a
  re-buscar `ultimosPorConta()`); o caminho de CRIAR (Novo Lançamento)
  não foi coberto — precisa confirmar se é o mesmo tipo de causa
  (re-fetch faltando) ou outra coisa. *(trazido em CSV, 2026-10-21)*

**Média**

- **85.** **Flag/marcador pra identificar transações que são "contas"**
  `tipo: Implementação` — prepara terreno pra feature futura Agenda de
  Contas (item 41, ainda stub). *(trazido em CSV, 2026-10-21)*

**Baixa**

- **33.** **Lançamento com mais de 1 categoria** `tipo: Implementação`
  (detalhe abaixo) — surgiu durante a análise do item 9 (migração de
  dados). Rebaixado de Média pra Baixa a pedido do usuário.
  *(2026-10-12)*
- **76.** **Criar/editar transações em lote** `tipo: Melhoria` — parte
  de criação/edição do antigo escopo do item 69 (ver item 69 acima,
  agora só exclusão) — inserir uma transação já está ágil (item 44),
  sem caso de uso concreto que justifique o custo de uma UI de lote
  pra criar/editar várias de uma vez. *(2026-10-14, desmembrado do
  item 69)*

#### Planejamento

**Baixa**

- **59.** **Ordenação das subcategorias dentro dos envelopes**
  `tipo: Melhoria` — em Planejamento. **Parte alfabética ✅ implementada
  2026-10-12** — as folhas de cada grupo agora ordenam por nome
  (`.sort()` no frontend, zero schema); antes a ordem nem era garantida
  (vinha da ordem física da tabela). **Ordenação manual/customizável
  (drag-and-drop) segue como opção registrada, não implementada** — é
  caro (coluna nova + endpoint de reordenar + biblioteca de D&D,
  nenhuma existe no projeto hoje) pro uso real que o usuário imagina
  (**ordenar por importância**, não por nome). Mantém baixa prioridade
  — vai usar o app no dia a dia com a alfabética e decidir depois se o
  manual compensa o custo. *(trazido em CSV, 2026-09-30; alfabética
  implementada 2026-10-12)*

#### Estrutura de Custo

**Alta**

- **10.** **Exportação de relatório mensal/anual** `tipo: Implementação`
  (detalhe abaixo) — **✅ implementado 2026-10-12**, aguardando teste do
  usuário.

**Baixa**

- **60.** **Ordenação das subcategorias dentro dos envelopes**
  `tipo: Melhoria` — mesmo pedido do item 59, aplicado também à tela de
  Estrutura de Custo (lá a ordem era ainda pior: vinha de um `set()` do
  Python, literalmente arbitrária). **Parte alfabética ✅ implementada
  2026-10-12**, mesma mudança do item 59. **Ordenação manual/
  customizável segue como opção registrada, não implementada** — mesma
  decisão do item 59, baixa prioridade, revisitar depois do uso real.
  *(trazido em CSV, 2026-09-30; alfabética implementada 2026-10-12)*

#### Gráficos

**Alta**

- **79.** **Gráfico/análise de saúde financeira prevendo sazonalidade**
  `tipo: Criação` — relacionar e evidenciar graficamente a saúde
  financeira baseada na estrutura de custo, com destaque pra custos
  sazonais PREVISTOS (não só o realizado histórico) — forma de
  visualização ainda a definir. *(trazido em CSV, 2026-10-21)*
- **80.** **Gráfico de estrutura de custos no tempo** `tipo: Criação`
  — **possível sobreposição com o item 51** (✅ implementado Rodada 91):
  o Comparador de Séries e o Ano a Ano já aceitam "estrutura de custo"
  (fixo/variável/sazonal/investimentos) como série selecionável ao
  longo do tempo. Vale conferir se os gráficos novos (`/graficos`)
  cobrem o que foi pedido aqui antes de tratar como trabalho
  adicional. *(trazido em CSV, 2026-10-21)*

**Média**

- **51.** **Gráfico de despesa por categoria/subcategoria no tempo**
  `tipo: Implementação` (detalhe abaixo) — **✅ implementado 2026-10-12**,
  aguardando teste do usuário. *(trazido em CSV, 2026-09-30)*

#### Configurações

**Baixa**

- **28.** **Aba Bancos em Configurações** `tipo: Implementação` — hoje
  resolvido como campo de texto em Conta, sem perda funcional real.
  *(2026-09-15, renumerado de 24 pra 28 em 2026-09-24 — colidia com o
  item 24 de média prioridade)*

#### Geral

**Alta**

- **32.** **Melhoria geral de layout da aplicação (V2, pós-MVP)**
  `tipo: Implantação` — reportado pelo usuário testando a Rodada 28-31: alguns elementos
  fora de escala, cabeçalho fixo um pouco desproporcional em algumas
  telas. Pedido explícito do usuário: não é pra corrigir ponto a ponto
  agora — é uma passada de revisão geral de layout depois do MVP
  fechado, numa V2. Sem escopo detalhado ainda (quais telas, quais
  elementos específicos) — a definir quando for priorizado.
- **81.** **2 guias de usuário (completo + rápido)** `tipo: Criação` —
  um guia completo com todos os detalhes de todas as funcionalidades
  do app, e um guia rápido resumido. *(trazido em CSV, 2026-10-21)*

**Média**

- **66.** **Avaliar atualização reativa entre telas após inserção de
  dados** (detalhe abaixo) `tipo: Melhoria` — **✅ implementado
  2026-10-12** (os 3 casos confirmados na investigação), aguardando
  teste do usuário. *(2026-10-02; investigação completa 2026-10-12)*

**Baixa**

- **26.** **Changelog estruturado** `tipo: Melhoria` — trocar a prosa narrativa de
  `changelog-proposta-original-do-redesign.md` pelo formato [Keep a
  Changelog](https://keepachangelog.com) (seções `Added/Changed/Fixed/
  Removed` por versão datada, amarrada a tag git). Ganho: escaneável e
  diffável, pronto pra virar release notes se o app for a público.
  Custo: perde o espaço pro "porquê" narrativo que o formato atual dá
  — por isso fica de baixa prioridade enquanto o projeto for de um
  usuário só. Sugestão minha (Claude), confirmada como baixa prioridade
  pelo usuário. *(2026-09-16)*
- **27.** **ADRs (Architecture Decision Records)** `tipo: Melhoria` — trocar o Q&A único
  de `sugestoes-e-decisoes-do-redesign.md` por um arquivo curto e
  imutável por decisão relevante (formato Nygard: contexto/decisão/
  consequências). Decisão revista vira um ADR novo que supersede o
  antigo, em vez de editar o `> Status:` por cima como hoje — histórico
  fica honesto, mas com mais arquivos pra navegar. Mesma origem e
  confirmação do item 26. *(2026-09-16)*
- **34.** **Fluxo de criação de usuário (cadastro)** `tipo: Implantação`
  (detalhe abaixo) — hoje só existe login; criar usuário é feito
  manualmente pelo painel do Supabase, sem tela/endpoint no app.
  *(2026-09-25)*

#### Agenda Contas

**Alta**

- **41.** **Agenda Contas** (nova feature) `tipo: Nova Feature` ·
  `maturidade: stub — a detalhar` — registrar entrada como item futuro
  que receberá subitens. *(trazido em CSV, 2026-09-30)*

#### Cartão

**Alta**

- **42.** **Cartão** (nova feature) `tipo: Nova Feature` ·
  `maturidade: stub — a detalhar` — registrar entrada como item futuro
  que receberá subitens. *(trazido em CSV, 2026-09-30)*

#### Investimentos

**Média**

- **52.** **Investimentos** (nova feature) `tipo: Nova Feature` ·
  `maturidade: stub — a detalhar` — registrar entrada como item futuro
  que receberá subitens. *(trazido em CSV, 2026-09-30)*

#### Imóveis

**Baixa**

- **57.** **Imóveis** (nova feature) `tipo: Nova Feature` ·
  `maturidade: stub — a detalhar` — registrar entrada como item futuro
  que receberá subitens. *(trazido em CSV, 2026-09-30)*

#### Calculadoras

**Alta**

- **78.** **Calculadora de compra à vista ou parcelada** (nova
  feature) `tipo: Nova Feature` — comparar o custo de pagar uma compra
  à vista vs. parcelada. *(trazido em CSV, 2026-10-21)*

### Concluído

Ordem numérica simples, riscado — sem reclassificação por área ou
prioridade; o changelog (`changelog-proposta-original-do-redesign.md`)
já documenta quando e como cada um foi entregue.

- **1.** ~~Delta vs mês anterior nos KPIs do Dashboard~~ **feito
  2026-09-13**
- **2.** ~~Tela de Planejamento~~ **feito 2026-09-14** — só configuração
- **3.** ~~Tela de Estrutura de Custo~~ **feito 2026-09-15** — tabela
  hierárquica com expand/collapse (bucket > categoria > subcategoria),
  fita de KPIs, vereditos de pool de despesas/piso de investimentos e
  drill-down pra Busca de Lançamentos. Backend não mudou (motor já
  existia).
- **4.** ~~Categorias "mais usadas" + criação inline no Novo
  Lançamento~~ **feito 2026-09-15** — chips de atalho (ranking por uso
  nos últimos 6 meses) + formulário inline de criação, sem sair da
  tela.
- **5.** ~~Feature "Gráficos" nova~~ **feita 2026-09-16**, em 3 rodadas
  (A: tela + migração + sparkline, com 2 ajustes extras 16.1/16.2; B:
  Pareto de despesas por categoria/subcategoria; C: tendência de
  Orçado×Realizado em vários meses, linka pra Estrutura de Custo), mais
  uma Rodada D de refinamento em 2026-09-22 (Base da média sempre
  visível e com efeito garantido em todo modo, reordenação por tema,
  curva de % acumulado no Pareto) — ver changelog pra detalhe completo
  de cada rodada.
- **6.** ~~Dashboard — 3 KPIs novos~~ **feito 2026-09-16** (ordem
  invertida com o item 5 a pedido do usuário, entregue antes por não
  ter dependência real de Gráficos) — "Meses com resultado negativo",
  "Resultado acumulado" (R$, ao lado da taxa em % que já existia) e
  "Maior categoria de despesa" (mesmo recorte do gráfico "Despesas por
  Categoria", sem endpoint novo — os 3 vêm de dados já buscados na
  tela).
- **7.** ~~Despesa fixa recorrente — aluguel, assinaturas~~ **feito
  2026-09-22** — projeção virtual (decisão discutida e aprovada nesta
  rodada, ver detalhe abaixo): `lancamentos_recorrentes` (tela em
  Configurações), `POST /lancamentos-recorrentes/{id}/confirmar`
  materializa a transação real só quando o mês é confirmado, `GET
  /dashboard/compromissos-futuros` mistura parcelas + ocorrências
  pendentes.
- **8.** ~~Edição de compra parcelada~~ **feito 2026-09-24** — níveis 1
  (metadado) + 3 (exclusão em grupo); nível 2 (recriar o grupo) fica
  pra decisão futura (detalhe abaixo).
- **9.** ~~Migração de dados do app antigo~~ **feito e executado
  2026-09-25** — script (`backend/scripts/migrar_dados_antigos.py`) +
  47 testes offline; rodado contra os dados reais pelo usuário (1.862
  lançamentos migrados). Reconciliação pós-migração apontou divergência
  em 9 meses por colisão de `hash_dedup` em transações reais idênticas
  — corrigido no mesmo dia. Detalhe na subseção própria abaixo, ver
  changelog Rodadas 33 e 34.
- **11.** ~~Compromissos futuros no Dashboard~~ **feito por completo
  2026-09-22** — parcelas futuras (2026-09-13) + despesa fixa
  recorrente (item 7, 2026-09-22).
- **12.** ~~Indicador visual de tooltip~~ **feito 2026-09-24** —
  componente `InfoIcon` único pro app inteiro (Dashboard, Lançamentos,
  Base da média), clicável (não depende de hover — não existe em
  touchscreen, corrigido na Rodada 22.1). Ver changelog Rodadas
  22/22.1.
- **13.** ~~Persistir estado de filtros ao navegar entre features~~
  **feito 2026-09-24** — Detalhe na subseção própria abaixo, ver
  changelog Rodada 24.
- **14.** ~~Filtro específico pra recorrentes~~ **feito 2026-09-24** —
  Detalhe na subseção própria abaixo, ver changelog Rodada 25.
- **15.** ~~Lista de "meses pulados" muito grande~~ **feito
  2026-09-24** — acordeão por ano, escolhido pelo usuário entre 2
  mockups. Detalhe na subseção própria abaixo, ver changelog Rodada 26.
- **16.** ~~Cabeçalho fixo/controles fixos por feature~~ **feito
  2026-09-24** — decidido via mockups (Lançamentos, Gráficos, Estrutura
  de Custo, Planejamento, Dashboard). Ver changelog Rodada 23.
- **17.** ~~Barra lateral não deve sumir ao rolar~~ **feito
  2026-09-24** — Ver changelog Rodada 23.
- **19.** ~~Tooltip: balão abre perto da borda/canto no mobile
  aumentando a área que precisa ser rolada~~ **feito 2026-09-25** —
  `InfoIcon` passou a `position:fixed` com coordenadas calculadas via
  `getBoundingClientRect`, clampadas dentro do viewport. Detalhe na
  subseção própria abaixo, ver changelog Rodada 30.
- **20.** ~~Lançamentos: cards quebrando no layout mobile~~ **feito
  2026-09-25** — causa era compartilhada com Contas/Categorias/
  Caixinhas/Recorrentes (mesmo componente de lista, `crud.css`), não só
  Lançamentos. Detalhe na subseção própria abaixo, ver changelog Rodada
  30.
- **21.** ~~Botões inferiores (barra de navegação mobile) pequenos e
  colados~~ **feito 2026-09-25** — decidido via 3 rodadas de mockups
  (Opção A/B/C, Opção C mesclada escolhida e refinada pelo usuário).
  Ajuste de acabamento (FAB colado na barra) feito na Rodada 31. Detalhe
  na subseção própria abaixo, ver changelog Rodadas 28 e 31.
- **22.** ~~Estrutura de Custo carregando devagar~~ **feito
  2026-09-24** — causa raiz era a mesma classe de bug já corrigida em
  Gráficos (Rodada 19.2/19.3), só que ainda não tinha sido aplicada em
  `obter()` (a tela de 1 mês). Detalhe na subseção própria abaixo, ver
  changelog Rodada 27.
- **23.** ~~Lançamentos recorrentes: aplicação/retirada com caixinha
  (reserva)~~ **feito 2026-09-30** — reportado como bug ao testar
  (recorrente de aplicação/retirada em caixinha não salvava, exigindo
  categoria). Detalhe na subseção própria abaixo, ver changelog Rodada
  40.
- **24.** ~~Planejamento com o mesmo padrão de lentidão de Estrutura de
  Custo~~ **feito 2026-09-25** — mesmo fix portado pra
  `routers/orcamentos.py`. Detalhe na subseção própria abaixo, ver
  changelog Rodada 29.
- **29.** ~~Menu "mais" da barra de navegação mobile: promover item
  mais usado por contador de uso~~ **feito 2026-09-25** — contador em
  `localStorage`, sem endpoint novo. Detalhe na subseção própria abaixo,
  ver changelog Rodada 32.
- **30.** ~~Estrutura de Custo: tabela de itens quebrando no mobile~~
  **feito 2026-09-25** — reportado com prints do app real; causa igual
  à do item 20 (colunas de largura fixa que não cabem em tela estreita),
  só que numa tela ainda não coberta por aquele fix. Detalhe na
  subseção própria abaixo, ver changelog Rodada 31.
- **36.** ~~Caixinhas com saldo errado / "outras também não estão
  batendo"~~ **feito 2026-09-25** — causa raiz era o limite padrão de
  1000 linhas do Supabase/PostgREST, silencioso (sem erro), acertando em
  cheio todo query sem paginação sobre `transacoes` — a conta real já
  passa de 1862 linhas. Detalhe na subseção própria abaixo, ver
  changelog Rodada 35.
- **37.** ~~Compromissos Futuros: mostrar todas as parcelas, não só 5~~
  **feito 2026-09-25** — "ver mais" + card mais compacto, decisão do
  usuário. Detalhe na subseção própria abaixo, ver changelog Rodada 36.
- **38.** ~~Agregações que crescem pra sempre com o histórico (caixinhas,
  "Todos os meses", cadeia de orçamento) movidas pra RPC no Postgres~~
  **feito 2026-09-25** — decisão de arquitetura de longo prazo, a pedido
  do usuário (volume projetado de ~15-20k transações em 6-7 anos).
  Detalhe na subseção própria abaixo, ver changelog Rodada 37.
- **39.** ~~Planejamento: "Gerar orçamento" travando + form de edição
  abrindo fora de vista~~ **feito 2026-09-29, fix de lentidão completo
  2026-09-30** — 2 bugs reportados dogfooding a aplicação; a correção
  de lentidão da Rodada 38 era só parcial (havia mais 2 N+1 no mesmo
  endpoint). Detalhe na subseção própria abaixo, ver changelog Rodadas
  38 e 41.
- **40.** ~~Planejamento: layout não alinhado com Estrutura de Custo~~
  **feito 2026-09-30** — 3 mockups apresentados, usuário escolheu
  acordeão de 2 níveis (bucket → categoria pai → subcategoria), igual
  Estrutura de Custo. Detalhe na subseção própria abaixo, ver changelog
  Rodada 39.
- **65.** ~~Subitem do bucket Reservas mostra nome da conta em vez da
  caixinha~~ **feito 2026-10-02** — 1ª versão (Rodada 42) invertia a
  hierarquia (caixinha virava o nível pai, conta desaparecia); corrigido
  na mesma rodada (Rodada 42, correção) pra conta permanecer 1º nível e
  caixinha ser o 2º. Detalhe na subseção própria abaixo, ver changelog
  Rodada 42.
- **67.** ~~Bucket Reservas mostrando Orçado/Diferença/Status sem
  sentido (reserva não tem orçamento configurável)~~ **feito 2026-10-02**
  — virou puramente informativo: Saldo acumulado da caixinha + Aportado
  no mês, no lugar de Orçado/Diferença/Status. Mockup aprovado antes da
  implementação. Detalhe na subseção própria abaixo, ver changelog
  Rodada 43.
- **35.** ~~`hash_dedup` não distingue 2 despesas reais idênticas no
  mesmo dia~~ **feito 2026-10-02** — `POST /transacoes` e
  `PATCH /transacoes/{id}` ganharam `forcar_duplicado`; o frontend
  oferece "Lançar mesmo assim" no 409, em Novo Lançamento e em Editar.
  Detalhe na subseção própria abaixo, ver changelog Rodada 44.
- **18.** ~~Janela de meses pra trás × ano civil (jan-dez) nos
  gráficos~~ **feito 2026-10-02** — decisão: manter trailing 12 meses
  como padrão (sempre 12 pontos preenchidos) e adicionar toggle opt-in
  "Ano civil" pra quem quiser essa leitura sem trocar pro modo
  Intervalo. Detalhe na subseção própria abaixo, ver changelog Rodada
  45.
- **68.** ~~Compra parcelada não tem proteção real contra
  double-submit~~ **feito 2026-10-02** — checagem em nível de
  aplicação antes de criar o grupo (`_existe_compra_parcelada_igual`),
  com `forcar_duplicado` pro caso de 2 compras reais e diferentes
  coincidirem. Detalhe na subseção própria abaixo, ver changelog Rodada
  46.
- **56.** ~~Botão de apagar orçamento~~ **feito 2026-10-10** — ver
  detalhe na subseção própria abaixo. *(trazido em CSV, 2026-09-30)*
- **62.** ~~Decisão: criação manual de item em Planejamento ainda é
  necessária?~~ **decidido e removida 2026-10-10** — ver detalhe na
  subseção própria abaixo. *(2026-10-01)*
- **43.** ~~Consulta rápida durante a inserção~~ **feito 2026-10-11** —
  ver detalhe na subseção própria abaixo. *(trazido em CSV, 2026-09-30)*
- **44.** ~~Agilidade na inserção de transações~~ **feito 2026-10-11** —
  ver detalhe na subseção própria abaixo; CRUD em lote desmembrado e
  rebaixado pra baixa prioridade (item 69, não implementado). *(trazido
  em CSV, 2026-09-30)*
- **45.** ~~Busca por descrição parcial~~ **feito 2026-10-11** — ver
  changelog Rodada 58. *(trazido em CSV, 2026-09-30)*
- **46.** ~~Botões fixos + expandir tudo no Planejamento~~ **feito
  2026-10-11** — ver changelog Rodada 58. *(trazido em CSV, 2026-09-30)*
- **47.** ~~Renomear bucket→envelope, sobra→saldo do envelope~~ **feito
  2026-10-11** — troca só de rótulo visível (campo/schema/API continuam
  `bucket`, por decisão explícita do usuário). Ver changelog Rodada 58.
  *(trazido em CSV, 2026-09-30)*
- **53.** ~~Filtro por tipo de transação: parcelado ou à vista~~ **feito
  2026-10-11** — ver changelog Rodada 60. *(trazido em CSV, 2026-09-30)*
- **54.** ~~Últimas transações lançadas por conta~~ **feito 2026-10-11**
  — ver changelog Rodada 61, mockups de decisão na Rodada 60. *(trazido
  em CSV, 2026-09-30)*
- **55.** ~~Esquema de cores das transações~~ **feito 2026-10-11** — ver
  changelog Rodada 61, mockups de decisão na Rodada 60. *(trazido em
  CSV, 2026-09-30)*
- **63.** ~~Racional de testes com `/financeapp-ref`~~ **rodado
  2026-10-10/11** — contra a conta real
  (`referencia_saldo_anterior.py` + `/financeapp-ref`), achou 2 bugs: um
  no próprio script (cache sem a chave `bucket`) e um real no app —
  `realizado` de item de Planejamento vazando entre buckets quando a
  mesma categoria está em 2 buckets diferentes no mesmo mês (corrigido
  2026-10-11). Validou a cadeia de `saldo_anterior` inteira (625 itens,
  0 divergências pós-fix). 1 dos 6 pontos do roteiro (Caixinhas/
  Patrimônio batendo com "Guardado") segue sem reconfirmação formal
  pós-RPC — baixo risco, mesma fórmula já confirmada por cálculo direto
  do CSV na Rodada 35. *(2026-10-01)*
- **61.** ~~Reduzir tamanho dos cards de caixinha no Dashboard~~ **feito
  2026-10-12** — viraram grid (2+ por linha, conforme largura) em vez
  de 1 linha cheia por caixinha, mesmo padrão visual dos cards de
  resumo do topo. Mockup com 2 opções, usuário escolheu grid. Ver
  changelog Rodada 76. *(2026-10-01)*
- **64.** ~~Compromissos Futuros: card ainda mais compacto em telas
  maiores~~ **feito 2026-10-12** — título+detalhe numa linha só (eram
  2) + padding/fonte dos botões reduzidos; "Confirmar"/"Pular"
  continuam EMPILHADOS (fix deliberado de clique errado, item 21, não
  reaberto). Ver changelog Rodada 76. *(2026-10-02)*
- **71.** ~~Novo Lançamento: reordenar campos pra tirar proveito dos
  chips de descrição~~ **feito 2026-10-12** — Categoria/Subcategoria
  passaram a vir ANTES de Descrição (já que os chips de descrição
  sugerida dependem da categoria escolhida — item 43 —, escolher
  categoria primeiro faz os chips já aparecerem quando chega em
  Descrição). Nova ordem: Valor/Data → Categoria/Subcategoria (ou
  Caixinha, se Reserva) → Conta → Descrição → Estrutura de custo/Meio
  de pagamento → botões. Ver changelog Rodada 80.
- **31.** ~~Lançamentos: painel de filtros muito alto no mobile em
  paisagem~~ **feito 2026-10-12** — 4 causas encontradas em rodadas
  sucessivas de reteste: (1) gatilho do toggle mobile só por largura
  (`max-width: 720px`) — paisagem costuma passar disso; (2) o mesmo
  critério faltava no `AppShell.css` (sidebar vs. barra inferior), app
  ficava num híbrido desktop+mobile; (3) o FAB não tinha `z-index`,
  então o card de filtros/legenda (que tem) desenhava por cima dele;
  (4) o menu mobile ("•••") tinha `z-index` menor que o card, mesmo bug
  invertido. Ver changelog Rodadas 69-74. *(reportado 2026-09-25)*
- **58.** ~~Marcador de origem caixinha~~ **feito 2026-10-12** — virou
  lembrete ativo de "falta retirar da caixinha" (motivo real do pedido,
  esclarecido com o usuário: evitar esquecer o saque de uma despesa já
  coberta por uma reserva), não só um marcador passivo. Campo opcional
  `caixinha_origem_id` no Novo Lançamento/Editar (despesa), card
  "Retiradas pendentes de caixinha" no Dashboard com "Lançar
  retirada"/"Já retirei", badge na lista de Lançamentos. Mockup
  aprovado antes de implementar; testado e confirmado 2026-10-12. 2
  melhorias de usabilidade levantadas no teste, ambas feitas: excluir a
  transação de retirada volta a marcar a despesa como pendente (Rodada
  86); indicador + ação de "marcar como pendente de novo" em Editar
  Lançamento (Rodada 87, mockup aprovado antes). Ver changelog Rodada
  77. *(trazido em CSV, 2026-09-30)*
- **48.** ~~Mover subcategoria entre categorias~~ **feito 2026-10-12**
  — só entre categorias despesa. Ver changelog Rodada 70. *(trazido em
  CSV, 2026-09-30)*
- **49.** ~~Título da aba do navegador = nome da feature ativa~~ **feito
  2026-10-12** — ver changelog Rodada 70. *(trazido em CSV, 2026-09-30)*
- **50.** ~~Fuso horário dinâmico, não fixo~~ **feito 2026-10-12** —
  achado bug real (`toISOString()` convertia pra UTC, deslocando
  "hoje"/"mês atual" à noite num fuso negativo) — corrigido com data
  local do dispositivo em vez de fixar um fuso no código, a pedido do
  usuário (pode mudar de cidade). Ver changelog Rodada 70. *(trazido em
  CSV, 2026-09-30)*
- **70.** ~~Botão pra recolher a barra lateral em telas grandes~~
  **feito 2026-10-12** — vira um trilho de ícones (60px), preferência
  salva por dispositivo (localStorage, mesmo padrão do contador de uso
  do menu mobile). Ver changelog Rodada 75.
- **72.** ~~Identificar qual versão/commit está carregado no
  navegador/mobile~~ **feito 2026-10-12** — hash curto do commit (+
  data/hora do build no tooltip), pra conferir depois de um deploy que
  a versão nova realmente propagou. 1ª versão (Rodada 83) só aparecia
  na sidebar desktop; corrigido repetindo o rótulo na barra superior
  mobile pra cobrir telas ≤720px/mobile (Rodada 84). Ver changelog.

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

**O que o plano original previa** (`docs/plano-de-evolucao-original.md`):
rodar sobre histórico consolidado/deduplicado (não CSV bruto de banco),
normalizar texto (`_normalize_text` do app antigo) pra agrupar variações,
manter uma coluna de auditoria `categoria_raw`, reaproveitar `hash_dedup`
pra idempotência, dry-run antes de gravar, reconciliação pós-migração
(soma de receita/despesa por mês tem que bater).

**Desenho técnico (2026-09-25, revisa o plano acima com base na análise
real dos arquivos do usuário — ver changelog/histórico da conversa pro
diagnóstico completo):** a análise linha a linha dos CSVs reais (1.862
lançamentos válidos, dez/2025–mai/2027, mais `Categorias.csv` e
`Caixinhas.csv`) mostrou que a hierarquia categoria→subcategoria e as
caixinhas já batem 100% sem nenhum typo — **normalização de texto e
`categoria_raw` não são necessários**, o dado de origem já está limpo. O
que sobrou pra resolver foi outra coisa: como preencher os ~4% de
lançamentos sem estrutura de custo e como reconstruir o vínculo de
compra parcelada que o app antigo nunca guardou.

**Fontes de dados:** `Lançamentos_Calculado.csv` (principal),
`Categorias.csv`, `Caixinhas.csv`. Nunca são commitados no repo (dados
financeiros pessoais) — o script recebe os 3 caminhos por argumento de
linha de comando; os arquivos ficam fora do controle de versão.

**Onde mora o script:** `backend/scripts/migrar_dados_antigos.py` (novo
diretório `backend/scripts/`, paralelo a `backend/tests/`). Segue o
mesmo padrão já usado por `tests/seed_dados_teste.py`: `TestClient(app)`
+ `sign_in()` via `POST /auth/v1/token` do Supabase + header `Bearer` —
chama os endpoints reais (`POST /contas`, `/categorias`, `/subcategorias`,
`/caixinhas`, `/transacoes`) em vez de escrever direto no Supabase, o que
reaproveita de graça toda validação já implementada (campos obrigatórios,
`hash_dedup`, cálculo de fatura). Só roda localmente, com `backend/.env`
preenchido — mesma limitação dos testes de integração, não roda nesta
sessão remota.

**Exceção — compras parceladas:** `POST /transacoes/parceladas` não serve
pra isso. Ele foi desenhado pra criar as `parcela_total` transações de
uma vez, dividindo `valor_total` igualmente e calculando as datas a
partir de uma única data inicial — nosso histórico tem valor real
(não-uniforme) por parcela, séries truncadas (começam ou terminam fora
da janela do CSV) e nem sempre começam na parcela 1. Pra isso, o script
importa direto os módulos de serviço já existentes — `app.services.
transacao_insercao.inserir_transacao`/`fatura_referencia_para`,
`app.services.dedup.compute_hash`, `app.services.orcamento_sync.
sincronizar_item_orcamento`, `app.auth.get_user_client` (o mesmo client
autenticado que `get_db` usa por trás de cada request) — grava o
cabeçalho em `compras_parceladas` e cada parcela com o valor e a data
reais do CSV, reaproveitando a mesma lógica de fatura/hash do endpoint
principal, só pulando a parte (divisão uniforme) que não se aplica.

**Ordem de criação:** Contas → Categorias/Subcategorias → Caixinhas →
Transações (avista, parceladas e reserva juntas, processadas em ordem
cronológica pra formar os grupos de parcela corretamente).

**Contas (mapeamento fixo, 6 contas):**

| Nome | `tipo_conta` | Regra de roteamento |
|---|---|---|
| BTG Corrente | corrente | Banco=BTG + Meio de Pagamento ≠ Cartão de Crédito |
| BTG Cartão | cartao_credito (fechamento 8, vencimento 11) | Banco=BTG + Meio de Pagamento = Cartão de Crédito |
| Mercado Pago Wagner | corrente | Banco=Mercado Pago |
| Mercado Pago Josi | corrente | Banco=Mercado Pago Josi |
| Banco do Brasil | corrente | Banco=Banco do Brasil |
| Pluxee | carteira | Banco=Pluxee |

**Categorias/Subcategorias:** geradas a partir de `Categorias.csv`,
excluindo a categoria-pai "Forma de Pagamento" (é a lista de meios de
pagamento do app antigo disfarçada de categoria — nenhum lançamento a usa
de verdade). "Receitas" vira `tipo='receita'`, todas as demais
`tipo='despesa'` (não existe categoria-pai de investimento no CSV — os
movimentos de aplicação/retirada não usam `categoria_id`, só
`caixinha_id`, e isso já bate 100% nos dados). Cada subcategoria recebe
`estrutura_custo_padrao` a partir do valor aprendido (ver abaixo), quando
existir um único valor consistente.

**Mapeamento de `meio_pagamento`:** Pix→`pix`, Cartão de Débito→
`cartao_debito`, Cartão de Crédito→`cartao_credito`, Boleto→`boleto`,
Débito Automático→`debito_automatico`, Crédito em Conta→`null` (só
ocorre em Receita, que não exige esse campo — decidido com o usuário,
sem impacto).

**Mapeamento de `tipo_movimento`** (`Movimentação` + `Tipo do Pag /
Movimento` do CSV → enum do app): Despesa+(Compra à vista|Parcela sem
juros|Compra internacional)→`despesa`; Despesa+Estorno→`estorno` (valor
gravado como `abs(valor do CSV)` — o CSV usa sinal negativo só como
convenção própria do usuário pra diferenciar de ressarcimento, decidido
que não há problema em normalizar); Despesa+Ressarcimento→
`ressarcimento`; Receita+Recebimento→`receita`; Reserva+Aplicação→
`aplicacao`; Reserva+Retirada→`retirada`. `ajuste_de_transacao_id` fica
`null` em todos os casos — o CSV não tem uma referência de ID à despesa
original (só texto livre), então o abatimento de estorno/ressarcimento
acontece no total da categoria/estrutura de custo (`ResumoLancamentos.
ajustes_vinculados`), não linha a linha — confirmado com o usuário que
isso atende.

**`estrutura_custo` — ordem de resolução por linha:**
1. Valor literal do CSV, quando presente (maioria das linhas).
2. Valor aprendido: se todas as linhas já preenchidas de uma subcategoria
   concordam num único valor, os vazios dessa subcategoria usam esse
   valor (calculado no início do dry-run, cobre a maior parte dos casos).
3. Caso reste ambíguo (subcategoria sem nenhum dado, ou com valores
   diferentes entre linhas — sem consenso possível), pergunta interativa
   no dry-run (abaixo).

**Fluxo interativo do dry-run:** a 1ª passada do dry-run carrega todas as
linhas pendentes (hoje: 66) e, pra cada uma, mostra data/descrição/
valor/categoria/subcategoria e pergunta `[F]ixo / [V]ariável / [S]azonal
/ [P]ular`. Cada resposta é salva em `backend/scripts/
migracao_overrides.json` (fora do git — é dado financeiro pessoal),
indexado por um hash estável da linha (mesmos campos do `hash_dedup`,
sem `user_id`). Reexecuções do dry-run pulam o que já foi respondido —
só pergunta o que falta. O dry-run só "fecha verde" (pronto pra rodar de
verdade) quando 0 linhas ficarem pendentes ou todas forem explicitamente
puladas.

**Parcelas — agrupamento cronológico:** regex `^(.*?)\s*\((\d+)/(\d+)\)
(.*)$` extrai base/N/total/resto de cada `Descrição`. Agrupa por (base,
total, resto, categoria, subcategoria, banco), ordena por data, e só
mantém o mesmo grupo enquanto o próximo N for exatamente o anterior + 1
— reinício (N volta a 1) ou salto quebra o grupo e começa um novo. Essa
checagem cronológica foi um achado desta análise: sem ela, duas compras
diferentes de "Flamengo Nação" (mesma descrição, mesmo total de 12
parcelas, uma terminando e outra começando no mesmo mês) seriam unidas
numa só, porque os números 1-12 apareciam completos ao juntar as duas.
Cada grupo final gera 1 linha em `compras_parceladas` (`valor_total` =
soma dos valores reais presentes, `parcela_total` = M do texto) + N
transações com o valor e a data reais de cada linha do CSV — nunca
recalculados. Grupos truncados (não começam em 1, ou não terminam em M)
são esperados — a parte que falta ficou fora da janela do arquivo (antes
de dez/2025) ou ainda não venceu, e **não** é gerada por projeção.

**Duplicatas:** todas mantidas como estão — nenhuma é remoção
automática. Uma única linha (21/01/2026, "pix josi", R$ 14,35) foi
confirmada pelo usuário como duplicata de digitação e é removida do CSV
antes de rodar (não pelo script).

**Reconciliação pós-migração:** soma de receita/despesa por mês no banco
(via `GET /transacoes/resumo` por período, ou query direta) comparada
com a soma equivalente calculada a partir do CSV — o relatório final
aponta qualquer diferença, mês a mês.

**Idempotência:** `hash_dedup` garante isso pras transações avista
(passam pelo endpoint normal, que já traduz a constraint em 409 — o
script trata como "já existe, pula"). Nas parceladas **não** dá pra
confiar só nisso — achado durante a implementação: o hash do endpoint
inclui `compra_parcelada_id`, que é gerado de novo a cada cabeçalho
criado, então rodar 2x geraria hashes diferentes mesmo pra dados
idênticos. Pra esse caminho o script checa antes se a 1ª parcela do
grupo já existe (mesma descrição/parcela_atual/parcela_total/data) e
pula o grupo inteiro se sim.

**Bug real achado rodando a migração pra valer (2026-09-25):** a
reconciliação pós-migração apontou divergência em 9 meses — a soma de
despesa no banco ficava sempre um pouco menor que a do CSV (de R$14,99
a R$156,84 por mês). Causa: `hash_dedup` do `POST /transacoes` usa só
(data, valor, descrição, conta, tipo) — **não** categoria. Duas
transações reais e diferentes que coincidem nesses 5 campos (ex: a
mesma assinatura de R$14,99 cobrada todo dia 13, ou um Pix de R$10 pra
"pix josi" duas vezes no mesmo dia — casos que o próprio usuário já
tinha revisado e confirmado como reais, não duplicata de digitação)
colidem na mesma constraint UNIQUE que existe pra evitar duplicar. O
script tratava qualquer 409 como "já existe, idempotente" sem
distinguir os dois casos — perdendo silenciosamente a 2ª ocorrência.
Cada uma das 9 diferenças bateu, centavo a centavo, com a soma das
linhas confirmadas como reais daquele mês.

**Fix:** `agrupar_por_chave_hash` (mesmos 5 campos do `hash_dedup` do
endpoint) agrupa os lançamentos avista antes de criar; a 1ª ocorrência
de cada grupo usa `POST /transacoes` normalmente, a 2ª+ grava direto
via `inserir_transacao` com um índice de ocorrência somado só ao
cálculo do hash (nunca gravado na linha) — evita a colisão sem alterar
o dado salvo. Continua idempotente numa 2ª execução (mesmo índice,
mesmo resultado). Coberto por teste de regressão.

**Limitação de design que sobrava, fora do escopo da migração:** esse
mesmo hash raso existe pro uso normal do app, não só pra migração —
lançar manualmente 2 despesas reais idênticas nesses 5 campos no mesmo
dia esbarrava no mesmo 409, sem como seguir adiante. **Resolvido
2026-10-02** (item 35) — ver subseção própria "`hash_dedup` bloqueando
lançamento manual legítimo" abaixo.

**Depois da migração:** importação de CSV vira opcional (import assistido
de extrato bancário, mapeando pras categorias já existentes) — não é mais
o único caminho de entrada, já que o formulário guiado já cobre o uso do
dia a dia.

**Status:** implementado 2026-09-25 — `backend/scripts/migrar_dados_antigos.py`
+ módulos em `backend/scripts/migracao/` (parsing, contas, mapeamento,
parcelas, overrides), 47 testes offline cobrindo toda a lógica pura
(inclui o caso do "Flamengo Nação" e o do `hash_dedup` colidindo em
transações reais idênticas como testes de regressão). **Executado pelo
usuário contra os dados reais em 2026-09-25** — 1.862 lançamentos
migrados; a reconciliação apontou 9 meses com divergência (bug do
`hash_dedup`, descrito acima), corrigido no mesmo dia. Ver changelog
Rodadas 33 (entrega original) e 34 (esse fix) pro detalhe técnico.

### Lançamento com mais de 1 categoria

**Contexto:** surgiu durante a discussão do item 9 (migração de dados,
2026-09-25) — no CSV histórico apareceu uma compra de materiais
("materiais casa (1/2)"/"(2/2)", R$ 45,78) que a princípio parecia ser 1
única compra parcelada dividida entre 2 categorias diferentes
(`Moradia/Manutenção da casa` e `Outros Gastos/Casa Mauá`). Na conferência
com o usuário, esse caso específico acabou sendo 2 compras parceladas
distintas (cada uma já fechando 1/2 + 2/2 dentro da sua própria
categoria) — não era o cenário real. Mas o usuário levantou a pergunta de
propósito geral por trás do caso: hoje, se uma compra única precisa ser
dividida entre categorias (ex: nota de R$ 300 onde R$ 50 é de uma
categoria e o resto de outra), o único jeito é lançar 2 transações
separadas no mesmo dia — o que já atende, mas é manual.

**Proposta a decidir no futuro:** permitir que 1 lançamento carregue mais
de 1 categoria/valor (ex: um "split" dentro do próprio formulário de Novo
Lançamento), em vez de exigir 2 lançamentos separados. Precisa de decisão
de modelo de dados (linha única com múltiplas categorias vs. tabela de
"itens" por lançamento, similar ao padrão já usado em `orcamento_itens`)
antes de virar trabalho de implementação.

**Status:** registrado 2026-09-25, prioridade média — nenhuma decisão de
modelo tomada ainda; o workaround atual (2 lançamentos separados) atende
o usuário no dia a dia.

### Consulta rápida ao preencher a Descrição

**Motivo real do pedido:** a necessidade não era uma tela de consulta geral
de lançamentos — era uniformizar a Descrição no Novo Lançamento. Sem ajuda,
a mesma compra vira "Supermercado Extra", "supermercado extra" e
"Super Extra" em lançamentos diferentes, dependendo de como o usuário
digitou naquele dia.

**3 opções avaliadas (mockup interativo antes de decidir):**
1. Chips com as descrições mais usadas na categoria/subcategoria (mesmo
   padrão já usado pra categoria/subcategoria "mais usadas").
2. Autocomplete nativo via `<datalist>` — mais barato, mas visual não
   estilizável e inconsistente em mobile.
3. Aviso de "quase-duplicata": compara o texto digitado com as já usadas
   e sugere substituir quando for parecido.

**Decisão:** combinar 1 + 3. Chip cobre quem aceita escolher de uma lista;
aviso cobre quem ignora os chips e digita por hábito ou erro de grafia —
as duas usam a mesma lista de descrições, custo incremental baixo.

**Calibração do aviso (também no mockup, antes de codar):** a 1ª versão só
normalizava maiúscula/espaço — não pegava erro de digitação real. Trocado
por distância de edição (Levenshtein), com tolerância proporcional ao
tamanho do texto. Testado ao vivo em 15%, 25% e 40% (mínimo 1, máximo 5
caracteres) até o usuário fechar em **40%**.

**Decisão de acompanhamento (descartada):** contador de parcela (`N/M`)
embutido na Descrição de compra parcelada — descartado porque
`parcela_atual`/`parcela_total` já são colunas próprias, mostradas
separadamente no card; embutir no texto seria redundante e quebraria a
comparação de uniformidade entre as parcelas da mesma compra.

**Escopo:** só Novo Lançamento (onde foi pedido) — Editar Lançamento não
foi tocado. Cobre compra parcelada de graça, por ser o mesmo campo
Descrição com Categoria/Subcategoria escolhidas antes nos dois fluxos.
Estendido na Rodada 53 pra cobrir também Reserva (aplicação/retirada de
caixinha), que não usa categoria/subcategoria — agrupa por `caixinha_id`.

**Status:** implementado 2026-10-11 — `GET /transacoes/descricoes-mais-usadas`
(backend, com `categoria_id`/`subcategoria_id`/`caixinha_id`) + chips/aviso
em `NovoLancamento.tsx`, lógica de distância em `frontend/src/lib/texto.ts`.
Ver changelog Rodadas 52 e 53 pro detalhe técnico completo e os
checklists de teste manual.

### Agilidade na inserção de transações

**3 caminhos avaliados:**
1. Duplicar transação — botão na lista de Lançamentos pra duplicar
   qualquer transação já existente (não só a última), reabrindo o Novo
   Lançamento pré-preenchido.
2. Copiar da última transação lançada.
3. CRUD em lote — avaliar custo de implementação.

**Decisão original:** ir só com o caminho 1 (Duplicar) — ele é
estritamente mais flexível que o 2 (deixa escolher qualquer transação
passada como modelo, não só a cronologicamente mais recente) pelo mesmo
custo, então absorve o caso de uso do 2 sem precisar construir os dois.

**Mudança de escopo (mesma conversa):** usuário apontou que a dor real
é na tela de SUCESSO do Novo Lançamento — depois de salvar, só existe
"Lançar outro" (do zero) ou "Ver Dashboard" (sair), sem ver a lista de
lançamentos pra duplicar o que acabou de inserir. Isso é efetivamente o
caminho 2, mas resolvido no lugar certo: a própria tela de sucesso, sem
precisar navegar pra lista.

**Fix (mockup aprovado antes de implementar — canvas de design):**
3º botão **"Lançar outro igual"** na tela de sucesso, ao lado de
"Lançar outro"/"Ver Dashboard". Copia tudo do lançamento que acabou de
ser salvo (tipo, conta, categoria, subcategoria, estrutura de custo,
meio de pagamento, descrição, data) e limpa só o Valor — campo que
quase sempre muda entre lançamentos repetidos. Funciona pra Reserva
também (mantém a caixinha escolhida). Tela de sucesso ganhou um recap
do que foi salvo, pra dar contexto a essa decisão.

**Decisão de acompanhamento:** usuário concordou em rebaixar CRUD em
lote (caminho 3) pra baixa prioridade — ver item 69.

**Caminho 1 (Duplicar) implementado também, custo avaliado como baixo**
— reaproveita `derivarTipoLancamento()` (extraída de `EditarLancamento.tsx`
pra `lib/rotulos.ts`, já fazia a conversão transação→campos do
formulário) e o mesmo padrão de "limpar só o valor" do `lancarOutroIgual`.
Botão "Duplicar" em Lançamentos, ao lado de "Editar", navega pro Novo
Lançamento (`state: { duplicar: transacao }`) pré-preenchido, sempre
como à vista (repetir um parcelamento exigiria recalcular valor_total/
parcelas — fora de escopo, usuário escolhe "Parcelado" de novo se
quiser). Cobre o caso que o "Lançar outro igual" não cobre: repetir
algo que NÃO foi o último lançamento.

**Status:** implementado 2026-10-11 em `NovoLancamento.tsx`
(`lancarOutroIgual()`, estado `avisoCopiado`, recap via
`resumoUltimoLancamento`, efeito que consome `location.state.duplicar`)
e `Lancamentos.tsx` (botão "Duplicar"). Mockup interativo (canvas de
design, não faz parte do repositório):
https://claude.ai/artifact/FHKfVknzVa8GrzvcAVF1Kh — demonstra a tela de
sucesso com recap + as 2 transições ("Lançar outro igual" vs "Lançar
outro"). 2 achados testando, corrigidos nas Rodadas 56/57: "Cancelar"
generalizado via `navigate(-1)` (qualquer tela de origem, não só
Dashboard/Lançamentos) e `EditarLancamento.tsx` ganhou busca+"Trocar"
pra despesa original de Estorno/Ressarcimento (bug pré-existente, só
tinha isso no Novo Lançamento). Ver changelog Rodadas 54-57 pro detalhe
técnico e os checklists de teste manual.

### Excluir categoria/subcategoria sem transação associada (item 74)

**Pedido pelo usuário 2026-10-14**, prioridade alta. Hoje só existe
desativar (`PATCH /categorias/{id}/ativo`, `PATCH
/subcategorias/{id}/ativo`) — some dos formulários de novo lançamento,
mas continua existindo e visível em telas de histórico/filtro. Nenhum
endpoint `DELETE` existe pra nenhuma das duas tabelas.

**Por que não é só "adicionar um DELETE":** `db/schema.sql` não declara
`on delete cascade`/`set null` em NENHUMA referência a
`categorias`/`subcategorias` fora de `subcategorias.categoria_id → categorias`
(essa sim cascade — apagar uma categoria já apaga suas subcategorias
hoje). As 3 tabelas abaixo referenciam categoria/subcategoria com FK
padrão (`on delete` implícito = `restrict`) — um `DELETE` direto no
Postgres contra uma categoria/subcategoria ainda referenciada por
qualquer uma delas falha com erro de integridade (não um 404/409
amigável):
- `transacoes.categoria_id`/`subcategoria_id` — o caso que o usuário
  pediu pra checar ("não associada a nenhuma transação").
- `lancamentos_recorrentes.categoria_id`/`subcategoria_id` — um molde
  recorrente ativo (ou inativo) apontando pra ela também bloqueia.
- `orcamento_itens.categoria_id`/`subcategoria_id` — item de orçamento
  (ativo ou não) apontando pra ela também bloqueia.

**Decisão em aberto antes de implementar:** o pedido foi "não
associada a nenhuma TRANSAÇÃO" — mas como o banco bloqueia pelos 3
vínculos acima, a checagem do endpoint precisa cobrir os 3 de
qualquer forma (senão o usuário recebe um erro 500 cru do Postgres em
vez de uma mensagem clara). Falta decidir só a REDAÇÃO da mensagem de
erro quando o bloqueio vem de recorrente/orçamento e não de transação
(ex: "não é possível excluir — ainda usada por 1 lançamento recorrente
ativo (Aluguel)", nomeando o que está segurando).

**Custo estimado:** baixo. Backend: `DELETE /categorias/{id}` e
`DELETE /subcategorias/{id}` (~1-1.5h) — 1 `SELECT count` em cada uma
das 3 tabelas (ou 1 query com `or_` combinando categoria/subcategoria),
404 se a categoria não existe, 409 com a contagem/nome do que bloqueia
se houver vínculo, senão `DELETE` normal. Subcategoria é mais simples
(só 2 tabelas têm `subcategoria_id` relevante pro bloqueio, já que
cascade de categoria não se aplica aqui). Testes: ~4-6 casos (bloqueio
por transação/recorrente/orçamento, sucesso sem vínculo nenhum, 404).
Frontend (`CategoriasSection.tsx`/`CaixinhasSection.tsx`... na verdade
`CategoriasSection.tsx` cobre as duas): botão "Excluir" ao lado do já
existente toggle ativo/inativo, com `window.confirm`, tratando o 409
como mensagem inline (mesmo padrão já usado em `erroCategoria`/
`erroSubcategoria` dessa tela) (~1h). **Total: ~2.5-3.5h.**

**Status:** registrado 2026-10-14, não implementado — falta confirmar
a decisão em aberto acima antes de codar.

### Excluir transações em massa (item 69, repriorizado)

**Pedido original 2026-10-11** (então "CRUD em lote", baixa
prioridade — ver "Agilidade na inserção de transações" acima).
**Repriorizado pra alta 2026-10-14**, escopo reduzido só a exclusão
(criação/edição em lote segue como item 76, baixa prioridade, sem
pedido novo).

**Estado atual:** `DELETE /transacoes/{id}` exclui 1 transação por
vez; se ela veio de "Lançar retirada" (tem
`despesa_origem_retirada_id`), reabre a pendência da despesa de origem
(`_reabrir_retirada_pendente_se_aplicavel`, já coberto por teste).
`DELETE /transacoes/parceladas/{compra_parcelada_id}` já existe
separado, exclui o GRUPO inteiro de uma compra parcelada de uma vez
(não é bulk de transações arbitrárias — é 1 ação em cima de 1 compra
específica). Hoje não existe NENHUMA seleção múltipla na lista de
Lançamentos (sem checkbox, sem "selecionar todos").

**Decisão em aberto antes de implementar — linha de parcela dentro da
seleção:** a lista de Lançamentos mostra cada parcela de uma compra
parcelada como uma linha própria. Se o usuário marcar só ALGUMAS
parcelas de uma mesma compra (não todas) e mandar excluir em massa, o
comportamento correto é excluir só essas linhas (parcela a parcela,
reaproveitando o `DELETE /transacoes/{id}` existente, deixando a
compra com um grupo "furado") ou bloquear/avisar que parcela só se
exclui em grupo (via o endpoint de parcelada já existente)? Precisa de
decisão do usuário antes de codar — muda o contrato do endpoint novo.

**Custo estimado:** médio. Backend: 1 endpoint novo, ex. `POST
/transacoes/excluir-em-lote` com `{ids: list[str]}` — reaproveita o
mesmo corpo de `excluir()` (delete + reabertura de retirada pendente
condicional) num loop por id, todos escopados a `user_id` (~1.5-2h,
incluindo testes: sucesso parcial quando 1 id é de outro
usuário/não existe, reabertura de retirada pendente disparando pra
mais de 1 id ao mesmo tempo). Frontend: bem mais caro que o backend
aqui — checkbox por linha na lista de `Lancamentos.tsx`, "selecionar
todos (os filtrados)"/"limpar seleção", barra de ação fixa mostrando
"N selecionados" + botão "Excluir selecionados" com
`window.confirm` nomeando a quantidade, chamada ao endpoint novo,
depois reaproveita `carregar()` + `buscarUltimosPorConta()` (item 66)
pra refletir o resultado (~3-4h, é o mesmo tipo de UI de seleção que
qualquer lista com ação em lote precisa, sem padrão pronto no projeto
ainda pra copiar). **Total: ~4.5-6h** — a decisão em aberto acima
(parcela parcial) pode reduzir o escopo se a resposta for "bloquear".

**Status:** repriorizado pra alta 2026-10-14, não implementado — falta
confirmar a decisão em aberto acima antes de codar.

### Chips de "mais usadas" fora de Novo Lançamento (item 77)

**Pedido pelo usuário 2026-10-21**, prioridade alta — depois de notar,
testando a Rodada 89, que o formulário de Lançamento Recorrente não
tem os chips de categoria/subcategoria que Novo Lançamento tem.
Escopo ampliado explicitamente pelo próprio usuário: não é só
Recorrentes — é **todo formulário de criação/edição que envolva
categoria/subcategoria OU descrição**, com os dois tipos de chip
(categoria/subcategoria "mais usadas" do item 4 **e** descrição
"mais usadas" + aviso de quase-duplicata do item 43).

**Onde já existe (não precisa de trabalho):** `NovoLancamento.tsx` —
os dois tipos de chip, único lugar implementado até aqui.

**Onde falta, levantado 2026-10-21 (grep em todo `frontend/src`):**
- **`EditarLancamento.tsx`** — tem os selects de categoria/subcategoria
  (`categoriaId`/`subcategoriaId`) E o campo Descrição (2 variantes do
  formulário — despesa normal e estorno/ressarcimento), nenhum chip em
  nenhum dos dois. Maior ganho: é o 2º formulário mais usado do app
  depois de Novo Lançamento.
- **`RecorrentesSection.tsx`** (aba Recorrentes de Lançamentos) — select
  de categoria/subcategoria E campo Descrição, nenhum chip. Caso que
  disparou o pedido.
- **`Planejamento.tsx`** (formulário de item de orçamento) — select de
  categoria/subcategoria (sem campo Descrição — item de orçamento não
  tem um). **Decisão em aberto:** aqui a semântica é diferente —
  não é "etiquetar uma transação com a categoria mais usada", é
  "escolher pra qual categoria/subcategoria já existente este item de
  orçamento aponta" (tipicamente 1 item por categoria, não repetido
  mês a mês como uma transação). Vale confirmar se "mais usada" faz
  sentido aqui antes de implementar, ou se este formulário fica de
  fora do escopo.

**Onde NÃO se aplica (descartado da varredura):** `Lancamentos.tsx` usa
`descricao` só como filtro de busca (texto livre pra PROCURAR, não pra
CRIAR um lançamento) — chip de uniformidade na entrada não faz sentido
num campo de busca. `CategoriasSection.tsx` cria a categoria/
subcategoria em si (campo "nome" dela mesma) — não é um seletor de
categoria já existente, chip não se aplica. `Graficos.tsx`/
`EstruturaCusto.tsx` usam `categoria_id` só em filtro/leitura, sem
formulário de criação.

**Custo estimado:** baixo, backend em zero. Os 3 endpoints que os
chips consomem já são genéricos, sem acoplamento a Novo Lançamento:
`GET /categorias/mais-usadas?tipo=`, `GET
/subcategorias/mais-usadas?categoria_id=`, `GET
/transacoes/descricoes-mais-usadas?categoria_id=&subcategoria_id=&caixinha_id=`
— plugam direto em qualquer formulário novo. O custo é só frontend,
replicando a lógica (2 `useEffect` com guarda de corrida `cancelado` +
o aviso de Levenshtein de `lib/texto.ts`) nos 2-3 formulários acima.
**Recomendação de implementação:** extrair a lógica de
`NovoLancamento.tsx` pra um hook compartilhado (ex:
`useCategoriasMaisUsadas`/`useDescricoesSugeridas`) antes de
replicá-la pela 2ª e 3ª vez — 3 cópias do mesmo `useEffect` com guarda
de corrida é exatamente o tipo de duplicação que vale virar
abstração, diferente de uma duplicação pontual de 2 linhas. Estimativa:
~1-1.5h por formulário (EditarLancamento, Recorrentes) usando o hook
já extraído, mais ~1h pra extrair o hook em si — **total ~3.5-4.5h**
pros 2 formulários confirmados, decisão do Planejamento à parte.

**Status:** registrado 2026-10-21, não implementado — falta confirmar
a decisão em aberto sobre Planejamento antes de fechar o escopo final.

### Caixinhas com saldo errado / limite de 1000 linhas do Supabase

**Contexto:** depois de rodar a migração real e começar a usar a
aplicação no dia a dia, o usuário reportou (com prints comparando a
tela de Caixinhas contra o acumulado calculado à mão a partir do CSV
original) que os saldos de várias caixinhas não batiam — e, quando
questionado se era só as duas do print, confirmou que "não são só essas
caixinhas que tem problema de cálculo, outras também não estão
batendo".

**Investigação:** antes de suspeitar de paginação, foi preciso eliminar
a hipótese óbvia — dado migrado errado. Recalculando `aplicação -
retirada` por caixinha direto do CSV final migrado, o resultado bate
exatamente com a coluna "Guardado" da planilha do usuário (a coluna
"Real", que diverge, inclui rendimento de banco que o app nunca
rastreou — divergência esperada, não bug). O usuário também confirmou
por print que as caixinhas e as transações de cada uma existem
corretamente na tela de Lançamentos filtrada por caixinha — isolando o
problema pro caminho de leitura/agregação, não pra migração/escrita.

**Causa raiz:** o Supabase (PostgREST) tem um limite padrão de 1000
linhas por `.execute()` — `db-max-rows` — que corta o resultado **sem
lançar nenhum erro**. Qualquer query em `transacoes` sem paginação
explícita (`.range()`) simplesmente devolve até 1000 linhas e trunca o
resto, silenciosamente. A conta do usuário, pós-migração, tem ~1862
transações — bem acima do limite. `patrimonio_caixinhas` era o pior
caso: nenhum filtro de data de início ("desde sempre") e nenhum
`.order()`, então quais 1000 linhas voltam nem é estável entre chamadas.
Auditoria do código achou o mesmo padrão (query "todas as transações
do período", sem paginação) em vários outros lugares — não afetava só
Caixinhas:

- `GET /dashboard/resumo-periodo` nos modos "Todos os meses"/Intervalo
  (`_resumo_entre`).
- Gráfico de Evolução (`evolucao_mensal`).
- Despesas por categoria/subcategoria do Dashboard.
- Cálculo de saldo/realizado de Estrutura de Custo e Planejamento
  (`orcamento_saldo.carregar_dados_periodo`).
- `GET /transacoes` e `/transacoes/resumo` sem filtro de data (ex: tela
  de Lançamentos com filtros limpos).
- Ranking de categoria/subcategoria "mais usadas" (janela de 180 dias —
  perto do limite com o volume real de dados).

**Fix:** `buscar_todas_paginado()` (novo, em `app/services/crud.py`) —
helper genérico que itera `.range(offset, offset + 999)` acumulando
páginas até uma página vir com menos de 1000 linhas, substituindo
`.execute().data` direto em todo ponto acima. `tests/fakes.py` ganhou
suporte a `.range()` no `FakeQuery` fake pra poder testar a paginação
offline.

**Status:** implementado 2026-09-25 — sem migração nova, sem endpoint
novo; conserta só o caminho de leitura (os dados no banco sempre
estiveram certos). 348 testes offline passando. Ver changelog Rodada
35 pro detalhe técnico completo e o checklist de teste manual.

### Compromissos Futuros: mostrar todas as parcelas, não só 5

**Contexto:** reportado junto com o bug de Caixinhas acima, na mesma
rodada de dogfooding — "compromissos futuros não são todos mostrados,
cadê o restante das parcelas?"

**Causa raiz:** dois fatores, não um só. `GET
/dashboard/compromissos-futuros` tem `limite: int = Query(5, ge=1,
le=20)` e o frontend (`Dashboard.tsx`) chama sem passar `limite` — cai
sempre em 5. Além disso, por design, o endpoint mostra só a **próxima**
parcela pendente de cada `compra_parcelada_id` ativa (dedup via um
`set`), nunca a lista completa das parcelas restantes de uma mesma
compra — esse segundo comportamento é intencional, não bug.

**Opções discutidas:** aumentar o limite fixo (simples, mas qualquer
número fixo volta a cortar em algum momento) vs. um "ver mais"
expansível.

**Decisão do usuário:** "ver mais" em vez de limite fixo maior —
"[um número fixo] é sempre provável de cortar e não ficar na cara o
tempo todo tb é mais confortável. Se quero ver as próximas todas vou lá
e expando." Junto, pediu pra deixar o card mais compacto/enxuto (menor
altura) sem perder informação, já que ele fica sempre visível no
Dashboard.

**Status:** implementado 2026-09-25 — frontend busca um lote maior
(`limite=50`, backend também teve o teto de `le=20` pra `le=100` pra
não recriar o mesmo problema de corte silencioso) e mostra só as 4
primeiras por padrão, com botão "Ver mais (N)"/"Ver menos" pra
expandir a lista já carregada (sem nova requisição). Card mais enxuto
via classe `.lista-compromissos` (padding e fonte do detalhe menores),
sem remover nenhuma informação exibida. Sem QA visual via Playwright
nesta sessão — exige login real, e esta sessão remota não tem
`backend/.env` com credenciais do Supabase (mesma limitação já
registrada em `CLAUDE.md`); verificado só via `tsc`+`vite build` +
`oxlint`. Ver changelog Rodada 36 e o checklist de teste manual.

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

### Gráfico de despesa por categoria/subcategoria no tempo (item 51)

**Detalhado 2026-10-12.** O que `/graficos` já tem hoje, pra não
duplicar: Evolução Mensal (totais globais — receita/despesa/resultado
— ao longo de vários meses), Pareto (ranking por categoria OU
subcategoria, mas de UM período só, snapshot) e Despesas por Categoria
(mesma coisa, snapshot). **Falta uma visão de TENDÊNCIA por
categoria** — como o gasto em "Lazer" (ou numa subcategoria dela)
evoluiu mês a mês, não só o total do período inteiro.

**Por que não dá pra reaproveitar os endpoints existentes:**
`/dashboard/despesas-por-categoria-periodo` soma o período INTEIRO num
total por categoria (1 número cada) — não quebra por mês dentro do
período. Nenhum endpoint hoje agrega por mês E por categoria ao mesmo
tempo.

**Endpoint novo proposto:** `GET /dashboard/despesas-por-categoria-
evolucao?inicio=&fim=&categoria_id=` — mesmo padrão de performance já
usado em `/dashboard/evolucao` (Rodada 19.3): busca o período INTEIRO
numa query só, agrupa por mês em Python, e dentro de cada mês agrupa
por categoria (ou por subcategoria, quando `categoria_id` vem
preenchido — mesmo toggle categoria/subcategoria que o Pareto já tem).
Resposta: `{ inicio, fim, meses: [{ vigencia_mes, categorias: [{
categoria_id, categoria_nome, valor }] }] }`.

**Frontend:** gráfico novo em `Graficos.tsx`, SVG desenhado à mão
(mesmo padrão de `EvolucaoChart.tsx`/`ParetoTendenciaChart.tsx` —
projeto não usa biblioteca de gráficos) — linhas múltiplas (1 por
categoria) ou barras empilhadas por mês, com legenda e cor por
categoria. Mais complexo que os gráficos atuais (múltiplas séries em
vez de 1), estimativa na faixa de `EvolucaoChart.tsx` (~230 linhas) a
um pouco mais.

**Decisão em aberto:** categoria ou subcategoria por padrão, e quantas
categorias mostrar ao mesmo tempo antes de virar ilegível (ex: top 5 +
"outras agrupadas", como o Pareto já faz implicitamente pelo ranking) —
a definir quando for priorizado.

**Custo estimado:** médio. Backend: ~1 endpoint novo seguindo um
padrão já existente (2-3h, incluindo testes). Frontend: o mais caro
aqui — gráfico multi-série novo do zero (4-6h, dado o padrão de SVG à
mão do projeto).

**Mockups aprovados 2026-10-12** (canvas de mockups, 5 artboards —
usuário aprovou todos, "ótimo"/"perfeito"):
- **Comparador dinâmico de séries** (ideia do usuário: liberdade total
  pra escolher qualquer combinação — subcategoria de receita/despesa,
  estrutura de custo, caixinha — no mesmo gráfico de linhas). Ganhou
  um extra aprovado nesta rodada: **linha de média calculada sobre as
  séries selecionadas**, mês a mês — cálculo 100% client-side (soma os
  valores das séries marcadas em cada mês, divide pela quantidade),
  sem endpoint novo nem mudança de backend.
- **Comparativo ano a ano** (mesma categoria, anos sobrepostos — usuário
  escolhe qual série comparar).
- **Heatmap categoria × mês**.
- **Caixinhas: aporte vs. retirada no tempo** (barras + linha de saldo
  acumulado).
Todos de linha ou barra, exceto o heatmap (grade de células coloridas,
sem eixo de valor).

**Status:** ✅ implementado 2026-10-12 — ver changelog Rodada 91. O
endpoint final não seguiu a proposta de `/dashboard/despesas-por-
categoria-evolucao` acima — ficou mais genérico: `GET /dashboard/
series-mensais?series=tipo:id&inicio=&fim=` aceita uma lista de chaves
(`subcategoria:<id>`, `categoria:<id>`, `estrutura:<fixo|variavel|
sazonal|investimentos>`, `caixinha_aporte:<id>`,
`caixinha_retirada:<id>`), 1 série por chave — o MESMO endpoint serve
os 4 gráficos dos mockups (cada um só varia como monta a chamada/
reorganiza a resposta no frontend), em vez de 1 endpoint por gráfico.
Resolve também a "decisão em aberto" acima: não há mais um
categoria×subcategoria "padrão" fixo — o Comparador dinâmico deixa
escolher qualquer combinação, sem limite de quantidade (usuário decide
o que é legível). 4 componentes novos em `frontend/src/components/`:
`ComparadorSeries.tsx`, `ComparadorAnoAno.tsx`, `HeatmapCategorias.tsx`,
`CaixinhaFluxo.tsx` — todos com toggle Linha/Barra e linha de média
(exceto o heatmap), aguardando teste do usuário (checklist no
changelog).

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
  **Ressalva explícita do usuário (2026-10-12): local provisório.**
  Pretende criar uma feature nova onde o botão ficaria melhor alocado
  — mudar de lugar quando essa feature existir. Não é decisão final.

**Formato do JSON — detalhado 2026-10-12** (o app ganhou Planejamento,
caixinhas/patrimônio e o lembrete de retirada — item 58 — desde
2026-09-15; reavaliando o que entra no export com o estado atual):

```jsonc
{
  "periodo": { "tipo": "mes" | "ano", "inicio": "2026-09-01", "fim": "2026-09-30" },
  "resumo": { /* mesmos campos de ResumoLancamentos — GET /transacoes/resumo */ },
  "lancamentos": [ /* Transacao[], nomes de categoria/subcategoria/conta/caixinha
                      já resolvidos (não só os ids) — pra ficar legível fora do
                      app, sem precisar cruzar com outra tabela */ ],
  "despesas_por_categoria": [ /* DespesaPorCategoria[] */ ],
  "despesas_por_subcategoria": [ /* DespesaPorSubcategoria[] */ ],
  "estrutura_custo": { /* EstruturaCustoMes — orçado × realizado por bucket */ },
  "planejamento": { /* Orcamento + itens do mês, se houver orçamento no período */ },
  "caixinhas": {
    "patrimonio": [ /* SaldoCaixinha[] */ ],
    "retiradas_pendentes": [ /* Transacao[] com retirada_pendente=true no período */ ]
  },
  "evolucao_mensal": [ /* só no tipo "ano" — um ResumoMensal por mês */ ]
}
```

**Endpoint novo:** `GET /relatorios/mes/{vigencia_mes}` e `GET
/relatorios/ano/{ano}` (ou unificado com `inicio`/`fim`, mesmo padrão
de `/dashboard/evolucao`) — compõe a resposta reaproveitando as funções
internas que já existem em `dashboard.py`/`estrutura_custo.py`/
`orcamentos.py` (`_resumo_do_mes`, `_despesas_por_categoria_entre`
etc. — hoje privadas ao módulo, precisam ficar importáveis ou o
endpoint novo mora no mesmo arquivo). Sem lógica de agregação nova, só
composição do que já existe numa resposta só.

**Custo estimado:** baixo-médio. Backend: ~1 endpoint novo + 1 schema
de resposta + testes, a maior parte reaproveitando código já testado
(2-4h). Frontend: 1 botão em Estrutura de Custo (já decidido o local)
que baixa o JSON como arquivo (`Blob` + link), sem tela nova (~30min-
1h). Risco baixo — não toca nada existente, só lê.

**Status:** ✅ implementado 2026-10-12 — ver changelog Rodada 90.
Formato final simplificado em relação ao JSON detalhado acima: a seção
`planejamento` separada foi descartada (redundante — `estrutura_custo`
já cobre orçado × realizado por bucket e por item, ano inteiro vira
`estrutura_custo_mensal` com 12 meses). Endpoints reais: `GET
/relatorios/mes/{vigencia_mes}` e `GET /relatorios/ano/{ano}`. Aguarda
teste do usuário (checklist no changelog).

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

**Decisão de UX (2026-09-30):** diferente da proposta original acima
("Investimento × Reserva" como um 3º discriminador de tipo, igual Novo
Lançamento), a implementação usou um seletor de caixinha opcional dentro
do próprio `tipo_movimento` aplicação/retirada já existente — mais simples
porque `RecorrentesSection.tsx` não tem o discriminador `tipo`
intermediário que `NovoLancamento.tsx` tem (lá, `tipo` já distingue
receita/despesa/reserva/investimento/ajuste/estorno/ressarcimento antes
de chegar em `tipo_movimento`). Categoria some do formulário quando uma
caixinha é escolhida (reserva não usa categoria pra classificação —
bucket vem do `caixinha_id`, não dela); sem caixinha, o campo continua
disponível, agora opcional (mesma regra de `transacoes.py`, que nunca
exigiu categoria pra aplicação/retirada, com ou sem caixinha).

**Fix:** `caixinha_id` nullable em `lancamentos_recorrentes`
(`db/schema.sql` + migração no `README.md`), `categoria_id` deixou de
ser `not null`. `_check_regras_caixinha()` novo em
`routers/lancamentos_recorrentes.py`, espelhando `transacoes.py::
_check_regras_tipo_movimento` (caixinha só em aplicação/retirada; conta
do recorrente precisa bater com a conta vinculada à caixinha).
`_normalizar_e_validar()`: com caixinha zera `estrutura_custo`/
`meio_pagamento`; sem caixinha continua forçando `'investimentos'` como
já era. `confirmar()` parou de hardcodar `caixinha_id: None` na
transação materializada. Detalhe completo no changelog, Rodada 40.

**Status:** implementado 2026-09-30. Ver changelog Rodada 40.

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

**Ajuste de acabamento (Rodada 31, 2026-09-25):** usuário testou no
aparelho real e reportou o FAB ("+") muito colado na barra — o gap era
`--shell-altura-barra-mobile (64px, valor ESTIMADO) + 8px`. Duas causas
juntas: o gap em si (8px) era pequeno, e a constante da altura da barra
estava errada — a altura real medida (soma do padding do container +
padding do próprio link + ícone + rótulo) é ~70-71px, não 64px, então a
sheet/backdrop do menu também sobrepunham ~7px do topo da barra sem que
desse pra perceber a olho nu contra o fundo escurecido. Corrigido os
dois: constante ajustada pra 72px (mais próxima da real) e gap do FAB
subiu de 8px pra 20px. Confirmado via `getBoundingClientRect` no
Playwright: gap FAB→barra foi de ~13px (ainda contaminado pela
constante errada) pra ~21px; gap sheet→barra foi de -6.6px (sobrepondo)
pra ~1px (colado, sem sobrepor).

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

### Estrutura de Custo: tabela de itens quebrando no mobile

**Contexto:** reportado 2026-09-25 com 3 prints do app real (não emulado)
mostrando números cortados na borda direita da tela (ex: "R$ 2.000,0"
sem o último dígito, "R$ 1.32" separado de "7,51"). Mesma classe de bug
do item 20 (colunas de largura fixa em px que não cabem em tela
estreita), só que numa tela ainda não coberta por aquele fix —
`.estrutura-custo-sub-linha` (a linha de cada categoria/subcategoria
dentro de um bucket expandido) usa `display: grid` com colunas fixas.

**Causa raiz, em detalhe:** já existia um ajuste pra mobile (Rodada
25.1) que reduzia a grade de `1fr 140px 100px 100px 90px 26px` pra
`1fr 100px 80px 60px` abaixo de 480px, escondendo status/link. Não
bastou — a última coluna (Diferença, 60px) é estreita demais pra
valores de 4+ dígitos ("-R$ 2.000,00" não cabe, e como é 1 token só,
sem espaço pra quebrar, o CSS Grid não tem como encolher: ele deixa o
conteúdo vazar da coluna e da tela em vez de cortar). Um segundo
problema, estrutural: esse breakpoint (480px) era diferente do
breakpoint em que o resto do app (`AppShell.css`) já vira layout mobile
(720px) — um aparelho entre 480 e 720px de largura (comum: tablet
retrato, ou um celular grande com zoom do sistema reduzindo a densidade
de pixels efetiva) caía numa zona intermediária nunca testada, ainda
usando a grade "desktop" de 140/100/100/90/26px, pior ainda.

**Fix:**
- `frontend/src/components/estruturaCusto.css`: breakpoint unificado com
  o do `AppShell` (720px, não mais 480px — elimina a zona intermediária
  quebrada). `.estrutura-custo-sub-linha` troca `display: grid` (colunas
  fixas) por `display: flex; flex-wrap: wrap` nesse breakpoint — o nome
  do item ocupa a linha inteira, os valores (Orçado/Realizado/Diferença
  + status + link) fluem numa 2ª linha e quebram entre si se precisar,
  em vez de vazar pra fora do card (mesmo princípio do fix do item 20).
  `.rotulo-inline` generalizado (antes só existia escopado a
  `.estrutura-custo-bucket-valores`) e reaproveitado aqui.
- `frontend/src/routes/EstruturaCusto.tsx`: como o cabeçalho de coluna
  (`.estrutura-custo-cabecalho-colunas`, que dizia "Orçado"/"Realizado"/
  etc.) continua escondido no mobile, cada valor da linha de item ganhou
  um rótulo inline (`<span className="rotulo-inline">Orçado</span>` etc,
  mesmo padrão já usado no cabeçalho de bucket/categoria) — sem isso, um
  usuário não teria como saber qual número é qual só pela ordem, já
  quebrada em várias linhas.

**Status:** implementado 2026-09-25 (Rodada 31). QA visual via
Playwright (harness de auth mockada) reproduzindo os valores exatos dos
prints do usuário (Aluguel, Conta de Luz, Condomínio, Plano de Saúde,
com sobra/furo do mês anterior) a 390px e 360px de largura, bucket
"Custos Fixos" e categoria "Moradia" expandidos: `scrollWidth` do
documento bate exato com a largura do viewport nos dois tamanhos,
varredura de `getBoundingClientRect()` não achou nenhum elemento
passando da borda. Mudança 100% CSS/JSX — `tsc`/`vite build`/`oxlint`
limpos, sem warning novo.

**Checklist de teste manual:**
- [ ] Num celular de verdade, Estrutura de Custo, expandir um bucket com
      vários itens (incluindo algum com sobra/furo do mês anterior,
      linha maior): nenhum número corta na borda da tela.
- [ ] Os rótulos "Orçado"/"Realizado"/"Diferença" aparecem antes de cada
      valor no mobile (cabeçalho de coluna reaparece só no desktop).
- [ ] Um tablet ou celular grande em modo retrato (~500-700px de
      largura): mesma barra inferior mobile do resto do app, e a tabela
      de itens também no layout quebrado em linha (não mais a grade
      "desktop").

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

**Fix:**
- `frontend/src/lib/usoMenuMobile.ts` (novo arquivo): `registrarUsoMenuMobile(rota)`
  incrementa um contador por rota num único objeto em
  `localStorage['financeapp:menu-mobile-uso']` (mesmo padrão try/catch de
  acesso a `localStorage` já usado em `PrivacyContext`, silencioso se
  indisponível — aba privada, storage bloqueado). `itemMaisUsadoMenuMobile(itens)`
  ordena por contagem e só retorna um vencedor se ele tiver pelo menos o
  dobro de cliques do 2º colocado **e** um mínimo absoluto de 3 cliques —
  sem o mínimo absoluto, a 1ª navegação a qualquer rota já promovia (2º
  colocado em 0 cliques satisfaz "o dobro" trivialmente), destacando algo
  como "mais usado" cedo demais; achado durante o QA desta rodada, não
  estava no desenho original.
- `frontend/src/components/AppShell.tsx`: o `useEffect` que já existia
  pra fechar o menu ao trocar de rota ganhou a chamada de
  `registrarUsoMenuMobile` quando a rota visitada é uma das que vivem
  dentro do menu "mais" (`SECOES_MENU_MOBILE`). Um `itemDestaqueMenuMobile`
  (via `useMemo`, invalidado por um contador `usoRegistrado` que sobe a
  cada registro — o dado real mora fora do ciclo de render do React, em
  `localStorage`) decide se renderiza o bloco de destaque "Mais usado" no
  topo da sheet, fora dos grupos normais, antes do `.map` que desenha
  Planejamento/Configurações.
- `frontend/src/components/AppShell.css`: `.shell-menu-sheet-destaque` —
  fundo com leve tingimento na cor de acento
  (`color-mix(in srgb, var(--cor-acento) 8%, transparent)`) e título do
  grupo também na cor de acento, pra destacar sem precisar de mais uma
  cor nova na paleta.

**Status:** implementado 2026-09-25 (Rodada 32). Sem endpoint novo, sem
mudança de schema — só frontend. QA via Playwright (harness de auth
mockada, build de produção — o dev server em StrictMode duplica o
contador por rodar effects 2x, então a contagem só é confiável testando
contra `vite build` + `vite preview`) cobrindo: 1 navegação isolada não
promove nada; 2 rotas empatadas (1×1) não promovem; 3 navegações a uma
rota vs. 1 a outra (razão 3:1, acima do mínimo de 3 cliques) promove e
exibe o link correto; aparência conferida em claro e escuro. `tsc`/`vite
build`/`oxlint` limpos, sem warning novo (bundle 232,93 kB, igual à
baseline).

**Checklist de teste manual:**
- [ ] Navegar pra Configurações e Planejamento pelo menu "•••" algumas
      vezes num celular real, priorizando bem mais uma rota que a outra
      (ex: 4x Configurações, 1x Planejamento): depois de recarregar o
      app, o atalho "Mais usado" aparece no topo da sheet, fora dos
      grupos, apontando pra rota certa.
- [ ] Com uso ainda empatado ou abaixo do mínimo, o atalho não aparece
      (sheet mostra só os grupos normais).
- [ ] Fechar e reabrir o app (contador é local ao aparelho): o destaque
      permanece, confirmando que persiste em `localStorage` entre
      sessões.
- [ ] Aba anônima/privada (ou `localStorage` bloqueado): app não quebra,
      menu funciona normalmente, só sem o atalho de destaque.

---

### Fluxo de criação de usuário (cadastro)

**Contexto:** surgiu na hora de rodar a migração de dados (item 9,
2026-09-25) — o usuário perguntou como criar o usuário/senha da conta
real e descobriu que o app nunca teve tela nem endpoint de cadastro,
só login (`AuthContext.signIn`, que chama `supabase.auth.
signInWithPassword`). Pra essa migração, criou o usuário manualmente
pelo painel do Supabase (Authentication → Users → Add user), que
resolve bem pra um usuário só.

**Por que não é urgente:** o app é de uso pessoal, o usuário já tem a
conta criada pelo painel — nenhum fluxo de auto-cadastro é necessário
pro uso do dia a dia. Só passaria a importar se o app ganhasse mais de
um usuário (ex: esposa, outro membro da família com conta separada) ou
se o processo manual pelo painel se tornasse repetitivo.

**O que envolveria, quando for priorizado:**
- Tela de cadastro no frontend (nome/e-mail/senha) + `supabase.auth.
  signUp` no `AuthContext`.
- Decisão de confirmação de e-mail (Supabase manda e-mail de
  confirmação por padrão — decidir se mantém isso ou usa auto-confirm,
  como foi feito manualmente agora).
- Nenhuma mudança de schema — RLS já isola dados por `user_id`
  automaticamente pra qualquer novo usuário.

**Status:** registrado 2026-09-25, baixa prioridade — sem previsão,
processo manual atual resolve.

### Agregações que crescem pra sempre com o histórico — RPCs no Postgres

**Contexto:** depois dos fixes de Caixinhas/Compromissos Futuros (itens
36-37), o usuário levantou a pergunta de fundo: com ~2,5k transações por
ano, em 6-7 anos a conta chega a 15-20k linhas — o `buscar_todas_paginado`
corrige o corte silencioso do Supabase pra qualquer volume, mas ainda
traz 1 linha por transação pra somar em Python. Existe risco real de
latência crescente ao longo dos anos, mesmo sem bug de corretude?

**Diagnóstico:** a resposta divide em duas partes independentes.
Corretude já está resolvida pra qualquer volume (paginação nunca mais
trunca, seja com 2k ou 200k linhas). Performance é o ponto real: nem
toda query cresce com a idade da conta — a maioria é limitada pela
largura do período pedido (resumo mensal, "mais usadas" com janela de
180 dias), então não piora sozinha com o tempo. Só 3 pontos realmente
crescem pra sempre, porque não têm limite de data (ou o limite é "desde
o início da conta"):

1. `patrimonio_caixinhas` — soma aplicações/retiradas desde sempre.
2. Dashboard no modo "Todos os meses" (`_resumo_entre` via
   `/resumo-periodo`).
3. `orcamento_saldo.carregar_dados_periodo` — sobe a cadeia de
   `saldo_anterior` até o orçamento mais antigo.

**Decisão (aprovada pelo usuário):** mover a agregação desses 3 pontos
pro Postgres via função RPC (`db.rpc(...)`), em vez de trazer as linhas
cruas pra somar em Python. O resultado que volta já é agregado (1 linha
por caixinha, ou por grupo de mês/categoria/subcategoria/conta/tipo) —
o custo de rede e de Python passa a depender da complexidade da conta
(nº de categorias/contas/caixinhas × meses), não do volume de
lançamentos.

**Alternativa descartada:** manter um saldo pré-calculado, incrementado
a cada insert/delete de transação (cache de saldo). Rejeitada de
propósito — é exatamente o padrão que o próprio código já evita (ver
docstring de `orcamento_saldo.py`: `saldo_anterior` nunca confia num
valor gravado, porque edição/backfill dessincroniza silenciosamente).
RPC recalcula do zero a cada leitura (fonte única de verdade), só que
dentro do banco.

**Fix:** 3 funções SQL novas em `db/schema.sql` (`saldo_caixinhas`,
`resumo_agregado_transacoes`, `saldo_transacoes_agregado`), chamadas via
`db.rpc(...)` em `dashboard.py` (`_resumo_entre`, `patrimonio_caixinhas`)
e `orcamento_saldo.carregar_dados_periodo`. As funções puras que
consomem o resultado (`calcular_resumo`, `calcular_realizado_item_em_lote`,
`_agregar_estrutura_custo`) não mudaram — só passam a receber "linhas
sintéticas" já somadas por grupo em vez de 1 por lançamento real (a soma
de sinal×valor por grupo é idêntica à soma lançamento a lançamento,
já que o agrupamento usa exatamente os mesmos campos que essas funções
já filtravam). `tests/fakes.py` ganhou suporte a `.rpc(...)`, espelhando
cada função SQL sobre o mesmo `store["transacoes"]` que os testes já
povoam — nenhum teste existente precisou mudar como monta seus dados.

**Migração pendente no Supabase real:** as 3 funções não existiam antes
desta entrega — precisam ser criadas uma vez no *SQL Editor* do projeto
(ver seção própria no `README.md` raiz) antes de usar em produção.

**Status:** implementado 2026-09-25 — 350 testes offline passando
(2 novos, de regressão: múltiplas transações no mesmo grupo de
agregação precisam somar, não sobrescrever/duplicar). Ver changelog
Rodada 37 pro detalhe técnico completo.

### Planejamento: "Gerar orçamento" travando + form de edição fora de vista

**Contexto:** usuário começou a usar a aplicação no dia a dia (item 9
migrado, RPCs aplicadas) e reportou 3 problemas em Planejamento:
"Gerar orçamento" ficando eternamente em "Gerando…", o form de "Editar
configuração" parecendo abrir depois dos buckets, e o layout visual não
bater com Estrutura de Custo. Os 2 primeiros tinham causa raiz
concreta; o terceiro é uma decisão de design registrada como item 40.

**Bug 1 — "Gerando…" travado:** `POST /orcamentos/{id}/proximo-mes`
chamava `calcular_realizado_item()` **uma vez por item** do orçamento,
cada chamada com sua própria busca de transações do mês — N itens
virava N idas e voltas sequenciais ao Supabase, exatamente a mesma
classe de N+1 já corrigida em Estrutura de Custo (Rodada 27) e na
listagem de itens de Planejamento (Rodada 29), só que nunca tinha sido
portada pra este endpoint de escrita. Com uma conta real (dezenas de
itens configurados), isso deixava o botão visivelmente travado —
resolvia eventualmente, mas em segundos ou dezenas de segundos, lido
pelo usuário como "eternamente carregando".

**Fix 1:** troca `calcular_realizado_item` (1 busca por item) por
`carregar_dados_periodo` + `calcular_realizado_item_em_lote` (1 busca
agregada pro mês inteiro, mesmo helper já usado por
`listar_itens`/Estrutura de Custo desde as Rodadas 27/29). Regressão
coberta por teste que cria 4 itens em categorias diferentes e confirma
que a agregação de transações roda 1 vez só, não 4.

**Atualização 2026-09-30 — Fix 1 era incompleto:** usuário testou de
novo com dados reais e reportou que "Gerar orçamento"/"Criar do zero"
continuavam lentos. Havia uma 2ª e 3ª N+1 no mesmo endpoint, nunca
percebidas porque o teste da Fix 1 só tinha poucos itens/transações de
teste (o N+1 existe, mas com N pequeno o tempo extra é imperceptível):
(a) o loop que copia os itens do mês atual pro seguinte fazia **1
INSERT por item**; (b) `_popular_itens_de_transacoes_existentes`
(alimenta itens a partir de transações já lançadas no mês, retroativo)
chamava `sincronizar_item_orcamento` **uma vez por transação do mês**,
cada chamada refazendo sua própria busca de orçamento/itens
existentes — numa conta real, com centenas de transações/mês, isso é
a lentidão dominante, muito maior que a do Fix 1 original (dezenas de
itens × 1 busca vs. centenas de transações × 2-3 buscas cada). Fix:
`(a)` virou 1 insert em lote com a lista inteira; `(b)` virou 1 busca
de transações + 1 busca de itens existentes + no máximo 1 insert em
lote, independente de quantas transações o mês tiver (extraído
`classificar_transacao_para_orcamento()` de
`orcamento_sync.py::sincronizar_item_orcamento` pra reaproveitar a
mesma regra sem repetir a parte cara). 2 testes novos de regressão
provam que o nº de idas ao "banco" não escala com N (nem itens
copiados, nem transações do mês). Ver changelog Rodada 41.

**Bug 2 — form de edição "abrindo depois dos buckets":** o form de
"Editar configuração" e a lista de buckets são mutuamente exclusivos no
JSX (um substitui o outro, nunca coexistem) — mas nada reposicionava o
scroll da página quando o form abria. Se o usuário tinha rolado pra ver
os buckets/itens e clicava em "Editar configuração", os buckets
desapareciam e a página encolhia; sem scroll para o topo, o navegador
mantinha a posição de rolagem anterior, jogando o usuário pro fim da
página (agora bem mais curta) — dava a impressão de que o form "abriu
depois dos buckets", quando na verdade os buckets já tinham sumido e o
form estava lá em cima, fora da vista.

**Fix 2:** `window.scrollTo({ top: 0, behavior: 'smooth' })` ao abrir o
form de configuração (criação ou edição).

**Status:** implementado e testado 2026-09-29 — 351 testes offline
passando (1 novo, de regressão). Sem QA visual via Playwright nesta
sessão (mesma limitação de sempre — sem `backend/.env` com credenciais
reais pra logar). Ver changelog Rodada 38.

### Planejamento: layout não alinhado com Estrutura de Custo

**Contexto:** mesmo relato do item 39 acima — o usuário comparou o
visual de Planejamento (prints anexados) com Estrutura de Custo e achou
inconsistente.

**Diagnóstico:** as duas telas já compartilham a mesma ideia de base
pras linhas de item (grid de colunas fixas, mesmo padrão numérico), mas
divergem em pontos estruturais:

- Estrutura de Custo: 1 cabeçalho de colunas único no topo da página,
  buckets como acordeão (expande/recolhe, sem card próprio, sem borda
  extra), hierarquia bucket → categoria → subcategoria, badge de status
  (Dentro/Excedido) por linha.
- Planejamento: cada bucket é um card próprio (borda, fundo, sempre
  expandido), com cabeçalho de colunas repetido dentro de cada card,
  itens em lista flat (sem hierarquia categoria/subcategoria — cada
  item de Planejamento já É a unidade configurável, não uma agregação
  de lançamentos), sem badge de status, com barra de progresso
  "alocado/teto" que Estrutura de Custo não tem (métrica própria de
  Planejamento — quanto do teto já foi destinado, diferente de
  "realizado vs orçado").

Parte da diferença é proposital (Planejamento configura alvos/aloca
teto; Estrutura de Custo reporta o que já aconteceu — métricas
diferentes), mas card-por-bucket vs. acordeão, cabeçalho repetido vs.
único, e ausência de badge de status são puramente visuais e dá pra
alinhar sem mudar o que cada tela faz.

**Decisão:** apresentados 3 mockups (artifact "Design" — Opção A
alinhamento leve, Opção B acordeão + cabeçalho único, Opção C acordeão
+ badge de status/coluna Realizado, essa última exigindo mudança de
backend). Usuário escolheu a Opção B, com um ajuste: o acordeão de
categoria (2º nível) precisa refletir bucket → categoria PAI →
subcategoria, igual Estrutura de Custo — não só bucket → item flat.

**Fix:** `agruparItensPorCategoria()` (nova, em Planejamento.tsx) —
mesma ideia de `EstruturaCusto.tsx:agruparPorCategoria`, adaptada aos
campos de `OrcamentoItem` (`orcamento_mensal`/`saldo_anterior`/
`disponivel` em vez de `orcado`/`realizado`): item de subcategoria
agrupa pela categoria pai; item só-categoria vira a folha "Geral (sem
subcategoria)" dentro do mesmo grupo (pode coexistir com itens de
subcategoria da mesma categoria); item de conta vinculada ou nome
livre vira seu próprio grupo de 1 folha (mesmo padrão do grupo "conta"
de Estrutura de Custo). Reaproveita as classes CSS de
`estruturaCusto.css` direto (`estrutura-custo-bucket`,
`-bucket-cabecalho`, `-categoria-lista`, `-categoria-linha`, `-seta`,
`-vazio`, `-ir-busca`) em vez de recriar equivalentes em
`planejamento.css` — garante paridade visual permanente entre as duas
telas, não só no dia da entrega. Barra de progresso e cabeçalho de
colunas (Orçado/Sobra do envelope/Disponível, diferente de Orçado/
Realizado/Diferença/Status de Estrutura de Custo) continuam
específicos de Planejamento. Todos os 4 buckets nascem abertos por
padrão (diferente de Estrutura de Custo, que só abre bucket com
lançamento) — Planejamento é tela de configurar os 4 buckets, não de
revisar um relatório. Criar um item novo expande automaticamente o
grupo de categoria dele (sem isso, o item recém-criado nasceria dentro
de um grupo ainda fechado).

**Status:** implementado 2026-09-30. Sem QA visual via Playwright —
mesma limitação de sempre (sem `backend/.env` com credenciais reais do
Supabase nesta sessão remota). Ver changelog Rodada 39.

### Avaliar atualização reativa entre telas após inserção de dados

**Contexto:** pedido do usuário (2026-10-02), a partir de um exemplo
concreto notado testando o Dashboard: clicar em "Confirmar" numa
transação recorrente de aplicação em caixinha (em Compromissos
Futuros) não atualiza o saldo daquela caixinha mostrado mais acima, na
mesma tela do Dashboard — só reaparece certo depois de recarregar a
página inteira.

**Arquitetura atual (por que isso acontece):** não existe cache nem
camada de invalidação compartilhada entre telas (nada tipo React
Query/SWR) — cada tela busca seus próprios dados num `useEffect` ao
montar, e cada ação local (criar/editar/confirmar) só atualiza, na
melhor das hipóteses, o próprio pedaço de estado que ela mesma mexeu.
No exemplo citado: `Dashboard.tsx::confirmarRecorrente()` chama `POST
/lancamentos-recorrentes/{id}/confirmar` e depois só re-busca
`buscarCompromissos()` — nunca `/dashboard/patrimonio/{mes}` (saldo das
caixinhas), nem o resumo mensal/evolução/despesas por categoria, mesmo
quando a transação confirmada afeta esses números no mesmo mês.

**Avaliação pedida, por feature (ponto de partida, não um levantamento
completo ainda):**

- **Dashboard** — o exemplo acima é o caso mais claro: confirmar/pular
  um recorrente (`confirmarRecorrente`/`pularRecorrente`) deveria
  também re-buscar patrimônio de caixinhas e o resumo do mês, quando o
  recorrente confirmado cai dentro do período exibido.
- **Lançamentos (Busca)** — criar/editar/excluir uma transação atualiza
  a própria lista; não atualiza cartões de resumo de outras telas (não
  aplicável dentro da mesma tela, já que Busca não mostra resumo de
  outras seções).
- **Planejamento/Estrutura de Custo** — uma despesa nova cria
  reativamente um item de orçamento no servidor
  (`sincronizar_item_orcamento`); se o usuário estiver com a tela de
  Planejamento aberta e a transação entrar por outro caminho (outra
  aba, Novo Lançamento em nova navegação), o item novo só aparece após
  recarregar — candidato a revisão, mas prioridade menor (cenário de
  múltiplas abas é incomum no uso real relatado até aqui).
- **Caixinhas (Configurações)** — criar/editar uma caixinha não
  precisa propagar pra Dashboard em tempo real, porque navegar pro
  Dashboard já é um novo `useEffect`/fetch — só é um problema se as
  duas telas coexistirem na mesma visão (não coexistem hoje).

**Decisão em aberto, não tomada:** a correção pontual (ex: Dashboard
re-buscar mais 1-2 endpoints depois de confirmar) é barata e resolve o
exemplo citado, mas não escala — cada novo cruzamento de dado exigiria
lembrar de atualizar manualmente o lugar certo. Uma camada de cache
compartilhado com invalidação por chave (React Query ou similar)
resolve de forma genérica, mas é uma mudança de arquitetura maior,
tocando toda tela que busca dado hoje. Avaliar o custo-benefício
feature a feature, como pedido, antes de decidir qual caminho.

**Revisitado 2026-10-12 (item 58 não introduz caso novo):** "Lançar
retirada" sai do Dashboard pra Novo Lançamento (navegação de página,
não ação na mesma tela) — ao voltar pro Dashboard o `useEffect` de
carga roda de novo e o patrimônio da caixinha já vem certo. "Já
retirei" não cria transação (só liga/desliga o lembrete), não move
saldo nenhum. Nenhum dos dois reabre o problema original.

**Investigação mais a fundo 2026-10-12 (a pedido do usuário) — todas as
telas verificadas, lendo o código real, não especulação:**

- **EstruturaCusto.tsx / Graficos.tsx** — 100% leitura, nenhuma ação de
  mutação. Não tem como o padrão deste item existir aqui.
- **Planejamento.tsx** — tem várias mutações (config, sincronizar
  itens, apagar orçamento, gerar com rollover, ativar/desativar item,
  forçar estouro), mas todas mantêm `orcamentos`/`itens` em sincronia
  entre si, e é só desses 2 estados que TODAS as seções visíveis da
  tela derivam (`useMemo`). Sem segunda fonte de busca independente
  ficando pra trás.
- **Configuracoes.tsx** (Contas/Categorias/Caixinhas) — cada aba é um
  componente separado que desmonta/remonta do zero a cada troca,
  sempre buscando dado fresco. Sem estado sobrevivente pra desatualizar.
- **NovoLancamento.tsx / EditarLancamento.tsx** — formulário de tela
  única; criação inline de categoria/subcategoria só alimenta o
  próprio formulário, não existe 2ª seção na mesma tela.
- **Dashboard.tsx** — confirmei que `marcarRetiradaResolvida` (PATCH
  `/transacoes/{id}/retirada-pendente`) só liga/desliga um boolean, sem
  efeito em saldo/patrimônio — nada a re-buscar além do que já faz. Sem
  caso novo aqui, além do já conhecido (recorrente confirmado).

**2 achados NOVOS, ambos em `Lancamentos.tsx`:**

1. **Criar categoria/subcategoria na aba "Recorrentes" não atualiza os
   filtros da aba "Lançamentos".** `RecorrentesSection.tsx` (renderizada
   como aba DENTRO de `Lancamentos.tsx`, sem navegação de rota — trocar
   de aba não remonta o pai) tem seu próprio `criarCategoria`/
   `criarSubcategoria` (chips inline do formulário de recorrente) que só
   atualizam o estado local da aba. `Lancamentos.tsx` busca sua PRÓPRIA
   cópia de categorias/subcategorias uma vez ao montar, e é essa cópia
   (não a da aba filha) que alimenta os selects de filtro da aba
   "Lançamentos". Resultado: criar categoria na aba Recorrentes e voltar
   pra aba Lançamentos não mostra a categoria nova no filtro, só reload
   completo resolve.
2. **Excluir um lançamento não atualiza "Últimos lançamentos por
   conta".** `excluir()`/`excluirCompraParcelada()` em `Lancamentos.tsx`
   só re-chamam `carregar()` (lista filtrada + resumo) — nunca a busca
   de `ultimosPorConta` (`/transacoes/ultimos-por-conta`), que alimenta
   a seção "Últimos lançamentos por conta" (item 54), visível ao mesmo
   tempo na mesma aba. Se o excluído for um dos 10 mais recentes da
   conta (bem provável, é exatamente o que a seção mostra), ele continua
   aparecendo ali com dado que já não existe, até reload manual.

**Recomendação (não implementado ainda, aguardando confirmação):**
Opção A (re-busca pontual) pros 3 casos confirmados agora:
- `Dashboard.tsx`: `confirmarRecorrente`/`pularRecorrente` também
  re-buscam `buscarPatrimonio()` e o resumo do mês.
- `Lancamentos.tsx`: criar categoria/subcategoria na aba Recorrentes
  também atualiza a cópia do pai (ou — mais simples — a aba Recorrentes
  recebe as listas via prop do pai em vez de buscar a própria cópia,
  única fonte de verdade).
- `Lancamentos.tsx`: `excluir()`/`excluirCompraParcelada()` também
  re-buscam `ultimosPorConta`.

Custo baixo pros 3 (~3-4h no total, reaproveita funções de busca que já
existem nos componentes, zero mudança de backend). Opção B (cache
compartilhado tipo React Query) continua descartada por ora — mudança
de arquitetura grande pro número de casos reais (3) encontrados até
agora; revisitar se mais pontos de dor aparecerem com o uso.

**Status:** ✅ implementado 2026-10-12 — ver changelog Rodada 89.
Opção A aplicada nos 3 casos: `Dashboard.tsx` extraiu o fetch de
período pra `buscarDadosPeriodo()` e chama também ela (junto com
`buscarCompromissos()`) ao confirmar um recorrente; `RecorrentesSection.tsx`
ganhou props `onCategoriaCriada`/`onSubcategoriaCriada` que
`Lancamentos.tsx` usa pra atualizar sua própria cópia de
categorias/subcategorias (variante escolhida: notificar o pai via
callback, não a alternativa de a aba filha parar de buscar e receber
tudo via prop); `excluir()`/`excluirCompraParcelada()` em
`Lancamentos.tsx` também re-buscam `ultimosPorConta()`. Aguarda teste
do usuário (checklist no changelog).

### Subitem do bucket Reservas mostra nome da conta em vez da caixinha

**Contexto:** achado testando o checklist da Rodada 40 (2026-10-02) —
item 7 pedia só pra confirmar que uma aplicação/retirada com caixinha
NÃO aparece em Estrutura de Custo como item de investimento, e isso bate
(aparece em "Reservas", correto). Mas ao expandir o bucket "Reservas",
o usuário notou que o subitem (2º nível do acordeão) repete o nome da
CONTA ("Mercado Pago Josi") tanto no nível pai quanto no filho, em vez
de mostrar o nome da caixinha (ex: "Viagem").

**Causa raiz (lida no código, não só inferida):** `_agregar_estrutura_
custo()` (`backend/app/routers/estrutura_custo.py`) agrupa cada
transação por `_chave(t, "conta_id")`, que checa só
`subcategoria_id` → `categoria_id` → `conta_id`, nessa ordem —
`caixinha_id` nunca é olhado. Uma transação de reserva (aplicação/
retirada com `caixinha_id`) não tem categoria nem subcategoria (regra
de negócio, ver "Lançamentos Recorrentes"/transações avulsas), então
cai direto no fallback "conta" — o item de orçamento/resposta da API
carrega só `conta_id`, nunca `caixinha_id` (o campo não existe no
dict do item nem no schema `EstruturaCustoMes`). No frontend
(`EstruturaCusto.tsx`, função que agrupa os itens), o branch `else if
(item.conta_id)` usa `contaNome` tanto pro nome do grupo quanto pro
nome da folha — daí o nome da conta aparecer duplicado onde deveria
aparecer conta (pai, correto hoje) e caixinha (filho, errado hoje).

**O que precisaria:** backend passar a checar `caixinha_id` antes de
cair no fallback de conta em `_chave()` (ou numa checagem própria,
já que hoje `_chave()` é genérica pra orçamento e transação — caixinha
só existe em transação), incluir `caixinha_id` no item retornado por
`_agregar_estrutura_custo`, e no schema `EstruturaCustoMes`. Frontend
busca `/caixinhas` (já é feito em outras telas) e ganha um branch
`else if (item.caixinha_id)` que usa o nome da caixinha pra folha,
mantendo o nome da conta (ou agrupando por caixinha também no nível
pai — a decidir) só como contexto.

**Fix (1ª versão, Rodada 42):** `_chave()` ganhou uma checagem de
`caixinha_id` antes de subcategoria/categoria/conta (orçamento item
nunca tem esse campo, então a checagem nova é inofensiva pro caminho
que já funcionava). `ItemEstruturaCusto` (schema + tipo TS) ganhou
`caixinha_id`. `EstruturaCusto.tsx` ganhou o branch `item.caixinha_id`
usando o nome da caixinha tanto pro grupo (pai) quanto pra folha
(filho).

**Achado do usuário testando essa 1ª versão:** o branch novo tornava a
CAIXINHA o nível pai também, não só o filho — a tela mostrava
"Reservas" → caixinha → caixinha (nome repetido, mesmo bug de antes, só
invertido) e a conta desaparecia inteiramente do agrupamento (`conta_id`
sempre `None` no item, porque `_chave()` retorna só 1 tipo por vez). A
intenção original era conta = 1º nível (sem alterar), caixinha = 2º.

**Fix (correção, mesma Rodada 42):** `_agregar_estrutura_custo` passou
a rastrear, à parte da chave de dedup (que continua sendo a caixinha —
2 caixinhas na mesma conta não podem colapsar), a conta de cada
transação de reserva (`conta_da_caixinha_por_chave`). O item retornado
pela API agora carrega `conta_id` E `caixinha_id` juntos nesse caso
(único caso em que os dois vêm preenchidos ao mesmo tempo).
`EstruturaCusto.tsx` passou a agrupar reserva por `item.conta_id` (igual
ao branch de conta já existente) e usar o nome da caixinha só na folha.

**Status:** implementado 2026-10-02 — teste de regressão ajustado pra
confirmar `conta_id` correto (não mais `None`) junto com `caixinha_id`
em cada item. Suíte completa 363 passed, 33 skipped. Frontend
verificado via `tsc -b && vite build` + `oxlint` — sem erro, sem
warning novo. Sem QA visual via Playwright — mesma limitação de
sempre. Ver changelog Rodada 42.

### Bucket Reservas: Orçado/Diferença/Status sem sentido

**Contexto:** ressalva do usuário testando a Rodada 42 (2026-10-02) —
caixinha/reserva não tem como ser orçada em Planejamento (bucket
"reservas" não existe no `Literal` de `OrcamentoItemCreate.bucket`,
só os 4 buckets de despesa/investimento), mas Estrutura de Custo
mostrava "Orçado"/"Diferença"/"Status" pra cada item de reserva como se
fosse comparável. Usuário propôs 2 caminhos (remover orçado de
Estrutura de Custo, virando só informativo; ou permitir orçar reserva
em Planejamento) e pediu opinião com liberdade pra discordar.

**Decisão (discutida, não só implementada):** nenhum dos dois caminhos
como proposto — o 2º (orçar reserva em Planejamento) mistura um modelo
de alocação percentual de renda (teto%, pool, sobra que rola) com um
comportamento de aporte/resgate discricionário, que não tem "meta
mensal fixa" nem leitura clara de orçado×realizado quando há aplicação
e retirada no mesmo mês pra mesma caixinha. Caminho escolhido: variação
do 1º — Reservas vira puramente informativo, mas em vez de só remover a
coluna Orçado, ela é substituída por algo que diz mais sobre reserva:
**Saldo acumulado** da caixinha (quanto já tem guardado, não só o
realizado do mês) + **Aportado no mês** (o `realizado` que a API já
calculava). Mockup publicado e aprovado antes da implementação.

**Fix:**
- `_enriquecer_saldo_reservas()` (`backend/app/routers/estrutura_custo.py`),
  chamada só por `obter()` (não entra em `evolucao_orcamento()`, que
  nunca usa detalhe por item de reserva) — reaproveita a RPC
  `saldo_caixinhas` que `/dashboard/patrimonio` já usa (1 linha por
  caixinha, já somada "desde sempre" até o fim do mês), preenchendo
  `item["saldo_caixinha"]` em cada item do bucket reservas.
- `ItemEstruturaCusto` (schema + tipo TS) ganhou `saldo_caixinha: float
  | None` — só preenchido pra item de reserva, `None` nos demais.
- `EstruturaCusto.tsx`: o cabeçalho de colunas, antes 1 só pra tela
  inteira, passou a ser renderizado por bucket (`BucketBloco`), porque
  Reservas agora usa colunas diferentes dos outros buckets (Saldo
  acumulado / Aportado no mês, sem Diferença/Status) e um cabeçalho
  único não dava pra rotular os dois ao mesmo tempo. Bucket Reservas
  ganhou um badge "Informativo" ao lado do nome.

**Testes:** 2 testes novos — `saldo_caixinha` acumula entre meses (não
é só o realizado do mês repetido) e fica `None` em item sem caixinha.
Suíte completa: 365 passed, 33 skipped. Frontend verificado via
`tsc -b && vite build` + `oxlint` — sem erro, sem warning novo.

**Status:** implementado 2026-10-02. Sem QA visual via Playwright —
mesma limitação de sempre (sem `backend/.env` com credenciais reais do
Supabase nesta sessão remota). Ver changelog Rodada 43.

### `hash_dedup` bloqueando lançamento manual legítimo

**Contexto:** achado rodando a migração de dados reais (2026-09-25,
ver seção "Migração de dados do app antigo" acima) — `hash_dedup` em
`POST /transacoes` usa só (data, valor, descrição, conta, tipo), sem
categoria. Duas transações reais e diferentes que coincidem nesses 5
campos (ex: 2 assinaturas iguais de R$14,99 cobradas no mesmo dia)
colidem na mesma constraint UNIQUE que existe pra pegar double-submit
acidental (duplo clique) — a API responde 409 "Já existe um lançamento
idêntico" e, até aqui, não havia como seguir adiante: um lançamento
real e legítimo ficava bloqueado. O fix de 2026-09-25
(`agrupar_por_chave_hash`) resolveu isso só dentro do script de
migração, não no uso normal do app.

**Fix:** mesma técnica do script de migração (`gravar_avista_duplicado`),
exposta pelo fluxo normal de criação. `TransacaoCreate` ganhou
`forcar_duplicado: bool` (Pydantic `exclude=True` — nunca vira coluna
na tabela). `_com_desambiguacao_de_duplicata()` (`backend/app/routers/
transacoes.py`): sem forçar, comportamento idêntico a hoje (409 na
colisão); com `forcar_duplicado=true`, soma um índice de ocorrência só
ao cálculo do hash (nunca gravado na linha) e tenta de novo, até 20x.
Frontend (`NovoLancamento.tsx`): ao receber 409, mostra um botão
"Lançar mesmo assim (é outro lançamento real)" que reenvia o mesmo
payload com `forcar_duplicado: true` — só no caminho avista (`POST
/transacoes`), não em compra parcelada.

**Por que manter o 409 por padrão:** a constraint ainda existe pra
pegar double-submit acidental — sem o flag explícito, o comportamento
de hoje não muda em nada. O usuário só vê "lançar mesmo assim" quando a
API já rejeitou, nunca antes.

**Achado testando a Rodada 44 (mesmo dia):** o fluxo de EDIÇÃO
(`PATCH /transacoes/{id}`, usado por `EditarLancamento.tsx`) tinha o
mesmo bug — editar uma transação pra ficar idêntica a outra já
existente batia no mesmo 409, sem `forcar_duplicado` nem botão "Lançar
mesmo assim". Estendido no mesmo dia: `_com_desambiguacao_de_
duplicata()` generalizada (recebe a operação — inserir ou atualizar —
como função) e reusada também em `atualizar()`; `EditarLancamento.tsx`
ganhou o mesmo botão de `NovoLancamento.tsx`. Achado também expôs uma
lacuna no fake de teste: `tests/fakes.py` só simulava a constraint
UNIQUE em `insert`, nunca em `update` — o teste novo batia 200 onde
devia bater 409. Corrigido (`update` agora checa `hash_dedup` e as
constraints de `_UNIQUE_CONSTRAINTS` contra as outras linhas, excluindo
a própria linha sendo atualizada) — espelha o Postgres real, que aplica
UNIQUE em UPDATE tanto quanto em INSERT.

**Testes:** 3 testes novos — repetição com `forcar_duplicado` cria uma
2ª transação idêntica; repetição 3x confirma que o índice de ocorrência
continua funcionando além da 1ª desambiguação; editar uma transação pra
ficar idêntica a outra dá 409 sem forçar e 200 com `forcar_duplicado`.
Suíte completa: 368 passed, 33 skipped. Frontend verificado via
`tsc -b && vite build` + `oxlint` — sem erro, sem warning novo.

**Status:** implementado 2026-10-02 (criação + edição, mesmo dia). Sem
QA visual via Playwright — mesma limitação de sempre. Ver changelog
Rodada 44.

### Compra parcelada não tem proteção real contra double-submit

**Contexto:** usuário testando a Rodada 44 (checklist item 5 — "Tentar
o mesmo cenário de duplicata em compra PARCELADA e confirmar que
continua dando 409") reportou que a operação parcelada NÃO deu 409,
criou normalmente. O checklist estava errado — não por regressão deste
fix, mas porque a premissa (hash_dedup protege parceladas do mesmo
jeito que avista) nunca foi verdade.

**Causa raiz (lida no código):** `criar_parcelada()`
(`backend/app/routers/transacoes.py`) sempre insere 1 linha nova em
`compras_parceladas` primeiro (`grupo["id"]`, gerado pelo banco a cada
chamada), e o `hash_dedup` de cada parcela inclui esse
`compra_parcelada_id`. Duas submissões com o MESMO payload (mesma
descrição/valor/parcelas/data/conta/categoria — ex: duplo clique no
botão "Salvar") geram 2 `compra_parcelada_id` diferentes, logo hashes
diferentes, logo nunca colidem — o `hash_dedup` nunca bloqueia nada
aqui. Isso é o oposto do item 35 (hash bloqueando demais): aqui o hash
não bloqueia o suficiente, e um duplo clique acidental cria 2 grupos de
parcela inteiros (ex: 2x "Celular 12x de R$200") sem aviso nenhum.

**Diferença do que o endpoint avista resolve:** em `POST /transacoes`,
o hash é só da própria linha, então 2 submissões idênticas colidem
naturalmente (é o comportamento "certo" por padrão) — o problema ali
era não ter como confirmar uma exceção legítima. Em `/transacoes/
parceladas`, o problema é o inverso: não existe proteção nenhuma contra
o caso comum (double-submit acidental), porque a chave inclui um
identificador que nunca se repete.

**Fix:** checagem em nível de aplicação, ANTES de criar o grupo em
`compras_parceladas` — `_existe_compra_parcelada_igual()`
(`backend/app/routers/transacoes.py`) busca a 1ª parcela (sempre
existe) com a mesma `descricao`/`data_compra`/`conta_id` do payload, e
confirma `valor_total`/`parcela_total` no cabeçalho do grupo dela. Achou
→ 409 (a menos que `forcar_duplicado=true`, mesmo flag do item 35,
adicionado em `CompraParceladaCreate`). Evita o grupo fantasma em
`compras_parceladas` que bloquear só no `INSERT` da parcela deixaria
pra trás (lá, o `INSERT` falho não grava nada parcial no endpoint
avista — aqui tinha que checar antes de qualquer `INSERT`).
Simplificação da proposta original: `categoria_id`/`subcategoria_id`
saíram da chave de checagem (evita `.eq(coluna, None)`, sem padrão
estabelecido no código pra isso ainda) — os 5 campos restantes já
identificam um double-submit real com segurança suficiente, já que um
double-submit sempre reenvia o payload idêntico em TODOS os campos, não
só nesses 5. Frontend (`NovoLancamento.tsx`): o botão "Lançar mesmo
assim" (já existente do item 35) passou a cobrir também o caminho
parcelado — `montarPayloadParcelada()` extraída e reusada por
`handleSubmit`/`handleForcarDuplicado`, igual ao padrão já usado pro
caminho avista.

**Testes:** 2 testes novos — payload idêntico dá 409 sem forçar e 201
com `forcar_duplicado` (2 grupos distintos); `valor_total` diferente
não é bloqueado. Suíte completa: 370 passed, 33 skipped. Frontend:
`tsc -b && vite build` + `oxlint` — sem erro, sem warning novo.

**Status:** implementado 2026-10-02. Sem QA visual via Playwright —
mesma limitação de sempre. Ver changelog Rodada 46.

### `realizado` de item de Planejamento soma transação de outro bucket quando a categoria é a mesma

**Contexto:** investigando os 2 itens que `scripts/referencia_saldo_anterior.py`
apontou como divergentes (ver seção "Racional de testes com
`/financeapp-ref`" abaixo — este é o item de validação do Orçado,
mesmo racional, método diferente), encontrei primeiro um bug no próprio
script (chave de cache sem o `bucket` — corrigido, commit `7e80642`,
não afeta o app). Mas, reproduzindo o cenário pra
testar esse fix (mesma categoria vinculada a 2 itens de buckets
diferentes no mesmo mês — algo que o app permite, não há constraint de
unicidade), descobri que o PRÓPRIO APP também tem um bug ali, e é mais
sério que o do script.

**Causa raiz (lida no código):** `calcular_realizado_item` e
`calcular_realizado_item_em_lote` (`backend/app/services/
orcamento_saldo.py`) filtram as transações do período só por
`subcategoria_id`/`categoria_id`/`conta_vinculada_id` do item — nunca
pelo `bucket` do item nem pelo `estrutura_custo` da transação. Já
`_item_equivalente_no_mes_em_lote` (mesmo arquivo), que acha o item
"equivalente" no mês anterior pra rolar o `saldo_anterior`, EXIGE
`bucket` igual. Essa assimetria faz: se a mesma categoria está
vinculada a um item de `custos_variaveis` E a um item de
`sazonalidades` no mesmo mês, o `realizado` de CADA UM dos dois conta
TODAS as transações da categoria, inclusive as que "pertencem" ao
outro item — nenhum dos dois fecha certo, mesmo isolado. Confirmado com
teste offline (`FakeSupabaseClient`): 2 itens, mesma categoria, buckets
`sazonalidades` (orçado 1000, despesa real 300) e `custos_variaveis`
(orçado 50, despesa real 10) no mesmo mês — `saldo_anterior` do item
sazonal no mês seguinte saiu 690 (deveria ser 1000−300=700; 690 =
1000−310, ou seja, somou a despesa de 10 do outro item também).

**Confirmado nos dados reais do usuário (2026-10-10):** rodada real da
checagem estrutural (`detectar_vinculo_em_buckets_diferentes`) achou
exatamente os 2 vínculos que batem com os itens divergentes originais,
e os dois pares estão **ATIVOS** nos dois lados — não é item esquecido/
inativo:

- 2026-06, subcategoria "Livros Técnicos": `custos_fixos` (orçado
  R$50, item `eb959aed-...`, ativo) **e** `sazonalidades` (orçado R$0,
  item `ef7bc455-...`, ativo).
- 2026-10, subcategoria "Outros Cartões de Crédito": `custos_fixos`
  (orçado R$5, item `3f8c8ebe-...`, ativo) **e** `custos_variaveis`
  (orçado R$0, item `d27cc0d6-...`, ativo).

Usuário confirma não ter lançamento algum com `estrutura_custo=fixo`
pra essas subcategorias — ou seja, o item de `custos_fixos` nos dois
casos é uma duplicata sem uso real (orçado baixo, provavelmente criado
num teste/reorganização e nunca desativado), mas por estar ATIVO e
compartilhar a mesma subcategoria do item correto, está vazando
`realizado` pra ele de verdade, agora — não é só risco teórico.

**Decisão de fix pendente — não implementado ainda:** a correção óbvia
é filtrar `calcular_realizado_item(_em_lote)` também por
`estrutura_custo` da transação == bucket do item (hoje o campo existe
em `transacoes` e já é usado pra agregação em Estrutura de Custo). Mas
isso precisa de decisão antes de implementar: (1) transação de
aplicação/retirada/estorno não tem `estrutura_custo` preenchido (só
despesa tem, ver `_check_campos_obrigatorios`) — item de bucket
`investimentos` usa `conta_vinculada_id`, não cai nesse filtro, então
não é afetado; (2) precisa confirmar que nenhum dado histórico migrado
tem `estrutura_custo` "errado" em relação ao bucket do item de
Planejamento que hoje usa aquela categoria (improvável, mas item e) da
lista de pontos extras abaixo já cobre esse tipo de inconsistência).

**2 frentes de fix, independentes:**

1. **Dado do usuário (imediato, manual):** desativar os 2 itens
   duplicados de `custos_fixos` (`eb959aed-...` e `3f8c8ebe-...`) em
   Planejamento, já que não têm lançamento real associado — some o
   vazamento pra esses 2 casos sem precisar de deploy.
2. **App (estrutural):** (a) filtrar `calcular_realizado_item(_em_lote)`
   também por `estrutura_custo` da transação == bucket do item, e/ou
   (b) impedir na criação/edição de item de Planejamento vincular a
   mesma categoria/subcategoria a 2 buckets no mesmo orçamento (hoje
   não há validação nenhuma pra isso). Ressalvas da opção (a): aplicação/
   retirada/estorno não preenchem `estrutura_custo` (só despesa tem,
   ver `_check_campos_obrigatorios`) — item de bucket `investimentos`
   usa `conta_vinculada_id`, não cai nesse filtro, não é afetado.

**Rodada real pós-fix do cache:** 625 itens verificados, 0 divergências
de `saldo_anterior` — confirma que o bug 1 (cache) era a causa raiz dos
2 itens flagados antes, e valida a lógica da cadeia de rollover
inteira. A checagem estrutural separada
(`detectar_vinculo_em_buckets_diferentes`) foi o que de fato confirmou
este item nos dados reais (2026-06 Livros Técnicos e 2026-10 Outros
Cartões de Crédito, os 2 mesmos itens — ambos com uma duplicata ATIVA
de `custos_fixos` sem lançamento real, orçado R$50/R$5), já que a
comparação script×app bate mesmo com o vazamento presente (mesma
fórmula nos dois lados).

**Correção de rota, 2026-10-11:** a 1ª implementação (2026-10-10)
escolheu a frente (b) — bloquear qualquer vínculo duplicado, em
qualquer bucket. Usuário (dono do domínio) apontou que isso está
ERRADO: categoria pode legitimamente estar em 2 buckets diferentes —
"Espiritualidade" como custo fixo (dízimo mensal) E sazonal (retiro
ocasional); "Flamengo" fixo (mensalidade) E variável (compra avulsa). A
categoria é um tópico, não pertence a um bucket só — por isso
`estrutura_custo` é campo da TRANSAÇÃO, não da categoria. Bloquear a
criação/edição cross-bucket impedia um uso real (e, na prática,
quebrava a edição comum de "só mudar o valor orçado": o formulário
reenvia a categoria atual no PATCH mesmo sem o usuário mexer nela, e o
bloqueio cross-bucket batia como falso-positivo contra qualquer item
ativo de mesma categoria em outro bucket).

**Fix definitivo, implementado 2026-10-11:** frente (a) da lista acima
— `calcular_realizado_item(_em_lote)` agora filtra por
`estrutura_custo` (`_bate_com_bucket()`, novo helper em
`orcamento_saldo.py`): só conta uma transação pro item se o
`estrutura_custo` dela bater com o bucket do item, OU se a transação
não tiver `estrutura_custo` preenchido (estorno/ressarcimento às vezes
não preenche — mantém contando, pra não quebrar o abatimento que já
funciona). `_check_vinculo_duplicado()` (ver seção abaixo) voltou a
bloquear só dentro do MESMO bucket — vínculo duplicado entre buckets
diferentes está liberado de novo. Os 2 itens duplicados reais do
usuário (ambos em `custos_fixos`, sem lançamento associado) foram
apagados por ele via "Apagar orçamento" (apagou o mês inteiro de junho
e outubro de propósito, ciente do efeito colateral).

**Status:** resolvido 2026-10-11. Ver detalhe completo do fix em
"Correção: vínculo duplicado é permitido entre buckets" logo abaixo.

### Criação manual de item em Planejamento removida

**Contexto:** o item 62 do backlog pedia uma decisão sobre manter ou
remover o botão "+ Novo item" em Planejamento. A investigação do achado
acima deu o racional que faltava: os 2 itens duplicados reais do
usuário (`eb959aed-...`, `3f8c8ebe-...`) foram criados manualmente
("itens que fiz para teste"), e `criar_item()` nunca validou vínculo
duplicado — foi essa falta de validação, não o automático
(`sincronizar_item_orcamento`), que causou o vazamento de `realizado`.

Avaliados os usos reais possíveis da criação manual (meta de poupança
sem categoria → já coberto, melhor, por caixinha; investimento futuro
sem categoria ainda cadastrada → convida a recriar este mesmo bug
quando a categoria for enfim criada; buffer/margem sem destino → baixa
utilidade prática) — usuário não reconheceu ter pedido a feature
originalmente (não está em `sugestoes-e-decisoes-do-redesign.md`; foi
adicionada numa rodada anterior como CRUD simétrico aos 4 tipos de
vínculo possíveis, não por pedido explícito) e decidiu remover.

**Implementado:**

- **Frontend** (`Planejamento.tsx`): removido o botão "+ Novo item" e
  `iniciarCriacaoItem()`. `handleSubmitItem()` simplificado — só edita
  item existente (`itemEditando` sempre presente; o `else` que fazia
  `POST` saiu). O formulário (categoria/subcategoria/nome livre/conta
  vinculada/valor) continua disponível só pra **editar** um item que já
  existe — essa capacidade não foi removida, só a de criar um novo do
  zero.
- **Backend** (`orcamentos.py`): criação manual (`POST .../itens`)
  continua existindo como endpoint — usada internamente por
  `sincronizar_item_orcamento`/`_popular_itens_de_transacoes_existentes`
  como padrão de dado, e por boa parte da suíte de testes como
  infraestrutura de fixture (~90 call sites; reescrever tudo pra outro
  mecanismo só pra "apagar o endpoint" seria custo alto sem ganho real,
  já que o endpoint não é mais alcançável pela tela). `_check_vinculo_duplicado()`
  bloqueia com 409 item ativo duplicado — ver escopo corrigido na seção
  seguinte.
- **Frontend, correção 2026-10-11:** campo "Nome livre" removido do
  formulário de edição por completo (não só escondido condicionalmente)
  — usuário confirmou que nenhum item é ou será nome-livre na conta
  (criação manual não existe mais, e o automático sempre vincula
  categoria/subcategoria).

**Testes:** suíte completa em `test_orcamentos_api.py`, atualizada na
correção seguinte. Frontend: `tsc -b` + `vite build` + `oxlint` sem
erro novo.

**Status:** implementado 2026-10-10, ajustado 2026-10-11 (ver seção
"Correção: vínculo duplicado é permitido entre buckets").

### Correção: vínculo duplicado é permitido entre buckets

**Contexto:** a primeira versão de `_check_vinculo_duplicado()`
(2026-10-10) bloqueava qualquer vínculo repetido entre itens ativos,
em qualquer bucket. Usuário reportou 2026-10-11 que isso quebra um uso
legítimo real (categoria em 2 buckets, ex. "Espiritualidade"
fixo+sazonal) e, na prática, bloqueava até edições que só mudavam o
valor orçado — o formulário sempre reenvia a categoria/subcategoria
atual do item no PATCH, então qualquer item cuja categoria também
existisse em OUTRO bucket (uso legítimo) ficava impossível de editar,
mesmo sem tocar no vínculo.

**Fix:**
- `_check_vinculo_duplicado()` (`orcamentos.py`) ganhou o parâmetro
  `bucket` — só bloqueia quando o item colidente está no MESMO bucket.
  Vínculo duplicado em buckets diferentes está liberado.
- `calcular_realizado_item`/`calcular_realizado_item_em_lote`
  (`orcamento_saldo.py`) ganharam `_bate_com_bucket()`: só soma uma
  transação pro `realizado` do item se o `estrutura_custo` dela bater
  com o bucket do item (mapa `custos_fixos↔"fixo"`,
  `custos_variaveis↔"variavel"`, `sazonalidades↔"sazonal"`,
  `investimentos↔"investimentos"`), ou se a transação não tiver
  `estrutura_custo` preenchido (estorno/ressarcimento, campo opcional
  pra esses tipos — conta pra qualquer item, mantendo o abatimento que
  já funcionava). Esse é o fix que de fato resolve o vazamento de
  `realizado` entre buckets — a validação de criação/edição nunca foi
  a correção certa pra isso, só evitava o sintoma mais óbvio (e
  errava o alvo, bloqueando uso legítimo).
- `scripts/referencia_saldo_anterior.py`: `realizado_independente()`
  ganhou o mesmo filtro (`_bate_com_bucket`), mantendo o script fiel à
  regra real do app. `detectar_vinculo_em_buckets_diferentes()`
  deixou de apontar "risco de vazamento" — agora é só informativo
  (vínculo em 2+ buckets é esperado, não indica bug).
- `Planejamento.tsx`: campo "Nome livre" removido da edição (ver seção
  anterior).

**Testes:** `test_orcamentos_api.py` — os 3 testes que afirmavam 409
entre buckets viraram 201/200 (permitido), mais os equivalentes dentro
do MESMO bucket continuam 409; novo
`test_realizado_nao_vaza_entre_buckets_com_mesma_categoria` reproduz o
exemplo da Espiritualidade fim a fim (2 itens, 2 buckets, 2 despesas
com `estrutura_custo` diferente, confirma `saldo_anterior` correto em
cada um via `/proximo-mes`). Suíte completa: 383 passed, 33 skipped.

**Status:** implementado 2026-10-11.

### Botão de apagar orçamento

**Contexto:** item 56 do backlog, decisão de implementar junto com o
item 62 acima (mesma rodada de conversa). Antes só existia uma forma
indireta de apagar um orçamento: `POST /orcamentos/{id}/proximo-mes?
substituir=true`, que apaga o orçamento do mês **seguinte** como efeito
colateral de regenerá-lo a partir de outro — não serve pra apagar um
mês específico isoladamente, nem pra apagar sem recriar.

**Implementado:**

- **Backend:** `DELETE /orcamentos/{id}` (`orcamentos.py`) — apaga os
  itens do orçamento e o orçamento em si. Não mexe em lançamentos reais
  nem em outro mês (`saldo_anterior` do mês seguinte, se existir, fica
  congelado com o valor já gravado até alguém gerar esse mês de novo —
  mesma limitação documentada em `gerar_proximo_mes`).
- **Frontend** (`Planejamento.tsx`): botão "Apagar orçamento" ao lado
  de "Editar configuração", com confirmação (`window.confirm`, mesmo
  padrão já usado em "substituir"). Depois de apagar, a tela volta pro
  estado "Nenhum orçamento configurado para este mês" — que já oferece
  as duas formas de recriar (criar do zero, ou a partir do mês
  anterior), ambas pré-existentes.

**Testes:** 3 novos em `test_orcamentos_api.py` — apaga orçamento e
itens, 404 em orçamento inexistente, 404 (não apaga) orçamento de outro
usuário.

**Status:** implementado 2026-10-10.

### Teto de bucket deixa de bloquear a gravação, vira aviso visual

**Contexto:** usuário reportou "edição de item do bucket em
Planejamento não está funcionando" — ao vivo, tentando só ajustar o
valor orçado de um item em `custos_fixos` cujo bucket já estava bem
acima do teto efetivo (sobra acumulada deeply negativa, de vários
meses de orçamento criado sem preencher valor real), o backend
recusava com `422`. Erro ficava pouco visível (parágrafo de erro no
topo da página, longe do formulário que estava sendo editado, dentro
de um bucket expandido — "tento editar e não recebo qualquer
feedback").

Questionado se bloquear é o comportamento certo: **não é** — orçamento
é planejamento, e tem categoria que precisa de valor orçado mesmo
estourado (supermercado é o exemplo do usuário: você não deixa de
orçar mercado só porque já estourou o teto do bucket esse mês).
Bloquear a gravação impedia o usuário de simplesmente registrar a
realidade do planejamento.

**Fix:**
- `_validar_teto_bucket()` removida inteira de `orcamentos.py` (era
  chamada em `criar_item`, `atualizar_item`, `alternar_item_ativo`) —
  nada mais bloqueia por teto no backend.
- `Planejamento.tsx` já tinha a infraestrutura visual pronta (cores
  "acima do teto" nos cabeçalhos de bucket e no resumo fixo do topo) —
  só precisava poder salvar o valor estourado pra aparecer. Corrigido
  de quebra: esse aviso visual usava só o teto PURO (percentual × renda
  base), sem somar a sobra/furo acumulado — diferente do que o backend
  removido validava. Novo `tetoEfetivoBucket()` (teto puro + soma do
  `saldo_anterior` dos itens ativos do bucket) substitui o teto puro
  nos dois pontos de exibição, deixando o aviso fiel ao número real
  (sem isso, o cenário do usuário — bucket deeply negativo por sobra
  acumulada, mas item novo pequeno — não teria acionado aviso nenhum).
- Erro de formulário agora também aparece direto acima dos botões
  "Salvar alterações"/"Cancelar" do item sendo editado, não só no topo
  da página.

**Testes:** `test_orcamentos_api.py` — os testes que afirmavam `422`
viraram `201`/`200` (permitido); teste que validava só a fórmula do
teto efetivo via bloqueio foi removido (o cálculo migrou pro frontend,
que não tem suíte automatizada neste repo). Suíte completa: 381
passed, 33 skipped. Frontend: `tsc -b` + `vite build` + `oxlint` sem
erro novo. `README.md` atualizado (regra de negócio documentada).

**Status:** implementado 2026-10-10 (aviso puramente passivo), ajustado
2026-10-11 — ver "Teto de bucket volta a confirmar antes de estourar"
abaixo.

### Teto de bucket volta a confirmar antes de estourar

**Contexto:** pedi avaliação de ter removido o bloqueio por completo
(seção acima). Ressalvas levantadas: (1) zero rede de segurança contra
erro de digitação — nada impede salvar um valor absurdo por engano; (2)
aviso 100% passivo (cor no cabeçalho do bucket) tem o mesmo risco de
passar despercebido que já causou a confusão original ("não recebo
feedback"); (3) existia um meio-termo não usado — o padrão
`forcar_duplicado` já estabelecido no app pra duplicata de transação
(bloqueia a 1ª tentativa com confirmação explícita, aceita a 2ª com a
flag). Usuário concordou e pediu pra trocar pro padrão de confirmação.

**Fix:** `_validar_teto_bucket()` restaurada em `orcamentos.py`, agora
com parâmetro `forcar` — se estourado e não forçado, `409` (não mais
`422` — alinhado ao `409` de `forcar_duplicado`); com `forcar=true`,
sempre permite. `OrcamentoItemCreate`/`OrcamentoItemUpdate` ganharam
`forcar_estouro: bool = Field(default=False, exclude=True)`, mesmo
padrão de `TransacaoCreate.forcar_duplicado`. `alternar_item_ativo`
(reativação) ganhou `forcar_estouro` como query param, já que não tem
corpo de requisição.

Frontend (`Planejamento.tsx`): formulário de edição — 1ª tentativa que
estoura mostra o erro + botão "Salvar mesmo assim (acima do teto do
bucket)" (`handleForcarEstouroItem`), mesmo padrão visual de "Lançar
mesmo assim" em Novo Lançamento. Reativação (botão rápido "Reativar",
fora do formulário) usa `window.confirm()` em vez de um botão extra na
lista — mesmo padrão já usado em "substituir orçamento" nesta mesma
tela, mais adequado pra uma ação de 1 clique.
`tetoEfetivoBucket()`/o aviso visual passivo da seção anterior
continuam existindo — a confirmação cobre o MOMENTO de salvar, o aviso
visual continua mostrando o estado mesmo depois de confirmado.

**Testes:** os 3 testes que afirmavam `201`/`200` sem condição viraram
`409` sem `forcar_estouro` + `201`/`200` com `forcar_estouro=true`.
Suíte completa: 381 passed, 33 skipped. Frontend: `tsc -b` + `vite
build` + `oxlint` sem erro novo. `README.md` atualizado.

**Status:** implementado 2026-10-11.

### Criação automática de item ignorava bucket — despesa ficava sem item em Planejamento

**Contexto:** usuário testando a Rodada 48 (vínculo duplicado entre buckets) reportou não conseguir testar porque "os itens não estão se repetindo entre buckets" — categoria com despesa fixa todo mês (ex: Flamengo) não ganhava item em `custos_variaveis` quando surgia uma despesa variável da mesma categoria; Estrutura de Custo mostrava o valor certo (soma direto dos lançamentos), Planejamento não mostrava nada (depende do item existir). Confirmado com teste controlado: 3 despesas mesma subcategoria, mesmo dia, `estrutura_custo` diferente (fixo/variável/sazonal) — só apareceu em Planejamento o bucket que já tinha item antes do teste.

**Causa raiz:** `sincronizar_item_orcamento()` (`orcamento_sync.py`, reativo — roda a cada despesa nova) e `_popular_itens_de_transacoes_existentes()` (`orcamentos.py`, retroativo — roda ao criar orçamento) checam "já existe item pra essa categoria/subcategoria" só por categoria/subcategoria, **sem olhar o bucket** — mesma classe de bug do achado de `calcular_realizado_item` (2026-10-10), só que na criação automática do item, não no cálculo do realizado. Resultado: categoria com item em QUALQUER bucket nunca ganhava item nos outros, mesmo tendo despesa real lá.

**Fix:**
- `sincronizar_item_orcamento()`: `itens_existentes` passou a selecionar `bucket` também, e `ja_existe` passou a comparar `(bucket, vínculo)` em vez de só vínculo.
- `_popular_itens_de_transacoes_existentes()`: mesmo ajuste — chave de `chaves_existentes`/`chaves_novas` ganhou `bucket`.
- Esses 2 fixes só valem daqui pra frente (não retroagem em orçamento já criado com o bug). Novo endpoint `POST /orcamentos/{id}/sincronizar-itens` (idempotente — roda `_popular_itens_de_transacoes_existentes` de novo contra um orçamento já existente) cobre o retroativo. Botão "Sincronizar itens com lançamentos" em Planejamento, ao lado de "Editar configuração"/"Apagar orçamento".

**Esclarecimento (item 4 do teste do usuário):** o `409` de vínculo duplicado (Rodada 48) é sobre **itens de orçamento** (editar um item em Planejamento apontando pra vínculo já usado no mesmo bucket), não sobre lançamentos — 2 despesas reais com a mesma categoria/`estrutura_custo` são normais e nunca deveriam dar erro. Checklist mal redigido, não é bug.

**Testes:** 4 novos — despesa cria item próprio mesmo com a categoria já tendo item em outro bucket (reativo e retroativo), sincronizar-itens preenche o buraco que o bug antigo deixaria (simulado removendo o item direto do "banco" de teste), 404 em orçamento de outro usuário. Suíte completa: 385 passed, 33 skipped. Frontend: `tsc -b` + `vite build` + `oxlint` sem erro novo.

**Status:** implementado 2026-10-11. Usuário ainda precisa clicar "Sincronizar itens com lançamentos" nos meses já afetados (os que já tinham despesa real de categoria com item em outro bucket) pra ver os itens que faltam.

### Janela de meses pra trás × ano civil nos gráficos

**Contexto:** modo "Mês" em `/graficos` sempre mostrou uma janela
trailing de 12 meses terminando no mês selecionado (Evolução Mensal +
Orçado × Realizado). Pergunta registrada 2026-09-16 (Rodada 16.2):
repensar se um ano civil fixo (jan-dez) seria mais legível.

**Discussão (2026-10-02):** prós/contras levantados e decisão tomada
com o usuário, antes de implementar.

- Trailing 12 meses (atual): sempre 12 pontos preenchidos qualquer mês
  escolhido; é o padrão de análise financeira pra "como estou
  evoluindo" (TTM); sem o "penhasco" visual de dezembro→janeiro.
- Ano civil fixo: bate com o jeito mais comum de pensar (extrato,
  IRPF, "quanto gastei esse ano"); mas em janeiro/fevereiro mostraria
  um gráfico quase vazio (só 1-2 meses com dado real).

**Decisão:** não trocar o padrão (trailing 12 meses continua sendo o
que abre por default) — ano civil fixo já existia como alternativa via
modo "Intervalo" (escolher jan-dez manualmente), então a única lacuna
real era não ter um atalho de 1 clique pra isso no modo "Mês". Fix
escolhido: toggle opt-in "Últimos 12 meses" / "Ano civil (AAAA)" dentro
do modo "Mês", que só troca a janela de `/dashboard/evolucao` e
`/estrutura-custo/evolucao/tendencia` (Evolução Mensal + Orçado ×
Realizado) — não afeta Pareto/despesas por categoria, que já são só do
mês de referência selecionado, com ou sem o toggle.

**Fix:** `Graficos.tsx` ganhou `verAnoCivil` (estado local, não
persistido entre navegações — como `nivelPareto`, mesma classe de
estado "barato" já usada na tela) e um segmentado "Últimos 12 meses" /
"Ano civil (AAAA)" ao lado do seletor de período, visível só no modo
"Mês". Quando ligado, `evolucaoInicio`/`evolucaoFim` passam a ser
jan-dez do ano do mês selecionado, em vez de `mesesAntes(vigenciaMes,
11)`. Nenhuma mudança de backend — os 2 endpoints já aceitam qualquer
intervalo arbitrário (é o mesmo contrato que o modo "Intervalo" já usa
hoje, inclusive com fim no futuro, dentro do ano em curso).

**Status:** implementado 2026-10-02 — só frontend. `tsc -b && vite
build` + `oxlint` sem erro, sem warning novo. Sem teste automatizado
novo (troca de janela de busca, sem lógica de cálculo nova — mesmo
padrão de cobertura dos outros toggles de período da tela). Sem QA
visual via Playwright — mesma limitação de sempre. Ver changelog
Rodada 45.

**Achado testando a Rodada 45 (2026-10-10):** o toggle tinha sido
colocado como irmão de `<SeletorPeriodo>`, fora do card
`.dashboard-seletor` que desenha o fundo opaco — `.cabecalho-fixo`
(`position: sticky`) não tem fundo próprio, então ao rolar a página o
toggle "flutuava" transparente sobre o gráfico atrás (print anexado
pelo usuário). Fix: `SeletorPeriodo` ganhou suporte a `children`,
renderizado dentro do mesmo `.dashboard-seletor` — mesmo mecanismo que
atende o pedido do usuário de quebra ("colocar dentro do cabeçalho pra
ficar fácil de acessar ao rolar"). Ver changelog Rodada 45, seção
"Correção".

### Racional de testes com `/financeapp-ref`

**Origem:** o usuário vinha testando os checklists manuais das Rodadas
35-41 e bateu em vários itens que não tinha mais como verificar de
memória (não lembra os valores antigos pra comparar). Perguntou se
dava pra usar a skill `/financeapp-ref` pra esses casos — resposta:
parcial, e esta seção organiza exatamente o que ela cobre, o que não
cobre, e o que merece atenção extra. **Fila: só entrar nisso depois do
usuário terminar de verificar a Rodada 40** (ordem pedida
explicitamente) — **liberado 2026-10-02**, a Rodada 40 já foi
verificada por completo (7/7 itens ok).

**Extensão feita em 2026-10-01:** `backend/scripts/referencia_dashboard.py`
ganhou `realizado_por_bucket` (por mês) — reimplementação independente
de `app/routers/estrutura_custo.py::_bucket_da_transacao`/
`_SINAL_REALIZADO`, reaproveitando só a camada de parsing/interpretação
do CSV já existente (`scripts/migracao/mapeamento.py::
resolver_estrutura_custo`, com os mesmos 3 níveis de resolução da
migração real: literal → aprendido por subcategoria → override salvo).
Novo argumento `--overrides` aceita o mesmo arquivo usado na migração
real (default `backend/scripts/migracao_overrides.json`); sem ele,
despesas ambíguas caem em "sem_estrutura" e o script avisa no stderr.
A skill `.claude/commands/financeapp-ref.md` foi atualizada com o novo
campo e esse aviso.

**Como rodar — não é o usuário quem executa o script.** A skill
`/financeapp-ref` É o script: o usuário aciona a skill numa conversa
(digitando `/financeapp-ref` ou só pedindo), **anexa os arquivos** (o
CSV + opcionalmente `migracao_overrides.json`, os 2 como upload na
própria conversa — nunca um caminho de disco, a sessão que roda o
script não tem acesso ao computador do usuário), e é o Claude, do lado
de dentro da sessão, que roda `backend/scripts/referencia_dashboard.py`
com `--csv .../--overrides ...` apontando pros 2 arquivos recebidos e
devolve o resultado na conversa. Não existe "rodar a skill" e "rodar o
script" como 2 coisas separadas — achado 2026-10-01, a 1ª explicação
dada ficou confusa nesse ponto.

**Por que 1 item do checklist pode ficar só "meio resolvido" — exemplo
concreto** (achado 2026-10-01, a explicação original também ficou
confusa aqui): o item 4 da Rodada 37 pede pra confirmar "saldo/
realizado de um bucket" — esse texto mistura 2 números que a tela de
Estrutura de Custo/Planejamento mostra lado a lado pro mesmo bucket,
mas que vêm de fontes completamente diferentes:

- **Realizado** = quanto você gastou/investiu de verdade naquele
  bucket naquele mês. Isso é só histórico de transação (data, valor,
  categoria, tipo) — **existe no CSV**, e é exatamente o que
  `realizado_por_bucket` calcula.
- **Orçado / saldo_anterior** = quanto você *planejou* gastar naquele
  bucket (o número que você digitou na tela de Planejamento,
  `orcamento_mensal`) + a sobra acumulada dos meses anteriores. Isso
  **nunca esteve no CSV** — o CSV é histórico de lançamentos reais, não
  tem campo nenhum pra "quanto eu pretendia gastar". Esse dado só
  existe nas tabelas `orcamentos`/`orcamento_itens` do Supabase, que a
  tela de Planejamento escreve.

Não tem como estender o script pra cobrir essa 2ª metade — não é falta
de código, é que a fonte de dado (o CSV) nunca teve essa informação.
Por isso um mesmo item de checklist (ex: Rodada 37 item 4) aparece
**parcialmente** na lista "resolve" abaixo (a metade Realizado) e
também teve a outra metade registrada como "não resolve" (Orçado/
saldo_anterior) — não é number duplicado nem contradição, é o mesmo
item do checklist partido nas 2 metades que ele de fato cobre.

**O que a skill resolve** (realizado, derivado 100% do CSV):

1. Rodada 35, item 1 / Rodada 37, item 2 — Caixinhas/Patrimônio
   batendo com a coluna "Guardado": `patrimonio_caixinhas` do JSON, por
   mês, contra o que a tela mostra (mesmo cálculo nas duas rodadas, a
   única mudança entre elas foi a fonte virar RPC).
2. Rodada 35, item 2 / Rodada 37, item 3 — Dashboard "Todos os
   meses"/Intervalo: `todos_os_meses_ate_hoje` (ou a soma dos meses do
   intervalo escolhido) contra os totais de receita/despesa/resultado
   da tela.
3. Rodada 35, item 3 / Rodada 37, item 4 — Estrutura de Custo/
   Planejamento, **só a metade Realizado** (ver exemplo acima):
   `realizado_por_bucket` de 1-2 meses contra o "Realizado" que a tela
   mostra pra esses meses.

**O que a skill NÃO resolve** (não existe no CSV, só no Supabase):

4. A outra metade dos itens 35.3/37.4 acima — a coluna Orçado, o teto
   por bucket (`receita_base × percentual_geral% × limite_bucket%`) e
   a cadeia de `saldo_anterior` do modo envelope (ver exemplo acima).
   Verificação manual (ver pontos extras abaixo).
5. Rodada 41, item 3 (itens do mês novo saem com o mesmo orçado do mês
   anterior, categoria sem item aparece em R$ 0,00) — mesmo motivo do
   item 4, é 100% dado de configuração copiado entre orçamentos.
6. Rodada 36, itens 3-4 (card de Compromissos Futuros sem descrição/
   botões de recorrente) — não é cálculo numérico, é layout/UI; fora
   do escopo desta skill, resolver junto da Rodada 40 como já decidido.

**Pontos extras que merecem atenção** (sugestão, não pedido original —
pra fechar a lacuna que a skill deixa no lado orçado):

a. **Cadeia de `saldo_anterior`** — é o cálculo mais complexo do app e
   não dá pra validar pelo CSV. Sugestão de teste manual dirigido, uma
   vez só: escolher 1 bucket com ≥3 meses de histórico e confirmar à
   mão, mês a mês, que `saldo_anterior(mês) = orcamento_mensal(mês−1)
   + saldo_anterior(mês−1) − realizado(mês−1)`. Bater em 3 meses
   seguidos já dá confiança alta na recursão inteira (se o padrão
   vale pra 1 passo, vale pra N).
b. **Pool de despesas / piso de investimentos** (`dentro_do_teto`/
   `meta_batida`) — mesma limitação do item a. Sugestão: escolher 1 mês
   em que o usuário sabe que estourou ou bateu a meta de propósito, e
   confirmar à mão que o veredito mostrado bate com a conta manual do
   teto efetivo (teto puro + saldo_anterior acumulado do bucket).
c. **`hash_dedup` colidindo em transações reais idênticas** (item 35
   deste backlog) — não é cálculo, é perda silenciosa de dado; na
   próxima vez que lançar 2 despesas reais idênticas (mesma data/
   valor/descrição/conta/tipo) no mesmo dia, confirmar que a 2ª
   realmente aparece — hoje é um 409 que o frontend não trata, e o bug
   nunca foi reproduzido ao vivo, só em teste automatizado.
d. **Reserva com caixinha, depois do fix da Rodada 40** — depois de
   confirmar um recorrente de aplicação/retirada com caixinha,
   cross-check com `/financeapp-ref`: como essa transação é nova (não
   existe no CSV histórico), comparar à mão: saldo da caixinha antes
   do aporte/resgate (já validado pelo item 1 acima) + o valor do
   aporte/resgate = saldo mostrado depois na tela.
e. **"sem_estrutura" inesperado** — a migração real fechou com 0
   pendências de estrutura de custo (ver "Migração de dados do app
   antigo" acima), então nenhuma despesa migrada deveria cair em
   "sem_estrutura" na referência (com `--overrides` certo). Se aparecer
   um valor != 0 mesmo assim, é sinal de uma despesa lançada DIRETO no
   app sem estrutura de custo preenchida — o que não devia ser
   possível (`estrutura_custo` é campo obrigatório pra despesa,
   `_check_campos_obrigatorios` em `transacoes.py`). Um "sem_estrutura"
   positivo aqui é, na prática, um jeito indireto de pegar um bug de
   validação que não está exigindo o campo de verdade em algum
   caminho (ex: `PATCH` deixando um despesa sem o campo).

**Status:** feito 2026-10-10/11. Itens 2 e 3 da lista "o que a skill
resolve" (Dashboard Todos-os-meses/Intervalo; Estrutura de
Custo/Planejamento metade Realizado) confirmados contra a conta real
via `/financeapp-ref` + `referencia_saldo_anterior.py`, com
screenshots/relatório (ver changelog Rodadas 35 e 37, confirmações de
2026-10-11). Ponto extra (a) (cadeia de `saldo_anterior`) também
coberto pelo mesmo script: 625 itens, 0 divergências pós-fix de um bug
de cache no próprio script (chave sem o `bucket`, commit `7e80642`,
não afetava o app). A rodada real encontrou, além disso, um bug sério
**no app** — `realizado` de item de Planejamento somando transação de
outro bucket quando a mesma categoria está vinculada a 2 buckets no
mesmo mês — corrigido 2026-10-11 (ver seção "`realizado` de item de
Planejamento soma transação de outro bucket..." abaixo, detalhe
completo). Único ponto do roteiro sem reconfirmação formal: item 1
(Caixinhas/Patrimônio × coluna "Guardado") — segue sem rodar de novo
pós-RPC (Rodada 37), mas a mesma fórmula já bateu por cálculo direto do
CSV na investigação original da Rodada 35; risco residual baixo.

---

Todas as propostas trazidas em 2026-09-15 (6 mockups de referência) foram
decididas nesta mesma rodada — nenhuma pendência de aprovação restante. Ver
o changelog em `changelog-proposta-original-do-redesign.md` pro raciocínio completo por
trás de cada recomendação.
