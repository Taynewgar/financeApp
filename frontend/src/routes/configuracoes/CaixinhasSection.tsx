import { useEffect, useState, type FormEvent } from 'react'
import '../../components/crud.css'
import '../../components/forms.css'
import { ApiError, apiFetch } from '../../lib/api'
import { ordenarPorNome } from '../../lib/ordenar'
import type { Caixinha, Conta } from '../../lib/types'

type FormState = { nome: string; conta_id: string }

export function CaixinhasSection() {
  const [caixinhas, setCaixinhas] = useState<Caixinha[] | null>(null)
  const [contas, setContas] = useState<Conta[]>([])
  const [erro, setErro] = useState<string | null>(null)
  const [mostrarForm, setMostrarForm] = useState(false)
  const [editandoId, setEditandoId] = useState<string | null>(null)
  // guarda a conta original ao editar — vinculada a caixinha, a conta fica
  // travada (evita "teleportar" o saldo da reserva de uma conta pra outra)
  const [contaTravada, setContaTravada] = useState(false)
  const [form, setForm] = useState<FormState>({ nome: '', conta_id: '' })
  const [salvando, setSalvando] = useState(false)

  useEffect(() => {
    Promise.all([apiFetch<Caixinha[]>('/caixinhas'), apiFetch<Conta[]>('/contas')])
      .then(([cx, c]) => {
        setCaixinhas(ordenarPorNome(cx))
        setContas(c.filter((x) => x.ativo))
      })
      .catch((e) => setErro(e instanceof ApiError ? e.message : 'Falha ao carregar caixinhas'))
  }, [])

  function iniciarCriacao() {
    setForm({ nome: '', conta_id: '' })
    setEditandoId(null)
    setContaTravada(false)
    setMostrarForm(true)
  }

  function iniciarEdicao(caixinha: Caixinha) {
    setForm({ nome: caixinha.nome, conta_id: caixinha.conta_id ?? '' })
    setEditandoId(caixinha.id)
    setContaTravada(!!caixinha.conta_id)
    setMostrarForm(true)
  }

  async function toggleAtivo(caixinha: Caixinha) {
    const atualizada = await apiFetch<Caixinha>(
      `/caixinhas/${caixinha.id}/ativo?ativo=${!caixinha.ativo}`,
      { method: 'PATCH' },
    )
    setCaixinhas((atual) => atual!.map((c) => (c.id === atualizada.id ? atualizada : c)))
  }

  async function handleSubmit(event: FormEvent) {
    event.preventDefault()
    setSalvando(true)
    setErro(null)
    try {
      const payload: { nome: string; conta_id?: string | null } = { nome: form.nome }
      if (!contaTravada) {
        payload.conta_id = form.conta_id || null
      }
      if (editandoId) {
        const atualizada = await apiFetch<Caixinha>(`/caixinhas/${editandoId}`, {
          method: 'PATCH',
          body: JSON.stringify(payload),
        })
        setCaixinhas((atual) => ordenarPorNome(atual!.map((c) => (c.id === atualizada.id ? atualizada : c))))
      } else {
        const criada = await apiFetch<Caixinha>('/caixinhas', { method: 'POST', body: JSON.stringify(payload) })
        setCaixinhas((atual) => ordenarPorNome([...(atual ?? []), criada]))
      }
      setMostrarForm(false)
    } catch (e) {
      setErro(
        e instanceof ApiError ? (typeof e.detail === 'string' ? e.detail : e.message) : 'Falha ao salvar caixinha',
      )
    } finally {
      setSalvando(false)
    }
  }

  return (
    <div>
      <div className="secao-cabecalho">
        <h2>Caixinhas</h2>
        {!mostrarForm && (
          <button type="button" className="botao-primario" onClick={iniciarCriacao}>
            + Nova caixinha
          </button>
        )}
      </div>

      <p style={{ color: 'var(--cor-texto-suave)', fontSize: 13, marginTop: -4 }}>
        Caixinha é reserva, não investimento — no Novo Lançamento ela só aparece no tipo Reserva.
      </p>

      {erro && <p className="mensagem-erro">{erro}</p>}

      {mostrarForm && (
        <form className="form" onSubmit={handleSubmit} style={{ marginBottom: 20 }}>
          <div className="campo-linha">
            <label className="campo">
              Nome
              <input
                type="text"
                required
                value={form.nome}
                onChange={(e) => setForm({ ...form, nome: e.target.value })}
              />
            </label>
            <label className="campo">
              Conta vinculada
              <select
                value={form.conta_id}
                onChange={(e) => setForm({ ...form, conta_id: e.target.value })}
                disabled={contaTravada}
              >
                <option value="">Nenhuma</option>
                {contas.map((c) => (
                  <option key={c.id} value={c.id}>
                    {c.nome}
                  </option>
                ))}
              </select>
              {contaTravada && (
                <span style={{ fontSize: 12, color: 'var(--cor-texto-suave)' }}>
                  Já vinculada — não é possível trocar a conta depois de vinculada.
                </span>
              )}
            </label>
          </div>
          <div className="form-acoes">
            <button type="submit" className="botao-primario" disabled={salvando}>
              {salvando ? 'Salvando…' : editandoId ? 'Salvar alterações' : 'Criar caixinha'}
            </button>
            <button type="button" className="botao-secundario" onClick={() => setMostrarForm(false)}>
              Cancelar
            </button>
          </div>
        </form>
      )}

      {caixinhas === null && <p>Carregando…</p>}
      {caixinhas?.length === 0 && <p>Nenhuma caixinha cadastrada ainda.</p>}
      {caixinhas && caixinhas.length > 0 && (
        <ul className="lista-crud">
          {caixinhas.map((caixinha) => (
            <li key={caixinha.id} className={caixinha.ativo ? '' : 'item-inativo'}>
              <div className="item-linha">
                <div className="item-info">
                  <span className="item-titulo">{caixinha.nome}</span>
                  <span className="item-detalhe">
                    {contas.find((c) => c.id === caixinha.conta_id)?.nome ?? 'sem conta vinculada'}
                    {!caixinha.ativo && ' — inativa'}
                  </span>
                </div>
                <div className="item-acoes">
                  <button type="button" className="botao-link" onClick={() => iniciarEdicao(caixinha)}>
                    Editar
                  </button>
                  <button type="button" className="botao-link" onClick={() => toggleAtivo(caixinha)}>
                    {caixinha.ativo ? 'Desativar' : 'Reativar'}
                  </button>
                </div>
              </div>
            </li>
          ))}
        </ul>
      )}
    </div>
  )
}
