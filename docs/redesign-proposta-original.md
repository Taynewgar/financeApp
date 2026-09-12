# Proposta original do redesign — o que foi combinado x o que existe hoje

Este documento existe pra não perder o que foi desenhado no início do projeto,
quando o ZIP do app antigo (`v6_Estrutura_de_custos.zip`, Tkinter + relatório
HTML local) foi analisado e viraram 4 mockups de tela. Serve de referência pra
continuar o trabalho sem precisar redescobrir o que já foi decidido.

**Fonte:** artifact de design "Finance App Redesign", publicado a partir da
análise do ZIP original —
[ver mockups](https://claude.ai/code/artifact/aca7d916-7ef2-4b93-b482-bce337d343ed).
O ZIP em si não está neste repositório (foi um anexo de conversa, não um
arquivo versionado) — se quiser preservá-lo de forma durável, vale anexar de
novo e commitar num lugar como `docs/app-original/`.

Cada seção abaixo lista o que o mockup propôs, o que existe hoje (código real,
não memória — conferido nos routers/telas na data deste documento) e o que
falta. Legenda: ✅ implementado · 🟡 parcial · ⬜ não implementado.

---

## Dashboard

Mockup: número de patrimônio no topo, seletor de mês com opções de intervalo,
alternância entre as duas leituras financeiras, KPIs com variação percentual
vs mês anterior, saldo por conta, compromissos futuros, evolução de 3 séries,
e despesas por categoria do mês.

| Proposto no mockup | Status | Observação |
|---|---|---|
| Saldo histórico / patrimônio total (topo, "desde jan/2019") | ⬜ | Não existe endpoint de saldo atual ainda (só `saldo_inicial` estático em `Conta`) |
| Seletor de mês | ✅ | `<input type="month">` |
| Intervalo (Todos os meses / mês específico) | ⬜ | Só dá pra ver 1 mês por vez |
| Base da média (Até o mês / Todos os meses) | ⬜ | Não existe esse conceito na tela |
| Alternância "Leitura de Caixa" / "Leitura de Saúde" | ⬜ | As duas leituras aparecem juntas nos cards, não como toggle |
| KPI: Despesas Líquidas, Receita, Resultado de Saúde, Taxa de Poupança | ✅ | Implementado como cards + número principal (hero) |
| Delta de cada KPI vs mês anterior (ex: "6,2% vs mês anterior") | ⬜ | Cards mostram só o valor absoluto do mês, sem comparação |
| Taxa de poupança acumulada no ano | ⬜ | Backend calcula acumulado em `/dashboard/evolucao` (`taxa_poupanca_acumulada`), mas o Dashboard não expõe isso ainda |
| Patrimônio por conta (saldo de cada conta/caixinha/fatura) | ⬜ | Mesma dependência do saldo atual acima |
| Compromissos futuros (parcelas futuras, fixos recorrentes) | ⬜ | Feature nova, nada implementado (nem backend) |
| Evolução mensal — 3 linhas (Receita/Despesa/Resultado) | 🟡 | Implementado com 2 linhas (Receita/Despesa); falta a linha de Resultado |
| Despesas por categoria do mês (% por categoria) | ⬜ | Existe conceito parecido na Estrutura de Custo (por bucket, não por categoria), que também não tem frontend ainda |

**Arquivo:** `frontend/src/routes/Dashboard.tsx`, `frontend/src/components/EvolucaoChart.tsx`.

---

## Novo Lançamento

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

Ordenado por (a) o que já tem backend pronto — custo baixo de fechar — antes
do que exige feature nova:

1. Delta vs mês anterior nos KPIs do Dashboard (dado já existe, é reprocessar).
2. Tela de Planejamento (motor de orçamento já pronto no backend).
3. Tela de Estrutura de Custo (motor já pronto no backend).
4. Endpoint + UI de saldo atual por conta/caixinha (destrava "Patrimônio por
   Conta" no Dashboard e a coluna de saldo em Configurações de uma vez).
5. Linha de Resultado na Evolução Mensal (ajuste pequeno no gráfico existente).
6. Categorias "mais usadas" + criação inline no Novo Lançamento.
7. Compromissos futuros no Dashboard (feature nova, maior escopo).
8. Aba Bancos em Configurações (baixa prioridade — hoje resolvido como campo
   de texto em Conta, sem perda funcional real).

Este documento não substitui o `README.md` (que descreve o que existe) nem o
`/status-projeto` (relatório de andamento) — é o registro do que foi
*proposto*, pra comparar contra o que foi *decidido mudar* ao longo do
desenvolvimento real.
