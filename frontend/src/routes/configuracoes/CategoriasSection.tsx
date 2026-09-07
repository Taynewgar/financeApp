import { useEffect, useMemo, useState, type FormEvent } from 'react'
import '../../components/crud.css'
import '../../components/forms.css'
import { ApiError, apiFetch } from '../../lib/api'
import { ordenarPorNome } from '../../lib/ordenar'
import type { Categoria, EstruturaCusto, Subcategoria, TipoCategoria } from '../../lib/types'

const TIPOS_CATEGORIA: { valor: TipoCategoria; rotulo: string }[] = [
  { valor: 'despesa', rotulo: 'Despesa' },
  { valor: 'receita', rotulo: 'Receita' },
  { valor: 'investimento', rotulo: 'Investimento' },
]

function estruturasPara(tipo: TipoCategoria): { valor: EstruturaCusto; rotulo: string }[] {
  if (tipo === 'despesa') {
    return [
      { valor: 'fixo', rotulo: 'Fixo' },
      { valor: 'variavel', rotulo: 'Variável' },
      { valor: 'sazonal', rotulo: 'Sazonal' },
    ]
  }
  if (tipo === 'investimento') {
    return [{ valor: 'investimentos', rotulo: 'Investimentos' }]
  }
  return []
}

type FormCategoria = { nome: string; tipo: TipoCategoria }
type FormSubcategoria = { nome: string; estrutura_custo_padrao: EstruturaCusto | '' }

