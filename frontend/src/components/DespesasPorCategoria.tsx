import './despesasPorCategoria.css'
import { formatarMoeda } from '../lib/formatar'
import type { DespesaPorCategoria } from '../lib/types'

const PALETA = ['var(--cat-1)', 'var(--cat-2)', 'var(--cat-3)', 'var(--cat-4)', 'var(--cat-5)', 'var(--cat-6)', 'var(--cat-7)', 'var(--cat-8)']
const LIMITE_CATEGORIAS = PALETA.length

type Linha = { categoria_id: string; categoria_nome: string; valor: number; percentual: number }

/** Cor por categoria atribuída em ordem alfabética (não por valor) — assim
 * a cor de uma categoria não muda de mês a mês só porque ela subiu ou
 * desceu de posição no ranking (regra da skill de dataviz: cor segue a
 * entidade, nunca o rank). A ordem de exibição (maior valor primeiro)
 * continua vindo do backend. */
function corPorCategoria(dados: DespesaPorCategoria[]): Map<string, string> {
  const ordenadoPorNome = [...dados].sort((a, b) => a.categoria_nome.localeCompare(b.categoria_nome, 'pt-BR'))
  const mapa = new Map<string, string>()
  ordenadoPorNome.forEach((d, i) => {
    if (i < LIMITE_CATEGORIAS) mapa.set(d.categoria_id, PALETA[i])
  })
  return mapa
}

export function DespesasPorCategoria({ dados }: { dados: DespesaPorCategoria[] }) {
  if (dados.length === 0) {
    return <p style={{ color: 'var(--cor-texto-suave)' }}>Nenhuma despesa no período.</p>
  }

  // "principais" (por valor, vem ordenado do backend) é o conjunto que de
  // fato vira segmento próprio — a cor tem que ser atribuída sobre ESSE
  // mesmo conjunto (ordenado por nome só pra estabilidade), senão uma
  // categoria que está nos top-N por valor mas não nos top-N por nome fica
  // sem cor nenhuma (bug: dois "top 8" diferentes disputando o mesmo mapa)
  const principais = dados.slice(0, LIMITE_CATEGORIAS)
  const outras = dados.slice(LIMITE_CATEGORIAS)
  const cores = corPorCategoria(principais)

  const linhas: Linha[] = principais
  if (outras.length > 0) {
    linhas.push({
      categoria_id: '_outras',
      categoria_nome: `Outras (${outras.length})`,
      valor: outras.reduce((soma, d) => soma + d.valor, 0),
      percentual: outras.reduce((soma, d) => soma + d.percentual, 0),
    })
  }

  const corDe = (id: string) => (id === '_outras' ? 'var(--cat-outras)' : cores.get(id))

  return (
    <div className="despesas-categoria">
      <div className="despesas-categoria-barra">
        {linhas.map((l) => (
          <div
            key={l.categoria_id}
            className="despesas-categoria-segmento"
            style={{ width: `${l.percentual}%`, background: corDe(l.categoria_id) }}
            title={`${l.categoria_nome}: ${formatarMoeda(l.valor)} (${l.percentual.toFixed(1)}%)`}
          />
        ))}
      </div>
      <ul className="despesas-categoria-lista">
        {linhas.map((l) => (
          <li key={l.categoria_id}>
            <span className="despesas-categoria-swatch" style={{ background: corDe(l.categoria_id) }} />
            <span className="despesas-categoria-nome">{l.categoria_nome}</span>
            <span className="despesas-categoria-valor">{formatarMoeda(l.valor)}</span>
            <span className="despesas-categoria-percentual">{l.percentual.toFixed(1)}%</span>
          </li>
        ))}
      </ul>
    </div>
  )
}
