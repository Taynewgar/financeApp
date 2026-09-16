import { Fragment } from 'react'
import './pareto.css'
import { formatarMoeda } from '../lib/formatar'
import { usePrivacidade } from '../lib/PrivacyContext'

type ItemPareto = { id: string; nome: string; valor: number; percentual: number }

/** Ranking de despesas por magnitude + curva de % acumulado — responde
 * "quantas categorias concentram a maior parte do gasto". Linhas
 * horizontais em vez de colunas verticais: evita rótulo de categoria
 * colidindo em cima do outro (skill de dataviz: "vai horizontal pra
 * muitas categorias/nomes longos") e já é uma tabela por natureza, sem
 * precisar de um "ver como tabela" à parte. Barra escalada pelo MAIOR
 * valor da lista (não pelo total, que é o padrão de "Despesas por
 * Categoria") — aqui o que importa é comparar magnitude entre linhas,
 * não composição de um todo. */
export function Pareto({ itens }: { itens: ItemPareto[] }) {
  const { oculto } = usePrivacidade()

  if (itens.length === 0) {
    return <p style={{ color: 'var(--cor-texto-suave)' }}>Nenhuma despesa no período.</p>
  }

  const maiorValor = Math.max(...itens.map((i) => i.valor))
  // acumulado ANTES de cada linha (soma dos percentuais das linhas
  // anteriores) — não usa mutação externa ao map pra não disparar
  // reatribuição de variável entre renders
  const acumuladosAntes = itens.reduce<number[]>((acc, _item, i) => {
    acc.push(i === 0 ? 0 : acc[i - 1] + itens[i - 1].percentual)
    return acc
  }, [])
  const linhas = itens.map((item, i) => {
    const acumuladoAntes = acumuladosAntes[i]
    return {
      ...item,
      percentualAcumulado: Math.min(acumuladoAntes + item.percentual, 100),
      // "vital few": linhas necessárias pra alcançar 80% acumulado —
      // pelo critério clássico de Pareto (80/20)
      dentroDoOitenta: acumuladoAntes < 80,
    }
  })
  const indiceCorte = linhas.findIndex((l) => !l.dentroDoOitenta)

  return (
    <div className="pareto">
      <table className="pareto-tabela">
        <thead>
          <tr>
            <th>Categoria</th>
            <th className="pareto-col-numerica">Valor</th>
            <th className="pareto-col-numerica">%</th>
            <th className="pareto-col-numerica">% acumulado</th>
          </tr>
        </thead>
        <tbody>
          {linhas.map((l, i) => (
            <Fragment key={l.id}>
              {i === indiceCorte && indiceCorte > 0 && (
                <tr className="pareto-linha-corte" aria-hidden="true">
                  <td colSpan={4}>80% do gasto acumulado até aqui</td>
                </tr>
              )}
              <tr className={l.dentroDoOitenta ? '' : 'pareto-linha-fora'}>
                <td>
                  <div className="pareto-barra-trilho">
                    <div className="pareto-barra" style={{ width: `${(l.valor / maiorValor) * 100}%` }} />
                    <span className="pareto-nome">{l.nome}</span>
                  </div>
                </td>
                <td className="pareto-col-numerica">{formatarMoeda(l.valor, oculto)}</td>
                <td className="pareto-col-numerica">{l.percentual.toFixed(1)}%</td>
                <td className="pareto-col-numerica">{l.percentualAcumulado.toFixed(1)}%</td>
              </tr>
            </Fragment>
          ))}
        </tbody>
      </table>
    </div>
  )
}
