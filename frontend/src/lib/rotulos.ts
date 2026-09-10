// Rótulos compartilhados entre NovoLancamento, EditarLancamento e Lancamentos
// — um único lugar pra manter em sincronia com os enums do backend.
import type { EstruturaCusto, MeioPagamento, TipoMovimento } from './types'

export const ESTRUTURAS: { valor: EstruturaCusto; rotulo: string }[] = [
  { valor: 'fixo', rotulo: 'Fixo' },
  { valor: 'variavel', rotulo: 'Variável' },
  { valor: 'sazonal', rotulo: 'Sazonal' },
  { valor: 'investimentos', rotulo: 'Investimentos' },
]

export const MEIOS_PAGAMENTO: { valor: MeioPagamento; rotulo: string }[] = [
  { valor: 'pix', rotulo: 'Pix' },
  { valor: 'cartao_debito', rotulo: 'Cartão de débito' },
  { valor: 'cartao_credito', rotulo: 'Cartão de crédito' },
  { valor: 'boleto', rotulo: 'Boleto' },
  { valor: 'debito_automatico', rotulo: 'Débito automático' },
  { valor: 'dinheiro', rotulo: 'Dinheiro' },
  { valor: 'transferencia', rotulo: 'Transferência' },
  { valor: 'outro', rotulo: 'Outro' },
]

export const TIPOS_MOVIMENTO: { valor: TipoMovimento; rotulo: string }[] = [
  { valor: 'receita', rotulo: 'Receita' },
  { valor: 'despesa', rotulo: 'Despesa' },
  { valor: 'aplicacao', rotulo: 'Aplicação' },
  { valor: 'retirada', rotulo: 'Retirada' },
  { valor: 'estorno', rotulo: 'Estorno' },
  { valor: 'ressarcimento', rotulo: 'Ressarcimento' },
]

// mesmo mapeamento de backend/app/routers/transacoes.py::_TIPO_CATEGORIA_ESPERADO
export const TIPO_CATEGORIA_ESPERADO: Record<TipoMovimento, 'receita' | 'despesa' | 'investimento'> = {
  receita: 'receita',
  despesa: 'despesa',
  estorno: 'despesa',
  ressarcimento: 'despesa',
  aplicacao: 'investimento',
  retirada: 'investimento',
}

export function rotuloEstruturaCusto(valor: EstruturaCusto): string {
  return ESTRUTURAS.find((e) => e.valor === valor)?.rotulo ?? valor
}

export function rotuloMeioPagamento(valor: MeioPagamento): string {
  return MEIOS_PAGAMENTO.find((m) => m.valor === valor)?.rotulo ?? valor
}

export function rotuloTipoMovimento(valor: TipoMovimento): string {
  return TIPOS_MOVIMENTO.find((t) => t.valor === valor)?.rotulo ?? valor
}
