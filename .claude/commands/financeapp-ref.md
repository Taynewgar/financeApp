---
description: Calcula, a partir do CSV histórico, os parâmetros do Dashboard e o REALIZADO por bucket de Estrutura de Custo/Planejamento, de forma independente (regra escrita do zero) — referência pra testar a aplicação real
---

Esta skill gera um número de referência pra cada parâmetro que o
Dashboard mostra, e também o **realizado por bucket** (custos fixos/
variáveis/sazonalidades/investimentos/reservas) que Estrutura de Custo
e Planejamento mostram — calculado a partir do CSV histórico
("Lançamentos Calculado" do app antigo), não do código do app, e sim
de uma reimplementação independente da regra de negócio. Serve pra
comparar "o que o app deveria mostrar" contra "o que o app mostra de
verdade".

**Não cobre o lado ORÇADO** (teto por bucket, `orcamento_mensal` de
cada item, `saldo_anterior` do modo envelope) — essa configuração só
existe no Supabase, nunca no CSV histórico. Pra esses 3, a verificação
é manual (ver "Racional de testes" em `docs/backlog.md`, item
registrado pra depois da Rodada 40).

Como o Dashboard real lê da base **já migrada** (não do CSV direto),
essa comparação valida duas coisas ao mesmo tempo, não só uma: a regra
de negócio (o cálculo está certo?) e a fidelidade da migração (o dado
chegou certo no banco?). Se os dois baterem, regra, implementação e
migração estão todas alinhadas; se não baterem, o problema está em um
desses três pontos — regra mal entendida nesta reimplementação, bug no
Dashboard, ou lançamento que não migrou corretamente.

## Antes de rodar

**Quem roda isto é o Claude, dentro da sessão — o usuário nunca roda o
script.** Não existem "a skill" e "o script" como 2 coisas separadas
pro usuário escolher entre uma ou outra: acionar a skill (`/financeapp-
ref` ou só pedir) É o Claude rodando `backend/scripts/
referencia_dashboard.py` por baixo, dentro desta sessão. O usuário só
precisa fazer 1 coisa — anexar o(s) arquivo(s) na própria conversa
(upload do CSV e, se tiver, do `migracao_overrides.json`) — o resto é
o Claude que faz.

**O CSV (e o arquivo de overrides, se usado) são dado financeiro
pessoal e nunca são commitados neste repo** — cada sessão precisa que
o usuário anexe os arquivos de novo (upload na conversa). Se a sessão
não tiver o CSV em mãos, peça-o antes de continuar. Não assuma que um
upload de uma sessão anterior ainda existe — o diretório de uploads é
por sessão.

## Passo a passo

1. Localize o CSV anexado (procure em `/root/.claude/uploads/` pelo
   nome mais recente que contenha "Lançamentos" ou "Lancamentos" —
   confirme com o usuário se houver mais de uma versão candidata; a de
   modificação mais recente costuma ser a correta, ver histórico de
   sessões anteriores pra um exemplo real disso). Se o usuário mencionar
   que também tem o arquivo de overrides de estrutura de custo gerado
   durante a migração real (`migracao_overrides.json` — as respostas
   que ele deu linha a linha pras despesas ambíguas), peça pra anexar
   esse também e localize do mesmo jeito em `/root/.claude/uploads/`
   (nome costuma conter "overrides"). Sem ele, o passo 2 ainda funciona,
   só que com a limitação descrita lá.

2. Rode o script de cálculo (reaproveita só o parsing já validado da
   migração — `scripts/migracao/parsing.py`/`mapeamento.py`/
   `parcelas.py` —, mas as fórmulas em si são uma reimplementação
   própria, não uma cópia de `app/services/resumo_financeiro.py`).

   O script só usa biblioteca padrão do Python (nenhuma dependência de
   `requirements.txt`) — normalmente roda direto, sem precisar do venv
   do backend:

   ```bash
   cd backend
   python3 scripts/referencia_dashboard.py --csv /caminho/do/CSV.csv > /tmp/ref.json
   ```

   Se isso falhar (ex: `python3` ausente do PATH ou versão muito
   antiga), só então caia pro venv do backend:

   ```bash
   cd backend
   source venv/bin/activate
   python scripts/referencia_dashboard.py --csv /caminho/do/CSV.csv > /tmp/ref.json
   ```

   Use `--hoje AAAA-MM-DD` se quiser simular uma data diferente da real
   (afeta só "Compromissos Futuros" e o corte de "Todos os meses").

   Se o passo 1 achou um arquivo de overrides anexado, use
   `--overrides /root/.claude/uploads/<nome-do-arquivo>` (o caminho do
   upload NESTA sessão, nunca um caminho do computador do usuário — a
   sessão não alcança a máquina dele, só o que foi anexado na
   conversa). Sem esse arquivo, o script segue rodando igual, só que
   despesas com estrutura de custo ambígua (nem literal no CSV, nem
   aprendida por subcategoria) caem em "sem_estrutura" em vez do bucket
   que o usuário escolheu de verdade na migração — o script avisa isso
   no stderr, com a contagem; não é bug, é só o arquivo faltando.

