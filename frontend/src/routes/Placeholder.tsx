export function Placeholder({ titulo }: { titulo: string }) {
  return (
    <div>
      <h1 style={{ fontSize: 22, marginTop: 0 }}>{titulo}</h1>
      <p style={{ color: 'var(--cor-texto-suave)' }}>Esta tela ainda não foi construída — chega numa próxima entrega.</p>
    </div>
  )
}
