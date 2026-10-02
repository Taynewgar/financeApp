# Sugestões e decisões do redesign — conversa completa

Esta é a conversa que aconteceu logo depois dos 4 mockups serem mostrados
pela primeira vez (ver `changelog-proposta-original-do-redesign.md` e `docs/mockups/`):
uma rodada de perguntas suas sobre cada decisão do `plano-de-evolucao-original.md`,
com minhas respostas detalhadas, que terminou na divisão final em 7 entregas
que efetivamente guiou o desenvolvimento. Recuperada do histórico da sessão
e salva aqui porque só existia em texto de conversa.

As perguntas estão resumidas/citadas pra dar contexto; as respostas são
reproduzidas na íntegra — são "as sugestões" que este documento existe pra
preservar.

---

## 1) PWA + linguagem para escalar

**Pergunta:** PWA confirmado. Python é uma boa escolha se um dia precisar escalar?

**Resposta:**

Combinação PWA (frontend) e Python/FastAPI (backend) faz sentido para o seu caso. Recomendo manter Python:

- O gargalo de um app financeiro pessoal quase nunca é a linguagem — é banco de dados (índices, agregações). FastAPI + Uvicorn roda async e aguenta tranquilamente a escala de um app pessoal/familiar até SaaS pequeno (milhares de usuários) sem trocar de linguagem.
- Você já tem lógica de negócio testada em Python (`data_processor.py`, `budget_repository.py`, 76 testes). Reescrever em Node/Go para "escalar" jogaria fora esse trabalho por um ganho de performance que você provavelmente nunca vai sentir nesse tipo de aplicação.
- Caminho real de escala, se um dia precisar: empurrar agregações pesadas para SQL/views no Postgres (Supabase) em vez de pandas, e escalar horizontalmente instâncias do FastAPI no Render (stateless). É um problema de arquitetura de dados, não de linguagem.

Só reconsideraria a linguagem se o plano fosse virar produto com processamento massivo em tempo real (não é o seu caso).

---

## 2) Feature de cartão de crédito — implantar antes da nova arquitetura de contas?

**Pergunta:** Existe intenção de fazer análise detalhada da fatura de cartão. Vale implementar antes de migrar pra contas novas?

**Resposta:**

Recomendo **não** implantar antes. Análise de fatura precisa de duas coisas que só existem no modelo `contas` novo: dia de fechamento/vencimento e agrupamento por ciclo (não mês civil). Construir isso em cima da estrutura atual (texto livre em "Meio de Pagamento") significaria hardcodar essas datas em algum lugar improvisado — exatamente o tipo de acoplamento que já identifiquei como problema no código atual (`file_loader.py` acoplado ao Tkinter).

Minha sugestão: **é uma das primeiras features a construir *na nova arquitetura*** — logo depois do schema de `contas` (fase 1/2), antes até de outras análises. Ela é de alto valor e valida o modelo novo cedo. Só não a construa como remendo no app antigo.

*(Decisão seguida: virou parte da Entrega 4 — "Lançamento + Cartão de Crédito".)*

---

## 3) Segurança da migração de dados

**Pergunta:** O script de migração já roda contra a estrutura nova? Existe risco de corromper, duplicar ou perder dados?

**Resposta:**

Sim, o script trabalha direto contra o schema novo (lê do `historico_lancamentos.csv`/`orcamentos.json` antigos, escreve nas tabelas novas). Mitigação concreta:

- Roda primeiro contra um Supabase de staging vazio — nunca contra produção direto.
- Reaproveita o hash de deduplicação que já existe (`LedgerRepository.row_key`) como *unique constraint* no Postgres → rodar de novo não duplica, é idempotente.
- Migração inteira em transação (ou lotes com checkpoint) → falha no meio faz rollback, não deixa estado inconsistente.
- Modo dry-run primeiro: só conta e reporta, não grava.
- **Os arquivos originais nunca são tocados** — ficam como ponto de rollback até você validar o sistema novo rodando em paralelo por um tempo.
- Checagem de reconciliação automática pós-migração: soma de receita/despesa por mês no CSV antigo tem que bater exatamente com a soma no banco novo.

