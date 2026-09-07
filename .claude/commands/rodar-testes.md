---
description: Roda a suíte de testes completa (offline + integração real) e confere se bate o esperado
---

Rode a suíte de testes do backend, na pasta `backend/`, usando o venv do projeto (`venv/bin/python -m pytest -q`, não `pytest` direto — evita o erro de "externally-managed-environment" do pip/venv):

1. Offline: `venv/bin/python -m pytest -q`
2. Integração real (toca o Supabase): `TEST_USER_EMAIL=teste@teste.com TEST_USER_PASSWORD=teste venv/bin/python -m pytest -q`

Depois de rodar, me diga:
- Quantos passaram/falharam em cada rodada
- Se algum teste falhou, o nome do teste e a mensagem de erro completa
- Confirme se o total da rodada de integração bate com offline + skipped da rodada anterior (esse é o sinal de que nada ficou faltando rodar)

Se o venv não existir ainda ou o pip não estiver instalado nele, recrie com:
```bash
cd backend
python3 -m venv venv
source venv/bin/activate
venv/bin/python -m pip install -r requirements-dev.txt
```
