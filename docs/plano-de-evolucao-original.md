# Plano de evolução original (análise do ZIP + plano de migração)

Estes são os dois documentos que abriram o projeto, escritos a partir da
análise do ZIP do app antigo (`v6_Estrutura_de_custos.zip`), antes de
qualquer linha de código da versão web ser escrita. Recuperados do histórico
da sessão e salvos aqui porque só existiam em texto de conversa — não
tinham lugar nenhum versionado. Ver também `redesign-proposta-original.md`
(os mockups visuais que vieram logo depois destes textos, e a comparação
proposto x implementado) e `sugestoes-e-decisoes-do-redesign.md` (a rodada
de perguntas e respostas que refinou este plano até a divisão final em 7
entregas).

---

# Análise — `v6 Estrutura de custos` (Finance App)

Extraí o ZIP (contém inclusive 3 ZIPs aninhados de lotes anteriores em `zips/`). O projeto principal está em `lote_2_funcional/`: app desktop em Python/Tkinter que lê CSV/Excel de lançamentos financeiros e gera um relatório HTML standalone interativo, com um servidor HTTP local para persistir orçamentos.

**Tamanho:** ~3.200 linhas Python (app) + ~5.000 linhas JS/CSS (relatório) + 9 arquivos de teste. **Testes:** 76/76 passando (rodei localmente).

## 1. Estrutura/Arquitetura

Boa separação em camadas: `core/` (dados/regras), `features/*/` (um gerador de HTML por aba), `ui/` (Tkinter), `assets/` (CSS/JS do relatório), `tests/`. Isso facilita localizar e evoluir cada aba isoladamente — é o ponto mais forte do projeto.

**Problema real encontrado na prática:** `core/file_loader.py:6` importa `from tkinter import messagebox` direto na camada `core`. Isso quebrou meus testes num ambiente headless (sem Tkinter) até eu simular o módulo — prova que a camada de dados está indevidamente acoplada à UI. O ideal é `core` levantar exceções e a UI (`tkinter_app.py`) decidir como exibir o erro.

Outros pontos de estrutura:
- `orcamento_html.py`: `_gerar_tabela_custos` e `_gerar_tabela_investimentos` (~90 linhas cada) são quase duplicadas — boa oportunidade de unificação.
- Geração de HTML por concatenação de strings (`html += f'...'`) em todas as features. Funciona e está bem escapado, mas é mais frágil a longo prazo que um template engine (fácil esquecer de escapar um campo novo).
- O ZIP entregue traz `__pycache__`, `.bak`, log de inicialização, CSVs pessoais e os 3 ZIPs de lotes anteriores — sinal de que é um snapshot de working dir, não um pacote limpo.

## 2. Segurança

**Pontos positivos, e sólidos:**
- **Dinheiro com `Decimal`** (`budget_repository.py:62-69`) evita erros de ponto flutuante em valores monetários.
- **Concorrência otimista bem feita**: revisão + fingerprint SHA-256, lock de arquivo com detecção de lock "travado" (stale), escrita atômica (`temp` + `fsync` + `os.replace`) e backup automático antes de sobrescrever, com restauração automática se o arquivo corromper (`budget_repository.py:195-249`). Isso é nível "produção", incomum em app pessoal.
- **Anti-XSS consistente**: dados do usuário injetados no HTML são escapados com `html.escape()` (`orcamento_html.py`, `busca_html.py`), e o JSON embutido no `<script type="application/json">` escapa `& < >` para não quebrar a tag (`html_utils.py:18-25`). No JS, os valores dinâmicos usam `textContent`/`createElement`, não `innerHTML` — evita XSS via DOM.
- Servidor HTTP local só escuta em `127.0.0.1` com porta efêmera (`local_server.py:53-55`).
- Nenhum `eval`, `exec`, `subprocess`, `pickle` ou segredo hardcoded encontrado.