Com isso, perda ≈ zero (fonte nunca é alterada), duplicação ≈ zero (constraint de hash), corrupção mitigada (transação + dry-run + reconciliação).

> **Status:** `hash_dedup` (a constraint) está implementado desde a Entrega 1. O script de migração em si ainda não foi construído — é o gap "migração de dados" do backlog atual.

---

## 4) Compras parceladas — modelo

**Pergunta:** Existe previsão pra compra parcelada? Ela é lançada mês a mês conforme a parcela é paga?

**Resposta:**

Sim, já desenhei `parcela_atual`/`parcela_total` no schema. Recomendo o modelo que **espelha a fatura real do cartão**: ao registrar a compra parcelada (ex: Notebook R$ 2.450 em 10x), o sistema já cria as 10 transações de uma vez, uma por ciclo futuro, ligadas por um `compra_parcelada_id` — igual ao extrato do banco, onde cada parcela já aparece como linha separada em cada fatura. Isso evita lógica de "projeção calculada" por trás dos panos (mais frágil) e permite cancelar/ajustar parcelas restantes individualmente se a compra for estornada no meio do caminho.

Numa rodada seguinte você perguntou se "projeção calculada" era o que o app antigo já fazia — não: hoje **não existe nenhum tratamento de parcela** no app antigo. Cada parcela é só uma transação comum, sem vínculo com as outras parcelas da mesma compra e sem visibilidade do que ainda vai vir. O modelo proposto (materializar todas as parcelas no ato do lançamento) é uma capacidade nova, não uma evolução de algo que já existia.

> **Status:** ✅ implementado exatamente assim (`POST /transacoes/parceladas`, `compra_parcelada_id`).

---

## 5) Diagnóstico de qualidade dos dados / CSV opcional

**Pergunta:** O diagnóstico de dados seria essencial por manter a importação de CSV como opcional, certo?

**Resposta:**

Sim, exatamente — fica **ainda mais essencial** se o CSV continuar como via opcional, porque importação de banco não passa pela validação/divulgação progressiva do formulário guiado e pode trazer linhas incompletas. Sugiro reforçar: transformar o diagnóstico numa **tela de revisão de importação** (mostra o que não mapeou antes de gravar, você corrige ali), não só um painel que você olha depois no relatório.

> **Status:** ⬜ não implementado — depende da fase de migração/import, ainda não iniciada.

---

## 6) Fatura por ciclo de fechamento — o problema real que você relatou

**Pergunta original:** "Hoje encontro problemas pois algumas compras não são computadas para a fatura do mês, caso sejam realizadas próximo ao dia de fechamento, logo preciso alterar a data real da compra para o próximo ciclo. Existe forma fluida de contornar esse problema?"

**Resposta:**

Isso se resolve estruturalmente com `dia_fechamento` na conta. Proposta:

- `data_compra` fica **sempre real, imutável** — você nunca mais "engana" a data.
- Um campo calculado `fatura_referencia` deriva automaticamente de `data_compra` + `dia_fechamento` da conta. Cartão fecha dia 25: compra em 24/08 → fatura Agosto; compra em 26/08 → fatura Setembro. Isso sozinho resolve 95% do seu problema hoje.
- **"Transferir para a próxima fatura" como ação manual**: sim, vale ter como exceção — útil para quando o próprio banco posta a transação um ciclo atrasada (atraso de processamento, não é matemática de ciclo). Um botão "mover fatura" que seta um `fatura_override` sem tocar a `data_compra`. Mas isso deve ser a exceção, não o mecanismo principal.

**Você então detalhou seu caso real** (fechamento dia 8, vencimento dia 10, compra no dia 5 às vezes cai na fatura seguinte por atraso de lojista/adquirente) e perguntou minha sugestão específica. Resposta:

