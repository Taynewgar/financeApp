# Documentação de planejamento — índice

Ponto de entrada único para entender **o que foi decidido, por que, o que
disso já existe de verdade no código, e o que vem a seguir**. Escrito para
ser confiável em qualquer conversa nova (aqui ou em outra sessão) sem
precisar reconstruir contexto perdido — cada afirmação de status abaixo foi
conferida contra o código real, não contra memória de conversa.

**Os 4 arquivos deste diretório, o que cada um É:**

| Arquivo | O que é | Quando muda |
|---|---|---|
| `backlog.md` | **A lista de trabalho.** O que vem a seguir, em ordem de prioridade, e os itens registrados pra decidir depois (com detalhe técnico de cada um). | Toda vez que uma prioridade muda, um item novo é registrado, ou um item do backlog é entregue (some daqui, vira changelog no arquivo abaixo). |
| `changelog-proposta-original-do-redesign.md` | **O histórico de decisão tela a tela.** Mockup × o que existe hoje, tela por tela, mais o changelog cronológico de cada rodada de entrega. | A cada entrega (changelog novo) ou quando uma tabela "proposto × status" precisa ser corrigida. |
| `sugestoes-e-decisoes-do-redesign.md` | **O porquê das decisões de design.** 16 pontos de pergunta-resposta que refinaram o plano original logo depois dos mockups. | Raramente — só quando uma decisão registrada aqui é revisitada/corrigida. |
| `plano-de-evolucao-original.md` | **O ponto de partida.** Auditoria do ZIP do app antigo + plano de migração original, escrito antes de qualquer mockup. | Quase nunca — é o documento mais "congelado", histórico puro. |

Se você só tem uma pergunta — "o que fazer a seguir?" — a resposta está em
`backlog.md`. Os outros 3 existem pra explicar *por que* o backlog e o
código estão do jeito que estão.

## Onde encontrar o quê

| Pergunta | Documento |
|---|---|
| "O que fazer a seguir? Qual a prioridade?" | `backlog.md`, "Ordem de prioridade atual" |
| "Por que a arquitetura é FastAPI + Supabase?" | `plano-de-evolucao-original.md`, seção 1 |
| "O que o app antigo já fazia, que não pode se perder (paridade)?" | `plano-de-evolucao-original.md`, "Funcionalidades já implementadas" |
| "Como era o mockup dessa tela? O que já foi implementado dela?" | `changelog-proposta-original-do-redesign.md` (uma seção por tela) + `docs/mockups/*.png` |
| "Essa decisão de design mudou depois do mockup? Por quê?" | `sugestoes-e-decisoes-do-redesign.md` (16 pontos numerados) |
| "O que foi entregue em cada rodada, em ordem cronológica?" | `changelog-proposta-original-do-redesign.md`, seção "Changelog deste documento" |
| "O que está registrado pra decidir depois, mas ainda não foi?" | `backlog.md`, "Detalhamento dos itens maiores" |
| "A aba 'Gráficos' do app antigo tinha o quê, e o que disso ainda falta?" | `changelog-proposta-original-do-redesign.md`, seção "Gráficos / Análise" |
| "O que existe no código *agora*, tecnicamente?" | `README.md` (raiz do repo) — não duplica decisão/histórico, só descreve o que está implementado |
| "Qual o andamento geral / relatório de status?" | skill `/status-projeto` |

## Estado atual em uma tabela (resumo de leitura rápida)

Telas do frontend, na ordem do menu:

| Tela | Status | Detalhe |
|---|---|---|
| Dashboard | 🟡 rico, mas incompleto | Caixa/Saúde, deltas, patrimônio (só caixinhas), compromissos futuros (só parcelas), evolução 3 séries, despesas por categoria. Falta: patrimônio por conta, "base da média" funcional, saldo histórico no topo |
| Lançamentos | ✅ | Busca/filtro/edição completos |
| Novo Lançamento | 🟡 | 5 tipos completos; falta categorias "mais usadas" + criação inline |
| Planejamento | ✅ *(entregue 2026-09-14)* | Configuração do orçamento (renda, % por bucket, itens reativos a partir dos lançamentos, modo envelope). **Por decisão:** não mostra orçado×realizado nem mês anterior — isso é escopo da Estrutura de Custo |
| Estruturas de Custo | ⬜ | **Próxima prioridade.** Motor já pronto no backend (`GET /estrutura-custo/{mes}`), só falta a tela |
| Configurações | ✅ | Contas/Categorias+Subcategorias/Caixinhas — "Bancos" não virou aba própria (decisão: campo texto em Conta) |

