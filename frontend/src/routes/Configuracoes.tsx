import { useState } from 'react'
import '../components/crud.css'
import { CaixinhasSection } from './configuracoes/CaixinhasSection'
import { CategoriasSection } from './configuracoes/CategoriasSection'
import { ContasSection } from './configuracoes/ContasSection'
import { LancamentosRecorrentesSection } from './configuracoes/LancamentosRecorrentesSection'

type Aba = 'contas' | 'categorias' | 'caixinhas' | 'recorrentes'

const ABAS: { valor: Aba; rotulo: string }[] = [
  { valor: 'contas', rotulo: 'Contas' },
  { valor: 'categorias', rotulo: 'Categorias' },
  { valor: 'caixinhas', rotulo: 'Caixinhas' },
  { valor: 'recorrentes', rotulo: 'Despesas Fixas' },
]

export function Configuracoes() {
  const [aba, setAba] = useState<Aba>('contas')

  return (
    <div>
      <h1 style={{ fontSize: 22, marginTop: 0 }}>Configurações</h1>

      <div className="tabs">
        {ABAS.map((a) => (
          <button key={a.valor} type="button" className={aba === a.valor ? 'ativo' : ''} onClick={() => setAba(a.valor)}>
            {a.rotulo}
          </button>
        ))}
      </div>

      {aba === 'contas' && <ContasSection />}
      {aba === 'categorias' && <CategoriasSection />}
      {aba === 'caixinhas' && <CaixinhasSection />}
      {aba === 'recorrentes' && <LancamentosRecorrentesSection />}
    </div>
  )
}
