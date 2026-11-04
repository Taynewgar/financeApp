export function ordenarPorNome<T extends { nome: string }>(lista: T[]): T[] {
  return [...lista].sort((a, b) => a.nome.localeCompare(b.nome, 'pt-BR'))
}