**Achados a corrigir/considerar:**
1. **Código morto/enganoso em `html_utils.py:24`**: `.replace('\u2028', '\u2028')` — como está escrito em source (`'\\u2028'`), procura o texto literal `\u2028` (que nunca ocorre, pois `json.dumps(ensure_ascii=False)` gera o caractere Unicode real, não a sequência escapada). É um no-op — a intenção de neutralizar U+2028/U+2029 não é cumprida. Não é explorável hoje porque o JSON está dentro de um `<script type="application/json">` parseado via `JSON.parse` (não avaliado como JS), mas é um bug de "falsa sensação de segurança" que vale corrigir para `\u2028`/`\u2029` reais.
2. **Servidor local sem proteção CSRF** (`local_server.py:28-46`): o endpoint `POST /api/orcamentos` aceita qualquer requisição que chegue à porta, sem token/Origin check. Como a porta é efêmera (`port=0`), o risco de um site malicioso aberto no mesmo navegador "adivinhar" a porta é baixo, mas não nulo — vale adicionar um token de sessão ou checagem de `Origin`/`Referer` como defesa extra.
3. `SimpleHTTPRequestHandler` serve todo o `project_root` via GET — qualquer arquivo da pasta do app (inclusive `.bak`, CSVs, `orcamentos.json`) fica acessível enquanto o app roda. Aceitável para uso local single-user, mas sem autenticação nenhuma.
4. **`except:` genérico** em `file_loader.py` (`_read_csv`, `_read_excel`) engole qualquer exceção nas tentativas de fallback de encoding — mascara erros reais (ex: arquivo corrompido) até esgotar todas as tentativas, dificultando diagnóstico.
5. Dados financeiros ficam em **texto plano** (CSV/JSON) — normal para app local, mas se a pasta for sincronizada em nuvem/backup, os dados vão sem criptografia.

## 3. Qualidade de código

- **Boa cobertura de testes** (76 testes, todos passando), cobrindo regras de orçamento, parsing de arquivos, processamento de dados e até o fluxo da UI Tkinter.
- Lógica de negócio bem documentada com docstrings explicando o *porquê* (ex: alocação de estornos, retroatividade de custos) — acima da média.
- Validação de dados robusta em `validate_budget()` (schema, moeda, percentuais, soma de limites ≤ 100%).
- Duplicação moderada entre `dashboard_html.py` e `graficos_html.py` (mesmo bloco `monthly_series` montado duas vezes) e dentro de `orcamento_html.py` (tabelas de custo vs. investimentos).
- Nomenclatura em português consistente, mas mistura `orcamento`/`orcamento_mensal` como chaves alternativas em vários lugares — sinal de dívida de migração de schema que aumenta a complexidade condicional (`item.get('orcamento_mensal', item.get('orcamento', 0))` repetido dezenas de vezes).

---

## Funcionalidades já implementadas (no app antigo)

**Importação e consolidação de dados**
- Leitura de CSV (formato BR e US, com fallback de encoding) e Excel (.xls/.xlsx), com fallback para extrair tabela de HTML
- Normalização automática de nomes de colunas e validação de colunas obrigatórias
- Consolidação de múltiplos arquivos com deduplicação idempotente do histórico (não duplica ao reprocessar)
- Persistência do histórico consolidado (CSV) com backup e escrita atômica

**Classificação financeira automática**
- Classificação de lançamentos em receita / despesa / aplicação / retirada / ajuste (estorno, ressarcimento)
- Duas leituras paralelas: fluxo de caixa (bruto) e saúde financeira (líquida, pós-ajustes)
- Alocação heurística de estornos/ressarcimentos à despesa correspondente (mesmo grupo e mês)
- Classificação retroativa de "Custo" (fixo/variável/sazonal) por categoria+subcategoria

**Dashboard**
- KPIs: despesas líquidas, receita de caixa, resultado de saúde, taxa de poupança, saldo acumulado no ano, saldo histórico
- Movimentações de reservas (aplicações/retiradas)
- Gráfico de evolução mensal e gráficos de pizza por categoria/subcategoria
- Gráfico de evolução da estrutura de custos

