import { Navigate, Route, BrowserRouter as Router, Routes } from 'react-router-dom'
import { AuthProvider } from './auth/AuthContext'
import { ProtectedRoute } from './auth/ProtectedRoute'
import { AppShell } from './components/AppShell'
import { Configuracoes } from './routes/Configuracoes'
import { Dashboard } from './routes/Dashboard'
import { Lancamentos } from './routes/Lancamentos'
import { Login } from './routes/Login'
import { NovoLancamento } from './routes/NovoLancamento'
import { Placeholder } from './routes/Placeholder'

function App() {
  return (
    <Router>
      <AuthProvider>
        <Routes>
          <Route path="/login" element={<Login />} />
          <Route
            path="/"
            element={
              <ProtectedRoute>
                <AppShell />
              </ProtectedRoute>
            }
          >
            <Route index element={<Navigate to="/dashboard" replace />} />
            <Route path="dashboard" element={<Dashboard />} />
            <Route path="lancamentos" element={<Lancamentos />} />
            <Route path="lancamentos/novo" element={<NovoLancamento />} />
            <Route path="planejamento" element={<Placeholder titulo="Planejamento (Orçamento)" />} />
            <Route path="estruturas-de-custo" element={<Placeholder titulo="Estruturas de Custo" />} />
            <Route path="configuracoes" element={<Configuracoes />} />
          </Route>
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </AuthProvider>
    </Router>
  )
}

export default App
