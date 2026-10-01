---
description: Relatório de status do projeto — andamento do redesign, funcionalidades implementadas e próximos passos
---

Gere um relatório de status do financeApp com exatamente estas 3 seções, nessa ordem:

1. **Andamento do redesign** — o que já foi feito e o que falta, comparado com as 7 fases combinadas no redesign (infraestrutura viva; backend completo; migração dos dados antigos; lançamento + cartão de crédito/PWA; paridade analítica; orçamento redesenhado; corte do app antigo). Seja honesto sobre o que está parcial (ex: lógica de backend pronta mas frontend/PWA ainda não existe).

2. **Funcionalidades já implementadas** — liste por recurso (contas, categorias, subcategorias, caixinhas, transações, orçamento, estrutura de custo, dashboard, busca de lançamentos, segurança/RLS, testes, infra de deploy), com o suficiente de detalhe pra lembrar o que cada uma faz sem precisar abrir o código.

3. **Plano para as próximas implementações** — próximos passos **em ordem de prioridade** (Alta, depois Média, depois Baixa), não por área nem por tela. Fonte: `docs/backlog.md`, seção "Pendente, por área" — esse arquivo está organizado por área e, dentro de cada área, por prioridade; para esta seção, achate isso numa lista única ordenada só por prioridade (dentro de um mesmo nível, mantenha a ordem em que os itens aparecem no backlog). Justifique brevemente cada item (por que importa, o que depende dele). Não omita a área de origem — cite entre parênteses (ex: "Dashboard", "Lançamentos") pra manter rastreável contra o backlog.

Antes de escrever, confira o estado real do código (não responda de memória): rode `git log --oneline -30` na raiz do repo, liste os routers em `backend/app/routers/`, leia o `README.md` e leia `docs/backlog.md` por inteiro (é a fonte de verdade da seção 3) — a lista de endpoints, funcionalidades e pendências deve refletir o que existe de fato no branch atual e no backlog, não o que foi discutido em conversas anteriores. Se algo foi combinado em conversa mas ainda não foi implementado nem registrado no backlog, deixe isso claro na seção 3, não na 2.

Formato: direto, sem headers em excesso, do jeito que já vinha sendo respondido nas conversas anteriores sobre isso.