Você está certo, isso não é raro — é atraso de processamento do lojista/adquirente, não erro de matemática de data. A matemática pura (`data_compra` + `dia_fechamento`) acerta a maioria dos casos, mas não prevê esse atraso de liquidação. Recomendo tratar como fluxo normal, não exceção escondida:

1. **Cálculo automático continua sendo o padrão** — resolve a maior parte dos casos.
2. **"Mover para próxima fatura" como ação de primeira classe**, não enterrada em um menu — um botão visível na transação, que muda só a `fatura_referencia`, nunca a `data_compra` real.
3. **Aviso preventivo**: para compras feitas nos últimos N dias antes do fechamento (configurável — no seu caso uns 3-5 dias antes do dia 8), a transação ganha um selo discreto "Perto do fechamento — confira em qual fatura caiu", pra você não descobrir só quando a fatura fechar.
4. **Fluxo de reconciliação da fatura**: ao fechar o ciclo, uma tela mostra tudo que o app colocou em "Fatura Agosto" lado a lado com o extrato real do banco, pra mover em lote o que caiu errado — em vez de caçar transação por transação.

**Você perguntou se dava pra carregar o arquivo da fatura do banco nesse fluxo de reconciliação.** Resposta:

Boa ideia, e reforça o fluxo que já propus. Funcionaria assim:

- **Se o banco exporta OFX** (a maioria dos grandes bancos brasileiros exporta): é o formato ideal, porque cada transação já vem com um ID único (FITID) — o casamento com o que você já lançou fica quase exato, sem ambiguidade.
- **Se só tiver CSV/PDF da fatura**: casamento por aproximação (valor + data + descrição), reaproveitando a mesma lógica de correspondência fuzzy que o `file_loader.py` atual já usa para variações de formato.
- O resultado do casamento alimenta a tela de reconciliação: o que bateu fica confirmado automaticamente; o que está no banco mas não no app vira sugestão de lançamento faltante; o que está no app mas em fatura diferente da que o banco mostrou vira sugestão de "mover fatura" com 1 clique.

Isso entraria como parte da Entrega 4 (junto com a feature de cartão de crédito).

> **Status:** ✅ cálculo automático de `fatura_referencia` implementado; ✅ "mover fatura" manual implementado (`PATCH /transacoes/{id}/fatura`, marca `fatura_override`). ⬜ Aviso preventivo de "perto do fechamento", ⬜ tela de reconciliação, e ⬜ upload de OFX/fatura do banco — nenhum dos três foi implementado ainda.

---

## 7) Orçamento em R$ — correção sobre o que já existia

**Pergunta:** "Hoje já existe em reais e percentual. Em reais é um campo editável, não?"

**Resposta:**

Você está certo, me equivoquei — hoje o campo de orçamento em R$ **já é editável** por item (junto com o percentual) no app antigo. O gap real não é "adicionar R$", é outro: R$ e % são dois campos editados **independentemente**, sem sincronização — você pode editar um e esquecer de atualizar o outro, e eles ficam representando coisas diferentes. Sugestão real: escolher uma fonte de verdade por item (ex: você digita R$, o % é recalculado automaticamente a partir da renda disponível, com um toggle pra inverter quem manda) em vez de dois campos soltos.

**Você perguntou se dava pra fazer rollback caso não gostasse do toggle.** Resposta:

Sim, é seguro testar. É uma preferência de **interação**, não uma decisão de schema: os dois valores (R$ e %) continuam sempre salvos e sincronizados — o toggle só define qual campo você edita diretamente (o outro é recalculado). Trocar de volta pra % depois não perde nem migra dado nenhum.

> **Status:** ⬜ não implementado — backend hoje só aceita entrada em R$ por item (`orcamento_mensal`), sem toggle de fonte de verdade.

---

## 8) Orçado × realizado × mês anterior fica em Estruturas de Custo

**Pergunta:** "Comparação de orçado x realizado x mês fica em estrutura de custos. Orçamento seria só uma configuração dos valores que pretendo gastar que alimentaria as outras features."

**Resposta:**

