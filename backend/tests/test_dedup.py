from app.services.dedup import compute_hash


def test_mesmos_campos_geram_o_mesmo_hash():
    a = compute_hash(user_id="u1", valor=10, data_compra="2026-08-05")
    b = compute_hash(user_id="u1", valor=10, data_compra="2026-08-05")
    assert a == b


def test_ordem_dos_campos_nao_altera_o_hash():
    a = compute_hash(valor=10, user_id="u1", data_compra="2026-08-05")
    b = compute_hash(data_compra="2026-08-05", user_id="u1", valor=10)
    assert a == b


def test_campo_diferente_gera_hash_diferente():
    a = compute_hash(user_id="u1", valor=10, data_compra="2026-08-05")
    b = compute_hash(user_id="u1", valor=11, data_compra="2026-08-05")
    assert a != b
