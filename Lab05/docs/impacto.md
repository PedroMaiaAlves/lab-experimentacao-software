# Estimativa de Impacto — Lab05S01 (Papel C: Lorran)

Este documento reúne as fontes públicas de adoção do Apache Kafka e do RabbitMQ e define o método
de conversão das medições do experimento em **custo computacional (vCPU-hora e GiB-hora por
milhão de mensagens)**, seguido da primeira estimativa obtida no piloto.

---

## 1. Fontes públicas de escala e adoção

Os números abaixo foram coletados de forma reproduzível via `python Lab05/evidencias.py` e
preservados em [`data/evidencias/impacto_2026-11-19.json`](../data/evidencias/impacto_2026-11-19.json)
(acesso em **19/11/2026**, UTC):

| Software | Evidência de impacto | Número observado | Fonte |
| --- | --- | --- | --- |
| **RabbitMQ 4.4.1** | Pulls da imagem oficial `library/rabbitmq` | **3.922.921.733** pulls | [API Docker Hub — rabbitmq](https://hub.docker.com/v2/repositories/library/rabbitmq/) |
| **RabbitMQ** | Oferta gerenciada em nuvem pública (RabbitMQ 4) | Amazon MQ (suporte desde 05/2026) | [AWS What's New](https://aws.amazon.com/about-aws/whats-new/2026/05/amazon-mq-inplace-upgrades-rabbitmq4/) |
| **Apache Kafka 4.4.0** | Adoção corporativa global | **> 80% das empresas Fortune 100** | [kafka.apache.org](https://kafka.apache.org/) |
| **Apache Kafka** | Adoção nos top 10 por setor | 10/10 manufatura, seguros e energia; 8/10 telecom e transporte; 7/10 bancos | [kafka.apache.org](https://kafka.apache.org/) |
| **Apache Kafka** | Pulls somados de 3 imagens principais no Docker Hub | **765.293.734** pulls (`confluentinc/cp-kafka`: 376,7M; `bitnami/kafka`: 331,4M; `apache/kafka`: 57,2M) | [Docker Hub API](https://hub.docker.com/r/apache/kafka) |

Esses números mostram que decisões de arquitetura entre Kafka e RabbitMQ afetam cargas de
mensageria em larga escala industrial, onde pequenas diferenças de eficiência por mensagem se
multiplicam por bilhões de eventos mensais.

---

## 2. Método de conversão para CPU-hora (e memória-hora)

O `docker stats` reporta `cpu_percent_medio` na convenção de **100% = 1 vCPU** (o container tem
teto de 4 vCPU, logo o valor varia de 0% a 400%) e `memoria_mib_media` em MiB.

Para cada execução válida, convertemos o consumo médio de recursos e o throughput medido
($T$, em mensagens/segundo) no custo computacional para processar **1 milhão de mensagens**:

$$\text{vCPU-hora por } 10^6 \text{ msg} = \frac{\text{CPU\%} / 100}{T} \times \frac{10^6}{3600}$$

Como contrapeso à **Falácia de McNamara** (olhar só CPU esconderia o custo de memória da JVM do
Kafka), calculamos pela mesma lógica o consumo de memória:

$$\text{GiB-hora por } 10^6 \text{ msg} = \frac{\text{RAM (MiB)} / 1024}{T} \times \frac{10^6}{3600}$$

**Interpretação:** a diferença $\Delta_{\text{CPU}} = \text{vCPU-h}_{\text{RabbitMQ}} - \text{vCPU-h}_{\text{Kafka}}$
indica quantas vCPU-horas são economizadas (se positiva) ou gastas a mais (se negativa) a cada
milhão de mensagens processadas. O cálculo está implementado em `estimar_cpu_hora` no
[`analisar.py`](../analisar.py).

---

## 3. Primeira estimativa de impacto no piloto

Valores medianos calculados sobre o piloto concluído
(`data/piloto/20261119T030115.153119Z/resultados.csv`, 23 execuções com sucesso):

| Exp | Tamanho | Broker | Throughput med. (msg/s) | CPU med. (%) | RAM med. (MiB) | vCPU-h / 1M msg | GiB-h / 1M msg |
| --- | ---: | --- | ---: | ---: | ---: | ---: | ---: |
| E1 | 1 KiB | Kafka | 22.380,60 | 126,56 | 3.290,33 | **0,0157** | 0,0399 |
| E1 | 1 KiB | RabbitMQ | 12.571,68 | 243,61 | 195,47 | **0,0538** | 0,0042 |
| E1 | 16 KiB | Kafka | 2.129,33 | 191,62 | 3.309,15 | **0,2500** | 0,4169 |
| E1 | 16 KiB | RabbitMQ | 2.700,48 | 182,19 | 210,99 | **0,1874** | 0,0212 |
| E2 | 1 KiB | Kafka | 6.319,55 | 165,29 | 1.001,70 | **0,0727** | 0,0430 |
| E2 | 1 KiB | RabbitMQ | 6.315,34 | 170,37 | 176,35 | **0,0837** | 0,0078 |
| E2 | 16 KiB | Kafka | 1.068,48 | 121,15 | 1.115,56 | **0,3148** | 0,2832 |
| E2 | 16 KiB | RabbitMQ | 1.069,67 | 105,18 | 176,66 | **0,2735** | 0,0449 |

### Leitura preliminar (sujeita à coleta completa da S02)
- **Mensagens pequenas (1 KiB):** o Kafka exigiu menos CPU por milhão de mensagens tanto na
  saturação (`0,0157` vs. `0,0538` vCPU-h/1M — cerca de **3,4× menos CPU**) quanto sob taxa fixa
  de 6.285 msg/s (`0,0727` vs. `0,0837` vCPU-h/1M — economia mediana de **0,0110 vCPU-h/1M**, ou
  ~13%). Em um fluxo hipotético de 1 bilhão de mensagens/mês (~386 msg/s contínuos), essa
  diferença em E2 corresponderia a cerca de **11 vCPU-horas/mês** (e ~38 vCPU-horas/mês no regime
  de saturação E1).
- **Mensagens grandes (16 KiB):** o RabbitMQ usou menos CPU por milhão de mensagens nos dois
  experimentos (`0,1874` vs. `0,2500` em E1; `0,2735` vs. `0,3148` em E2 — cerca de **13% a 25%
  menos CPU** no RabbitMQ).
- **Trade-off de memória:** em **todos** os cenários, o Kafka consumiu de **5,5× a 19,7× mais
  GiB-hora por milhão de mensagens** que o RabbitMQ, refletindo o *footprint* base da JVM.
- **SLO de latência (E2):** se o sistema exigir um SLO de latência p99 abaixo de 100 ms sob
  durabilidade forte, apenas o Kafka atendeu a essa faixa no piloto (3–22 ms contra 994–3.120 ms
  do RabbitMQ).

---

## 4. Limitações de validade externa da estimativa

1. **Nó único em Docker ≠ cluster replicado:** em produção com replicação entre 3 nós (tráfego de
   rede inter-broker, Raft/KRaft distribuído e discos dedicados), os valores absolutos de
   vCPU-hora e latência mudam. Por isso **não extrapolamos valores absolutos** para clusters de
   produção, apenas a direção, as razões relativas e o trade-off entre CPU, RAM e p99.
2. **Amostra piloto pequena e anomalias em E1:** o piloto teve $n = 2$ a $3$ por célula e duas
   execuções anômalas do Kafka em E1 (que puxam a média geométrica para cima; por isso esta seção
   usa a mediana e mantém o resultado como provisório até a coleta completa da S02).
3. **Escopo restrito:** mede apenas o container do broker sob 1 produtor, 1 consumidor e 1
   partição/fila; não contabiliza CPU do cliente gerador (OMB), disco, rede nem custo operacional
   de equipe.
