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
   `KeyError: 'id'` em cima de `orcamento["id"]`, é lixo de uma rodada
   anterior (ou de uso manual do app na mesma conta de teste) que não foi
   limpo — confirmado em 2026-09-24: uma conta com 76 transações, 15
   categorias e 4 orçamentos acumulados quebrava a suíte inteira; rodando
   `limpar_dados_integracao.py --sim` **imediatamente antes** do pytest
   (mesmo terminal, sem nada no meio) resolveu de cara. O detalhe que
   importa é a **sequência, não só a limpeza em algum momento anterior da
   sessão** — uso manual do app (Planejamento, Configurações, etc.) ou o
   script de seed realimentam a mesma conta entre uma limpeza e a
   próxima, então uma limpeza de horas atrás não garante nada. Sempre
   passe a sequência limpar→pytest como um bloco só, nessa ordem, sem
   comandos entre os dois:

   ```bash
   cd backend
   source venv/bin/activate
   TEST_USER_EMAIL=teste@teste.com TEST_USER_PASSWORD=teste venv/bin/python tests/limpar_dados_integracao.py --sim
   TEST_USER_EMAIL=teste@teste.com TEST_USER_PASSWORD=teste venv/bin/python -m pytest -q --tb=no
   ```

   Se AINDA assim falhar do mesmo jeito logo depois de uma limpeza que
   confirmou "já está limpa (0 registros)", isso sim seria inesperado —
   peça a saída completa do `limpar_dados_integracao.py --sim` (as
   contagens antes de zerar) junto com o pytest, pra conferir se as duas
   rodaram mesmo na mesma conta/ambiente (ex: `.env` apontando pro
   projeto Supabase certo, mesmo checkout do repo).

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
