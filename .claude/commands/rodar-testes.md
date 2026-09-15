---
description: Roda a suíte offline aqui e imprime os comandos pra você rodar a integração real no seu terminal
---

Esta sessão (ambiente remoto) não tem `backend/.env` com credenciais reais
do Supabase — os testes de integração sempre ficam pulados aqui, então nem
tente rodá-los nesta sessão (rodar de novo só reproduz o mesmo skip, sem
sinal nenhum a mais). Só a suíte offline roda de fato aqui.

1. Rode a suíte offline do backend, na pasta `backend/`, usando o venv do
   projeto (`venv/bin/python -m pytest -q`, não `pytest` direto — evita o
   erro de "externally-managed-environment" do pip/venv):

   `venv/bin/python -m pytest -q`

   Depois de rodar, me diga:
   - Quantos passaram/falharam/skiparam
   - Se algum teste falhou, o nome do teste e a mensagem de erro completa

2. Ao final, **imprima os comandos abaixo** (não tente executá-los você
   mesmo) para o usuário copiar e rodar no terminal dele, onde
   `backend/.env` já está preenchido com as credenciais do Supabase:

   ```bash
   cd backend
   source venv/bin/activate
   TEST_USER_EMAIL=teste@teste.com TEST_USER_PASSWORD=teste venv/bin/python -m pytest -q
   ```

   Explique que o sinal de que rodou tudo certo é o total de `passed`
   dessa rodada bater com `passed + skipped` da rodada offline (ou seja,
   nenhum teste sobrou sem rodar).

Se o venv não existir ainda ou o pip não estiver instalado nele, recrie com:
```bash
cd backend
python3 -m venv venv
source venv/bin/activate
venv/bin/python -m pip install -r requirements-dev.txt
```
