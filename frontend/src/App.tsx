import { Navigate, Route, BrowserRouter as Router, Routes } from 'react-router-dom'
import { AuthProvider } from './auth/AuthContext'
import { ProtectedRoute } from './auth/ProtectedRoute'
import { AppShell } from './components/AppShell'
import { PrivacyProvider } from './lib/PrivacyContext'
import { Configuracoes } from './routes/Configuracoes'
import { Dashboard } from './routes/Dashboard'
import { EditarLancamento } from './routes/EditarLancamento'
import { EstruturaCusto } from './routes/EstruturaCusto'
import { Graficos } from './routes/Graficos'
import { Lancamentos } from './routes/Lancamentos'
import { Login } from './routes/Login'
import { NovoLancamento } from './routes/NovoLancamento'
import { Planejamento } from './routes/Planejamento'

function App() {
  return (
    <Router>
      <AuthProvider>
        <PrivacyProvider>
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
              <Route path="lancamentos/:id/editar" element={<EditarLancamento />} />
              <Route path="planejamento" element={<Planejamento />} />
              <Route path="estruturas-de-custo" element={<EstruturaCusto />} />
              <Route path="graficos" element={<Graficos />} />
              <Route path="configuracoes" element={<Configuracoes />} />
            </Route>
            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
        </PrivacyProvider>
      </AuthProvider>
    </Router>
  )
}

export default App
