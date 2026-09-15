import { useEffect, useMemo, useState } from 'react'
import { Link } from 'react-router-dom'
import '../components/crud.css'
import '../components/estruturaCusto.css'
import { ApiError, apiFetch } from '../lib/api'
import { formatarMoeda } from '../lib/formatar'
import { usePrivacidade } from '../lib/PrivacyContext'
import type {
  BucketDaEstrutura,
  BucketEstruturaCusto,
  Categoria,
  Conta,
  EstruturaCustoMes,
  ItemEstruturaCusto,
  Subcategoria,
} from '../lib/types'

export const BUCKETS: { valor: BucketEstruturaCusto; rotulo: string; cor: string }[] = [
  { valor: 'custos_fixos', rotulo: 'Custos Fixos', cor: 'var(--bucket-fixos)' },
  { valor: 'custos_variaveis', rotulo: 'Custos Variáveis', cor: 'var(--bucket-variaveis)' },
  { valor: 'sazonalidades', rotulo: 'Sazonalidades', cor: 'var(--bucket-sazonalidades)' },
  { valor: 'investimentos', rotulo: 'Investimentos', cor: 'var(--bucket-investimentos)' },
  { valor: 'reservas', rotulo: 'Reservas', cor: 'var(--bucket-reservas)' },
  { valor: 'sem_estrutura', rotulo: 'Sem Estrutura Definida', cor: 'var(--bucket-sem-estrutura)' },
]

// buckets que participam do orçamento de verdade (reservas/sem_estrutura
// nunca recebem item de orcamento_itens — só existem aqui via lançamento)
const BUCKETS_ORCAMENTO: BucketEstruturaCusto[] = ['custos_fixos', 'custos_variaveis', 'sazonalidades', 'investimentos']

type Folha = {
  chave: string
  nome: string
  orcado: number
  realizado: number
  categoriaIdDrillDown: string | null
  subcategoriaIdDrillDown: string | null
}

type GrupoCategoria = {
  chave: string
  nome: string
  orcado: number
  realizado: number
  folhas: Folha[]
}

/** 'YYYY-MM' menos N meses, sempre 'YYYY-MM' de volta. Mesma lógica de Planejamento.tsx. */
function mesesAntes(anoMes: string, n: number): string {
  const [ano, mes] = anoMes.split('-').map(Number)
  const totalMeses = ano * 12 + (mes - 1) - n
  const anoResultado = Math.floor(totalMeses / 12)
  const mesResultado = (totalMeses % 12) + 1
  return `${anoResultado}-${String(mesResultado).padStart(2, '0')}`
}

function hojeAnoMes(): string {
  return new Date().toISOString().slice(0, 7)
}

function chaveCategoria(bucket: BucketEstruturaCusto, chave: string): string {
  return `${bucket}|${chave}`
}

/** Agrupa os itens flat do backend (1 por categoria OU subcategoria OU
 * conta) em bucket > categoria pai > subcategoria — a API não devolve essa
 * hierarquia pronta, só os totais por combinação categoria/subcategoria/conta. */