Concordo com a divisão. Ajusta bem o que eu tinha desenhado: Planejamento define os valores-alvo (R$/%), Estruturas de Custo faz a leitura fina do realizado. Nenhuma mudança necessária no mockup que você já validou como "resumo".

> **Status:** ✅ backend segue exatamente essa divisão (`orcamentos` define alvo, `GET /estrutura-custo/{mes}` lê o realizado). Comparação com "mês anterior" especificamente ainda não existe em nenhum dos dois.

---

## 9) Orçamento de envelope — explicado com exemplo

**Pergunta:** "Orçamento de envelope: como assim? Me dê exemplos."

**Resposta:**

É o modelo do YNAB: cada categoria é um "envelope" com dinheiro dentro pro mês. Exemplo: envelope "Restaurante" = R$400/mês. Em agosto você gastou R$310, sobram R$90.
- **Hoje** (sem envelope): a sobra some — setembro recomeça do zero em R$400, sem rastro.
- **Com envelope**: você decide explicitamente o que fazer com os R$90 — *acumular* (setembro passa a ter R$490 em Restaurante), *transferir* (mandar para outro envelope que estourou, tipo Mercado), ou *resgatar* (soma na Reserva de Emergência).

É complexidade real — sugiro tratar como opcional/avançado, não obrigatório no MVP.

Você respondeu "entendi e gostei, gostaria de testar" — anotei um exemplo visual no card "Custos Fixos" do mockup de Planejamento (sobra de R$130,00 com as ações Acumular/Transferir/Reserva).

> **Status:** 🟡 implementado ponta a ponta como acumulação automática — backend (`saldo_anterior`, `POST /orcamentos/{id}/proximo-mes`) e a tela de Planejamento já mostra a sobra por item — mas sem as três ações manuais (acumular/transferir/resgatar) do mockup; hoje é só "acumula sempre", sem escolha.

---

## 10) Múltiplos templates de orçamento — decisão de não fazer

**Pergunta:** "Acredito que isso estaria previsto pois existe orçamento para sazonalidades. Me dê sua opinião sobre o que seria melhor."

**Resposta:**

Concordo com você: Sazonalidades já cobre bem o caso "este mês tem um gasto fora do padrão" (IPVA, viagem, 13º). Templates completos só fariam sentido se o mês inteiro mudasse de formato (ex: mês sabático, licença). Minha recomendação: **não construir múltiplos templates** — em vez disso, dar **versionamento por mês** ao orçamento (editar agosto não altera setembro retroativamente). Resolve o mesmo problema com muito menos UI.

> **Status:** ✅ implementado — orçamento é versionado por `vigencia_mes`, exatamente como recomendado, sem sistema de templates.

---

## 11) Categorias com mais de um Custo (ex: Lazer em Fixo, Variável e Sazonal)

**Pergunta:** "Como tratar categorias que podem ser mais de 1 custo? Por exemplo Lazer: tenho gastos de lazer em custos fixos, variáveis e sazonais."

**Resposta:**

Boa correção ao que eu tinha proposto — "Custo" não pode ser uma propriedade fixa da categoria quando ela é genuinamente mista. Ajustei para: a **subcategoria carrega uma sugestão padrão** (pré-seleciona o chip mais provável, ex: Mercado → Variável), mas o campo continua visível e editável com 1 toque no formulário — não é mais um valor escondido/automático sem chance de correção. Pra combinações sabidamente mistas (ex: Lazer > Viagens), dá pra deixar a subcategoria sem sugestão padrão, forçando escolha consciente.

> **Status:** ✅ implementado exatamente assim — `estrutura_custo_padrao` é da *subcategoria* (não da categoria), sempre editável no formulário.

---

## 12) Reserva de Emergência: conta ou investimento?

**Pergunta:** "Reserva de emergência deve ser tratada como uma conta ou deveria ser tratada como um investimento? Foi removida a tabela investimento da estrutura de custos ou ela foi mantida?"

**Resposta:**

