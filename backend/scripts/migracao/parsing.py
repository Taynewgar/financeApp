"""Leitura e parsing bruto dos 3 CSVs de origem — só conversão de string
pra tipos Python, sem nenhuma regra de negócio (isso mora em
mapeamento.py e parcelas.py). Nenhum dos 3 CSVs é commitado no repo
(dado financeiro pessoal) — os caminhos vêm sempre por argumento de
linha de comando."""
from __future__ import annotations

import csv
from dataclasses import dataclass, field
from datetime import date, datetime
from pathlib import Path

# categoria-pai que é, na verdade, a lista de meios de pagamento do app
# antigo disfarçada de categoria — nenhum lançamento a usa de verdade
# (ver docs/backlog.md, "Migração de dados do app antigo")
CATEGORIA_FORMA_PAGAMENTO = "Forma de Pagamento"


@dataclass
class Lancamento:
    """Uma linha do CSV principal, já com tipos Python — 1:1 com as
    colunas do arquivo, nenhuma tradução pro vocabulário do app ainda."""

    data: date
    valor: float
    descricao: str
    categoria: str
    subcategoria: str
    meio_pagamento: str
    tipo_pag_movimento: str
    custo: str
    banco: str
    caixinha: str
    movimentacao: str


def parse_valor(bruto: str) -> float:
    """'R$ 1.234,56' / '-R$ 44,09' / '20,58' -> float. O sinal (usado só
    em Estorno) é preservado aqui; normalizar pra abs() é regra de
    negócio, fica em mapeamento.py."""
    texto = bruto.replace("R$", "").replace(" ", "").strip()
    texto = texto.replace(".", "").replace(",", ".")
    return float(texto)


def parse_data(bruto: str) -> date:
    return datetime.strptime(bruto.strip(), "%d/%m/%Y").date()


def _campo(linha: dict[str, str], nome: str) -> str:
    return linha.get(nome, "").strip()


def carregar_lancamentos(caminho: str | Path) -> list[Lancamento]:
    """Lê o CSV principal. Ignora linhas sem `Data` preenchida — sobra de
    template da planilha original (`Categoria: Preencher`, milhares de
    linhas em branco no fim do arquivo), não são lançamentos de verdade."""
    with Path(caminho).open(encoding="utf-8-sig", newline="") as f:
        amostra = f.read(4096)
        f.seek(0)
        delimitador = csv.Sniffer().sniff(amostra, delimiters=";,").delimiter
        linhas_brutas = list(csv.DictReader(f, delimiter=delimitador))

    lancamentos = []
    for bruta in linhas_brutas:
        if not _campo(bruta, "Data"):
            continue
        lancamentos.append(
            Lancamento(
                data=parse_data(bruta["Data"]),
                valor=parse_valor(bruta["Valor"]),
                descricao=_campo(bruta, "Descrição"),
                categoria=_campo(bruta, "Categoria"),
                subcategoria=_campo(bruta, "Sub Categoria"),
                meio_pagamento=_campo(bruta, "Meio de Pagamento"),
                tipo_pag_movimento=_campo(bruta, "Tipo do Pag / Movimento"),
                custo=_campo(bruta, "Custo"),
                banco=_campo(bruta, "Banco"),
                caixinha=_campo(bruta, "Caixinhas"),
                movimentacao=_campo(bruta, "Movimentação"),
            )
        )
    return lancamentos


def carregar_categorias(caminho: str | Path) -> dict[str, list[str]]:
    """Categorias.csv (2 colunas: Categoria, Categoria Pai) ->
    {"categoria pai": ["subcategoria", ...]}. Categorias-pai sem nenhuma
    subcategoria (não deveria acontecer, mas não é erro) entram com lista
    vazia. Exclui `CATEGORIA_FORMA_PAGAMENTO`."""
    with Path(caminho).open(encoding="utf-8-sig", newline="") as f:
        linhas = list(csv.DictReader(f))

    pais: dict[str, list[str]] = {}
    for linha in linhas:
        nome = linha["Categoria"].strip()
        pai = linha["Categoria Pai"].strip()
        if pai == "":
            pais.setdefault(nome, [])
        else:
            pais.setdefault(pai, []).append(nome)

    pais.pop(CATEGORIA_FORMA_PAGAMENTO, None)
    return pais


def carregar_caixinhas(caminho: str | Path) -> dict[str, str]:
    """Caixinhas.csv -> {"nome da caixinha": "banco custodiante"}."""
    with Path(caminho).open(encoding="utf-8-sig", newline="") as f:
        linhas = list(csv.DictReader(f))
    return {linha["Caixinha"].strip(): linha["Banco"].strip() for linha in linhas}