export function agruparPorCategoria(
  itens: ItemEstruturaCusto[],
  categorias: Categoria[],
  subcategorias: Subcategoria[],
  contas: Conta[],
): GrupoCategoria[] {
  const categoriasPorId = new Map(categorias.map((c) => [c.id, c]))
  const subcategoriasPorId = new Map(subcategorias.map((s) => [s.id, s]))
  const contasPorId = new Map(contas.map((c) => [c.id, c]))
  const grupos = new Map<string, GrupoCategoria>()

  function grupo(chave: string, nome: string): GrupoCategoria {
    let g = grupos.get(chave)
    if (!g) {
      g = { chave, nome, orcado: 0, realizado: 0, folhas: [] }
      grupos.set(chave, g)
    }
    return g
  }

  for (const item of itens) {
    let g: GrupoCategoria
    let folha: Folha

    if (item.subcategoria_id) {
      const sub = subcategoriasPorId.get(item.subcategoria_id)
      const catId = sub?.categoria_id ?? `sub-orfa-${item.subcategoria_id}`
      const catNome = (sub && categoriasPorId.get(sub.categoria_id)?.nome) ?? 'Categoria removida'
      g = grupo(catId, catNome)
      folha = {
        chave: item.subcategoria_id,
        nome: sub?.nome ?? 'Subcategoria removida',
        orcado: item.orcado,
        realizado: item.realizado,
        categoriaIdDrillDown: sub?.categoria_id ?? null,
        subcategoriaIdDrillDown: item.subcategoria_id,
      }
    } else if (item.categoria_id) {
      const catNome = categoriasPorId.get(item.categoria_id)?.nome ?? 'Categoria removida'
      g = grupo(item.categoria_id, catNome)
      folha = {
        chave: `geral-${item.categoria_id}`,
        nome: 'Geral (sem subcategoria)',
        orcado: item.orcado,
        realizado: item.realizado,
        categoriaIdDrillDown: item.categoria_id,
        subcategoriaIdDrillDown: null,
      }
    } else if (item.conta_id) {
      const contaNome = contasPorId.get(item.conta_id)?.nome ?? 'Conta removida'
      g = grupo(`conta-${item.conta_id}`, contaNome)
      folha = {
        chave: item.conta_id,
        nome: contaNome,
        orcado: item.orcado,
        realizado: item.realizado,
        categoriaIdDrillDown: null,
        subcategoriaIdDrillDown: null,
      }
    } else {
      g = grupo('sem-categoria', 'Sem categoria')
      folha = {
        chave: 'sem-categoria-folha',
        nome: 'Sem categoria',
        orcado: item.orcado,
        realizado: item.realizado,
        categoriaIdDrillDown: null,
        subcategoriaIdDrillDown: null,
      }
    }

    g.orcado = Math.round((g.orcado + folha.orcado) * 100) / 100
    g.realizado = Math.round((g.realizado + folha.realizado) * 100) / 100
    g.folhas.push(folha)
  }

  return [...grupos.values()].sort((a, b) => a.nome.localeCompare(b.nome, 'pt-BR'))
}

function linkBusca(mes: string, categoriaId: string | null, subcategoriaId: string | null): string {
  const params = new URLSearchParams({ mes })
  if (categoriaId) params.set('categoria_id', categoriaId)
  if (subcategoriaId) params.set('subcategoria_id', subcategoriaId)
  return `/lancamentos?${params.toString()}`
}

function BadgeStatus({ orcado, realizado }: { orcado: number; realizado: number }) {
  if (orcado <= 0) return <span style={{ color: 'var(--cor-texto-suave)' }}>—</span>
  const excedido = realizado > orcado + 0.005
  return <span className={`estrutura-custo-badge ${excedido ? 'excedido' : 'dentro'}`}>{excedido ? 'Excedido' : 'Dentro'}</span>
}