export function CategoriasSection() {
  const [categorias, setCategorias] = useState<Categoria[] | null>(null)
  const [subcategorias, setSubcategorias] = useState<Subcategoria[]>([])
  const [erro, setErro] = useState<string | null>(null)

  const [mostrarFormCategoria, setMostrarFormCategoria] = useState(false)
  const [editandoCategoriaId, setEditandoCategoriaId] = useState<string | null>(null)
  const [formCategoria, setFormCategoria] = useState<FormCategoria>({ nome: '', tipo: 'despesa' })

  const [expandida, setExpandida] = useState<string | null>(null)
  const [novaSubcategoriaDe, setNovaSubcategoriaDe] = useState<string | null>(null)
  const [editandoSubcategoria, setEditandoSubcategoria] = useState<Subcategoria | null>(null)
  const [formSubcategoria, setFormSubcategoria] = useState<FormSubcategoria>({
    nome: '',
    estrutura_custo_padrao: '',
  })
  const [salvando, setSalvando] = useState(false)

  useEffect(() => {
    Promise.all([apiFetch<Categoria[]>('/categorias'), apiFetch<Subcategoria[]>('/subcategorias')])
      .then(([cat, sub]) => {
        setCategorias(ordenarPorNome(cat))
        setSubcategorias(ordenarPorNome(sub))
      })
      .catch((e) => setErro(e instanceof ApiError ? e.message : 'Falha ao carregar categorias'))
  }, [])

  const subcategoriasPorCategoria = useMemo(() => {
    const mapa = new Map<string, Subcategoria[]>()
    for (const s of subcategorias) {
      const lista = mapa.get(s.categoria_id) ?? []
      lista.push(s)
      mapa.set(s.categoria_id, lista)
    }
    return mapa
  }, [subcategorias])

  function iniciarCriacaoCategoria() {
    setFormCategoria({ nome: '', tipo: 'despesa' })
    setEditandoCategoriaId(null)
    setMostrarFormCategoria(true)
  }

  function iniciarEdicaoCategoria(categoria: Categoria) {
    setFormCategoria({ nome: categoria.nome, tipo: categoria.tipo })
    setEditandoCategoriaId(categoria.id)
    setMostrarFormCategoria(true)
  }

  async function toggleAtivoCategoria(categoria: Categoria) {
    const atualizada = await apiFetch<Categoria>(
      `/categorias/${categoria.id}/ativo?ativo=${!categoria.ativo}`,
      { method: 'PATCH' },
    )
    setCategorias((atual) => atual!.map((c) => (c.id === atualizada.id ? atualizada : c)))
  }

  async function handleSubmitCategoria(event: FormEvent) {
    event.preventDefault()
    setSalvando(true)
    setErro(null)
    try {
      if (editandoCategoriaId) {
        const atualizada = await apiFetch<Categoria>(`/categorias/${editandoCategoriaId}`, {
          method: 'PATCH',
          body: JSON.stringify(formCategoria),
        })
        setCategorias((atual) => ordenarPorNome(atual!.map((c) => (c.id === atualizada.id ? atualizada : c))))
      } else {
        const criada = await apiFetch<Categoria>('/categorias', {
          method: 'POST',
          body: JSON.stringify(formCategoria),
        })
        setCategorias((atual) => ordenarPorNome([...(atual ?? []), criada]))
      }
      setMostrarFormCategoria(false)
    } catch (e) {
      setErro(
        e instanceof ApiError ? (typeof e.detail === 'string' ? e.detail : e.message) : 'Falha ao salvar categoria',
      )
    } finally {
      setSalvando(false)
    }
  }

  function iniciarCriacaoSubcategoria(categoriaId: string) {
    setFormSubcategoria({ nome: '', estrutura_custo_padrao: '' })
    setNovaSubcategoriaDe(categoriaId)
    setEditandoSubcategoria(null)
  }

  function iniciarEdicaoSubcategoria(sub: Subcategoria) {
    setFormSubcategoria({ nome: sub.nome, estrutura_custo_padrao: sub.estrutura_custo_padrao ?? '' })
    setEditandoSubcategoria(sub)
    setNovaSubcategoriaDe(null)
  }

  function cancelarFormSubcategoria() {
    setNovaSubcategoriaDe(null)
    setEditandoSubcategoria(null)
  }

  async function toggleAtivoSubcategoria(sub: Subcategoria) {
    const atualizada = await apiFetch<Subcategoria>(
      `/subcategorias/${sub.id}/ativo?ativo=${!sub.ativo}`,
      { method: 'PATCH' },
    )
    setSubcategorias((atual) => atual.map((s) => (s.id === atualizada.id ? atualizada : s)))
  }

  async function handleSubmitSubcategoria(event: FormEvent, categoriaId: string) {
    event.preventDefault()
    setSalvando(true)
    setErro(null)
    try {
      const payload = {
        nome: formSubcategoria.nome,
        estrutura_custo_padrao: formSubcategoria.estrutura_custo_padrao || null,
      }
      if (editandoSubcategoria) {
        const atualizada = await apiFetch<Subcategoria>(`/subcategorias/${editandoSubcategoria.id}`, {
          method: 'PATCH',
          body: JSON.stringify(payload),
        })
        setSubcategorias((atual) => ordenarPorNome(atual.map((s) => (s.id === atualizada.id ? atualizada : s))))
        setEditandoSubcategoria(null)
      } else {
        const criada = await apiFetch<Subcategoria>('/subcategorias', {
          method: 'POST',
          body: JSON.stringify({ categoria_id: categoriaId, ...payload }),
        })
        setSubcategorias((atual) => ordenarPorNome([...atual, criada]))
        setNovaSubcategoriaDe(null)
      }
    } catch (e) {
      setErro(
        e instanceof ApiError
          ? (typeof e.detail === 'string' ? e.detail : e.message)
          : 'Falha ao salvar subcategoria',
      )
    } finally {
      setSalvando(false)
    }
  }

  return (
    <div>
      <div className="secao-cabecalho">
        <h2>Categorias</h2>
        {!mostrarFormCategoria && (
          <button type="button" className="botao-primario" onClick={iniciarCriacaoCategoria}>
            + Nova categoria
          </button>
        )}
      </div>

      <p style={{ color: 'var(--cor-texto-suave)', fontSize: 13, marginTop: -4 }}>
        Receita e Investimento podem ter mais de uma categoria (ex: "Salário", "Freelance" em Receita) — o Novo
        Lançamento deixa escolher entre as do tipo certo. Investimento sempre usa estrutura de custo fixa; Receita
        não usa estrutura de custo nem meio de pagamento.
      </p>

      {erro && <p className="mensagem-erro">{erro}</p>}

      {mostrarFormCategoria && (
        <form className="form" onSubmit={handleSubmitCategoria} style={{ marginBottom: 20 }}>
          <div className="campo-linha">
            <label className="campo">
              Nome
              <input
                type="text"
                required
                value={formCategoria.nome}
                onChange={(e) => setFormCategoria({ ...formCategoria, nome: e.target.value })}
              />
            </label>
            <label className="campo">
              Tipo
              <select
                value={formCategoria.tipo}
                onChange={(e) => setFormCategoria({ ...formCategoria, tipo: e.target.value as TipoCategoria })}
              >
                {TIPOS_CATEGORIA.map((t) => (
                  <option key={t.valor} value={t.valor}>
                    {t.rotulo}
                  </option>
                ))}
              </select>
            </label>
          </div>
          <div className="form-acoes">
            <button type="submit" className="botao-primario" disabled={salvando}>
              {salvando ? 'Salvando…' : editandoCategoriaId ? 'Salvar alterações' : 'Criar categoria'}
            </button>
            <button type="button" className="botao-secundario" onClick={() => setMostrarFormCategoria(false)}>
              Cancelar
            </button>
          </div>
        </form>
      )}

      {categorias === null && <p>Carregando…</p>}
      {categorias?.length === 0 && <p>Nenhuma categoria cadastrada ainda.</p>}
      {categorias && categorias.length > 0 && (
        <ul className="lista-crud">
          {categorias.map((categoria) => {
            const subs = subcategoriasPorCategoria.get(categoria.id) ?? []
            const aberta = expandida === categoria.id
            const formAbertoAqui =
              novaSubcategoriaDe === categoria.id || editandoSubcategoria?.categoria_id === categoria.id
            return (
              <li key={categoria.id} className={categoria.ativo ? '' : 'item-inativo'}>
                <div className="item-linha">
                  <div className="item-info">
                    <span className="item-titulo">{categoria.nome}</span>
                    <span className="item-detalhe">
                      {TIPOS_CATEGORIA.find((t) => t.valor === categoria.tipo)?.rotulo}
                      {!categoria.ativo && ' — inativa'}
                    </span>
                  </div>
                  <div className="item-acoes">
                    <button
                      type="button"
                      className="botao-link"
                      onClick={() => setExpandida(aberta ? null : categoria.id)}
                    >
                      {aberta ? 'Ocultar subcategorias' : `Subcategorias (${subs.length})`}
                    </button>
                    <button type="button" className="botao-link" onClick={() => iniciarEdicaoCategoria(categoria)}>
                      Editar
                    </button>
                    <button type="button" className="botao-link" onClick={() => toggleAtivoCategoria(categoria)}>
                      {categoria.ativo ? 'Desativar' : 'Reativar'}
                    </button>
                  </div>
                </div>

                {aberta && (
                  <ul className="subcategorias">
                    {subs.map((sub) => (
                      <li key={sub.id} className={sub.ativo ? '' : 'item-inativo'}>
                        <div className="item-linha">
                          <div className="item-info">
                            <span>{sub.nome}</span>
                            <span className="item-detalhe">
                              {sub.estrutura_custo_padrao ?? 'sem estrutura padrão'}
                              {!sub.ativo && ' — inativa'}
                            </span>
                          </div>
                          <div className="item-acoes">
                            <button
                              type="button"
                              className="botao-link"
                              onClick={() => iniciarEdicaoSubcategoria(sub)}
                            >
                              Editar
                            </button>
                            <button type="button" className="botao-link" onClick={() => toggleAtivoSubcategoria(sub)}>
                              {sub.ativo ? 'Desativar' : 'Reativar'}
                            </button>
                          </div>
                        </div>
                      </li>
                    ))}

                    {formAbertoAqui ? (
                      <li>
                        <form
                          className="form"
                          onSubmit={(e) => handleSubmitSubcategoria(e, categoria.id)}
                          style={{ maxWidth: 420 }}
                        >
                          <div className="campo-linha">
                            <label className="campo">
                              Nome
                              <input
                                type="text"
                                required
                                value={formSubcategoria.nome}
                                onChange={(e) => setFormSubcategoria({ ...formSubcategoria, nome: e.target.value })}
                              />
                            </label>
                            {estruturasPara(categoria.tipo).length > 0 && (
                              <label className="campo">
                                Estrutura padrão
                                <select
                                  value={formSubcategoria.estrutura_custo_padrao}
                                  onChange={(e) =>
                                    setFormSubcategoria({
                                      ...formSubcategoria,
                                      estrutura_custo_padrao: e.target.value as EstruturaCusto | '',
                                    })
                                  }
                                >
                                  <option value="">Nenhuma (força escolha manual)</option>
                                  {estruturasPara(categoria.tipo).map((e) => (
                                    <option key={e.valor} value={e.valor}>
                                      {e.rotulo}
                                    </option>
                                  ))}
                                </select>
                              </label>
                            )}
                          </div>
                          <div className="form-acoes">
                            <button type="submit" className="botao-primario" disabled={salvando}>
                              {salvando ? 'Salvando…' : editandoSubcategoria ? 'Salvar alterações' : 'Criar subcategoria'}
                            </button>
                            <button type="button" className="botao-secundario" onClick={cancelarFormSubcategoria}>
                              Cancelar
                            </button>
                          </div>
                        </form>
                      </li>
                    ) : (
                      <li>
                        <button
                          type="button"
                          className="botao-link"
                          onClick={() => iniciarCriacaoSubcategoria(categoria.id)}
                        >
                          + Nova subcategoria
                        </button>
                      </li>
                    )}
                  </ul>
                )}
              </li>
            )
          })}
        </ul>
      )}
    </div>
  )
}
