# LAB02 — Experimento sobre programação com e sem IA

Este diretório reúne o planejamento e os artefatos do LAB02 da disciplina de
Laboratório de Experimentação de Software. O experimento compara a resolução de
pequenos exercícios de programação com ChatGPT e de forma manual.

> Estado atual: as entregas técnicas da Sprint 01 de Pedro, Diogo e Lorran
> estão integradas. A preparação técnica da Sprint 02 foi validada localmente:
> 35 testes passaram em CPython 3.11.16, e a validação do pacote passou.
> Pedro confirmou o mesmo assistente nas três contas; as verificações dos
> ambientes de Diogo e Lorran continuam pendentes. A tag `lab02-s02-baseline`
> ainda não foi publicada. Os trials já registrados começaram sem essa tag;
> isso é um desvio do protocolo, não uma execução sobre uma baseline congelada.
> Não iniciar novos trials antes de regularizar a preparação.

## Por onde começar

1. Preparar o [ambiente isolado Python 3.11.16](docs/ambiente.md).
2. Conferir as [pendências para publicar a baseline](#confirmações-para-a-baseline).
3. Depois da liberação, seguir o [roteiro passo a passo da Sprint 02](docs/execucao_sprint02.md).

### Onde estão os quatro exercícios

| Kata | Enunciado | Preparado por |
| --- | --- | --- |
| 01 | [Consolidar Janelas](katas/kata01/README.md) | Pedro |
| 02 | [Planejar Recargas](katas/kata02/README.md) | Diogo |
| 03 | [Agrupar Alertas](katas/kata03/README.md) | Lorran |
| 04 | [Distribuir Cotas](katas/kata04/README.md) | Lorran |

Todos resolvem os mesmos quatro exercícios, uma vez cada: dois com IA e dois
manuais. São **4 katas × 3 participantes = 12 trials**. A autoria do enunciado
não torna sua execução exclusiva de quem o preparou. Use a `main` integrada ou
a baseline liberada; as branches antigas da Sprint 01 podem conter só parte dos arquivos.

## Termos essenciais

- **Kata:** exercício pequeno de programação.
- **Trial:** uma execução de um kata por um participante.
- **Tratamento:** condição aplicada ao trial: `ia` ou `manual`.
- **Time-box:** limite máximo de 35 minutos.
- **Time-to-Green:** tempo até todos os testes de aceitação passarem.
- **Censura:** encerramento em 35 minutos sem todos os testes passando. O trial
  permanece nos dados com duração de 2.100 segundos.
- **Within-Subject/Crossover:** cada participante usa os dois tratamentos.
- **Contrabalanceamento:** variação de ordem e tratamento para reduzir efeitos
  de aprendizagem, fadiga e ordem.

## Questões de pesquisa e métricas

| Questão | Pergunta | Métrica principal |
| --- | --- | --- |
| RQ1 | A IA reduz o tempo de resolução? | Time-to-Green, mediana e IQR |
| RQ2 | A IA reduz defeitos? | Taxa de sucesso dos testes |
| RQ3 | A IA altera a estrutura do código? | Complexidade e duplicação, controladas por LOC |

O desenho completo, incluindo hipóteses e ameaças à validade, está em
[`docs/desenho_experimental.md`](docs/desenho_experimental.md).

## Sprint 01 — desenho e preparação

### Objetivo

Deixar o experimento pronto para execução, sem decisões metodológicas ou
operacionais pendentes. Nenhuma medição oficial é produzida nesta sprint.

### Entregáveis

- desenho experimental, GQM, hipóteses, variáveis e ameaças à validade;
- quatro katas autorais ou adaptados, com dificuldade semelhante;
- oito testes de aceitação por kata;
- protocolo com 3 participantes, 4 katas e 12 trials;
- ambiente reproduzível;
- ferramenta de cronometragem e coleta;
- ferramenta de métricas estáticas;
- validação automatizada do pacote;
- estrutura vazia para os resultados;
- modelo ou automação das Issues do GitHub Projects.

### Divisão e Issues

#### Pedro — `PedroMaiaAlves`

1. `[Lab02S01][Pedro] Documentar GQM, hipóteses e desenho experimental` — 3 pontos.
2. `[Lab02S01][Pedro] Definir protocolo e contrabalanceamento dos 12 trials` — 2 pontos.
3. `[Lab02S01][Pedro] Implementar cronômetro e coleta dos trials` — 5 pontos.
4. `[Lab02S01][Pedro] Criar Kata 01 — Consolidar Janelas e testes de aceitação` — 3 pontos.

#### Diogo — `DiogoBrunoro`

1. `[Lab02S01][Diogo] Configurar ambiente reproduzível do experimento` — 3 pontos.
2. `[Lab02S01][Diogo] Implementar coleta de métricas estáticas` — 5 pontos.
3. `[Lab02S01][Diogo] Criar Kata 02 — Planejar Recargas e testes de aceitação` — 3 pontos.
4. `[Lab02S01][Diogo] Automatizar validação do pacote experimental` — 2 pontos.

#### Lorran — `LorranX`

1. `[Lab02S01][Lorran] Selecionar e calibrar os quatro katas do experimento` — 3 pontos.
2. `[Lab02S01][Lorran] Criar Kata 03 — Agrupar Alertas e testes de aceitação` — 3 pontos.
3. `[Lab02S01][Lorran] Criar Kata 04 — Distribuir Cotas e testes de aceitação` — 3 pontos.
4. `[Lab02S01][Lorran] Automatizar Issues e configurar o GitHub Projects` — 4 pontos.

Cada integrante deve produzir código e commits próprios. Revisar ou commitar
uma implementação pronta de outra pessoa não substitui uma contribuição
técnica real.

### Configuração do GitHub Projects

- Milestone: `LAB02 — Sprint 01`.
- Iteration: `Sprint 01`.
- Labels comuns: `lab02` e `sprint-01`.
- Label de tipo: `metodologia`, `documentação`, `ferramenta`, `kata` ou `testes`.
- Fluxo: `Backlog -> Ready -> In Progress -> In Review -> Done`.
- WIP: no máximo uma Issue em andamento por integrante.
- Branch: `lab02-s01/issue-N-descricao`.
- Commit: `feat(lab02): descrição resumida #N`.

Corpo sugerido para cada Issue:

```markdown
## Objetivo

Descrever o resultado concreto esperado desta tarefa.

## Entregável

- Arquivos ou documentação que serão produzidos.
- Comportamento que deverá funcionar.

## Critérios de aceite

- [ ] Implementação ou documentação concluída
- [ ] Testes relevantes executados
- [ ] Nenhum resultado experimental foi inventado
- [ ] Revisão realizada por outro integrante
- [ ] Commit menciona esta Issue
- [ ] Hash do commit ou Pull Request adicionado à Issue
- [ ] Cartão atualizado no GitHub Projects

## Evidências

- Branch:
- Pull Request:
- Commit:
- Comando de teste:
- Revisor:
```

### Dependências entre as Issues

- O protocolo depende do desenho experimental.
- A ferramenta de trials depende do protocolo.
- A validação completa depende dos quatro katas e da ferramenta de métricas.
- A automação das Issues depende da estrutura final do protocolo.

## Protocolo

O arquivo [`protocol.json`](protocol.json) é a fonte de verdade para
participantes, katas, tratamentos e ordem.

### Matriz contrabalanceada

| Ordem | Pedro | Diogo | Lorran |
| --- | --- | --- | --- |
| 1 | Kata 01 — IA | Kata 02 — Manual | Kata 03 — Manual |
| 2 | Kata 02 — Manual | Kata 03 — IA | Kata 04 — IA |
| 3 | Kata 03 — IA | Kata 04 — IA | Kata 01 — Manual |
| 4 | Kata 04 — Manual | Kata 01 — Manual | Kata 02 — IA |

Essa matriz possui seis trials por tratamento, dois trials de cada tratamento
por pessoa e ambos os tratamentos em todos os katas. Como há três participantes,
o balanço por kata é necessariamente 2 × 1.

### Assistente padronizado

O protocolo prevê **ChatGPT Free com GPT-5.6 Luna**. Antes do primeiro trial, os três
participantes devem confirmar que veem o mesmo nome de modelo e preencher
`assistant.model_verified_at` em `protocol.json`. Se um participante não tiver
o mesmo modelo, nenhum trial com IA deve começar até a condição ser uniforme.

Referência: [OpenAI Docs — novidades do ChatGPT](https://learn.chatgpt.com/pt-BR/docs/whats-new).
A documentação não comprova a disponibilidade em uma conta individual.
Enquanto faltar uma confirmação, `assistant.model_verified_at` fica `null`.

Cada trial com IA usa uma conversa nova ou temporária, sem memória e sem
instruções personalizadas. Nos trials manuais, todos os assistentes de IA devem
estar desabilitados. Pesquisa convencional na web é permitida nos dois
tratamentos, mas as URLs consultadas precisam ser registradas na Issue.

## Ferramenta de trials

Os comandos abaixo são para Windows, na raiz do repositório, com o ambiente
exclusivo `Lab02/.venv`. Substitua os marcadores em maiúsculas pelos dados reais.
Não execute `start` para testar a instalação; use `validate` e a suíte automatizada.

```text
.\Lab02\.venv\Scripts\python.exe Lab02/tools/trial.py validate
.\Lab02\.venv\Scripts\python.exe Lab02/tools/trial.py start PARTICIPANTE KATA --issue NUMERO
.\Lab02\.venv\Scripts\python.exe Lab02/tools/trial.py check PARTICIPANTE KATA --prompts QUANTIDADE
.\Lab02\.venv\Scripts\python.exe Lab02/tools/trial.py finish PARTICIPANTE KATA --prompts QUANTIDADE
.\Lab02\.venv\Scripts\python.exe Lab02/tools/trial.py link-commit PARTICIPANTE KATA --commit HASH
```

- `validate` verifica a estrutura do protocolo, a presença dos artefatos,
  os testes dos stubs e o cabeçalho do CSV. Não substitui a suíte automatizada
  nem confirma o ambiente ou a conta de cada participante.
- `start` copia o stub para a área isolada do participante e inicia o relógio.
- `check` executa os testes; finaliza se estiver verde ou se o limite acabou.
- `finish` encerra quando estiver verde ou censura depois de 35 minutos.
- `link-commit` registra no CSV o commit que contém a solução congelada.

Informe a contagem **acumulada** de prompts em todo `check` e `finish`; no
tratamento manual use `0`. Cada mensagem enviada ao assistente conta como um
prompt, inclusive a primeira e os pedidos de correção. Ao aparecer
`TRIAL FINALIZADO`, pare de editar. Se já ficou verde, não execute `finish`
novamente. Trials vermelhos não podem terminar antes do limite.

Use um alarme externo de 35 minutos, ativado ao iniciar o trial. O programa
não executa em segundo plano: o encerramento ocorre quando `check` ou `finish`
é chamado. Ao atingir o prazo, pare de editar e execute `finish` imediatamente.

O Git é vinculado depois da medição para que o tempo de commit não seja contado
no Time-to-Green. Até essa vinculação, o CSV usa `PENDING` no campo
`commit_sha`. Primeiro faça o commit da solução e do resultado; depois rode
`link-commit --commit HEAD` e faça um segundo commit com o CSV atualizado.

### Fluxo de um trial

1. Criar uma branch diretamente do baseline congelado.
2. Mover a Issue para `In Progress`.
3. Executar `start` com o número da Issue.
4. Editar apenas o `solution.py` indicado pelo comando.
5. Usar `check --prompts QUANTIDADE` durante o trabalho, sempre com a contagem atual.
6. Parar ao ficar verde ou ao chegar a 35 minutos.
7. Executar `finish` se necessário e não modificar mais a solução.
8. Commitar solução e primeira versão do resultado mencionando a Issue.
9. Executar `link-commit` com o hash desse commit e commitar a atualização.
10. Anexar evidências e mover a Issue para revisão.

## Contrato do CSV

[`results/trials.csv`](results/trials.csv) contém uma linha por trial e usa a
combinação `participant + kata` como chave única.

- Datas: UTC em ISO 8601.
- Duração: segundos, limitada a 2.100.
- Taxa de sucesso: percentual entre 0 e 100.
- Trial censurado: `duration_seconds=2100`, `censored=true` e
  `time_to_green_seconds` vazio.
- Métrica indisponível: campo vazio e justificativa na Issue; nunca zero
  inventado.

## Entregas integradas da Sprint 01

### Diogo

- ambiente e dependências em `Lab02/requirements.txt` e `Lab02/docs/ambiente.md`;
- `Lab02/tools/metrics.py` com
  `collect(path) -> {loc, mean_complexity, maintainability_index, duplication_percent}`;
- Kata 02 com oito testes;
- testes de métricas e validação do pacote (Issues #62–#65).

### Lorran

- catálogo dos katas em `Lab02/docs/catalogo_katas.md`;
- Katas 03 e 04, com oito testes cada;
- `Lab02/tools/create_issues.py` com prévia segura por padrão (Issues #66–#69,
  integradas pela PR #78).

### Pedro

- desenho experimental, protocolo, ferramenta de trials e Kata 01
  (Issues #58–#61);
- preparação complementar para a Sprint 02: documentação operacional,
  fixtures sintéticas e ambiente local isolado.

As entregas integradas não comprovam, por si só, a revisão de todos os cartões
do Projects ou a instalação nas três máquinas. As evidências devem ser
registradas pelos responsáveis, sem atribuir commits de uma pessoa a outra.

## Definition of Done da Sprint 01

- [x] 12 trials válidos no protocolo, sendo 6 IA e 6 manuais.
- [x] Quatro katas com especificação, stub e oito testes cada.
- [x] Os quatro stubs falham; a solução sintética dos testes da ferramenta passa.
- [x] Cronometragem, censura, CSV e vínculo de commit testados.
- [x] Métricas estáticas testadas e dependências fixadas.
- [x] Instalação limpa documentada e validada no computador de Pedro.
- [ ] Instalação reproduzida e confirmada por Diogo e Lorran.
- [ ] Cada integrante possui código, commit e revisão rastreáveis.
- [x] Nenhum piloto foi incluído nos resultados oficiais; CSV somente com cabeçalho.

## Confirmações para a baseline

| Participante | Ambiente CPython 3.11.16 | ChatGPT Free / GPT-5.6 Luna |
| --- | --- | --- |
| Pedro | Validado em 2026-09-16: 35 testes e `validate` passaram | Confirmado conforme declaração de Pedro; ver registro abaixo |
| Diogo | Pendente: enviar saída da verificação | Confirmado conforme declaração de Pedro; ver registro abaixo |
| Lorran | Pendente: enviar saída da verificação | Confirmado conforme declaração de Pedro; ver registro abaixo |

Pedro declarou nesta preparação corretiva que os três participantes conferiram
o mesmo plano e modelo em suas próprias contas e confirmou o instante conjunto
de 2026-09-16 às 16:42 (UTC-03:00). O campo `assistant.model_verified_at` registra
o mesmo instante em UTC: `2026-09-16T19:42:00+00:00`. A fonte é a declaração de
Pedro na conversa de correção, não uma verificação automatizada das contas.
Essa confirmação não valida os ambientes de Diogo e Lorran. Não criar uma tag
retroativa para apresentar os trials já realizados como iniciados na baseline.

Para o ambiente, seguir a [conferência reproduzível](docs/ambiente.md#2-conferência-que-cada-participante-deve-executar)
e anexar a saída à PR de preparação. Para a conta, cada integrante fornece:

```text
Participante:
Plano exibido:
Modelo disponível:
Data da conferência:
```

Após as três confirmações compatíveis com o protocolo, registrar a data real
da confirmação conjunta em UTC, no formato ISO 8601, em
`assistant.model_verified_at`. Não preencher esse campo só para liberar `start`.
Se houver divergência de modelo, resolver a condição comum antes da baseline.

Pedro informou que o grupo não teve contato com soluções prontas. A familiaridade
com os enunciados preparados pelo próprio grupo continua sendo uma ameaça à validade.
As soluções anteriormente presentes nos testes internos são substituídas por
exercícios sintéticos; os commits antigos continuam no histórico e não devem
ser consultados para obter respostas durante os trials.

### Publicação da versão inicial comum

Somente depois de integrar a preparação e as confirmações à `main`, atualizar
a branch, executar os testes nessa versão final e confirmar CSV vazio e
árvore de trabalho limpa. Então publicar uma tag anotada:

```powershell
git switch main
git pull --ff-only
.\Lab02\.venv\Scripts\python.exe -m unittest discover -s Lab02/tests -v -b
.\Lab02\.venv\Scripts\python.exe Lab02/tools/trial.py validate
git status --short
git tag -a lab02-s02-baseline -m "Baseline validada para os 12 trials do LAB02"
git push origin refs/tags/lab02-s02-baseline
git rev-parse 'lab02-s02-baseline^{commit}'
git ls-remote origin 'refs/tags/lab02-s02-baseline^{}'
```

Parar se alguma verificação falhar, se `git status --short` listar mudanças ou
se faltar confirmação. Os dois últimos comandos devem mostrar o mesmo hash
do commit; a tag anotada tem um objeto próprio, diferente do commit apontado.
Não substituir nem mover uma tag já publicada. Enquanto houver pendências,
a PR técnica pode ser entregue, mas a baseline fica sem publicação.

## Sprint 02 — execução após a liberação

A Sprint 02 executará os 12 trials definidos no protocolo, em horários
individuais e seguindo a ordem da matriz. Fazer pausa mínima de 10 minutos
entre trials no mesmo dia. Nenhum resultado deve ser preenchido antecipadamente.

O [roteiro passo a passo](docs/execucao_sprint02.md) cobre Issues, branches,
início, arquivo a editar, prompts, testes, encerramento, commits e publicação.
A prévia dos 12 cartões pode ser consultada sem publicação:

```powershell
.\Lab02\.venv\Scripts\python.exe Lab02/tools/create_issues.py
```

Pedro fará o cadastro manual. Não usar `--apply` para evitar duplicação de
Issues. Guardar as soluções em branches locais até os três concluírem seus
quatro trials; depois publicar, revisar e consolidar as 12 linhas do CSV.
A análise estatística fica para a Sprint 03.
