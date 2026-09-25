"""Testes offline da lógica pura do script de migração
(scripts/migracao/*) — nada aqui toca rede nem Supabase. O que precisa
de rede (sign_in, criação via TestClient, gravação direta no Supabase)
fica de fora da suíte automatizada, mesma categoria de
tests/seed_dados_teste.py."""
from __future__ import annotations

import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from scripts.migracao.contas import BTG_CARTAO, BTG_CORRENTE, resolver_conta
from scripts.migracao.mapeamento import (
    aprender_estrutura_custo_por_subcategoria,
    resolver_estrutura_custo,
    resolver_meio_pagamento,
    resolver_tipo_movimento,
    resolver_valor,
)
from scripts.migracao.overrides import chave_linha
from scripts.migracao.parcelas import agrupar_parcelas, extrair_parcela
from scripts.migracao.parsing import Lancamento, carregar_lancamentos, parse_data, parse_valor

import pytest


def _lancamento(**kwargs) -> Lancamento:
    base = dict(
        data=date(2026, 1, 1),
        valor=100.0,
        descricao="teste",
        categoria="Moradia",
        subcategoria="Aluguel",
        meio_pagamento="Pix",
        tipo_pag_movimento="Compra à vista",
        custo="",
        banco="Banco do Brasil",
        caixinha="",
        movimentacao="Despesa",
    )
    base.update(kwargs)
    return Lancamento(**base)


class TestParseValor:
    def test_formato_com_prefixo_e_milhar(self):
        assert parse_valor("R$ 1.234,56") == 1234.56

    def test_formato_simples(self):
        assert parse_valor("20,58") == 20.58

    def test_negativo_com_prefixo(self):
        assert parse_valor("-R$ 44,09") == -44.09

    def test_negativo_sem_prefixo(self):
        assert parse_valor("-63,70") == -63.70


class TestParseData:
    def test_formato_br(self):
        assert parse_data("16/12/2025") == date(2025, 12, 16)


class TestResolverConta:
    def test_btg_cartao_credito_vai_pro_cartao(self):
        assert resolver_conta("BTG", "Cartão de Crédito") == BTG_CARTAO

    def test_btg_pix_vai_pra_corrente(self):
        assert resolver_conta("BTG", "Pix") == BTG_CORRENTE

    def test_btg_credito_em_conta_vai_pra_corrente(self):
        assert resolver_conta("BTG", "Crédito em Conta") == BTG_CORRENTE

    def test_mercado_pago_vira_mercado_pago_wagner(self):
        assert resolver_conta("Mercado Pago", "Pix") == "Mercado Pago Wagner"

    def test_banco_nao_mapeado_da_erro_claro(self):
        with pytest.raises(ValueError, match="Nubank"):
            resolver_conta("Nubank", "Pix")


class TestResolverTipoMovimento:
    @pytest.mark.parametrize(
        "movimentacao,tipo_pag,esperado",
        [
            ("Despesa", "Compra à vista", "despesa"),
            ("Despesa", "Parcela sem juros", "despesa"),
            ("Despesa", "Compra internacional", "despesa"),
            ("Despesa", "Estorno", "estorno"),
            ("Despesa", "Ressarcimento", "ressarcimento"),
            ("Receita", "Recebimento", "receita"),
            ("Reserva", "Aplicação", "aplicacao"),
            ("Reserva", "Retirada", "retirada"),
        ],
    )
    def test_combinacoes_conhecidas(self, movimentacao, tipo_pag, esperado):
        assert resolver_tipo_movimento(movimentacao, tipo_pag) == esperado

    def test_combinacao_desconhecida_da_erro_claro(self):
        with pytest.raises(ValueError, match="Transferência"):
            resolver_tipo_movimento("Despesa", "Transferência")


class TestResolverMeioPagamento:
    def test_credito_em_conta_vira_none(self):
        assert resolver_meio_pagamento("Crédito em Conta") is None

    def test_vazio_vira_none(self):
        assert resolver_meio_pagamento("") is None

    def test_pix_mapeia_direto(self):
        assert resolver_meio_pagamento("Pix") == "pix"

    def test_nao_mapeado_da_erro_claro(self):
        with pytest.raises(ValueError, match="Vale-Refeição"):
            resolver_meio_pagamento("Vale-Refeição")


