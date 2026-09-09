# LAB02 — Experimento sobre programação com e sem IA

Este diretório reúne o planejamento e os artefatos do LAB02 da disciplina de
Laboratório de Experimentação de Software. O experimento compara a resolução de
pequenos exercícios de programação com ChatGPT e de forma manual.

> Estado atual: a base comum e as entregas de Pedro da Sprint 01 estão
> implementadas. As entregas atribuídas a Diogo e Lorran continuam pendentes e
> a Sprint 02 ainda não deve ser executada.

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

O tratamento `ia` utilizará **ChatGPT Free com GPT-5.6 Luna**, modelo padrão da
oferta gratuita na data desta preparação. Antes do primeiro trial, os três
participantes devem confirmar que veem o mesmo nome de modelo e preencher
`assistant.model_verified_at` em `protocol.json`. Se um participante não tiver
o mesmo modelo, nenhum trial com IA deve começar até a condição ser uniforme.

Referência: [OpenAI Docs — novidades do ChatGPT](https://learn.chatgpt.com/pt-BR/docs/whats-new).

Cada trial com IA usa uma conversa nova ou temporária, sem memória e sem
instruções personalizadas. Nos trials manuais, todos os assistentes de IA devem
estar desabilitados. Pesquisa convencional na web é permitida nos dois
tratamentos, mas as URLs consultadas precisam ser registradas na Issue.

## Ferramenta de trials

Os comandos são executados a partir da raiz do repositório:

```text
python Lab02/tools/trial.py validate
python Lab02/tools/trial.py start PARTICIPANTE KATA --issue NUMERO
python Lab02/tools/trial.py check PARTICIPANTE KATA
python Lab02/tools/trial.py finish PARTICIPANTE KATA --prompts QUANTIDADE
python Lab02/tools/trial.py link-commit PARTICIPANTE KATA --commit HASH
```

- `validate` verifica o protocolo e todos os artefatos da Sprint 01.
- `start` copia o stub para a área isolada do participante e inicia o relógio.
- `check` executa os testes; finaliza se estiver verde ou se o limite acabou.
- `finish` encerra quando estiver verde ou censura depois de 35 minutos.
- `link-commit` registra no CSV o commit que contém a solução congelada.

O Git é vinculado depois da medição para que o tempo de commit não seja contado
no Time-to-Green. Até essa vinculação, o CSV usa `PENDING` no campo
`commit_sha`.

### Fluxo de um trial

1. Criar uma branch diretamente do baseline congelado.
2. Mover a Issue para `In Progress`.
3. Executar `start` com o número da Issue.
4. Editar apenas o `solution.py` indicado pelo comando.
5. Usar `check` durante o trabalho.
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

## Handoffs pendentes

### Diogo

- criar `Lab02/requirements.txt` e `Lab02/docs/ambiente.md`, documentando e
  fixando as versões do ambiente;
- implementar `Lab02/tools/metrics.py` com
  `collect(path) -> {loc, mean_complexity, maintainability_index, duplication_percent}`;
- implementar Kata 02 com oito testes;
- ampliar a validação automatizada e revisar a ferramenta de trials.

### Lorran

- criar `Lab02/docs/catalogo_katas.md` com a seleção, adaptação e calibração dos
  katas;
- implementar Katas 03 e 04, com oito testes cada;
- implementar `Lab02/tools/create_issues.py` com prévia segura por padrão;
- configurar e registrar evidências do GitHub Projects.

## Definition of Done da Sprint 01

- [ ] 12 trials válidos no protocolo, sendo 6 IA e 6 manuais.
- [ ] Quatro katas com especificação, stub e oito testes cada.
- [ ] Todos os stubs falham e as referências de validação passam.
- [ ] Cronometragem, censura, CSV e vínculo de commit testados.
- [ ] Métricas estáticas reproduzíveis.
- [ ] Instalação limpa documentada e validada.
- [ ] Cada integrante possui código, commit e revisão rastreáveis.
- [ ] Nenhum piloto foi incluído nos resultados oficiais.

## Sprint 02 — próxima etapa, ainda não executar

A Sprint 02 executará os 12 trials definidos no protocolo. Os títulos das
Issues poderão ser gerados a partir da matriz somente depois que a Sprint 01
atingir integralmente sua Definition of Done. Nenhum resultado deve ser criado
ou preenchido antecipadamente.