Melhorias globais de UX já entregues: tema claro/escuro automático, nav
mobile (barra inferior), botão flutuante de novo lançamento, modo
privacidade (ícone de olho, global na casca do app — sidebar no desktop,
faixa fina no topo no mobile — acessível em toda tela, não mais por
tela). Ainda faltam: PWA offline com fila de sincronização, busca/comando
rápido (Cmd+K), alertas/notificações.

Este resumo é um retrato rápido — pra qualquer detalhe, a tabela tela a
tela de `changelog-proposta-original-do-redesign.md` é a fonte de verdade (é ela que é
atualizada a cada entrega; este índice é revisado com menos frequência).

## Mockups

As 4 telas originais do redesign (Dashboard, Novo Lançamento, Configurações,
Planejamento) estão versionadas como PNG em `docs/mockups/` — não dependem
de login nem do artifact original continuar acessível:

- `docs/mockups/dashboard.png`
- `docs/mockups/novo-lancamento.png`
- `docs/mockups/contas-categorias.png`
- `docs/mockups/planejamento.png`

Cada uma é referenciada inline na seção correspondente de
`changelog-proposta-original-do-redesign.md`, junto da tabela comparando proposto ×
implementado. Não existe mockup próprio para Estruturas de Custo (não foi
desenhada nos 4 originais — ver nota na seção correspondente daquele
documento).

Mockups feitos depois (via Artifact Design, canvas interativo) seguem o
mesmo princípio — versionados como PNG aqui pelo mesmo motivo (não
depender do artifact original continuar acessível), referenciados
inline na seção da rodada correspondente:

- `rodada23-*.png` (9 arquivos) — 2 rodadas de decisão de cabeçalho
  fixo/barra lateral (Rodada 23): comparação de alternativas
  (`opcaoA-cabecalho-titulo-secao`, `opcaoB-botao-ciclar-descartada`,
  `sidebar-fixa`) + o controle real aprovado por tela
  (`lancamentos-desktop-filtro-fixo`, `lancamentos-mobile-filtro-fixo`,
  `graficos-seletor-fixo`, `estrutura-custo-cabecalho-fixo`,
  `planejamento-cabecalho-fixo`, `dashboard-cabecalho-fixo`).
- `rodada26-meses-pulados-*.png` (2 arquivos) — as 2 opções comparadas
  pra agrupar a lista de meses pulados (Rodada 26); `opcaoA-acordeao-
  escolhida` foi a decisão do usuário.

## Como manter isso confiável

Regra usada até aqui, e que deve continuar: **toda entrega nova ganha uma
entrada de changelog em `changelog-proposta-original-do-redesign.md`** (data + o que foi
pedido + o que foi entregue + o que ficou de fora e por quê), e as tabelas
"proposto × status" são reescritas por cima (o changelog é o histórico,
as tabelas são sempre o estado atual, nunca acumulam entradas antigas).
Quando uma rodada de conversa **corrige ou refina** uma decisão já registrada
em `sugestoes-e-decisoes-do-redesign.md`, atualiza-se o `> **Status:**` daquele
ponto em vez de duplicar a pergunta. Este índice (`docs/README.md`) só
precisa mudar quando uma tela muda de status geral (placeholder → entregue)
ou quando um novo documento de planejamento é criado.

