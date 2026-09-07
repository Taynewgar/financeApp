import { useEffect, useState, type FormEvent } from 'react'
import '../../components/crud.css'
import '../../components/forms.css'
import { ApiError, apiFetch } from '../../lib/api'
import type { Conta, TipoConta } from '../../lib/types'

const TIPOS_CONTA: { valor: TipoConta; rotulo: string }[] = [
  { valor: 'corrente', rotulo: 'Conta corrente' },
  { valor: 'cartao_credito', rotulo: 'Cartão de crédito' },
  { valor: 'carteira', rotulo: 'Carteira' },
  { valor: 'caixinha', rotulo: 'Caixinha' },
  { valor: 'investimento', rotulo: 'Investimento' },
]

type FormState = {
  nome: string
  tipo_conta: TipoConta
  banco: string
  saldo_inicial: string
  dia_fechamento: string
  dia_vencimento: string
}

const FORM_VAZIO: FormState = {
  nome: '',
  tipo_conta: 'corrente',
  banco: '',
  saldo_inicial: '0',
  dia_fechamento: '',
  dia_vencimento: '',
}

export function ContasSection() {
  const [contas, setContas] = useState<Conta[] | null>(null)
  const [erro, setErro] = useState<string | null>(null)
  const [mostrarForm, setMostrarForm] = useState(false)
  const [editandoId, setEditandoId] = useState<string | null>(null)
  const [form, setForm] = useState<FormState>(FORM_VAZIO)
  const [salvando, setSalvando] = useState(false)

  useEffect(() => {
    apiFetch<Conta[]>('/contas')
      .then(setContas)
      .catch((e) => setErro(e instanceof ApiError ? e.message : 'Falha ao carregar contas'))
  }, [])

  function iniciarCriacao() {
    setForm(FORM_VAZIO)
    setEditandoId(null)
    setMostrarForm(true)
  }

  function iniciarEdicao(conta: Conta) {
    setForm({
      nome: conta.nome,
      tipo_conta: conta.tipo_conta,
      banco: conta.banco ?? '',
      saldo_inicial: String(conta.saldo_inicial),
      dia_fechamento: conta.dia_fechamento ? String(conta.dia_fechamento) : '',
      dia_vencimento: conta.dia_vencimento ? String(conta.dia_vencimento) : '',
    })
    setEditandoId(conta.id)
    setMostrarForm(true)
  }

  async function toggleAtivo(conta: Conta) {
    const atualizada = await apiFetch<Conta>(`/contas/${conta.id}/ativo?ativo=${!conta.ativo}`, { method: 'PATCH' })
    setContas((atual) => atual!.map((c) => (c.id === atualizada.id ? atualizada : c)))
  }

  async function handleSubmit(event: FormEvent) {
    event.preventDefault()
    setSalvando(true)
    setErro(null)
    try {
      const payload = {
        nome: form.nome,
        tipo_conta: form.tipo_conta,
        banco: form.banco || null,
        saldo_inicial: Number(form.saldo_inicial || 0),
        dia_fechamento: form.dia_fechamento ? Number(form.dia_fechamento) : null,
        dia_vencimento: form.dia_vencimento ? Number(form.dia_vencimento) : null,
      }
      if (editandoId) {
        const atualizada = await apiFetch<Conta>(`/contas/${editandoId}`, {
          method: 'PATCH',
          body: JSON.stringify(payload),
        })
        setContas((atual) => atual!.map((c) => (c.id === atualizada.id ? atualizada : c)))
      } else {
        const criada = await apiFetch<Conta>('/contas', { method: 'POST', body: JSON.stringify(payload) })
        setContas((atual) => [...(atual ?? []), criada])
      }
      setMostrarForm(false)
    } catch (e) {
      setErro(e instanceof ApiError ? (typeof e.detail === 'string' ? e.detail : e.message) : 'Falha ao salvar conta')
    } finally {
      setSalvando(false)
    }
  }

  return (
    <div>
      <div className="secao-cabecalho">
        <h2>Contas</h2>
        {!mostrarForm && (
          <button type="button" className="botao-primario" onClick={iniciarCriacao}>
            + Nova conta
          </button>
        )}
      </div>

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
              Tipo
              <select
                value={form.tipo_conta}
                onChange={(e) => setForm({ ...form, tipo_conta: e.target.value as TipoConta })}
              >
                {TIPOS_CONTA.map((t) => (
                  <option key={t.valor} value={t.valor}>
                    {t.rotulo}
                  </option>
                ))}
              </select>
            </label>
          </div>
          <div className="campo-linha">
            <label className="campo">
              Banco
              <input type="text" value={form.banco} onChange={(e) => setForm({ ...form, banco: e.target.value })} />
            </label>
            <label className="campo">
              Saldo inicial
              <input
                type="number"
                step="0.01"
                value={form.saldo_inicial}
                onChange={(e) => setForm({ ...form, saldo_inicial: e.target.value })}
              />
            </label>
          </div>
          {form.tipo_conta === 'cartao_credito' && (
            <div className="campo-linha">
              <label className="campo">
                Dia de fechamento
                <input
                  type="number"
                  min="1"
                  max="31"
                  value={form.dia_fechamento}
                  onChange={(e) => setForm({ ...form, dia_fechamento: e.target.value })}
                />
              </label>
              <label className="campo">
                Dia de vencimento
                <input
                  type="number"
                  min="1"
                  max="31"
                  value={form.dia_vencimento}
                  onChange={(e) => setForm({ ...form, dia_vencimento: e.target.value })}
                />
              </label>
            </div>
          )}
          <div className="form-acoes">
            <button type="submit" className="botao-primario" disabled={salvando}>
              {salvando ? 'Salvando…' : editandoId ? 'Salvar alterações' : 'Criar conta'}
            </button>
            <button type="button" className="botao-secundario" onClick={() => setMostrarForm(false)}>
              Cancelar
            </button>
          </div>
        </form>
      )}

      {contas === null && <p>Carregando…</p>}
      {contas?.length === 0 && <p>Nenhuma conta cadastrada ainda.</p>}
      {contas && contas.length > 0 && (
        <ul className="lista-crud">
          {contas.map((conta) => (
            <li key={conta.id} className={conta.ativo ? '' : 'item-inativo'}>
              <div className="item-linha">
                <div className="item-info">
                  <span className="item-titulo">{conta.nome}</span>
                  <span className="item-detalhe">
                    {TIPOS_CONTA.find((t) => t.valor === conta.tipo_conta)?.rotulo}
                    {conta.banco && ` — ${conta.banco}`}
                    {!conta.ativo && ' — inativa'}
                  </span>
                </div>
                <div className="item-acoes">
                  <button type="button" className="botao-link" onClick={() => iniciarEdicao(conta)}>
                    Editar
                  </button>
                  <button type="button" className="botao-link" onClick={() => toggleAtivo(conta)}>
                    {conta.ativo ? 'Desativar' : 'Reativar'}
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