**Gráficos / Análise**
- KPIs de saúde financeira (poupança, meses negativos, maior categoria, desvio de orçamento, completude dos dados)
- Análise de Pareto (por categoria e subcategoria)
- Comparativo Orçado x Realizado
- Diagnóstico de qualidade dos dados (campos ausentes/pendências por lançamento)
- Gasto mensal no cartão de crédito

**Busca de lançamentos**
- Tabela filtrável por categoria, subcategoria, meio de pagamento, tipo, estrutura de custo, mês, caixinha, movimento de reserva e texto livre na descrição
- Resumo de totais do filtro aplicado (entradas, ajustes, saídas, despesas líquidas, saldo de caixa, resultado de saúde)

**Orçamentos**
- Renda base e percentual destinado ao orçamento
- Tabelas editáveis: Custos Fixos, Custos Variáveis, Sazonalidades, Investimentos
- Limites percentuais por tabela com validação (soma ≤ 100%) e indicadores visuais de alocação/estouro
- Categorias de custo derivadas automaticamente do CSV carregado
- Investimentos com itens fixos e itens customizáveis (adicionar/editar/excluir)
- Persistência com controle de concorrência otimista (revisão + fingerprint) e fallback de exportação/download quando o relatório é aberto via `file://`

**Estruturas de Custo (visão hierárquica)**
- Tabela hierárquica categoria pai > subcategoria com expand/collapse
- KPIs: orçado, realizado líquido, diferença, execução, itens acima do orçamento
- Drill-down direto para a aba Busca a partir de uma linha

**Persistência/backend local**
- Servidor HTTP local (127.0.0.1, porta efêmera) para salvar orçamentos sem reabrir o app
- Lock de arquivo com detecção de lock travado, escrita atômica e backup automático com restauração em caso de corrupção

**Interface desktop (Tkinter)**
- Fluxo guiado em 3 etapas (selecionar → gerar → abrir relatório) com log de progresso
- Reabertura de relatórios recentes e memória da última pasta/arquivos usados
- Launcher `.bat` para Windows com diagnóstico de ambiente e log de inicialização

**Relatório HTML**
- Filtro global de período (mês, intervalo personalizado, todos os meses) e modo de média
- Modo privacidade (ocultar/mostrar valores)
- Layout responsivo com tema próprio

---

# Plano de evolução — Finance App (offline → web hospedado)

Vou responder na ordem que você pediu: migração de arquitetura, redesenho de aquisição de dados, avaliação das analíticas, sugestões de orçamento/dashboard, e por fim o plano de ação com mockups visuais.

## 1) Migração para backend hospedado (Render) + banco (Supabase)

**Viável e faz sentido.** O código atual já está com boa separação (`core/` puro em pandas, `features/*` geram HTML, JS do relatório já usa `textContent`/`createElement` sem depender de framework) — isso reduz bastante o retrabalho.

**Stack sugerida:**

| Camada | Hoje | Proposto |
|---|---|---|
| Frontend | HTML gerado + JS vanilla embutido | Mesma base JS (reaproveitável), servida como SPA/PWA a partir do backend ou de um static host |
| Backend | Tkinter + `SimpleHTTPRequestHandler` local | **FastAPI** (Python) no **Render** — reaproveita quase 1:1 a lógica de `core/data_processor.py`, `budget_repository.py` (regras de negócio já são funções puras) |
| Banco | JSON + CSV em disco | **Supabase (Postgres)** — ganha Auth, Row Level Security, Storage e API REST automática (PostgREST) de graça |
| Auth | Nenhuma (app local) | **Supabase Auth** (email/senha ou magic link) — mesmo que hoje seja uso individual, desenhar o schema com `user_id` desde o início evita retrabalho se um dia vocês (casal/família) quiserem multiusuário |

**Por que essa combinação e não só Supabase Edge Functions:** a lógica de classificação (`classify_transactions`, alocação de estornos, retroatividade de custo) está em Python/pandas. Portar isso para Deno/TS (Edge Functions) seria reescrever tudo. Um serviço FastAPI no Render reaproveita o código Python quase direto, e o Supabase cobre banco+auth+storage. Fica um meio-termo pragmático.

