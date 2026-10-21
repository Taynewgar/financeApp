/** Picker em abas (Rodada 91/98) — compartilhado entre ComparadorSeries e
 * ComparadorAnoAno: mesma estrutura de grupos (Receita/Despesa sub/
 * Categoria pai/Estrutura/Caixinhas), mesmo corte "mais usadas" com "ver
 * todas" agrupado por seção. Só muda como cada componente RENDERIZA a
 * linha (checkbox multi-seleção vs. radio de 1 item só). */

export type ItemPicker = { chave: string; nome: string; cor: string; secao?: string }
export type LinhaPicker = { tipo: 'cabecalho'; titulo: string } | { tipo: 'item'; item: ItemPicker }
export type LinkRodapePicker = { mostrar: boolean; texto: string; acao: () => void }

export const LIMITE_PICKER = 5

/** Monta as linhas visíveis de 1 aba: corte "mais usadas" (os itens já
 * vêm ranqueados por uso do backend) quando a lista é grande e não há
 * busca nem expansão ativa; senão a lista filtrada (por busca, se houver),
 * agrupada por `secao` quando ela existe. `temCorte` informa se cabe um
 * link de "ver todas"/"recolher" (quem decide o texto/ação é o chamador,
 * que tem o `setVerTodas` da aba atual). */
export function montarLinhasPicker(
  todos: ItemPicker[],
  busca: string,
  expandida: boolean,
): { linhas: LinhaPicker[]; temCorte: boolean } {
  const buscaTexto = busca.trim().toLowerCase()
  const buscaAtiva = buscaTexto.length > 0
  const temCorte = todos.length > LIMITE_PICKER
  const fazerItem = (s: ItemPicker): LinhaPicker => ({ tipo: 'item', item: s })

  if (!buscaAtiva && temCorte && !expandida) {
    return { linhas: todos.slice(0, LIMITE_PICKER).map(fazerItem), temCorte }
  }

  const filtrados = buscaAtiva ? todos.filter((s) => s.nome.toLowerCase().includes(buscaTexto)) : todos
  const temSecoes = filtrados.some((s) => s.secao)
  if (temSecoes && !buscaAtiva) {
    const ordemSecoes: string[] = []
    const porSecao = new Map<string, ItemPicker[]>()
    filtrados.forEach((s) => {
      const chaveSecao = s.secao ?? ''
      if (!porSecao.has(chaveSecao)) {
        porSecao.set(chaveSecao, [])
        ordemSecoes.push(chaveSecao)
      }
      porSecao.get(chaveSecao)!.push(s)
    })
    const linhas: LinhaPicker[] = []
    ordemSecoes.forEach((secao) => {
      linhas.push({ tipo: 'cabecalho', titulo: secao })
      porSecao.get(secao)!.forEach((s) => linhas.push(fazerItem(s)))
    })
    return { linhas, temCorte }
  }

  return { linhas: filtrados.map(fazerItem), temCorte }
}