class TestResolverValor:
    def test_estorno_negativo_vira_positivo(self):
        assert resolver_valor(-44.09) == 44.09

    def test_positivo_permanece(self):
        assert resolver_valor(20.58) == 20.58


class TestAprenderEstruturaCustoPorSubcategoria:
    def test_subcategoria_consistente_e_aprendida(self):
        lancamentos = [
            _lancamento(categoria="Moradia", subcategoria="Aluguel", custo="Custos Fixos"),
            _lancamento(categoria="Moradia", subcategoria="Aluguel", custo="Custos Fixos"),
            _lancamento(categoria="Moradia", subcategoria="Aluguel", custo=""),
        ]
        aprendido = aprender_estrutura_custo_por_subcategoria(lancamentos)
        assert aprendido[("Moradia", "Aluguel")] == "fixo"

    def test_subcategoria_mista_nao_e_aprendida(self):
        lancamentos = [
            _lancamento(categoria="Pessoais", subcategoria="Espiritualidade", custo="Sazonalidades"),
            _lancamento(categoria="Pessoais", subcategoria="Espiritualidade", custo="Custos Variáveis"),
        ]
        aprendido = aprender_estrutura_custo_por_subcategoria(lancamentos)
        assert ("Pessoais", "Espiritualidade") not in aprendido

    def test_subcategoria_sem_dado_nenhum_nao_e_aprendida(self):
        lancamentos = [_lancamento(categoria="Saúde", subcategoria="Médicos", custo="")]
        aprendido = aprender_estrutura_custo_por_subcategoria(lancamentos)
        assert ("Saúde", "Médicos") not in aprendido

    def test_reserva_e_receita_nao_entram_no_aprendizado(self):
        lancamentos = [_lancamento(movimentacao="Reserva", categoria="", subcategoria="", custo="")]
        aprendido = aprender_estrutura_custo_por_subcategoria(lancamentos)
        assert aprendido == {}


class TestResolverEstruturaCusto:
    def test_valor_literal_tem_prioridade(self):
        l = _lancamento(custo="Custos Fixos")
        assert resolver_estrutura_custo(l, {}, {}, "chave") == "fixo"

    def test_cai_pro_aprendido_se_vazio(self):
        l = _lancamento(custo="", categoria="Moradia", subcategoria="Aluguel")
        aprendido = {("Moradia", "Aluguel"): "fixo"}
        assert resolver_estrutura_custo(l, aprendido, {}, "chave") == "fixo"

    def test_cai_pro_override_se_nao_ha_aprendido(self):
        l = _lancamento(custo="", categoria="Saúde", subcategoria="Médicos")
        assert resolver_estrutura_custo(l, {}, {"chave": "variavel"}, "chave") == "variavel"

    def test_pendente_se_nada_resolve(self):
        l = _lancamento(custo="", categoria="Saúde", subcategoria="Médicos")
        assert resolver_estrutura_custo(l, {}, {}, "chave") is None


class TestExtrairParcela:
    def test_padrao_simples(self):
        assert extrair_parcela("Globo Premiere (8/12)") == ("Globo Premiere", 8, 12, "")

    def test_com_resto_depois_do_marcador(self):
        resultado = extrair_parcela("Amazonmktplc Petsixcom (2/4) - Tapete e remedios")
        assert resultado == ("Amazonmktplc Petsixcom", 2, 4, "- Tapete e remedios")

    def test_sem_padrao_retorna_none(self):
        assert extrair_parcela("Seguro do Carro Junho") is None

    def test_sem_parenteses_retorna_none(self):
        assert extrair_parcela("Camicado 1/3") is None