export function BucketBloco({
  bucket,
  bucketId,
  vigenciaMes,
  oculto,
  aberto,
  onToggle,
  categoriasAbertas,
  onAlternarCategoria,
}: {
  bucket: BucketDaEstrutura & { rotulo: string; cor: string; grupos: GrupoCategoria[] }
  bucketId: BucketEstruturaCusto
  vigenciaMes: string
  oculto: boolean
  aberto: boolean
  onToggle: () => void
  categoriasAbertas: Set<string>
  onAlternarCategoria: (chave: string) => void
}) {
  const semLancamentos = bucket.grupos.length === 0

  return (
    <div className={`estrutura-custo-bucket${aberto ? ' aberto' : ''}`}>
      <button
        type="button"
        className="estrutura-custo-bucket-cabecalho"
        onClick={onToggle}
        disabled={semLancamentos}
        aria-expanded={aberto}
      >
        {!semLancamentos && <span className="estrutura-custo-seta" aria-hidden="true">▶</span>}
        {semLancamentos && <span style={{ width: 14 }} />}
        <span className="estrutura-custo-cor" style={{ background: bucket.cor }} />
        <span className="estrutura-custo-bucket-nome">{bucket.rotulo}</span>
        <span className="estrutura-custo-bucket-valores">
          <span><span className="rotulo-inline">Orçado</span>{formatarMoeda(bucket.orcado, oculto)}</span>
          <span><span className="rotulo-inline">Realizado</span>{formatarMoeda(bucket.realizado, oculto)}</span>
        </span>
      </button>

      {semLancamentos && <p className="estrutura-custo-vazio">Nenhum lançamento neste bucket no mês.</p>}

      {!semLancamentos && aberto && (
        <div className="estrutura-custo-categoria-lista">
          {bucket.grupos.map((g) => {
            const categoriaAberta = categoriasAbertas.has(chaveCategoria(bucketId, g.chave))
            return (
              <div key={g.chave}>
                <button
                  type="button"
                  className="estrutura-custo-categoria-linha"
                  onClick={() => onAlternarCategoria(g.chave)}
                  aria-expanded={categoriaAberta}
                >
                  <span className="estrutura-custo-seta" aria-hidden="true">▶</span>
                  <span className="estrutura-custo-categoria-nome">{g.nome}</span>
                  <span className="estrutura-custo-categoria-valores">
                    <span>{formatarMoeda(g.orcado, oculto)}</span>
                    <span>{formatarMoeda(g.realizado, oculto)}</span>
                  </span>
                </button>
                {categoriaAberta &&
                  g.folhas.map((f) => (
                    <div className="estrutura-custo-sub-linha" key={f.chave}>
                      <span>{f.nome}</span>
                      <span className="col-num">{formatarMoeda(f.orcado, oculto)}</span>
                      <span className="col-num">{formatarMoeda(f.realizado, oculto)}</span>
                      <span className="col-num">{formatarMoeda(f.orcado - f.realizado, oculto)}</span>
                      <span className="col-status">
                        <BadgeStatus orcado={f.orcado} realizado={f.realizado} />
                      </span>
                      <span className="col-ir">
                        {(f.categoriaIdDrillDown || f.subcategoriaIdDrillDown) && (
                          <Link
                            className="estrutura-custo-ir-busca"
                            to={linkBusca(vigenciaMes, f.categoriaIdDrillDown, f.subcategoriaIdDrillDown)}
                            title="Ver em Busca de Lançamentos"
                          >
                            →
                          </Link>
                        )}
                      </span>
                    </div>
                  ))}
              </div>
            )
          })}
        </div>
      )}
    </div>
  )
}

