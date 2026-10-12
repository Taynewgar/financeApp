import { useEffect, useMemo, useState } from 'react'
import './graficosComparativos.css'
import { ApiError, apiFetch } from '../lib/api'
import { formatarMoedaCompacta } from '../lib/formatar'
import { hojeAnoMes, mesesAntes } from '../lib/periodo'
import { usePrivacidade } from '../lib/PrivacyContext'
import type { Categoria, SerieMensal } from '../lib/types'

const MESES_JANELA = 12
const COR_MIN = { r: 0x13, g: 0x1c, b: 0x2e } // --cor-superficie
const COR_MAX = { r: 0x2d, g: 0xd4, b: 0xbf } // --cor-acento

function interpolarCor(t: number): string {
  const r = Math.round(COR_MIN.r + (COR_MAX.r - COR_MIN.r) * t)
  const g = Math.round(COR_MIN.g + (COR_MAX.g - COR_MIN.g) * t)
  const b = Math.round(COR_MIN.b + (COR_MAX.b - COR_MIN.b) * t)
  return `rgb(${r}, ${g}, ${b})`
}

function rotuloMes(vigenciaMes: string): string {
  const [ano, mes] = vigenciaMes.split('-')
  const nomes = ['jan', 'fev', 'mar', 'abr', 'mai', 'jun', 'jul', 'ago', 'set', 'out', 'nov', 'dez']
  return `${nomes[Number(mes) - 1]}/${ano.slice(2)}`
}

/** Item 51 do backlog — heatmap categoria × mês: visão rápida de onde o
 * gasto concentrou, célula mais clara = valor mais alto no período. */
export function HeatmapCategorias() {
  const { oculto } = usePrivacidade()
  const [categorias, setCategorias] = useState<Categoria[]>([])
  const [series, setSeries] = useState<SerieMensal[] | null>(null)
  const [erro, setErro] = useState<string | null>(null)

  const mesInicio = useMemo(() => mesesAntes(hojeAnoMes(), MESES_JANELA - 1), [])
  const mesFim = useMemo(() => hojeAnoMes(), [])

  useEffect(() => {
    apiFetch<Categoria[]>('/categorias?tipo=despesa')
      .then((r) => setCategorias(r.filter((c) => c.ativo)))
      .catch(() => {})
  }, [])

  useEffect(() => {
    if (categorias.length === 0) return
    const params = new URLSearchParams({ inicio: `${mesInicio}-01`, fim: `${mesFim}-01` })
    categorias.forEach((c) => params.append('series', `categoria:${c.id}`))
    apiFetch<SerieMensal[]>(`/dashboard/series-mensais?${params.toString()}`)
      .then((r) => {
        setSeries(r)
        setErro(null)
      })
      .catch((e) => setErro(e instanceof ApiError ? e.message : 'Falha ao carregar o heatmap'))
  }, [categorias, mesInicio, mesFim])

  const meses = series && series.length > 0 ? series[0].pontos.map((p) => p.vigencia_mes) : []
  const maiorValor = Math.max(1, ...(series ?? []).flatMap((s) => s.pontos.map((p) => Math.abs(p.valor))))

  const linhas = useMemo(() => {
    if (!series) return []
    return [...series]
      .map((s) => ({ ...s, total: s.pontos.reduce((acc, p) => acc + Math.abs(p.valor), 0) }))
      .sort((a, b) => b.total - a.total)
  }, [series])

  return (
    <div>
      {erro && <p className="mensagem-erro">{erro}</p>}
      {linhas.length === 0 && !erro && (
        <p style={{ color: 'var(--cor-texto-suave)', fontSize: 13 }}>Carregando heatmap…</p>
      )}
      {linhas.length > 0 && (
        <div style={{ overflowX: 'auto' }}>
          <table className="heatmap-tabela">
            <thead>
              <tr>
                <th className="heatmap-rotulo-categoria" />
                {meses.map((m) => (
                  <th key={m}>{rotuloMes(m)}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {linhas.map((serie) => (
                <tr key={serie.chave}>
                  <td className="heatmap-rotulo-categoria">{serie.nome}</td>
                  {serie.pontos.map((p) => {
                    const t = Math.abs(p.valor) / maiorValor
                    return (
                      <td
                        key={p.vigencia_mes}
                        className="heatmap-celula"
                        style={{ background: interpolarCor(t), color: t > 0.55 ? '#0b1220' : 'var(--cor-texto-suave)' }}
                        title={`${serie.nome} em ${rotuloMes(p.vigencia_mes)}`}
                      >
                        {oculto ? '•••' : p.valor === 0 ? '—' : formatarMoedaCompacta(p.valor)}
                      </td>
                    )
                  })}
                </tr>
              ))}
            </tbody>
          </table>
          <div className="heatmap-escala">
            <span>Menor</span>
            <span
              className="heatmap-escala-barra"
              style={{ background: `linear-gradient(90deg, ${interpolarCor(0)}, ${interpolarCor(1)})` }}
            />
            <span>Maior</span>
          </div>
        </div>
      )}
    </div>
  )
}