Os dois, em camadas diferentes:
- **Investimentos** continua existindo como bucket de orçamento (não removi — no mockup de Planejamento os 4 buckets, incluindo Investimentos, seguem lá) — essa é a camada de *planejamento*: "pretendo destinar X% aos investimentos, com uma linha Reserva de Emergência".
- **Conta tipo Caixinha/Reserva** é a camada de *saldo real*: quanto você realmente tem guardado.

Recomendo linkar os dois: a linha "Reserva de Emergência" do orçamento referencia a conta-caixinha correspondente. Quando você lança uma "Aplicação" pra ela, isso conta pra execução do orçamento de Investimentos **e** aumenta o saldo real da conta ao mesmo tempo. Não é ou/ou.

> **Status:** 🟡 parcial — a distinção Investimento (categoria) x Reserva (caixinha) foi implementada e é hoje exatamente essa separação em camadas (inclusive o bucket `investimentos` vs `reservas` na Estrutura de Custo). O que falta é o "link automático" — hoje uma aplicação numa caixinha não conta automaticamente pra execução de um item de orçamento de Investimentos, são leituras independentes.

---

## 13) Melhorias gerais de layout/UX para toda a aplicação

**Resposta (lista completa, você aprovou tudo):**

- **Botão flutuante de "+" novo lançamento** acessível de qualquer tela (não só pela nav) — é a ação mais frequente do app, merece atalho global.
- **Nav mobile**: sidebar desktop-only; no celular vira barra inferior (Dashboard / Lançamentos / + / Planejamento / Config).
- **PWA offline**: lançamento funcionando offline com fila de sincronização — reaproveita o mesmo princípio de hash idempotente da migração (evita duplicar ao sincronizar).
- **Modo escuro**: já que o app usa tokens CSS, é barato adicionar um segundo conjunto de valores — comum em app financeiro usado à noite.
- **Estados de carregamento**: skeleton loaders e salvamento otimista no formulário.
- **Busca/comando rápido (Cmd+K)**: expor a aba Busca como paleta de comando global também.
- **Acessibilidade**: manter a disciplina de `aria-label` do código atual nas telas novas.
- **Alertas**: notificação (push/e-mail) quando um bucket de orçamento se aproxima do limite ou uma parcela está prestes a vencer.

> **Status:** ✅ botão flutuante "+", ✅ nav mobile (barra inferior), ✅ tema claro/escuro automático (`prefers-color-scheme`), 🟡 estados de carregamento (existe pra alguns fluxos, ex: banner de "acordando" o backend, mas não skeleton loaders generalizados nem salvamento otimista). ⬜ PWA offline com fila de sincronização, ⬜ busca/comando rápido (Cmd+K), ⬜ alertas/notificações — nenhum dos três implementado. Acessibilidade (`aria-label`) mantida de forma pontual, não auditada sistematicamente.

---

## 14) Estimativa de custo

**Pergunta:** primeiro pedi previsão de custo antes de aprovar a implementação; depois esclareci que queria custo em **créditos convertido pra reais**, não custo de infraestrutura.

**Resposta (infraestrutura):**

| Item | Free tier | Se precisar de mais |
|---|---|---|
| Render (backend) | Gratuito — mas "dorme" após ~15min sem uso (delay de alguns segundos no primeiro acesso do dia) | Starter ~US$ 7/mês para ficar sempre ativo |
| Supabase (banco+auth) | Gratuito — 500MB de banco, 50k usuários/mês de auth. Para uso pessoal/familiar, dura **anos** | Pro US$ 25/mês só se crescer bem além de uso pessoal |
| Domínio próprio (opcional) | — | ~R$ 40-60/ano, não é necessário |

**Para o seu uso (pessoal, talvez família):** R$ 0/mês pra começar.

**Resposta (créditos/tokens, depois de você esclarecer o que realmente queria saber):**

Duas situações bem diferentes:

