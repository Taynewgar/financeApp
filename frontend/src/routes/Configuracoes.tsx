import { useEffect, useState } from 'react'
import { ApiError, apiFetch } from '../lib/api'

type Conta = {
  id: string
  nome: string
  tipo_conta: string
  ativo: boolean
}

export function Configuracoes() {
  const [contas, setContas] = useState<Conta[] | null>(null)
  const [erro, setErro] = useState<string | null>(null)

  useEffect(() => {
    apiFetch<Conta[]>('/contas')
      .then(setContas)
      .catch((e) => setErro(e instanceof ApiError ? e.message : 'Falha ao carregar contas'))
  }, [])

  return (
    <div>
      <h1 style={{ fontSize: 22, marginTop: 0 }}>Configurações</h1>
      <p style={{ color: 'var(--cor-texto-suave)' }}>
        Contas, categorias, subcategorias e caixinhas ganham formulários próprios numa próxima entrega. Por
        enquanto, esta lista já confirma que a API está retornando dados reais e autenticados.
      </p>

      <h2 style={{ fontSize: 16 }}>Suas contas</h2>
      {erro && <p style={{ color: 'var(--cor-perigo)' }}>{erro}</p>}
      {!erro && contas === null && <p>Carregando…</p>}
      {contas?.length === 0 && <p>Nenhuma conta cadastrada ainda.</p>}
      {contas && contas.length > 0 && (
        <ul style={{ paddingLeft: 20 }}>
          {contas.map((conta) => (
            <li key={conta.id}>
              {conta.nome} — {conta.tipo_conta}
              {!conta.ativo && ' (inativa)'}
            </li>
          ))}
        </ul>
      )}
    </div>
  )
}
