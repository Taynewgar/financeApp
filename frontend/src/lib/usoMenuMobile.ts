const CHAVE_STORAGE = 'financeapp:menu-mobile-uso'

// item promovido só se tiver pelo menos o dobro de cliques do 2º
// colocado — evita ficar trocando o destaque a cada clique quando 2
// itens estão empatados/próximos (ver docs/backlog.md, item 29)
const RAZAO_MINIMA_PARA_DESTACAR = 2

// sem isso, 1 clique num item nunca antes visitado já promovia (2º
// colocado em 0 cliques satisfaz qualquer "razão mínima" trivialmente) —
// exige uso mínimo antes de rotular algo como "mais usado"
const CLIQUES_MINIMOS_PARA_DESTACAR = 3

function lerContagens(): Record<string, number> {
  try {
    const bruto = localStorage.getItem(CHAVE_STORAGE)
    return bruto ? JSON.parse(bruto) : {}
  } catch {
    return {}
  }
}

/** Registra 1 navegação bem-sucedida pra uma rota do menu "mais" da
 * barra inferior mobile — contador local (por dispositivo, sem
 * sincronizar entre aparelhos; ver detalhe da decisão no backlog). */
export function registrarUsoMenuMobile(rota: string): void {
  try {
    const contagens = lerContagens()
    contagens[rota] = (contagens[rota] ?? 0) + 1
    localStorage.setItem(CHAVE_STORAGE, JSON.stringify(contagens))
  } catch {
    // localStorage indisponível (aba privada, storage bloqueado) — só não promove nada
  }
}

/** Dentre os itens informados, qual (se algum) já acumulou uso
 * suficiente pra ser destacado como atalho — só promove se o mais
 * clicado tiver pelo menos o dobro de cliques do 2º colocado. */
export function itemMaisUsadoMenuMobile<T extends { to: string }>(itens: T[]): T | null {
  const contagens = lerContagens()
  const ordenados = [...itens].sort((a, b) => (contagens[b.to] ?? 0) - (contagens[a.to] ?? 0))
  const primeiro = ordenados[0]
  const segundo = ordenados[1]
  if (!primeiro || (contagens[primeiro.to] ?? 0) < CLIQUES_MINIMOS_PARA_DESTACAR) return null
  const contagemSegundo = segundo ? (contagens[segundo.to] ?? 0) : 0
  if (contagemSegundo > 0 && contagens[primeiro.to]! < contagemSegundo * RAZAO_MINIMA_PARA_DESTACAR) return null
  return primeiro
}
