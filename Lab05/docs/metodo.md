# Método — 7 categorias, design e ameaças à validade (issue #197)

Este documento detalha as seções 4, 6 e 7 da [proposta](proposta.md). O que está aqui é
executável: o plano de execuções e a tabela de poder saem de `python Lab05/planejar.py`, e
os testes estão em `Lab05/tests/test_plano.py`.

## 1. As 7 categorias da pesquisa

| Categoria | Classificação | Por que esta e não a alternativa |
| --- | --- | --- |
| **Natureza** | Aplicada | O resultado serve a uma decisão concreta (que broker adotar e quando), não à construção de teoria. Não é básica. |
| **Objetivos** | Explicativa | Manipulamos o broker e o tamanho da mensagem para atribuir causa às diferenças de desempenho. Não é só descritiva (não nos limitamos a medir) nem exploratória (as hipóteses são definidas antes). |
| **Abordagem** | Quantitativa | Todas as métricas (msg/s, ms, % de CPU, MiB) são numéricas em escala de razão e analisadas com testes de hipótese e tamanho de efeito. Não há dado qualitativo. |
| **Procedimentos** | Experimental (benchmark controlado) | Há manipulação de fatores, controle das variáveis fixas e randomização da ordem. Não é levantamento (survey), estudo de caso nem pesquisa documental. |
| **Tempo** | Transversal | Cada execução é independente, numa janela de coleta curta. Não acompanhamos versões ao longo do tempo (isso seria longitudinal). |
| **Controle** | Experimento controlado em laboratório (*in vitro*) | Temos controle total de hardware, versões, configuração, carga e ordem. Não é quase-experimento, porque a atribuição da ordem é aleatória, nem observacional, porque intervimos. |
| **Nível de evidência** | Alto para a validade interna, limitado para a externa | A randomização e o controle sustentam a causalidade *neste ambiente*. Um nó único em Docker não representa clusters de produção (seção 3, validade externa). |

## 2. Design do experimento

### 2.1 Objetos, fatores e variáveis

- **Objetos experimentais:** as imagens oficiais `apache/kafka:4.4.0` (KRaft, 1 nó) e
  `rabbitmq:4.4.1` (*quorum queue*, 1 nó). Não há participantes humanos.
- **Fator principal (tratamento):** o broker, com 2 níveis.
- **Segundo fator:** o tamanho da mensagem, com 2 níveis: 1 KiB, típico de eventos e logs, e
  16 KiB, típico de documentos e payloads JSON maiores. Ele permite testar a interação (H3).
- **Variáveis dependentes:** M1 (throughput máximo), M2 (latência p50/p99 sob taxa fixa) e M4
  (CPU e memória). Ver o GQM na proposta.
- **Variáveis fixas:** estão em `experimento/plano.py` (`FIXAS`): 4 vCPU e 4 GiB por
  container; 1 produtor, 1 consumidor e 1 partição ou fila; `acks=all` ou *publisher
  confirms* com *quorum queue*; containers e volumes recriados a cada execução; 30 s de
  aquecimento descartado e 60 s medidos.

### 2.2 Tipo de design

**Fatorial completo 2 × 2 entre execuções** (*between-runs*): cada execução pertence a uma
única célula e começa de um estado limpo. Por isso as amostras das células são independentes
e a comparação usa testes para duas amostras independentes (Welch ou Mann-Whitney), e não os
pareados do Lab04.

São dois experimentos com o mesmo design:

| Experimento | Carga | Mede | Depende de |
| --- | --- | --- | --- |
| **E1 — saturação** | Produtor o mais rápido possível | M1 e M4 | — |
| **E2 — taxa fixa** | 50% do menor throughput mediano observado no E1 | M2 e M4 | E1 |

A latência é medida no E2, e não no E1, porque na saturação as filas internas crescem e a
latência mede o tamanho da fila, não o broker. Esse é o cuidado de construto e de Goodhart
discutido na proposta.

### 2.3 Randomização

- `gerar_plano` monta as 4 células × n repetições e embaralha a ordem com
  `numpy.random.default_rng([42, índice_do_experimento])`. A ordem é reprodutível e diferente
  entre E1 e E2.
- **Objetivo:** distribuir entre as células os efeitos de ordem (cache de disco, temperatura
  da CPU, atualizações do SO durante a coleta). Sem isso, rodar todas as execuções do Kafka
  antes das do RabbitMQ confundiria o broker com o momento da coleta.
