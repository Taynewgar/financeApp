---
description: Roda a suíte offline aqui e imprime os comandos pra você rodar a integração real no seu terminal
---

Esta sessão (ambiente remoto) não tem `backend/.env` com credenciais reais
do Supabase — os testes de integração sempre ficam pulados aqui, então nem
tente rodá-los nesta sessão (rodar de novo só reproduz o mesmo skip, sem
sinal nenhum a mais). Só a suíte offline roda de fato aqui.

1. Rode a suíte offline do backend, na pasta `backend/`, usando o venv do
   projeto (`venv/bin/python -m pytest -q`, não `pytest` direto — evita o
   erro de "externally-managed-environment" do pip/venv). Use sempre
   `--tb=no` — sem ele, cada falha imprime o traceback completo (chega a
   dezenas de linhas por teste); com ele, só a seção final "short test
   summary info" aparece, uma linha por falha com o tipo de erro/mensagem,
   suficiente pra diagnosticar sem rolar a tela:

   `venv/bin/python -m pytest -q --tb=no`

   Depois de rodar, me diga:
   - Quantos passaram/falharam/skiparam
   - Se algum teste falhou, o nome do teste e a linha de erro (a própria
     saída de `--tb=no` já traz isso — só peça o traceback completo de um
     teste específico se a linha do resumo não for suficiente pra
     diagnosticar)

2. Ao final, **imprima os comandos abaixo** (não tente executá-los você
   mesmo) para o usuário copiar e rodar no terminal dele, onde
   `backend/.env` já está preenchido com as credenciais do Supabase —
   sempre com `--tb=no` também:

   ```bash
   cd backend
   source venv/bin/activate
   TEST_USER_EMAIL=teste@teste.com TEST_USER_PASSWORD=teste venv/bin/python -m pytest -q --tb=no
   ```

   Explique que o sinal de que rodou tudo certo é o total de `passed`
   dessa rodada bater com `passed + skipped` da rodada offline (ou seja,
   nenhum teste sobrou sem rodar).

   Se o usuário colar de volta uma saída com falhas do tipo `duplicate key
   value violates unique constraint "categorias_user_id_nome_key"` ou um
   `KeyError: 'id'` em cima de `orcamento["id"]`, a explicação padrão era
   "lixo de uma rodada anterior que não terminou de limpar" — mas em
   2026-09-24 isso foi descartado numa conta comprovadamente zerada antes
   da rodada (`limpar_dados_integracao.py --sim` confirmou "já está limpa
   (0 registros)" e o pytest imediatamente seguinte já saiu com essas
   mesmas 21 falhas). Ou seja: **não assuma mais que é lixo de rodada
   anterior sem confirmar primeiro** — peça pro usuário rodar
   `limpar_dados_integracao.py --sim` isolado e colar a saída; só se ela
   mostrar contagem > 0 antes de zerar é que a causa é leftover. Se a
   conta já estava zerada e a suíte falha do mesmo jeito assim que roda,
   é sinal de um problema real de isolamento entre testes dentro da
   própria suíte de integração (um teste anterior não limpou o que criou
   antes do próximo, no mesmo run) — investigar em vez de mandar
   limpar+reseed de novo, que não resolve.

   Se o usuário quiser popular a conta com dados de exemplo pra testar
   telas manualmente (não é isso que resolve o cenário de falha acima),
   a sequência é:

   ```bash
   cd backend
   source venv/bin/activate
   TEST_USER_EMAIL=teste@teste.com TEST_USER_PASSWORD=teste venv/bin/python tests/limpar_dados_integracao.py --sim
   TEST_USER_EMAIL=teste@teste.com TEST_USER_PASSWORD=teste venv/bin/python tests/seed_dados_teste.py
   TEST_USER_EMAIL=teste@teste.com TEST_USER_PASSWORD=teste venv/bin/python -m pytest -q --tb=no
   ```

   Avise que o passo de seed não recria nada que o usuário tenha
   configurado manualmente pela tela (ex: percentuais/limites do
   orçamento além dos itens que o próprio seed cria) — só o que o script
   povoa sozinho.

Se o venv não existir ainda ou o pip não estiver instalado nele, recrie com:
```bash
cd backend
python3 -m venv venv
source venv/bin/activate
venv/bin/python -m pip install -r requirements-dev.txt
```
