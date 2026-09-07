// Espelha os schemas Pydantic do backend (backend/app/schemas/*.py) — os
// nomes de campo são os mesmos de propósito, pra evitar tradução mental.

export type TipoConta = 'corrente' | 'cartao_credito' | 'carteira' | 'caixinha' | 'investimento'

export type Conta = {
  id: string
  nome: string
  tipo_conta: TipoConta
  banco: string | null
  saldo_inicial: number
  dia_fechamento: number | null
  dia_vencimento: number | null
  ativo: boolean
}

export type Categoria = {
  id: string
  nome: string
  ativo: boolean
}

export type EstruturaCusto = 'fixo' | 'variavel' | 'sazonal'

export type Subcategoria = {
  id: string
  categoria_id: string
  nome: string
  estrutura_custo_padrao: EstruturaCusto | null
  ativo: boolean
}

export type Caixinha = {
  id: string
  nome: string
  conta_id: string | null
  ativo: boolean
}

export type TipoMovimento = 'receita' | 'despesa' | 'aplicacao' | 'retirada' | 'estorno' | 'ressarcimento'

export type MeioPagamento =
  | 'pix'
  | 'cartao_debito'
  | 'boleto'
  | 'debito_automatico'
  | 'dinheiro'
  | 'transferencia'
  | 'outro'

export type Transacao = {
  id: string
  data_compra: string
  valor: number
  descricao: string | null
  tipo_movimento: TipoMovimento
  pagamento: 'avista' | 'parcelado'
  parcela_atual: number | null
  parcela_total: number | null
  compra_parcelada_id: string | null
  conta_id: string
  categoria_id: string | null
  subcategoria_id: string | null
  estrutura_custo: EstruturaCusto | null
  caixinha_id: string | null
  meio_pagamento: MeioPagamento | null
  fatura_referencia: string | null
  fatura_override: boolean
  ajuste_de_transacao_id: string | null
}