class TestAgruparParcelas:
    def test_grupo_simples_completo(self):
        itens = [
            _lancamento(data=date(2026, 6, 25), descricao="Camicado (1/3)", tipo_pag_movimento="Parcela sem juros"),
            _lancamento(data=date(2026, 7, 25), descricao="Camicado (2/3)", tipo_pag_movimento="Parcela sem juros"),
            _lancamento(data=date(2026, 8, 25), descricao="Camicado (3/3)", tipo_pag_movimento="Parcela sem juros"),
        ]
        grupos, sem_padrao = agrupar_parcelas(itens)
        assert sem_padrao == []
        assert len(grupos) == 1
        assert grupos[0].completo
        assert [n for n, _ in grupos[0].itens] == [1, 2, 3]

    def test_grupo_truncado_no_inicio_nao_e_completo(self):
        """Parcela 1 não está no arquivo (comprada antes da janela do
        CSV) — grupo válido, só não `completo`."""
        itens = [
            _lancamento(data=date(2026, 2, 8), descricao="Amazonmktplc Petsixcom (2/4)", tipo_pag_movimento="Parcela sem juros"),
            _lancamento(data=date(2026, 3, 8), descricao="Amazonmktplc Petsixcom (3/4)", tipo_pag_movimento="Parcela sem juros"),
            _lancamento(data=date(2026, 4, 8), descricao="Amazonmktplc Petsixcom (4/4)", tipo_pag_movimento="Parcela sem juros"),
        ]
        grupos, _ = agrupar_parcelas(itens)
        assert len(grupos) == 1
        assert not grupos[0].completo

    def test_duas_compras_diferentes_nao_se_misturam(self):
        """Regressão do bug achado na análise real (Flamengo Nação):
        duas assinaturas de 12x diferentes, uma terminando (7..12) e
        outra começando (1..12) sem lacuna de datas entre elas, não
        podem virar 1 grupo só só porque a união dos números bate
        1..12. A checagem cronológica (reinício do N) precisa separar
        as duas."""
        itens = []
        # 1ª compra: parcelas 7 a 12, dez/2025 a mai/2026
        for i, n in enumerate(range(7, 13)):
            itens.append(
                _lancamento(
                    data=date(2025, 12, 16) if i == 0 else date(2026, i, 16),
                    descricao=f"Flamengo Nação ({n}/12)",
                    categoria="Lazer",
                    subcategoria="Flamengo",
                    tipo_pag_movimento="Parcela sem juros",
                )
            )
        # 2ª compra: parcelas 1 a 12, jun/2026 a mai/2027 (renovação)
        meses = [(2026, 6), (2026, 7), (2026, 8), (2026, 9), (2026, 10), (2026, 11),
                 (2026, 12), (2027, 1), (2027, 2), (2027, 3), (2027, 4), (2027, 5)]
        for n, (ano, mes) in zip(range(1, 13), meses):
            itens.append(
                _lancamento(
                    data=date(ano, mes, 16),
                    descricao=f"Flamengo Nação ({n}/12)",
                    categoria="Lazer",
                    subcategoria="Flamengo",
                    tipo_pag_movimento="Parcela sem juros",
                )
            )

        grupos, sem_padrao = agrupar_parcelas(itens)
        assert sem_padrao == []
        assert len(grupos) == 2
        primeiro, segundo = sorted(grupos, key=lambda g: g.itens[0][1].data)
        assert [n for n, _ in primeiro.itens] == [7, 8, 9, 10, 11, 12]
        assert not primeiro.completo
        assert [n for n, _ in segundo.itens] == list(range(1, 13))
        assert segundo.completo

    def test_linha_sem_padrao_nao_vira_grupo(self):
        itens = [_lancamento(descricao="Seguro do Carro Junho", tipo_pag_movimento="Parcela sem juros")]
        grupos, sem_padrao = agrupar_parcelas(itens)
        assert grupos == []
        assert len(sem_padrao) == 1

    def test_ignora_linhas_que_nao_sao_parcela(self):
        itens = [_lancamento(descricao="Compra qualquer", tipo_pag_movimento="Compra à vista")]
        grupos, sem_padrao = agrupar_parcelas(itens)
        assert grupos == []
        assert sem_padrao == []