**Estratégia de migração (strangler pattern):** o app desktop continua funcionando enquanto a API nova é construída em paralelo. Nada é "big bang".

## 2) Do CSV para formulário próprio

### 2.a / 2.b — Colunas do CSV: o que manter, o que descartar

O CSV original tinha 15 colunas:

```
Data; Sub Categoria; Categoria; Meio de Pagamento; Valor; Descrição;
Tipo do Pag / Movimento; Custo; Banco; Dia; Mês; Ano; Mês Texto; Caixinhas; Movimentação
```

| Coluna | Decisão | Motivo |
|---|---|---|
| `Data`, `Valor` | **Manter** | Núcleo da transação |
| `Categoria`, `Sub Categoria` | **Manter, mas virar tabelas** | Hoje é texto livre; vira FK para `categorias_pai`/`subcategorias` — elimina "Mercado" vs "mercado " vs "MERCADO" |
| `Tipo do Pag / Movimento` | **Manter, como vocabulário controlado** | Já é o campo que dirige toda a classificação (receita/despesa/estorno/aplicação/retirada) |
| `Meio de Pagamento` + `Banco` | **Fundir em uma entidade `contas`** | Hoje são dois campos de texto livre desacoplados; uma "conta" (ex: Nubank Cartão, Itaú Corrente) já carrega banco e tipo — evita redundância e abre caminho pro item 2.c |
| `Custo` (fixo/variável/sazonal) | **Manter, como tabela `estruturas_custo`** | É a base do orçamento e da aba Estruturas de Custo |
| `Descrição` | **Manter (opcional)** | Importante pra busca e auditoria |
| `Caixinhas` | **Manter, como tabela `caixinhas`** | Usado em aplicações/retiradas de reserva |
| `Movimentação` | **Descartar como campo separado** | É redundante com `Tipo do Pag/Movimento` (hoje o app já deriva "é reserva" cruzando os dois) — fundir num único vocabulário evita inconsistência |
| `Dia`, `Mês`, `Ano`, `Mês Texto` | **Descartar** | São 100% deriváveis de `Data` via SQL (`EXTRACT`). Armazenar isso separado é redundância pura e risco de dessincronia |

Resultado: de 15 colunas soltas → **~8 campos de negócio reais**, o resto vira metadado calculado ou entidade relacional.

### 2.c — Schema expansível para contas (cartão, corrente, reservas)

```
contas
├── id, nome, tipo_conta (corrente | cartao_credito | poupanca | caixinha | dinheiro | investimento)
├── banco_id (FK)
├── saldo_inicial, ativo
└── (cartão) dia_fechamento, dia_vencimento  ← já prepara fatura de cartão

transacoes
├── id, data, valor, descricao
├── conta_id (FK)                    ← de onde saiu/entrou
├── conta_destino_id (FK, nullable)  ← preparado para TRANSFERÊNCIAS entre contas
├── categoria_id, subcategoria_id (FK)
├── tipo_movimento (FK para tabela de vocabulário, não enum fixo em código)
├── estrutura_custo_id (FK, nullable)
├── caixinha_id (FK, nullable)
├── parcela_atual, parcela_total (nullable)  ← novo: compras parceladas
└── ajuste_de_transacao_id (FK, nullable)    ← formaliza o vínculo estorno→despesa que hoje é heurística
```

Desenhar assim desde já significa que "conta corrente", "cartão de crédito" e "reserva" não são casos especiais no código — são só linhas na tabela `contas` com `tipo_conta` diferente. Fatura de cartão, saldo consolidado por conta e transferência entre contas passam a ser possíveis sem reescrever o modelo depois.

> **Nota (implementação real):** `conta_destino_id` (transferências entre contas) não foi implementado — não existe hoje no schema real. `tipo_movimento` acabou como `enum`/`Literal` fixo no código (não uma tabela de vocabulário à parte), mais simples do que o proposto aqui. O resto do desenho (contas com `tipo_conta`, parcelamento, `ajuste_de_transacao_id`) foi implementado como descrito.

