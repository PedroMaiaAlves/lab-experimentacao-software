# Issues da Lab04S01 — prontas para cadastro manual

**Pedro:** `PedroMaiaAlves`; **Diogo:** `DiogoBrunoro`; **Lorran:** `LorranX`.

P1/P2/D1/D2/L1/L2 são códigos deste documento, não números do GitHub. Depois
do cadastro, usar os números reais nos vínculos e nos commits. Não foi criada
nenhuma issue automaticamente.

Issues de Pedro informadas para esta entrega:

- **P1: [#173](https://github.com/PedroMaiaAlves/lab-experimentacao-software/issues/173)** — estrutura e coleta.
- **P2: [#174](https://github.com/PedroMaiaAlves/lab-experimentacao-software/issues/174)** — cenário e simulação.

As duas issues foram cadastradas com o mesmo título e sem descrição. A divisão
de escopo acima é a usada nos commits e nas PRs; os títulos e as branches
informados por Pedro foram preservados. Para Diogo e Lorran, usar as tarefas
D1/D2/L1/L2 abaixo e associar os números efetivamente cadastrados.

Configuração comum: milestone `Lab04S01`; labels `lab04`, `sprint-01`; fluxo
`Backlog → Ready → In Progress → In Review → Done`; WIP máximo de uma issue
em andamento por pessoa. Pontos de esforço não foram confundidos com os
7 pontos acadêmicos da sprint.

## P1 — [Lab04S01][Pedro] Criar estrutura do laboratório e coletar tempos pareados de compilação

**Assignee:** `PedroMaiaAlves` · **Dependências:** nenhuma entrega de colega.

### Objetivo

Preparar um laboratório independente e obter medições reais da compilação
de bytecode do Django 5.2.8, comparando cache vazio e preenchido.

### Entregáveis

- Estrutura `Lab04`, ambiente Python isolado e dependências reproduzíveis.
- Protocolo e coletor com estado do cache controlado fora do cronômetro.
- 30 pares válidos, três pares de aquecimento separados, logs e inventário da fonte.
- Origem, hash oficial, comando, ambiente e horários registrados.

### Critérios de aceite

- [ ] 30 pares oficiais completos, com tempos positivos e IDs únicos.
- [ ] 15 pares por ordem, embaralhados com semente 42.
- [ ] Cache vazio/preenchido verificado antes e depois de cada execução.
- [ ] Preparação e verificação do cache fora do intervalo medido.
- [ ] Falhas preservadas; repetição do par inteiro; nenhuma exclusão por lentidão.
- [ ] Fonte e artefatos identificados por hash; coleta anterior não é sobrescrita.
- [ ] Testes do coletor aprovados e evidências anexadas.
- [ ] Revisão por outro integrante, commit com `#NUMERO` e cartão atualizado.

### Evidências a anexar

Comando: `python Lab04/validar.py` e testes de `Lab04/tests/test_coleta.py`.
Artefatos: `Lab04/data/real/`, `Lab04/docs/protocolo_coleta.md`.
Branch / commit / PR / revisor: preencher após cadastro e autorização de commit.

## P2 — [Lab04S01][Pedro] Definir cenário e implementar geração de dados simulados pareados

**Assignee:** `PedroMaiaAlves` · **Dependência:** P1, do próprio Pedro.

### Objetivo

Transformar a coleta real em um cenário explícito e um gerador reproduzível
de tempos pareados, pronto para os testes e gráficos dos colegas.

### Entregáveis

- Pergunta, hipóteses por teste, alpha 0,05, teste bicaudal e expectativa prévia.
- Calibração normal bivariada dos log-tempos, com médias e covariância amostrais.
- Gerador parametrizado por tamanho, semente e deslocamento médio logarítmico.
- CSV simulado, parâmetros, proveniência, documentação das interfaces e validação.

### Critérios de aceite

- [ ] Expectativa registrada antes da simulação, sem conclusão antecipada.
- [ ] Parâmetros calculados somente com os 30 pares reais, sem aquecimento.
- [ ] Dependência entre condições representada pela covariância dos log-tempos.
- [ ] Mesmos parâmetros e semente 42 reproduzem exatamente a amostra preservada.
- [ ] Tempos gerados positivos e finitos; entradas inválidas falham explicitamente.
- [ ] `delta_log=0` configura o modelo sob H0 sem modificar parâmetros originais.
- [ ] Limitações do modelo e distinção entre dados reais/simulados documentadas.
- [ ] Testes, revisão, commit com `#NUMERO` e atualização do Projects.

### Evidências a anexar

Comandos: `python Lab04/simular.py`, `python Lab04/validar.py` e suíte de testes.
Artefatos: `Lab04/data/simulado/`, `Lab04/docs/cenario.md`, `Lab04/docs/contratos.md`.
Branch / commit / PR / revisor: preencher posteriormente.

## D1 — [Lab04S01][Diogo] Implementar t pareado e Wilcoxon com interpretação dos resultados

**Assignee:** `DiogoBrunoro` · **Dependência para fechar:** P2.
Pode começar com pares sintéticos identificados como dados de teste.

### Objetivo

Aplicar os dois testes ao mesmo conjunto de diferenças logarítmicas pareadas
e devolver resultados interpretáveis pelo dashboard.

### Entregáveis

- `experimento/analise.py`, com a API definida em `docs/contratos.md`.
- Estatística, p-valor, método, decisão e interpretação de cada teste.
- Testes automatizados com exemplos conhecidos e casos especiais.
- Dependência SciPy fixada no ambiente integrado.

### Critérios de aceite

- [ ] Usar a mesma amostra simulada de P2 e preservar os pares.
- [ ] t pareado sobre os logs; Wilcoxon sobre `log(sem)-log(com)`.
- [ ] Ambos bicaudais, alpha 0,05; distinguir as hipóteses dos testes.
- [ ] Comparar resultados com referências calculadas diretamente no SciPy.
- [ ] Tratar empates, zeros, diferenças constantes e dados inválidos explicitamente.
- [ ] Informar método exato/aproximado quando aplicável.
- [ ] Não interpretar p-valor como probabilidade de H0, nem não rejeição como prova de igualdade.
- [ ] Código próprio, testes, revisão, commit com `#NUMERO` e cartão atualizado.

### Evidências a anexar

Resultado dos dois testes na amostra de P2, comando de teste, branch, commit/PR e revisor.
Não é necessário fazer a tabela final de testes nos dados reais nesta issue.

## D2 — [Lab04S01][Diogo] Construir G2 com distribuição nula, região de rejeição e p-valor

**Assignee:** `DiogoBrunoro` · **Dependências:** D1 e amostra definitiva de P2.

### Objetivo

Explicar visualmente como os dois testes obtêm a decisão e o p-valor do exemplo.

### Entregáveis

- `experimento/g2.py`, retornando figura Plotly sem iniciar Streamlit.
- Painel t contínuo e painel Wilcoxon discreto.
- Texto de duas a quatro frases, com interpretação correta das probabilidades.

### Critérios de aceite

- [ ] Distribuição sob H0 identificada em cada painel.
- [ ] Regiões de rejeição em alpha 0,05 e p-valor do exemplo destacados separadamente.
- [ ] No t, duas caudas e n−1 graus de liberdade.
- [ ] No Wilcoxon sem empates/zeros, distribuição exata de `min(W+, W-)`.
- [ ] Área/massa destacada coincide com o p-valor de D1, dentro da tolerância numérica.
- [ ] Caudas muito pequenas continuam explicadas por ampliação/anotação, sem trocar a semente.
- [ ] Título, eixos, unidade adimensional, legenda e cores fixas por teste.
- [ ] Testes, revisão, commit com `#NUMERO` e cartão atualizado.

### Evidências a anexar

Figura e conferência numérica das probabilidades. A figura só conclui a entrega
acadêmica quando integrada no dashboard por Lorran.

## L1 — [Lab04S01][Lorran] Implementar dashboard Streamlit e G1 de dados reais e simulados

**Assignee:** `LorranX` · **Dependência para fechar:** P2.
Pode começar com exemplos sintéticos explicitamente identificados.

### Objetivo

Apresentar o cenário e comparar dados reais e simulados dentro de um dashboard
que se explique sozinho e seja gerado pelo código do repositório.

### Entregáveis

- `Lab04/app.py` e `experimento/g1.py`.
- G1 com histogramas reais/simulados de cada condição.
- Cenário, fontes, tamanho da amostra e explicação da calibração.
- Dependências Streamlit/Plotly e comando de abertura documentados.

### Critérios de aceite

- [ ] Ler os dados preservados; abrir o app nunca inicia coleta.
- [ ] Mostrar 30 pares / 60 medições, origem e hipóteses corretas.
- [ ] G1 em segundos, bins comparáveis entre reais e simulados de cada condição.
- [ ] Textos de duas a quatro frases explicam forma, parâmetros e limitações.
- [ ] Sete seções na ordem do enunciado, com etapas futuras claramente pendentes.
- [ ] Links do dashboard e repositório no topo; Projects informado por Pedro.
- [ ] Validação visual e de execução, revisão, commit com `#NUMERO` e cartão atualizado.

### Evidências a anexar

Comando de execução, captura do G1 e da seção de cenário, branch, commit/PR e revisor.
Usar o contrato de `docs/contratos.md` para evitar alterações nos dados de Pedro.

## L2 — [Lab04S01][Lorran] Integrar testes e G2 e validar a entrega executável da sprint

**Assignee:** `LorranX` · **Dependências:** L1, P2 e D2.

### Objetivo

Fechar a sprint 1 com os testes interpretados e G1/G2 dentro do Streamlit,
reproduzíveis a partir da coleta preservada.

### Entregáveis

- Integração das APIs de Diogo no app.
- README final de execução e dependências integradas.
- Evidências de abertura, conferência dos gráficos e reprodução.

### Critérios de aceite

- [ ] Um comando abre o dashboard após instalar as dependências.
- [ ] G1 e G2 visíveis dentro do app, acompanhados dos textos exigidos.
- [ ] Resultados de D1 correspondem exatamente ao exemplo de G2.
- [ ] Títulos, eixos, unidades, legendas e cores consistentes.
- [ ] App abre com dados preservados e sem rede para recoleta.
- [ ] `validar.py` passa e testes integrados não apresentam erros.
- [ ] Nenhum resultado de Q1/Q2/Q3 ou conclusão final foi inventado.
- [ ] Cada integrante possui issue atribuída com código e commit referenciado.
- [ ] Revisão final, evidências e cartões atualizados.

### Evidências a anexar

Saída dos testes, capturas do dashboard, comando do README, links do repositório
e Projects, commit/PR e revisão. Não marcar a sprint concluída apenas porque
P1/P2 estão disponíveis.

## Ordem de trabalho

Pedro: **P1 → P2**, sem depender de entregas de colegas.
Diogo: **D1 → D2**, podendo iniciar por exemplos de teste.
Lorran: **L1 → L2**, integrando P2 e D2 ao final.

Os arquivos deste diretório são o material para cadastro manual; checkboxes
devem ser atualizados com evidências reais no GitHub, sem atribuir contribuições
de código de uma pessoa a outra.