class TestChaveLinha:
    def test_e_deterministica(self):
        l1 = _lancamento(descricao="mesma compra")
        l2 = _lancamento(descricao="mesma compra")
        assert chave_linha(l1) == chave_linha(l2)

    def test_muda_se_valor_muda(self):
        l1 = _lancamento(valor=100.0)
        l2 = _lancamento(valor=100.01)
        assert chave_linha(l1) != chave_linha(l2)


class TestCarregarLancamentos:
    """Regressão: achada rodando o script de verdade (2026-09-25) — uma
    linha 'curta' (menos colunas que o cabeçalho, comum nas linhas de
    sobra de template da planilha) faz o csv.DictReader preencher a
    coluna faltante com `None`, não com string vazia. `_campo()` batia
    de frente nisso (`None.strip()`) tanto pras linhas realmente
    puladas quanto, em tese, pra qualquer lançamento válido com uma
    coluna à direita faltando."""

    def test_linha_curta_nao_quebra_e_e_reportada_como_pulada(self, tmp_path: Path):
        csv_path = tmp_path / "lancamentos.csv"
        csv_path.write_text(
            "Data,Sub Categoria,Categoria,Meio de Pagamento,Valor,Descrição,"
            "Tipo do Pag / Movimento,Custo,Banco,Dia,Mês,Ano,Mês Texto,Caixinhas,Movimentação\n"
            '01/01/2026,Aluguel,Moradia,Pix,"R$ 1.000,00",Aluguel,Compra à vista,'
            "Custos Fixos,Banco do Brasil,1,1,2026,janeiro,,Despesa\n"
            ",,Preencher\n",  # linha curta: só 3 das 15 colunas
            encoding="utf-8",
        )
        lancamentos, puladas = carregar_lancamentos(csv_path)
        assert len(lancamentos) == 1
        assert len(puladas) == 1
        assert puladas[0].motivo == "sem Data preenchida"


class TestAgruparPorChaveHash:
    """Regressão: achada rodando a migração de verdade (2026-09-25) —
    9 meses de reconciliação com divergência, o valor de cada um batia
    exatamente com a soma das linhas 100% idênticas daquele mês. Causa:
    POST /transacoes calcula hash_dedup só com (data, valor, descrição,
    conta, tipo) — 2 transações reais que só coincidem nesses campos
    (ex: mesma assinatura de streaming cobrada 2x no mesmo dia por 2
    contas diferentes... não, pela mesma conta mesmo, tipo compra
    duplicada de propósito) colidem na constraint UNIQUE, e a 2ª vira
    'já existe' — silenciosamente descartada."""

    def test_lancamentos_identicos_formam_grupo_de_2(self):
        from scripts.migrar_dados_antigos import agrupar_por_chave_hash, contexto_local

        contexto = contexto_local({"Comunicação": ["Serviços Digitais"]}, {}, {}, {})
        l1 = _lancamento(
            data=date(2026, 3, 13), valor=14.99, descricao="Armazenamento Google. Apple",
            categoria="Comunicação", subcategoria="Serviços Digitais", banco="BTG",
        )
        l2 = _lancamento(
            data=date(2026, 3, 13), valor=14.99, descricao="Armazenamento Google. Apple",
            categoria="Comunicação", subcategoria="Serviços Digitais", banco="BTG",
        )
        grupos = agrupar_por_chave_hash([l1, l2], contexto)
        assert len(grupos) == 1
        (itens,) = grupos.values()
        assert len(itens) == 2

    def test_lancamentos_com_valor_diferente_nao_agrupam(self):
        from scripts.migrar_dados_antigos import agrupar_por_chave_hash, contexto_local

        contexto = contexto_local({"Comunicação": ["Serviços Digitais"]}, {}, {}, {})
        l1 = _lancamento(data=date(2026, 3, 13), valor=14.99, banco="BTG")
        l2 = _lancamento(data=date(2026, 3, 13), valor=15.00, banco="BTG")
        grupos = agrupar_por_chave_hash([l1, l2], contexto)
        assert len(grupos) == 2