### 2.d — CRUD de categorias/subcategorias/bancos/caixinhas

Uma tela de "Configurações" com 4 abas simples (listar → adicionar → editar → **desativar**, nunca excluir de fato). O próprio `orcamentos.json` atual já usa esse padrão (`"ativo": true/false`) — só estender pra tudo. Isso evita quebrar transações históricas que referenciam uma categoria "excluída".

> **Nota (implementação real):** ficaram 3 abas (Contas/Categorias/Caixinhas) — "Bancos" não virou entidade própria, é campo de texto livre em Conta. O padrão ativo/inativo (nunca excluir) foi seguido à risca em tudo.

### 2.e — Migrar dados existentes sem conflito

1. Rodar um script único de migração sobre `historico_lancamentos.csv` + `orcamentos.json` (não sobre o CSV bruto — o histórico já é o resultado consolidado e deduplicado).
2. Normalizar texto (reaproveitar a função `_normalize_text` que já existe em `data_processor.py`) para agrupar variações e gerar as tabelas `categorias`, `subcategorias`, `contas`, `caixinhas` a partir dos valores distintos.
3. Manter o texto original bruto numa coluna de auditoria (`categoria_raw`) durante a transição, para conferência.
4. Reaproveitar o hash de deduplicação que já existe (`LedgerRepository.row_key`) como *unique constraint* no Postgres — se a migração rodar de novo, não duplica.
5. Gerar um relatório de dry-run antes de gravar (quantas categorias novas, quantas transações, quantos itens não mapeados) para você validar antes do commit definitivo.
6. Depois da migração, importação de CSV vira **opcional** (import assistido: extrato do banco → mapeamento para as categorias já existentes), não mais o único caminho de entrada.

> **Nota (implementação real):** esta fase (2) ainda não começou — é o gap "migração de dados do app antigo" do backlog atual. `hash_dedup` (o unique constraint de dedup) foi implementado desde a Entrega 1, pronto pra quando a migração acontecer.

### 2.f — Formulário intuitivo

- Campos mudam conforme o **tipo** selecionado (esconder "Caixinha" a menos que seja aplicação/retirada) — divulgação progressiva, não uma tela com 15 campos sempre visíveis.
- Categoria → Subcategoria em cascata, com opção "+ nova categoria" sem sair do formulário.
- Categorias mais usadas como chips de atalho (reduz digitação no dia a dia).
- Mobile-first — lançamento manual acontece no celular, não sentado no desktop.
- Aviso de possível duplicidade (mesmo valor+data+conta em minutos) para pegar double-tap.
- Modelos recorrentes ("Aluguel" todo dia 5) para reduzir digitação repetitiva.

> **Nota (implementação real):** feito — divulgação progressiva por tipo, categoria→subcategoria em cascata, mobile-first (barra inferior). Não feito: "+ nova categoria" inline, chips de mais usadas, aviso de duplicidade *no formulário* (existe dedup no backend, mas retorna erro 409 depois de tentar salvar, não um aviso preventivo), modelos recorrentes.

## 3) Avaliação das analíticas (Gráficos / Estruturas de Custo)

**O que já estava bom e devia ser mantido:** leitura dupla caixa×saúde, Pareto, orçado×realizado, diagnóstico de qualidade dos dados, visão hierárquica categoria pai→subcategoria. Um conjunto analítico maduro pra um app pessoal.

**Lacunas a preencher com o novo modelo relacional:**
- **Fatura de cartão por ciclo de fechamento**, não por mês calendário (hoje tudo é agrupado por mês civil, o que distorce gastos de cartão). ✅ *implementado*
- **Compras parceladas em aberto** — com `parcela_atual/parcela_total` dá pra mostrar "compromisso futuro" (quanto já está comprometido nos próximos meses). 🟡 *parcelamento existe; a visão de "compromisso futuro" agregada não*
- **Comparativo ano a ano (YoY)** por categoria — hoje só existe evolução mensal contínua. ⬜ *não implementado*
- **Saldo consolidado por conta / patrimônio** — só é possível com `contas` tendo saldo. ⬜ *não implementado — é o gap "saldo atual" já discutido*

