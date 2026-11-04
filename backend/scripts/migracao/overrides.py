"""Persistência das respostas do fluxo interativo de estrutura de custo
(docs/backlog.md, "Fluxo interativo do dry-run") — fica fora do git (é
dado financeiro pessoal, não código), permite reexecutar o dry-run sem
perguntar de novo o que já foi respondido."""
from __future__ import annotations

import json
from pathlib import Path

from app.services.dedup import compute_hash

from .parsing import Lancamento

CAMINHO_PADRAO = Path(__file__).resolve().parent.parent / "migracao_overrides.json"

_OPCOES: dict[str, str | None] = {"f": "fixo", "v": "variavel", "s": "sazonal", "p": None}


def chave_linha(lancamento: Lancamento) -> str:
    """Hash estável da linha (mesma técnica do hash_dedup do app, mas
    sem user_id nem campos que mudam entre rodadas) — só serve pra
    indexar a resposta no arquivo de overrides, nunca é gravado no
    banco."""
    return compute_hash(
        data=lancamento.data.isoformat(),
        valor=lancamento.valor,
        descricao=lancamento.descricao,
        categoria=lancamento.categoria,
        subcategoria=lancamento.subcategoria,
        banco=lancamento.banco,
    )


def carregar(caminho: Path = CAMINHO_PADRAO) -> dict[str, str | None]:
    if not caminho.exists():
        return {}
    return json.loads(caminho.read_text(encoding="utf-8"))


def salvar(overrides: dict[str, str | None], caminho: Path = CAMINHO_PADRAO) -> None:
    caminho.write_text(json.dumps(overrides, indent=2, ensure_ascii=False, sort_keys=True), encoding="utf-8")


def perguntar_pendentes(
    pendentes: list[Lancamento],
    overrides: dict[str, str | None],
    caminho: Path = CAMINHO_PADRAO,
) -> dict[str, str | None]:
    """Pra cada lançamento em `pendentes` que ainda não tem resposta
    salva, pergunta no terminal e persiste a resposta antes de seguir
    pro próximo — interromper no meio (Ctrl+C) não perde o que já foi
    respondido, porque salva a cada resposta, não só no final."""
    restantes = [l for l in pendentes if chave_linha(l) not in overrides]
    if not restantes:
        return overrides

    print(f"\n{len(restantes)} lançamento(s) sem estrutura de custo resolvida — responda um a um:")
    for i, lancamento in enumerate(restantes, start=1):
        chave = chave_linha(lancamento)
        print(f"\n[{i}/{len(restantes)}] {lancamento.data:%d/%m/%Y}  R$ {abs(lancamento.valor):.2f}  "
              f"{lancamento.categoria}/{lancamento.subcategoria}")
        print(f"  {lancamento.descricao}")
        while True:
            resposta = input("  [F]ixo / [V]ariável / [S]azonal / [P]ular: ").strip().lower()
            if resposta[:1] in _OPCOES:
                overrides[chave] = _OPCOES[resposta[:1]]
                salvar(overrides, caminho)
                break
            print("  Resposta não reconhecida, tente de novo.")
    return overrides