- **Assinatura Claude (Pro/Max)** — o mais comum via CLI/terminal: sem cobrança por token separada. O "custo" é consumir parte da janela de uso (limite por 5h/semana), não dinheiro adicional. Resposta em R$: **R$ 0 adicional**.
- **API/console (pago por token)**: preços do modelo usado na sessão (Sonnet 5) — US$ 2,00/milhão de tokens de entrada, US$ 10,00/milhão de saída. Um projeto como esse tende a processar entre **10 e 80 milhões de tokens no total**, dando algo entre **US$ 50 e US$ 400** (≈ **R$ 270 a R$ 2.200**, câmbio ilustrativo). Estimativa de ordem de grandeza, não cotação — o número confiável é o painel de uso real (`console.anthropic.com/settings/billing` ou `claude.ai/settings/usage`).

---

## 15) Correção do cronograma

**Pergunta:** "Você levaria 1 semana inteira para fazer apenas a fase 0? Achei que poderia implementar em algumas horas no máximo toda essa migração."

**Resposta:**

Você está certo — minha estimativa de "1 semana" estava calibrada com heurística de projeto tradicional (reuniões, espera entre pessoas, ciclos de revisão), que não se aplica a trabalho iterativo direto no Claude Code. Recalibrando por **sessões de trabalho**, não semanas corridas:

| Fase | Escopo | Estimativa realista |
|---|---|---|
| 0. Discovery | Boa parte já feita na conversa (schema, colunas, regras). Falta só criar as contas Render/Supabase e formalizar o SQL final | **1 sessão, poucas horas** |
| 1. Backend base | Portar `core/`, schema completo + RLS, endpoints FastAPI, auth | 2–4 sessões |
| 2. Migração | Script + dry-run + reconciliação | 1 sessão |
| 3. Formulário + cartão de crédito + reconciliação de fatura | Maior superfície de UI | 3–5 sessões |
| 4. Paridade analítica | Adaptar Dashboard/Gráficos/Estruturas para a API | 1–2 sessões |
| 5. Novidades | Envelope, templates, parcelas | 2–3 sessões, incremental |
| 6. Corte | Tempo de uso real em paralelo, não esforço de implementação | Semanas de observação, não de trabalho |

O fator que determina a duração real é o quanto você quer revisar/testar entre cada entrega, não a tarefa em si.

---

## 16) Divisão final em 7 entregas — o plano que foi de fato seguido

Depois de toda essa rodada, o esqueleto do backend já tinha sido commitado
(Entrega 1), e a divisão em fases foi reorganizada numa forma mais concreta,
que é a que efetivamente guiou o desenvolvimento real (ver git log e
`README.md`):

| Entrega | Escopo | Status |
|---|---|---|
| **1. Infraestrutura viva** | API FastAPI com `/health`, schema SQL completo, blueprint do Render | ✅ |
| **2. Backend completo** | Portar lógica de negócio, autenticação Supabase, endpoints CRUD, RLS testada | ✅ |
| **3. Migração dos dados** | Script de normalização/dedup + dry-run + reconciliação do histórico atual | ⬜ |
| **4. Lançamento + Cartão de Crédito** | Formulário PWA, CRUD contas/categorias, fatura por ciclo, reconciliação de fatura | 🟡 (lançamento e fatura por ciclo prontos; reconciliação e upload de OFX não) |
| **5. Paridade analítica** | Dashboard/Gráficos/Estruturas de Custo consumindo a API nova | 🟡 (backend pronto; Dashboard parcial, Estruturas de Custo sem tela) |
| **6. Orçamento redesenhado** | Toggle R$/%, envelope, parcelas no orçamento | 🟡 (tela de Planejamento e envelope prontos, incluindo itens reativos a partir dos lançamentos; toggle R$/% não) |
| **7. Corte** | Rodar em paralelo com o app desktop, depois desligar | ⬜ |

Sobre credenciais, a orientação dada foi: nunca colar chaves no chat — criar
as contas Render/Supabase diretamente e preencher só nos painéis deles ou em
`backend/.env` (fora do Git). Essa prática foi seguida no projeto inteiro.

---

Ver também: `plano-de-evolucao-original.md` (auditoria do ZIP + plano de
fases original) e `changelog-proposta-original-do-redesign.md` (mockups + comparação
proposto x implementado, tela por tela).