**Regra do backlog** (`backlog.md`, desde 2026-09-15): item novo discutido e
registrado "pra decidir depois" entra na "Ordem de prioridade atual" (linha
numerada) e, se tiver detalhe técnico real (motivo, opções, recomendação),
ganha uma subseção em "Detalhamento dos itens maiores". Quando um item é
entregue, sai do backlog (fica só como linha riscada `~~...~~` **feito
DATA** na ordem de prioridade, ou remove-se de vez se a lista ficar longa
demais) e a entrega em si vira uma entrada de changelog em
`changelog-proposta-original-do-redesign.md` — o backlog nunca guarda histórico do que
já foi feito, só o que falta.

## Revisão de consistência — 2026-09-15

Auditoria pedida pelo usuário, percorrendo a conversa desde o início pra
confirmar que os 3 documentos ainda batem entre si e com o código.
Inconsistências encontradas e corrigidas nesta rodada:

- `changelog-proposta-original-do-redesign.md`: item 2 do "Resumo de prioridades" datava
  a entrega da tela de Planejamento em 2026-09-13; o changelog (fonte de
  verdade) registra 2026-09-14. Corrigido.
- `plano-de-evolucao-original.md`: a linha sobre "orçamento de envelope"
  ainda dizia "falta o frontend" — desatualizado desde a entrega da tela de
  Planejamento (2026-09-14), que já mostra a sobra por item. Corrigido.
- `plano-de-evolucao-original.md`: a tabela de fases (Fase 4 e Fase 5)
  ainda descrevia o Dashboard como "básico" e o orçamento redesenhado como
  "sem tela" — ambos defasados por várias rodadas de entrega. Corrigido.
- `README.md` (raiz do repo): ainda listava Planejamento como placeholder,
  o que deixaria qualquer sessão nova com uma leitura errada do estado do
  projeto. Corrigido.
- `sugestoes-e-decisoes-do-redesign.md`: passou batido na primeira rodada
  desta auditoria e só foi pego numa segunda comparação, pedida pelo
  usuário, direto contra a conversa — a tabela da seção 16 ("Divisão final
  em 7 entregas") ainda dizia, na linha da Entrega 6, "tela de Planejamento
  [...] não". Corrigido; a mesma seção também teve o status do orçamento de
  envelope (seção 9) precisado — dizia "implementado no backend", sem
  registrar que a tela de Planejamento já mostra a sobra por item.
- Nenhuma **decisão** registrada em `sugestoes-e-decisoes-do-redesign.md`
  (os 16 pontos) foi revertida ou contradita em rodada nenhuma — as
  decisões em si (divisão Planejamento/Estrutura de Custo, versionamento
  por mês em vez de templates, `estrutura_custo_padrao` na subcategoria,
  etc.) seguem exatamente como implementadas. O que ficou pra trás foram
  só os campos `> Status:` de acompanhamento (texto descritivo, não a
  decisão em si) desatualizados depois da entrega de 2026-09-14 — ponto
  já coberto acima.
- Este documento (`docs/README.md`) não existia antes desta rodada — criado
  porque os 3 documentos, embora cada um internamente consistente, exigiam
  ler os três inteiros para montar o quadro geral. Não substitui nenhum
  deles, só aponta pra eles.

## Gap registrado — aba "Gráficos" do app original (2026-09-15)

O usuário apontou que a aba **Gráficos** do app antigo (ZIP original, ainda
disponível na conversa) nunca foi mencionada em nenhum documento do
redesign — não virou mockup, não virou backlog. Reli o código-fonte
(`features/graficos/graficos_html.py` + `assets/report_scripts.js`, não só
a memória já documentada) e registrei a comparação completa, feature a
feature, em `changelog-proposta-original-do-redesign.md` (seção "Gráficos / Análise").

Não recomendei adoção 1:1 de tudo — o achado real é o **Pareto de despesas
por categoria/subcategoria** (capacidade genuinamente ausente hoje, sem
equivalente parcial), agora no backlog. Um item ("Escopo da evolução"
local) foi avaliado e não recomendado, por sobrepor o que o seletor de
período global do Dashboard já resolve. Um outro ("Gasto mensal no cartão
de crédito") era código morto no próprio app original, não uma
funcionalidade perdida — correção feita em `plano-de-evolucao-original.md`.
