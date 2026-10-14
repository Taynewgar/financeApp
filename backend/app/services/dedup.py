"""Hash determinístico para deduplicação idempotente de transações —
mesma ideia do LedgerRepository.row_key() do app antigo, adaptada ao
schema novo. Uma tentativa de criar duas vezes o "mesmo" lançamento
(mesmo usuário, data, valor, conta, tipo e posição na parcela) esbarra
na constraint UNIQUE de hash_dedup em vez de duplicar silenciosamente."""
from __future__ import annotations

import hashlib
import json
from typing import Any


def compute_hash(**fields: Any) -> str:
    encoded = json.dumps(fields, sort_keys=True, default=str, separators=(",", ":"))
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()
