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

export type TipoCategoria = 'receita' | 'despesa' | 'investimento'

export type Categoria = {
  id: string
  nome: string
  tipo: TipoCategoria
  ativo: boolean
}

export type EstruturaCusto = 'fixo' | 'variavel' | 'sazonal' | 'investimentos'

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
  | 'cartao_credito'
  | 'boleto'
  | 'debito_automatico'
  | 'dinheiro'
  | 'transferencia'
  | 'outro'

// Campos financeiros compartilhados entre um resumo de 1 mês (ResumoMensal)
// e de um período livre (ResumoPeriodo) — espelha _CamposFinanceiros do
// backend (schemas/dashboard.py).
export type CamposFinanceiros = {
  receitas: number
  despesas_brutas: number
  despesas_liquidas: number
  ajustes_vinculados: number
  ajustes_nao_vinculados: number
  aplicacoes: number
  retiradas: number
  // reserva: aplicação/retirada COM caixinha (guardar dinheiro)
  reservas: number
  // investimento: aplicação/retirada SEM caixinha — conceito diferente de reserva
  investimentos: number
  resultado_fluxo_caixa: number
  resultado_saude: number
  taxa_poupanca: number | null
}

export type ResumoLancamentos = CamposFinanceiros & {
  total_lancamentos: number
}

export type ResumoMensal = CamposFinanceiros & {
  vigencia_mes: string
}

export type ResumoPeriodo = CamposFinanceiros & {
  inicio: string
  fim: string
}

export type PontoEvolucaoMensal = ResumoMensal & {
  resultado_saude_acumulado: number
  taxa_poupanca_acumulada: number | null
}

export type EvolucaoMensal = {
  inicio: string
  fim: string
  meses: PontoEvolucaoMensal[]
}

export type SaldoCaixinha = {
  id: string
  nome: string
  saldo: number
}

export type CompromissoFuturo = {
  tipo: 'parcela' | 'recorrente'
  descricao: string | null
  valor: number
  data_compra: string
  parcela_atual: number | null
  parcela_total: number | null
  lancamento_recorrente_id: string | null
}

// despesa fixa recorrente (aluguel, assinatura) — projeção virtual, nada
// vira transação real até confirmar (ver POST /lancamentos-recorrentes/{id}/confirmar)
export type EstruturaCustoRecorrente = 'fixo' | 'variavel' | 'sazonal'

export type LancamentoRecorrente = {
  id: string
  descricao: string
  valor: number
  dia_mes: number
  conta_id: string
  categoria_id: string
  subcategoria_id: string | null
  estrutura_custo: EstruturaCustoRecorrente
  meio_pagamento: MeioPagamento
  data_inicio: string
  data_fim: string | null
  ativo: boolean
}

export type PrimeiroMes = {
  vigencia_mes: string | null
}

export type DespesaPorCategoria = {
  categoria_id: string
  categoria_nome: string
  valor: number
  percentual: number
}

export type DespesaPorSubcategoria = {
  subcategoria_id: string | null
  subcategoria_nome: string
  valor: number
  percentual: number
}

export type PontoTendenciaOrcamento = {
  vigencia_mes: string
  orcado: number
  realizado: number
  percentual_executado: number | null
}

export type TendenciaOrcamento = {
  inicio: string
  fim: string
  meses: PontoTendenciaOrcamento[]
}

export type Bucket = 'custos_fixos' | 'custos_variaveis' | 'sazonalidades' | 'investimentos'

export type Orcamento = {
  id: string
  vigencia_mes: string
  receita_base: number
  percentual_geral: number
  limite_custos_fixos: number
  limite_custos_variaveis: number
  limite_sazonalidades: number
  limite_investimentos: number
}

export type OrcamentoItem = {
  id: string
  orcamento_id: string
  bucket: Bucket
  categoria_id: string | null
  subcategoria_id: string | null
  nome: string | null
  conta_vinculada_id: string | null
  orcamento_mensal: number
  ativo: boolean
  // sobra (ou estouro, se negativo) trazida do mês anterior via "gerar
  // próximo mês" — 0 em item criado do zero
  saldo_anterior: number
  // calculados no backend, nunca gravados
  disponivel: number
  percentual_da_renda: number
  percentual_do_teto: number
}

// Estrutura de Custo lê 3 buckets a mais que o orçamento aceita como
// destino de item (reservas e sem_estrutura só existem aqui, derivados
// direto dos lançamentos — nunca de orcamento_itens).
export type BucketEstruturaCusto = Bucket | 'reservas' | 'sem_estrutura'

export type ItemEstruturaCusto = {
  // exatamente um destes vem preenchido (ou nenhum, se o lançamento não
  // tem categoria/subcategoria nem conta de investimento vinculada)
  categoria_id: string | null
  subcategoria_id: string | null
  conta_id: string | null
  orcado: number
  realizado: number
  // orcado = orcamento_mensal + saldo_anterior; os dois vêm separados pra
  // UI poder distinguir "o que eu planejei" da sobra/furo rolado do mês
  // anterior, em vez de só mostrar o total combinado.
  orcamento_mensal: number
  saldo_anterior: number
}

export type BucketDaEstrutura = {
  bucket: BucketEstruturaCusto
  orcado: number
  realizado: number
  itens: ItemEstruturaCusto[]
  saldo_anterior_acumulado: number
}

export type VereditoTeto = { teto: number; realizado: number; dentro_do_teto: boolean }
export type VereditoPiso = { teto: number; realizado: number; meta_batida: boolean }

export type EstruturaCustoMes = {
  vigencia_mes: string
  orcamento_id: string | null
  buckets: BucketDaEstrutura[]
  pool_despesas: VereditoTeto | null
  piso_investimentos: VereditoPiso | null
}

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
