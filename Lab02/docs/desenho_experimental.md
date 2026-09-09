# Desenho experimental do LAB02

## 1. GQM

### Goal

Analisar o uso de um assistente de IA generativa na resolução de tarefas de
programação, com o propósito de avaliar seus efeitos sobre tempo, defeitos e
estrutura do código, sob a perspectiva de estudantes de Engenharia de Software,
no contexto de quatro katas executados em ambiente controlado.

### Questions

- **RQ1:** o uso de IA reduz o tempo necessário para resolver uma tarefa?
- **RQ2:** o uso de IA reduz a quantidade de defeitos no código produzido?
- **RQ3:** o uso de IA altera a complexidade ou a duplicação do código?

### Metrics

| RQ | Métrica principal | Métricas complementares |
| --- | --- | --- |
| RQ1 | Time-to-Green em segundos | censura, mediana e IQR |
| RQ2 | taxa de sucesso dos testes | aprovados, falhando e total |
| RQ3 | complexidade e duplicação | LOC e índice de manutenibilidade |

LOC será usado como controle ao interpretar diferenças de complexidade ou
duplicação: soluções maiores naturalmente oferecem mais oportunidades para
decisões e repetição.

## 2. Hipóteses

### RQ1 — tempo

- **H0₁:** não existe diferença pareada no Time-to-Green entre IA e Manual.
- **H1₁:** o tratamento IA reduz o Time-to-Green em relação ao Manual.

### RQ2 — defeitos

- **H0₂:** não existe diferença pareada na taxa de sucesso dos testes.
- **H1₂:** o tratamento IA aumenta a taxa de sucesso dos testes.

### RQ3 — estrutura

- **H0₃:** não existe diferença estrutural entre os tratamentos, controlando LOC.
- **H1₃:** o tratamento IA altera complexidade ou duplicação, controlando LOC.

A hipótese de RQ3 é bilateral porque a questão pergunta se a estrutura muda,
sem presumir antecipadamente que ficará melhor ou pior.

## 3. Variáveis e tratamentos

- **Variável independente:** uso de ChatGPT durante o trial.
- **Tratamento IA:** ChatGPT Free com o mesmo modelo para todos.
- **Tratamento Manual:** nenhum assistente de IA habilitado.
- **Variáveis dependentes:** Time-to-Green, taxa de sucesso, testes falhando,
  LOC, complexidade e duplicação.
- **Variáveis de controle:** katas, testes, time-box, linguagem, versões,
  ambiente, instruções, acesso convencional à web e formato de coleta.

O uso convencional da web é permitido nos dois tratamentos. URLs devem ser
registradas para tornar essa influência observável.

## 4. Participantes e objetos experimentais

Participantes:

- Pedro (`PedroMaiaAlves`);
- Diogo (`DiogoBrunoro`);
- Lorran (`LorranX`).

Objetos experimentais:

1. Consolidar Janelas;
2. Planejar Recargas;
3. Agrupar Alertas;
4. Distribuir Cotas.

Os problemas são autorais ou adaptados e evitam exercícios extremamente
conhecidos, reduzindo a ameaça de memorização da IA.

## 5. Desenho crossover/within-subject

Cada participante resolve todos os quatro katas, sendo dois com IA e dois de
forma manual. Cada combinação participante + kata constitui um trial, totalizando
12 trials.

| Ordem | Pedro | Diogo | Lorran |
| --- | --- | --- | --- |
| 1 | kata01 / IA | kata02 / Manual | kata03 / Manual |
| 2 | kata02 / Manual | kata03 / IA | kata04 / IA |
| 3 | kata03 / IA | kata04 / IA | kata01 / Manual |
| 4 | kata04 / Manual | kata01 / Manual | kata02 / IA |

As ordens dos katas são rotações e as sequências de tratamento são diferentes.
Com três participantes, não é possível dividir cada kata igualmente entre dois
tratamentos; o melhor balanço possível é 2 × 1.

## 6. Procedimento

1. Validar o pacote experimental e congelar um baseline.
2. Criar cada branch de trial diretamente desse baseline.
3. Confirmar tratamento, recursos permitidos e ausência de soluções anteriores.
4. Iniciar a ferramenta de cronometragem com o número da Issue.
5. Resolver apenas o kata atribuído.
6. Encerrar no primeiro verde ou ao atingir 2.100 segundos.
7. Congelar o código e coletar testes e métricas.
8. Preservar trials incompletos e censurados.
9. Commitar solução e dados com referência à Issue.
10. Vincular o hash do commit ao registro e anexar evidências à Issue.

No tratamento IA, cada trial começa em uma conversa nova ou temporária, com
memória e instruções personalizadas desabilitadas. No tratamento Manual, todos
os assistentes de IA do navegador e IDE ficam desabilitados.

## 7. Coleta e análise futura

Cada trial registra horários, duração, censura, testes, taxa de sucesso, métricas
estáticas, tratamento, modelo, prompts, commit e Issue. Trials censurados recebem
2.100 segundos e não são descartados.

Na Sprint 03, a análise deve priorizar mediana e IQR. Comparações inferenciais
pareadas podem usar Wilcoxon, mas o grupo deve explicitar que somente três
participantes oferecem poder estatístico muito baixo. Os resultados serão
tratados principalmente como evidência exploratória e descritiva.

## 8. Ameaças à validade

### Validade interna

- **Aprendizagem e ordem:** mitigadas por crossover e contrabalanceamento.
- **Fadiga:** pausa mínima entre trials e registro da ordem.
- **Familiaridade com o kata:** os integrantes participam da preparação e podem
  conhecer parte dos problemas; registrar autores e evitar soluções de referência
  no repositório usado durante os trials.
- **Uso da web:** buscas podem revelar soluções; registrar URLs e proibir
  respostas ou resumos gerados por outras IAs.
- **Variação do assistente:** confirmar mesmo plano e modelo antes da execução.

### Validade de construção

- Time-to-Green não mede todas as dimensões de produtividade.
- Testes incompletos podem deixar defeitos sem observação.
- Métricas estruturais não equivalem, isoladamente, à qualidade do software.

Mitigação: combinar medidas, revisar testes e interpretar complexidade e
duplicação junto com LOC.

### Validade externa

Três estudantes e quatro katas pequenos não representam todos os profissionais,
linguagens ou projetos. As conclusões devem permanecer restritas ao contexto
observado.

### Validade de conclusão

A amostra é pequena e sujeita a alta variabilidade. Não tratar ausência de
significância como prova de ausência de efeito. Relatar valores individuais,
medianas, IQR, diferenças pareadas e limitações.

## 9. Artefatos esperados

- este desenho experimental;
- protocolo legível por máquina;
- especificações, stubs e testes dos quatro katas;
- ferramentas de trial, métricas, validação e Issues;
- CSV vazio com esquema versionado;
- README reproduzível;
- evidências de revisão e participação no GitHub Projects.
