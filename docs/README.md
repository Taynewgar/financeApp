# Documentação de planejamento — índice

Ponto de entrada único para entender **o que foi decidido, por que, e o que
disso já existe de verdade no código**. Escrito para ser confiável em
qualquer conversa nova (aqui ou em outra sessão) sem precisar reconstruir
contexto perdido — cada afirmação de status abaixo foi conferida contra o
código real, não contra memória de conversa.

## Ordem de leitura recomendada

1. **`plano-de-evolucao-original.md`** — o ponto de partida. Auditoria do
   ZIP do app antigo (arquitetura, segurança, funcionalidades) + o plano de
   migração original (schema, fases, stack). Escrito *antes* de qualquer
   mockup ou linha de código da versão web.
2. **`redesign-proposta-original.md`** — os 4 mockups visuais que vieram
   logo depois (imagens em `docs/mockups/`), com uma tabela **tela por
   tela** comparando o que o mockup propôs × o que existe hoje no código,
   mais o **changelog cronológico** de cada rodada de mudança entregue.
   É o documento mais vivo dos três — atualizado a cada entrega.
3. **`sugestoes-e-decisoes-do-redesign.md`** — a rodada de perguntas e
   respostas que aconteceu logo depois dos mockups, onde várias decisões
   do plano original foram corrigidas ou refinadas (16 pontos, cada um com
   pergunta original, resposta, e status atual).

## Onde encontrar o quê

| Pergunta | Documento |
|---|---|
| "Por que a arquitetura é FastAPI + Supabase?" | `plano-de-evolucao-original.md`, seção 1 |
| "O que o app antigo já fazia, que não pode se perder (paridade)?" | `plano-de-evolucao-original.md`, "Funcionalidades já implementadas" |
| "Como era o mockup dessa tela? O que já foi implementado dela?" | `redesign-proposta-original.md` (uma seção por tela) + `docs/mockups/*.png` |
| "Essa decisão de design mudou depois do mockup? Por quê?" | `sugestoes-e-decisoes-do-redesign.md` (16 pontos numerados) |
| "O que foi entregue em cada rodada, em ordem cronológica?" | `redesign-proposta-original.md`, seção "Changelog deste documento" |
| "O que está registrado pra decidir depois, mas ainda não foi?" | `redesign-proposta-original.md`, seção "Backlog registrado" |
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
privacidade (ícone de olho, um por tela, ao lado do seletor de mês/título).
Ainda faltam: PWA offline com fila de sincronização, busca/comando rápido
(Cmd+K), alertas/notificações.

Este resumo é um retrato rápido — pra qualquer detalhe, a tabela tela a
tela de `redesign-proposta-original.md` é a fonte de verdade (é ela que é
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
`redesign-proposta-original.md`, junto da tabela comparando proposto ×
implementado. Não existe mockup próprio para Estruturas de Custo (não foi
desenhada nos 4 originais — ver nota na seção correspondente daquele
documento).

## Como manter isso confiável

Regra usada até aqui, e que deve continuar: **toda entrega nova ganha uma
entrada de changelog em `redesign-proposta-original.md`** (data + o que foi
pedido + o que foi entregue + o que ficou de fora e por quê), e as tabelas
"proposto × status" são reescritas por cima (o changelog é o histórico,
as tabelas são sempre o estado atual, nunca acumulam entradas antigas).
Quando uma rodada de conversa **corrige ou refina** uma decisão já registrada
em `sugestoes-e-decisoes-do-redesign.md`, atualiza-se o `> **Status:**` daquele
ponto em vez de duplicar a pergunta. Este índice (`docs/README.md`) só
precisa mudar quando uma tela muda de status geral (placeholder → entregue)
ou quando um novo documento de planejamento é criado.

## Revisão de consistência — 2026-09-15

Auditoria pedida pelo usuário, percorrendo a conversa desde o início pra
confirmar que os 3 documentos ainda batem entre si e com o código.
Inconsistências encontradas e corrigidas nesta rodada:

- `redesign-proposta-original.md`: item 2 do "Resumo de prioridades" datava
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
- Nenhuma decisão registrada em `sugestoes-e-decisoes-do-redesign.md` (os
  16 pontos) foi revertida ou contradita em rodada nenhuma — as decisões
  descritas lá (divisão Planejamento/Estrutura de Custo, versionamento por
  mês em vez de templates, `estrutura_custo_padrao` na subcategoria, etc.)
  seguem exatamente como implementadas. Conferido item a item contra o
  código e contra `redesign-proposta-original.md`.
- Este documento (`docs/README.md`) não existia antes desta rodada — criado
  porque os 3 documentos, embora cada um internamente consistente, exigiam
  ler os três inteiros para montar o quadro geral. Não substitui nenhum
  deles, só aponta pra eles.