## Sugestões extras que foram pedidas

### Orçamentos — mudar a forma de lançar?

Sim, sugeri evoluir de "tabela editável dentro do relatório HTML" para uma tela dedicada de Planejamento, mantendo o que funciona (% por bucket, limite ≤100%) e adicionando:
- Entrada tanto em **R$ quanto em %** (hoje só %, mas muita gente pensa em reais). ⬜
- Comparação **orçado × realizado × mês anterior** com seta de tendência. 🟡 *orçado×realizado existe no backend; "mês anterior" não*
- Orçamento "de envelope" (estilo YNAB): sobra do mês fica visível e pode ser realocada, em vez de simplesmente resetar. ✅ *implementado no backend (`saldo_anterior`, `próximo-mes`) — falta o frontend*
- Múltiplos templates de orçamento (mês normal vs. mês de dezembro/IPVA, por exemplo). ⬜

### Dashboard — adicionar / remover?

**Adicionar:**
- Patrimônio líquido / saldo por conta ⬜
- Compromissos futuros (parcelas em aberto + contas fixas do mês) ⬜
- Comparação com mês anterior / mesmo mês ano passado (variação %) ⬜
- Metas de economia com barra de progresso (ligadas às caixinhas) ⬜
- Top 5 maiores gastos do mês ⬜

**Simplificar/remover:**
- O card **"Saldo Histórico"** (soma bruta desde o primeiro lançamento) tende a virar um número gigante e pouco acionável com o tempo — sugeri mover para uma tela "Histórico" separada em vez de ocupar espaço nobre do dashboard. *(nota: o mockup visual que veio depois deste texto acabou colocando esse card de volta no topo do Dashboard — contradição entre este texto e o mockup; nenhum dos dois foi implementado ainda, então a decisão final está em aberto)*
- Hoje o dashboard mostra caixa e saúde financeira **simultaneamente** (6 cards + faixa de leitura) — sugeri um toggle "ver leitura de caixa / ver leitura de saúde" para reduzir a carga cognitiva, mantendo os dois disponíveis sem empilhar tudo. ⬜ *não implementado — os cards atuais misturam as duas leituras*

## Plano de ação (fases)

| Fase | Entrega | Duração estimada | Status |
|---|---|---|---|
| 0. Discovery | Modelo de dados final (ER), decisão de auth, setup Render+Supabase | 1 semana | ✅ |
| 1. Backend base | FastAPI no Render, schema no Supabase, RLS, portar `core/` | 1–2 semanas | ✅ |
| 2. Migração de dados | Script de normalização + dedup + relatório de validação | 3–5 dias | ⬜ |
| 3. Formulário web | Novo lançamento, CRUD categorias/contas/caixinhas | 1–2 semanas | ✅ |
| 4. Paridade analítica | Dashboard/Gráficos/Estruturas consumindo API em vez de JSON embutido | 1 semana | 🟡 backend pronto; frontend parcial (só Dashboard básico + Busca de Lançamentos; Estruturas de Custo sem tela) |
| 5. Novidades | Orçamento redesenhado, parcelas, fatura por ciclo, metas | 1–2 semanas | 🟡 parcelas e fatura por ciclo prontos; orçamento redesenhado sem tela; metas não iniciado |
| 6. Corte | Rodar os dois em paralelo, depois desligar o app desktop | — | ⬜ |

Esta tabela é a origem das "7 fases" citadas em `/status-projeto` (que usa nomes
ligeiramente diferentes pros mesmos marcos: infraestrutura viva = fases 0+1;
backend completo = fase 1; migração dos dados antigos = fase 2; lançamento +
cartão de crédito/PWA = fase 3; paridade analítica = fase 4; orçamento
redesenhado = fase 5; corte do app antigo = fase 6).
