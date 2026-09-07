---
description: Relatório de status do projeto — andamento do redesign, funcionalidades implementadas e próximos passos
---

Gere um relatório de status do financeApp com exatamente estas 3 seções, nessa ordem:

1. **Andamento do redesign** — o que já foi feito e o que falta, comparado com as 7 fases combinadas no redesign (infraestrutura viva; backend completo; migração dos dados antigos; lançamento + cartão de crédito/PWA; paridade analítica; orçamento redesenhado; corte do app antigo). Seja honesto sobre o que está parcial (ex: lógica de backend pronta mas frontend/PWA ainda não existe).

2. **Funcionalidades já implementadas** — liste por recurso (contas, categorias, subcategorias, caixinhas, transações, orçamento, estrutura de custo, dashboard, busca de lançamentos, segurança/RLS, testes, infra de deploy), com o suficiente de detalhe pra lembrar o que cada uma faz sem precisar abrir o código.

3. **Plano para as próximas implementações** — lista ordenada e justificada do que falta, refletindo o que está pendente/combinado até agora (ex: frontend/PWA, saldo atual de contas/caixinhas, migração de dados, gráficos dedicados, reconciliação de fatura, refinamentos de orçamento).

Antes de escrever, confira o estado real do código (não responda de memória): rode `git log --oneline -30` na raiz do repo, liste os routers em `backend/app/routers/`, e leia o `README.md` — a lista de endpoints e funcionalidades deve refletir o que existe de fato no branch atual, não o que foi discutido em conversas anteriores. Se algo foi combinado em conversa mas ainda não foi implementado, deixe isso claro na seção 3, não na 2.

Formato: direto, sem headers em excesso, do jeito que já vinha sendo respondido nas conversas anteriores sobre isso.
