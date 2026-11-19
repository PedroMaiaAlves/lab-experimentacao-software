# Proposta — Lab05S01 (Papel A: Planejamento e Método — Diogo)

## 1. O software: real, em operação e de alto impacto

Os números foram consultados em **18/11/2026**.

| Critério | Apache Kafka | RabbitMQ |
| --- | --- | --- |
| **Real** | Projeto da Apache Software Foundation, com site oficial e documentação ([kafka.apache.org](https://kafka.apache.org/)) | Mantido pela Broadcom/VMware, com site e documentação oficiais ([rabbitmq.com](https://www.rabbitmq.com/)) |
| **Em operação** | Versão **4.4.0**, imagem oficial `apache/kafka` atualizada em 22/10/2026 ([Docker Hub](https://hub.docker.com/r/apache/kafka)); 4.3.0 lançada em 22/05/2026 ([blog Apache](https://kafka.apache.org/blog/)) | Versão **4.4.1**, imagem oficial `rabbitmq` atualizada em 17/11/2026 ([Docker Hub](https://hub.docker.com/_/rabbitmq)); série 4.3 com suporte até 2028 ([changelog](https://rabbitmq.com/changelog.html)) |
| **Alto impacto** | "Mais de 80% das empresas da Fortune 100 confiam no Kafka e o usam" ([kafka.apache.org](https://kafka.apache.org/)). Pulls no Docker Hub: `confluentinc/cp-kafka` com 376,7 milhões, `bitnami/kafka` com 331,4 milhões e `apache/kafka` com 57,2 milhões | Imagem oficial `rabbitmq` com **3,92 bilhões** de pulls ([API Docker Hub](https://hub.docker.com/v2/repositories/library/rabbitmq/)). Oferecido como serviço gerenciado pela AWS (Amazon MQ, que adotou o RabbitMQ 4 em 05/2026, [AWS](https://aws.amazon.com/about-aws/whats-new/2026/05/amazon-mq-inplace-upgrades-rabbitmq4/)) |

A página do Kafka também lista a adoção entre as 10 maiores empresas de cada setor: 10 de
10 em manufatura, seguros e energia; 8 de 10 em telecom e transporte; 7 de 10 em bancos.

**Reprodutibilidade.** Os números vêm de `python Lab05/evidencias.py`, que consulta a API do
Docker Hub e o site do Kafka (1 requisição por segundo) e salva um snapshot datado em
[`data/evidencias/`](../data/evidencias/), sem sobrescrever snapshots anteriores. O snapshot
de referência é `impacto_2026-11-19.json` (UTC): 3.922.921.733 pulls do RabbitMQ e
765.293.734 pulls somados das três imagens do Kafka. As tags `4.4.1` e `4.4.0` existem nas
imagens oficiais. Para atualizar os números na entrega final, basta rodar o script de novo.

O objeto de pesquisa é o **software em funcionamento** (o broker sob carga), não o
repositório. Nenhum dado de GitHub é minerado.

## 2. Pergunta de pesquisa e caminho

**QP:** com durabilidade equivalente e o mesmo hardware, Kafka e RabbitMQ diferem em
throughput máximo e em latência de cauda (p99)? Essa diferença muda com o tamanho da
mensagem?

**Caminho:** rodar o software no ambiente do grupo. Fazemos um experimento controlado em
laboratório, com a mesma versão usada em produção.

## 3. GQM

**Objetivo (template de Basili):** *analisar* os brokers Apache Kafka 4.4.0 e RabbitMQ
4.4.1, *com o propósito de* compará-los, *com respeito a* desempenho (throughput e latência),
*do ponto de vista de* engenheiros que escolhem a infraestrutura de mensageria, *no contexto
de* um nó único em Docker com recursos fixos e entrega durável (*at-least-once*).

| Pergunta | Métrica | Entidade / atributo | Tipo | Escala |
| --- | --- | --- | --- | --- |
| Q1. Quantas mensagens por segundo cada broker sustenta? | M1: throughput máximo (msg/s) e MB/s na saturação | Recurso (broker), atributo externo | Derivada (contagem ÷ tempo) | Razão |
| Q2. Quanto uma mensagem leva do produtor ao consumidor? | M2: latência ponta a ponta p50 e p99 (ms) sob taxa fixa | Recurso (broker), atributo externo | Derivada (percentil de medidas diretas) | Razão |
| Q3. O tamanho da mensagem muda a comparação? | M3: razão Kafka/RabbitMQ de M1 e de M2 por tamanho | Interação de fatores | Derivada | Razão |
| Q4. Que custo de recurso acompanha o desempenho? | M4: CPU (%) e memória (MiB) médias do container (`docker stats`) | Recurso, atributo interno | Direta | Razão |

Como todas as métricas estão em escala de razão, são permitidos média geométrica, razões,
testes paramétricos e não paramétricos.

**Armadilhas de medição.** A **Lei de Goodhart** se aplica aqui: o throughput sozinho pode
ser "jogado" desligando a durabilidade (`acks=0`, sem *publisher confirms*) ou com lotes
gigantes que pioram a latência. Por isso:

1. fixamos a durabilidade em `acks=all` no Kafka e *publisher confirms* com *quorum queue*
   no RabbitMQ;
2. medimos a latência sob uma **taxa fixa** abaixo da saturação dos dois brokers, e não na
   saturação;
3. reportamos throughput e latência juntos.

Pela **Falácia de McNamara**, o que fica de fora (facilidade de operação, ecossistema,
semântica de roteamento) aparece explicitamente nas limitações.

## 4. Classificação nas 7 categorias (primeira versão)

| Categoria | Classificação | Justificativa |
| --- | --- | --- |
| Natureza | Aplicada | Responde a uma decisão prática de arquitetura, a escolha do broker |
| Objetivos | Explicativa | Testa relações de causa entre o broker (fator manipulado) e o desempenho |
| Abordagem | Quantitativa | As métricas são numéricas e em escala de razão, analisadas com testes de hipótese |
| Procedimentos | Experimental (benchmark controlado) | Manipulamos broker e tamanho da mensagem, com o resto fixo e ordem aleatória |
| Tempo | Transversal | Medições em uma janela de coleta, sem acompanhar a evolução ao longo do tempo |
| Controle | Experimento controlado em laboratório (*in vitro*) | Controle total de hardware, versões, configuração e carga, com randomização da ordem das execuções |
| Nível de evidência | Alto para validade interna, limitado para a externa | Há causalidade no ambiente controlado, mas a generalização para clusters de produção multinó é restrita |

## 5. Hipóteses (bicaudais, α = 0,05)

Seja *r* = razão Kafka/RabbitMQ da métrica, em cada tamanho de mensagem.

- **H1 (throughput)** — H₀: a mediana do throughput máximo é igual nos dois brokers
  (log *r* = 0). H₁: é diferente.
- **H2 (latência p99)** — H₀: a latência p99 sob taxa fixa é igual nos dois brokers.
  H₁: é diferente.
- **H3 (interação)** — H₀: a razão *r* não depende do tamanho da mensagem. H₁: depende.

**Expectativa registrada antes de coletar** (não é hipótese de teste). Pela arquitetura de
log com escrita sequencial e lotes, o Kafka deve ter **throughput maior**, com vantagem
crescente para mensagens pequenas. O RabbitMQ deve ser **competitivo ou melhor em latência**
sob carga moderada. Registramos isso agora para não ajustar a narrativa depois de ver os
dados (como fizemos no Lab04).

## 6. Variáveis e design

| Tipo | Variável | Níveis / valor |
| --- | --- | --- |
| Independente (fator principal) | Broker | Kafka 4.4.0 (KRaft) × RabbitMQ 4.4.1 (*quorum queue*) |
| Independente (bloco) | Tamanho da mensagem | 1 KiB × 16 KiB |
| Dependentes | M1–M4 | Seção 3 |
| Fixas | Hardware e recursos | Mesma máquina, container limitado a 4 vCPU e 4 GiB, disco local |
| Fixas | Durabilidade | `acks=all` / *publisher confirms*; 1 produtor, 1 consumidor, 1 partição / 1 fila |
| Fixas | Ferramenta de carga | A mesma para os dois brokers ([OpenMessaging Benchmark](https://openmessaging.cloud/docs/benchmarks/)), com as ferramentas nativas como fallback a decidir no piloto (Pedro) |
| Fixas | Duração | 30 s de aquecimento descartado e 60 s medidos por execução |

**Design fatorial 2 × 2**, com **10 execuções independentes por célula** (40 execuções por
experimento). A ordem de todas as execuções é embaralhada com a **semente 42**, e cada
execução começa com containers e volumes recriados, para não haver estado residual nem
efeito de ordem. São dois experimentos:

- **E1 (saturação):** mede M1 e M4.
- **E2 (taxa fixa):** usa 50% do menor throughput medido no E1 e mede M2 e M4.

O tamanho amostral (10 execuções) será revisto depois do piloto, com uma simulação de poder
reaproveitando `simular.py` do Lab04 e a variância observada.

## 7. Ameaças à validade (versão inicial)

| Tipo | Ameaça | Mitigação |
| --- | --- | --- |
| Conclusão | Poucas execuções e variância alta do p99 | Simulação de poder sobre o piloto, teste não paramétrico, IC por bootstrap, correção de Holm para várias comparações |
| Interna | Interferência do SO e de outros processos; efeito de ordem e de aquecimento | Máquina dedicada, ordem aleatória, aquecimento descartado, recriar containers, registrar o ambiente |
| Interna | Configuração "injusta" (tuning favorecendo um lado) | Configuração padrão documentada, com só a durabilidade equalizada e a mesma ferramenta de carga |
| Construto | "Desempenho" reduzido a throughput e p99; latência medida na saturação distorce | GQM com quatro métricas, latência sob taxa fixa, CPU e memória reportadas |
| Externa | Nó único em Docker num notebook, diferente de clusters de produção com replicação | Declarar o limite; não extrapolar valores absolutos, só a direção e a razão relativa |

## 8. Plano de análise (detalhado por Lorran em `plano_analise.md`)

1. **Descritiva:** mediana, IQR e média geométrica por célula, com boxplots.
2. **Testes:** em cada tamanho, Welch sobre o log da métrica, se o piloto indicar
   normalidade (Shapiro), ou Mann-Whitney caso contrário. A interação H3 é testada com ANOVA
   sobre log ou com teste de permutação. Aplicamos correção de Holm.
3. **Tamanho do efeito:** razão das médias geométricas com IC de 95% por bootstrap e
   δ de Cliff.
4. **Impacto:** converter a diferença em CPU-hora economizada por milhão de mensagens.

## 9. Reaproveitamento dos laboratórios anteriores

| Lab | O que reaproveitamos |
| --- | --- |
| Lab01 | Kanban no GitHub Projects e coleta automatizada (aqui, da API do Docker Hub para as evidências de impacto) |
| Lab02 | Desenho com tratamentos: broker como tratamento e tamanho como bloco |
| Lab03 | Visão de operação: latência e throughput como SLIs, e a ideia de SLO no impacto |
| Lab04 | Escolha entre teste paramétrico e não paramétrico, simulação de poder, dashboard Streamlit, semente fixa e expectativa registrada antes |