export function EstruturaCusto() {
  const { oculto } = usePrivacidade()
  const [vigenciaMes, setVigenciaMes] = useState(hojeAnoMes())
  const [dados, setDados] = useState<EstruturaCustoMes | null>(null)
  const [categorias, setCategorias] = useState<Categoria[]>([])
  const [subcategorias, setSubcategorias] = useState<Subcategoria[]>([])
  const [contas, setContas] = useState<Conta[]>([])
  const [erro, setErro] = useState<string | null>(null)
  const [bucketsAbertos, setBucketsAbertos] = useState<Set<BucketEstruturaCusto>>(new Set())
  // chave composta "bucket|categoria" — uma categoria pode ter o mesmo id
  // de agrupamento em buckets diferentes só em teoria, mas isolar por
  // bucket evita qualquer ambiguidade e deixa "expandir/recolher tudo"
  // controlar os dois níveis a partir de um único Set aqui em cima
  const [categoriasAbertas, setCategoriasAbertas] = useState<Set<string>>(new Set())

  useEffect(() => {
    Promise.all([
      apiFetch<Categoria[]>('/categorias'),
      apiFetch<Subcategoria[]>('/subcategorias'),
      apiFetch<Conta[]>('/contas'),
    ])
      .then(([cat, sub, c]) => {
        setCategorias(cat)
        setSubcategorias(sub)
        setContas(c)
      })
      .catch((e) => setErro(e instanceof ApiError ? e.message : 'Falha ao carregar categorias/contas'))
  }, [])

  useEffect(() => {
    setErro(null)
    apiFetch<EstruturaCustoMes>(`/estrutura-custo/${vigenciaMes}-01`)
      .then((r) => {
        setDados(r)
        // buckets com lançamento começam abertos — é uma tela de análise,
        // ver tudo de cara vale mais que ter que abrir um por um
        setBucketsAbertos(new Set(r.buckets.filter((b) => b.itens.length > 0).map((b) => b.bucket)))
        setCategoriasAbertas(new Set())
      })
      .catch((e) => setErro(e instanceof ApiError ? e.message : 'Falha ao carregar a estrutura de custo'))
  }, [vigenciaMes])

  const bucketsComGrupo = useMemo(() => {
    if (!dados) return []
    return BUCKETS.map((meta) => {
      const bucket = dados.buckets.find((b) => b.bucket === meta.valor)
      const itens = bucket?.itens ?? []
      return {
        bucket: meta.valor,
        orcado: bucket?.orcado ?? 0,
        realizado: bucket?.realizado ?? 0,
        itens,
        saldo_anterior_acumulado: bucket?.saldo_anterior_acumulado ?? 0,
        rotulo: meta.rotulo,
        cor: meta.cor,
        grupos: agruparPorCategoria(itens, categorias, subcategorias, contas),
      }
    })
  }, [dados, categorias, subcategorias, contas])

  const resumoOrcamento = useMemo(() => {
    if (!dados) return null
    const relevantes = bucketsComGrupo.filter((b) => BUCKETS_ORCAMENTO.includes(b.bucket))
    const orcado = relevantes.reduce((soma, b) => soma + b.orcado, 0)
    const realizado = relevantes.reduce((soma, b) => soma + b.realizado, 0)
    return { orcado: Math.round(orcado * 100) / 100, realizado: Math.round(realizado * 100) / 100 }
  }, [dados, bucketsComGrupo])

  function alternarBucket(bucket: BucketEstruturaCusto) {
    setBucketsAbertos((atual) => {
      const proximo = new Set(atual)
      if (proximo.has(bucket)) proximo.delete(bucket)
      else proximo.add(bucket)
      return proximo
    })
  }

  function alternarCategoria(bucket: BucketEstruturaCusto, chave: string) {
    setCategoriasAbertas((atual) => {
      const proximo = new Set(atual)
      const chaveCompleta = chaveCategoria(bucket, chave)
      if (proximo.has(chaveCompleta)) proximo.delete(chaveCompleta)
      else proximo.add(chaveCompleta)
      return proximo
    })
  }

  const bucketsComItens = useMemo(() => bucketsComGrupo.filter((b) => b.grupos.length > 0), [bucketsComGrupo])

  const tudoExpandido = useMemo(() => {
    if (bucketsComItens.length === 0) return false
    return bucketsComItens.every(
      (b) => bucketsAbertos.has(b.bucket) && b.grupos.every((g) => categoriasAbertas.has(chaveCategoria(b.bucket, g.chave))),
    )
  }, [bucketsComItens, bucketsAbertos, categoriasAbertas])

  function alternarTudo() {
    if (tudoExpandido) {
      setBucketsAbertos(new Set())
      setCategoriasAbertas(new Set())
      return
    }
    setBucketsAbertos(new Set(bucketsComItens.map((b) => b.bucket)))
    setCategoriasAbertas(new Set(bucketsComItens.flatMap((b) => b.grupos.map((g) => chaveCategoria(b.bucket, g.chave)))))
  }

  const diferenca = resumoOrcamento ? resumoOrcamento.orcado - resumoOrcamento.realizado : 0
  const execucao = resumoOrcamento && resumoOrcamento.orcado > 0 ? (resumoOrcamento.realizado / resumoOrcamento.orcado) * 100 : null

  return (
    <div className="estrutura-custo">
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 12, flexWrap: 'wrap', marginBottom: 20 }}>
        <div>
          <h1 style={{ fontSize: 22, marginTop: 0, marginBottom: 4 }}>Estrutura de Custo</h1>
          <p className="estrutura-custo-resumo" style={{ margin: 0 }}>
            Leitura do que foi de fato gasto no mês, comparado com o que foi planejado em Planejamento.
          </p>
        </div>
        <div style={{ display: 'flex', alignItems: 'flex-end', gap: 6 }}>
          <button
            type="button"
            className="botao-secundario"
            onClick={() => setVigenciaMes(mesesAntes(vigenciaMes, 1))}
            title="Mês anterior"
            aria-label="Mês anterior"
          >
            ←
          </button>
          <label className="campo" style={{ maxWidth: 180 }}>
            Mês
            <input type="month" value={vigenciaMes} onChange={(e) => setVigenciaMes(e.target.value)} />
          </label>
          <button
            type="button"
            className="botao-secundario"
            onClick={() => setVigenciaMes(mesesAntes(vigenciaMes, -1))}
            title="Próximo mês"
            aria-label="Próximo mês"
          >
            →
          </button>
        </div>
      </div>

      {erro && <p className="mensagem-erro">{erro}</p>}

      {dados === null && !erro && <p>Carregando…</p>}

      {dados && !dados.orcamento_id && (
        <p className="estrutura-custo-aviso-sem-orcamento">
          Sem orçamento configurado para este mês — mostrando só o realizado. <Link to="/planejamento">Configurar em Planejamento →</Link>
        </p>
      )}

      {dados && resumoOrcamento && (
        <div className="estrutura-custo-fita">
          <div className="estrutura-custo-fita-item">
            <span className="rotulo">Orçado no mês</span>
            <span className="valor">{formatarMoeda(resumoOrcamento.orcado, oculto)}</span>
          </div>
          <div className="estrutura-custo-fita-item">
            <span className="rotulo">Realizado líquido</span>
            <span className="valor">{formatarMoeda(resumoOrcamento.realizado, oculto)}</span>
          </div>
          <div className="estrutura-custo-fita-item">
            <span className="rotulo">Diferença</span>
            <span className="valor" style={{ color: diferenca >= 0 ? 'var(--cor-sucesso)' : 'var(--cor-perigo)' }}>
              {formatarMoeda(diferenca, oculto)}
            </span>
          </div>
          <div className="estrutura-custo-fita-item">
            <span className="rotulo">Execução</span>
            <span className="valor">{execucao === null ? '—' : `${execucao.toFixed(1)}%`}</span>
          </div>
        </div>
      )}

      {dados && (dados.pool_despesas || dados.piso_investimentos) && (
        <div className="estrutura-custo-veredito">
          {dados.pool_despesas && (
            <div className={`estrutura-custo-veredito-item ${dados.pool_despesas.dentro_do_teto ? 'dentro' : 'fora'}`}>
              <strong>{dados.pool_despesas.dentro_do_teto ? 'Dentro do teto' : 'Acima do teto'}</strong>
              Fixos + Variáveis + Sazonalidades: {formatarMoeda(dados.pool_despesas.realizado, oculto)} de{' '}
              {formatarMoeda(dados.pool_despesas.teto, oculto)} (pool agregado — um bucket pode estourar se outro tiver folga)
            </div>
          )}
          {dados.piso_investimentos && (
            <div className={`estrutura-custo-veredito-item ${dados.piso_investimentos.meta_batida ? 'dentro' : 'fora'}`}>
              <strong>{dados.piso_investimentos.meta_batida ? 'Meta de investimento batida' : 'Abaixo da meta de investimento'}</strong>
              Investido: {formatarMoeda(dados.piso_investimentos.realizado, oculto)} de{' '}
              {formatarMoeda(dados.piso_investimentos.teto, oculto)} (piso — sobrar é bom, aqui)
            </div>
          )}
        </div>
      )}

      {dados && (
        <>
          {bucketsComItens.length > 0 && (
            <div style={{ display: 'flex', justifyContent: 'flex-end', marginBottom: 8 }}>
              <button type="button" className="botao-secundario" onClick={alternarTudo}>
                {tudoExpandido ? 'Recolher tudo' : 'Expandir tudo'}
              </button>
            </div>
          )}
          <div className="estrutura-custo-cabecalho-colunas">
            <span>Bucket / categoria / subcategoria</span>
            <span>Orçado</span>
            <span>Realizado</span>
            <span>Diferença</span>
            <span>Status</span>
            <span></span>
          </div>
          {bucketsComGrupo.map((b) => (
            <BucketBloco
              key={b.bucket}
              bucket={b}
              vigenciaMes={vigenciaMes}
              oculto={oculto}
              aberto={bucketsAbertos.has(b.bucket)}
              onToggle={() => alternarBucket(b.bucket)}
              categoriasAbertas={categoriasAbertas}
              bucketId={b.bucket}
              onAlternarCategoria={(chave) => alternarCategoria(b.bucket, chave)}
            />
          ))}
        </>
      )}
    </div>
  )
}