3. **Confira a saída antes de reportar** — não repasse números sem
   olhar: escolha 2-3 meses e confirme contra o CSV. Receita costuma
   bater numa soma simples (filtrar `Movimentação == "Receita"` do
   mês). Despesa quase nunca bate numa soma simples por `Movimentação
   == "Despesa"`, porque isso inclui Estorno/Ressarcimento, que o
   Dashboard trata à parte — pra conferir despesa, agrupe por
   `(Movimentação, Tipo do Pag / Movimento)` e some cada combinação:

   ```python
   import csv
   from collections import defaultdict
   totais = defaultdict(float)
   with open("/caminho/do/CSV.csv", encoding="utf-8-sig", newline="") as f:
       for row in csv.DictReader(f, delimiter=";"):  # confira o delimitador real (";" ou ",")
           totais[(row["Movimentação"], row["Tipo do Pag / Movimento"])] += float(
               row["Valor"].replace("R$", "").replace(".", "").replace(",", ".").strip()
           )
   ```

   `despesas_brutas` do JSON deve bater com a soma de `("Despesa",
   "Compra à vista")` + `("Despesa", "Parcela sem juros")` +
   `("Despesa", "Compra internacional")` — não inclui Estorno nem
   Ressarcimento, que entram em `ajustes_*`. Se algo parecer
   implausível mesmo depois dessa quebra, investigue antes de reportar
   — pode ser dado real (renda irregular, 13º, etc.) ou bug no script.

4. **Nunca commite `/tmp/ref.json` nem cole os valores calculados em
   texto que vá pro repositório** — é resultado derivado de dado
   financeiro pessoal, mesma regra do CSV em si. Fica só na
   conversa/scratchpad da sessão.

5. Se o usuário quiser o mock visual do Dashboard (opcional, mas
   valioso — permite navegar mês a mês e comparar direto com o app):
   monte o artifact a partir do template genérico e sem dados em
   `backend/scripts/referencia_dashboard_template.html` — substitua o
   placeholder `__DADOS_JSON__` pelo conteúdo do JSON gerado no passo 2
   (mantendo a mesma estrutura: `meses` por chave `AAAA-MM-01`,
   `todos_os_meses_ate_hoje`, `compromissos_futuros`, `hoje_referencia`,
   `total_lancamentos`). Publique com o Artifact tool — artifacts
   começam privados, mas ainda contêm dado financeiro pessoal
   embutido no HTML, então trate como sensível mesmo assim.

6. Reporte direto na conversa, neste formato fixo:
   - O que foi conferido no passo 3 (qual mês, bateu ou não).
   - Mês atual (mesmo que parcial): despesas, receitas, resultado
     saúde, maior categoria de despesa.
   - "Todos os meses até hoje": receitas, despesas brutas, resultado
     fluxo de caixa, resultado saúde, taxa de poupança, reservas,
     investimentos.
   - Quantidade de compromissos futuros.
   - Se o usuário também quiser validar Estrutura de Custo/Planejamento
     (ver "Racional de testes" em `docs/backlog.md`): `realizado_por_
     bucket` de 1-2 meses, comparado contra o "Realizado" que a tela
     real mostra pra esses mesmos meses — deixe claro que só o
     Realizado está sendo validado, não o Orçado/saldo_anterior.
   - Link do artifact, se foi gerado (passo 5).
   - Limitações conhecidas (seção abaixo) relevantes pro que foi
     reportado.

   Nunca registre isso em `docs/backlog.md`/changelog — é ferramenta
   de teste do usuário, não entrega de produto.

## Limitações conhecidas (não são bugs desta skill)

- `ajustes_vinculados` sai sempre 0 pros dados migrados — o CSV antigo
  não guardava vínculo de estorno/ressarcimento com a despesa
  original. Se o usuário tiver criado ajustes vinculados manualmente
  no app DEPOIS da migração, eles não aparecem aqui (não estão no
  CSV) — a comparação do mês corrente pode divergir por esse motivo,
  não por bug.
- Da mesma forma, qualquer lançamento criado no app diretamente (sem
  passar pela migração) depois da data do CSV não entra neste
  cálculo.
- Dezembro/2025 (ou o que for o primeiro mês do CSV) costuma ser
  parcial — taxa de poupança pode sair com valor extremo (denominador
  perto de zero). Esperado, não é bug.
- `realizado_por_bucket` só reflete despesa/aplicação/retirada — não
  valida o lado orçado nem `saldo_anterior` (ver aviso no topo deste
  arquivo). Sem `--overrides` certo, "sem_estrutura" pode vir maior
  aqui do que no app real.
- Qualquer transação lançada direto no app (recorrente confirmado,
  reserva/investimento, edição de categoria depois da migração) não
  está no CSV — mesma limitação geral já descrita acima pros outros
  parâmetros, vale igual pro realizado por bucket.