- **Saídas:** [`data/plano/plano_E1.csv`](../data/plano/plano_E1.csv) e
  [`plano_E2.csv`](../data/plano/plano_E2.csv), com 40 linhas cada. O coletor de Pedro (#199)
  executa as linhas na ordem da coluna `ordem` e grava o resultado com o mesmo
  `id_execucao`.
- **Testes:** verificam o balanceamento (n por célula), os IDs únicos, a reprodutibilidade,
  que a ordem não é a das células e as versões da proposta.

### 2.4 Tamanho amostral: poder a priori

Ainda não temos o piloto, então não conhecemos a variabilidade entre execuções. Simulamos
(`experimento/poder.py`, 2000 repetições por cenário, semente 42) uma métrica log-normal com
coeficiente de variação (CV) de 5%, 10% e 20%, testada com Welch sobre o log e com
Mann-Whitney. O nível usado é **α/4 = 0,0125**, o pior caso de Holm para as 4 comparações
principais (H1 e H2 × 2 tamanhos).

Menor n por célula para atingir 80% de poder (os dois testes coincidiram):

| CV entre execuções | razão 1,05 | razão 1,10 | razão 1,20 | razão 1,50 |
| --- | --- | --- | --- | --- |
| 5% | > 20 | 10 | 5 | 5 |
| 10% | > 20 | > 20 | 10 | 5 |
| 20% | > 20 | > 20 | > 20 | 8 |

**Decisão provisória: n = 10 por célula** (40 execuções e cerca de 1 h de coleta por
experimento). Com esse n, detectamos uma diferença de 10% se o CV for de até 5%, ou de 20%
se o CV for de até 10%. Benchmarks publicados de Kafka e RabbitMQ costumam mostrar
diferenças bem maiores que 20%. Diferenças menores que 10% teriam pouco efeito prático na
escolha do broker.

**Regra de revisão (fecha a pendência da #197 depois do piloto):** se o CV observado no
piloto (#199) passar de 10% em alguma célula, Lorran (#201) roda a mesma simulação com o CV
observado e aumentamos n até 80% de poder para razão 1,20, com limite de 20 por célula. O n
final é registrado aqui **antes** da coleta completa.

## 3. Ameaças à validade

| Tipo | Ameaça | Mitigação | Responsável |
| --- | --- | --- | --- |
| **Conclusão** | Baixo poder para efeitos pequenos | Poder a priori (2.4) e revisão com o CV do piloto | Diogo / Lorran |
| **Conclusão** | Várias comparações inflam o erro tipo I | Correção de Holm sobre as 4 comparações principais | Lorran |
| **Conclusão** | Normalidade incerta do log da métrica | Reportar Mann-Whitney junto com Welch-log; IC por bootstrap da razão geométrica | Lorran |
| **Conclusão** | O p99 de uma execução é instável | Usar 60 s medidos (milhares de mensagens por percentil) e analisar a distribuição dos p99 entre execuções | Pedro / Lorran |
| **Interna** | Efeito de ordem e deriva da máquina | Ordem randomizada (2.3) e registro do horário de cada execução para checar tendência | Diogo / Pedro |
| **Interna** | Estado residual (dados, page cache, JIT) | Recriar containers e volumes a cada execução e descartar 30 s de aquecimento | Pedro |
| **Interna** | Interferência de outros processos | Máquina na tomada, sem outros programas, perfil de energia fixo e registro de `docker stats` | Pedro |
| **Interna** | Ferramenta de carga favorece um broker | Mesma ferramenta (OpenMessaging Benchmark) para os dois; se for preciso usar as nativas, documentar a diferença como limitação | Pedro |
| **Construto** | "Desempenho" reduzido a um número | Quatro métricas (throughput, p50, p99 e recursos) e latência sob taxa fixa | Diogo |
| **Construto** | Durabilidade não equivalente torna a comparação injusta | Equalizar a garantia *at-least-once* com persistência (`acks=all` × *publisher confirms* + *quorum*) | Diogo / Pedro |
| **Construto** | Configuração padrão não é a de produção | Declarar que comparamos a configuração padrão com durabilidade equalizada, não o tuning ótimo | Diogo |
| **Externa** | Nó único em notebook × cluster replicado em servidor | Não extrapolar valores absolutos; reportar só razões e direção; discutir no impacto | Lorran |
| **Externa** | Só dois tamanhos e um padrão de carga (1 produtor e 1 consumidor) | Declarar o escopo; listar como trabalho futuro mais partições e mais consumidores | Diogo |
| **Externa** | Versões específicas (4.4.x) | Usar as versões mantidas atuais e registrar os hashes das imagens no protocolo | Pedro |
