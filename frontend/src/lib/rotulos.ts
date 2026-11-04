// Rótulos compartilhados entre NovoLancamento, EditarLancamento e Lancamentos
// — um único lugar pra manter em sincronia com os enums do backend.
import type { EstruturaCusto, MeioPagamento, Transacao, TipoMovimento, TipoMovimentoRecorrente } from './types'

// o segmento escolhido no formulário (NovoLancamento/EditarLancamento) não
// é 1:1 com tipo_movimento — aplicação/retirada vira "investimento" ou
// "reserva" dependendo de ter caixinha_id, estorno/ressarcimento viram
// "ajuste". Extraído de EditarLancamento.tsx pra reaproveitar em
// NovoLancamento.tsx (item 44, duplicar lançamento existente).
export type TipoLancamentoDerivado = 'receita' | 'despesa' | 'investimento' | 'reserva' | 'ajuste'

export function derivarTipoLancamento(t: Pick<Transacao, 'tipo_movimento' | 'caixinha_id'>): TipoLancamentoDerivado {
  if (t.tipo_movimento === 'receita') return 'receita'
  if (t.tipo_movimento === 'despesa') return 'despesa'
  if (t.tipo_movimento === 'estorno' || t.tipo_movimento === 'ressarcimento') return 'ajuste'
  return t.caixinha_id ? 'reserva' : 'investimento'
}

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

// subconjunto de TIPOS_MOVIMENTO válido pra um molde de Lançamento
// Recorrente (sem estorno/ressarcimento — só existem vinculados a uma
// despesa específica já lançada, não fazem sentido como molde recorrente)
export const TIPOS_MOVIMENTO_RECORRENTE: { valor: TipoMovimentoRecorrente; rotulo: string }[] = [
  { valor: 'receita', rotulo: 'Receita' },
  { valor: 'despesa', rotulo: 'Despesa' },
  { valor: 'aplicacao', rotulo: 'Aplicação' },
  { valor: 'retirada', rotulo: 'Retirada' },
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

// cor por categoria: receita/estorno/ressarcimento = verde, despesa =
// vermelho, aplicação/retirada em caixinha (reserva) = roxo, aplicação/
// retirada sem caixinha (investimento de verdade) = azul — mesma
// distinção de bucket "reservas" vs "investimentos" de Estrutura de
// Custo. Usado em Lançamentos (lista de transações) e no Dashboard
// (Compromissos Futuros, que não carrega caixinha_id — sempre cai no
// ramo investimento ali, limitação pré-existente).
export function classePorTipoMovimento(tipo: TipoMovimento, caixinhaId?: string | null): string {
  if (tipo === 'receita' || tipo === 'estorno' || tipo === 'ressarcimento') return 'valor-receita'
  if (tipo === 'despesa') return 'valor-despesa'
  if (tipo === 'aplicacao' || tipo === 'retirada') return caixinhaId ? 'valor-reserva' : 'valor-investimento'
  return ''
}

// aplicação = dinheiro entrando no investimento/caixinha, retirada =
// saindo — usado pra decidir pílula preenchida (entra) vs contorno (sai)
// na lista de Lançamentos (item 55 do backlog).
export function direcaoAplicacaoRetirada(tipo: TipoMovimento): 'entrada' | 'saida' | null {
  if (tipo === 'aplicacao') return 'entrada'
  if (tipo === 'retirada') return 'saida'
  return null
}

// rótulo do badge pra estorno/ressarcimento — os dois ficam na cor de
// receita (reduzem/compensam uma despesa), o badge evita confundir com
// receita de verdade (item 55 do backlog).
export function badgeAjuste(tipo: TipoMovimento): 'estorno' | 'ressarcimento' | null {
  if (tipo === 'estorno') return 'estorno'
  if (tipo === 'ressarcimento') return 'ressarcimento'
  return null
}
