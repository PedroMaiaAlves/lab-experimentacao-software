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

- `gerar_plano` monta as 4 células × n repetições em dois blocos balanceados por experimento
  e embaralha cada bloco com `numpy.random.default_rng([42, índice_do_experimento,
  índice_do_bloco])`. A ordem é reprodutível e diferente entre E1 e E2.
- **Objetivo:** distribuir entre as células os efeitos de ordem (cache de disco, temperatura
  da CPU, atualizações do SO durante a coleta). Sem isso, rodar todas as execuções do Kafka
  antes das do RabbitMQ confundiria o broker com o momento da coleta.
- **Saídas:** [`data/plano/plano_E1.csv`](../data/plano/plano_E1.csv) e
  [`plano_E2.csv`](../data/plano/plano_E2.csv), com 80 linhas cada. O coletor de Pedro (#199)
  executa as linhas na ordem da coluna `ordem` e grava o resultado com o mesmo
  `id_execucao`.
- **Testes:** verificam o balanceamento (n por célula), os IDs únicos, a reprodutibilidade,
  que a ordem não é a das células e as versões da proposta.

### 2.4 Tamanho amostral: revisão com o CV observado

O pré-registro original simulou uma métrica log-normal, com Welch sobre o log e
Mann-Whitney bicaudal, usando **α/4 = 0,0125** (pior caso de Holm para H1 e H2 nos dois
tamanhos). A revisão da #207 executa a mesma simulação com 10.000 repetições, semente 42 e os
CVs do mini-piloto estabilizado do E1. A tabela completa está em
[`data/plano/poder_observado.csv`](../data/plano/poder_observado.csv).

| Célula E1 | CV observado | Poder MW, n=20, razão 1,20 | Poder Welch-log, n=20, razão 1,20 |
| --- | ---: | ---: | ---: |
| Kafka 1 KiB | 20,10% | 58,0% | 60,5% |
| Kafka 16 KiB | 30,34% | 24,1% | 25,4% |
| RabbitMQ 1 KiB | 3,74% | 100,0% | 100,0% |
| RabbitMQ 16 KiB | 11,18% | 99,1% | 99,4% |

O portão G1 **reprovou** nas duas células Kafka (limite pré-registrado: CV ≤ 20%). Mesmo no
teto de 20 execuções, não é possível obter 80% de poder para uma razão 1,20 no pior caso:
o Kafka 16 KiB alcança somente cerca de 24–25%. O critério não foi alterado depois de ver os
dados e esta limitação deve acompanhar qualquer conclusão sobre efeitos pequenos.

O p99 do piloto de 19/11 é inválido para dimensionamento porque o timestamp do driver
RabbitMQ tinha resolução de segundos. A verificação corrigida tem somente 1–2 observações
por célula e nenhuma observação de Kafka 16 KiB; portanto **não existe CV estabilizado de
p99**. O arquivo de poder registra `cv_indisponivel`, em vez de estimar poder com evidência
insuficiente.

**Decisão final antes da coleta: n = 20 por célula**, o teto pré-registrado. São 80 execuções
por experimento e 160 no total, além de repetições exclusivamente técnicas. O n não é
apresentado como suficiente para razão 1,20 no Kafka; é a maior amostra permitida pelo
protocolo e reduz a incerteza dentro do tempo disponível.

Cada experimento é dividido em dois blocos balanceados de 40 execuções (10 por célula):
`E1-B1`, `E1-B2`, `E2-B1` e `E2-B2`. Todo o E1 precede o E2. O E1 mede por 120 s; o E2,
por 60 s. As colunas `bloco`, `ordem` e `ordem_no_bloco` ficam congeladas nos planos.

### 2.5 Falhas, repetições, exclusões e outliers

- **Falha técnica:** erro ao iniciar broker ou ferramenta, timeout, código de saída diferente
  de zero, interrupção, JSON bruto ausente ou JSON que não pode ser interpretado.
- **Repetição:** somente um ID sem tentativa bem-sucedida pode ser repetido. Repete-se a
  execução inteira, mantendo bloco, `ordem` e `ordem_no_bloco`; cada tentativa recebe número
  e arquivos próprios. Nenhuma tentativa é sobrescrita.
- **Exclusão:** somente a tentativa com falha técnica registrada fica fora das métricas. Um
  ID com mais de uma tentativa bem-sucedida é erro de protocolo, não amostra adicional.
- **Outliers:** valores extremos, mas tecnicamente válidos, são mantidos, marcados e
  reportados. Nunca são removidos por parecerem “estranhos”.

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

## 4. Revisão das ameaças com evidência (S02, #208)

A tabela da seção 3 foi escrita antes de qualquer dado. Esta seção registra o que o piloto
(19/11), os mini-pilotos do portão G1 (25/11) e a verificação do E2 mostraram de fato. Cada
linha traz a **evidência**, a **mitigação aplicada** e o **risco residual**.

> **Situação:** esta é a revisão parcial. A coleta oficial (#210) e a análise (#211) ainda não
> existem. As linhas marcadas com ⏳ dependem delas e serão completadas quando forem entregues.

### 4.1 Ameaças confirmadas pela evidência

| Tipo | Ameaça | Evidência observada | Mitigação aplicada | Risco residual |
| --- | --- | --- | --- | --- |
| **Construto** | O E1 não media o throughput máximo do broker | `producerRate: 0` ligava o `RateController` adaptativo do OMB; no piloto, 4 execuções do Kafka caíram a cerca de 1 msg/s e o CV foi de 52% a 128% (`protocolo_coleta.md`, #209) | Taxa fixa aberta (`TAXA_E1_ABERTA`); zero colapsos nos mini-pilotos; o Kafka 1 KiB passou de 22 mil para cerca de 125 mil msg/s | Baixo para o artefato. **Os resultados de E1 do piloto de 19/11 não devem ser usados como estimativa**: subestimam o Kafka em cerca de 6× |
| **Construto** | A latência ponta a ponta do RabbitMQ era medida com erro sistemático | No piloto, o p50 do RabbitMQ no E2 ficou em cerca de 500 ms e o p99 em cerca de 995 ms em **todas** as execuções, com latência de publicação de 10–20 ms. O driver do OMB grava o tempo na propriedade `timestamp` do AMQP 0-9-1, que tem resolução de **segundos**: o erro é uniforme entre 0 e 1000 ms. O Kafka usa timestamp em ms | Patch `benchmark/omb-rabbitmq-timestamp-ms.patch`: tempo em ms no header `omb-ts-ms`; imagem renomeada para `5b1fa709-ts-ms`, para não usar a antiga por engano. Verificação em `data/verificacao_e2/` (seção 4.3) | Baixo depois da correção (confirmado na seção 4.3). **A latência do RabbitMQ no piloto de 19/11 é inválida**, e a comparação da H2 feita com ela favoreceria o Kafka por construção |
| **Construto** | A taxa do E2 ("50% do menor throughput do E1") não representa a mesma carga relativa para os dois brokers | A taxa do piloto (6.285 msg/s em 1 KiB) veio do E1 com o artefato. No RabbitMQ 1 KiB (cerca de 8,7 mil msg/s nos mini-pilotos) isso é cerca de 72% da capacidade, não 50%. Nas execuções `E2-rabbitmq-1k-r01` e `r03`, a taxa de publicação caiu abaixo do alvo e a latência de publicação subiu para 1,6–2,5 s, sinal de carga perto da saturação | A taxa do E2 **precisa** ser recalculada a partir do E1 oficial, já corrigido (a regra do coletor `taxas_e2` continua valendo). Registrar a carga relativa de cada broker (taxa ÷ throughput mediano do E1) | Médio: a 50% do *menor* throughput, o Kafka roda bem abaixo de 50% da sua capacidade. Isso é intencional (mesma carga absoluta) e precisa ser dito na interpretação |
| **Conclusão** | A variância do Kafka no E1 é alta | Portão G1 reprovado para o Kafka: CV de 20,3% (1 KiB) e 30% (16 KiB), com CV de 20–43% entre intervalos de cada execução. A CPU do broker fica em 90–150% de 400%, então o limite não é CPU | Medição de 120 s (estabilizou o RabbitMQ: CV de 4% e 11%); n revisado na #207 com o CV observado (n = 15 dá poder ≥ 84% para razão 1,5) | Médio: diferenças menores que cerca de 1,5× entre os brokers no E1 não serão detectáveis. As razões observadas (cerca de 14× e 2,2×) estão muito acima disso |
| **Interna** | Interrupção da máquina durante a coleta | No mini-piloto de 25/11 a máquina suspendeu: 3 execuções ficaram horas paradas e falharam com timeout negativo (salto de relógio) | O coletor bloqueia a suspensão (`sem_suspensao`); as falhas foram preservadas e repetidas com `--repetir-falhas` | Baixo. Fechar a tampa do notebook ainda suspende: está no protocolo |
| **Interna** | Falha de partida do broker confundida com desempenho | `E1-rabbitmq-1k-r02` falhou duas vezes, em coletas diferentes: o healthcheck `ping` aprovava o container antes de a porta AMQP abrir | Healthcheck `check_port_connectivity` | Baixo; as falhas são registradas e não entram na análise |
| **Interna** | Mudança de máquina entre as fases | O piloto de 19/11 rodou na máquina do Pedro (Ryzen 5 5600, 16 GiB); os mini-pilotos do G1, na do Diogo (16 processadores lógicos, 7,6 GiB para a VM Docker). O throughput absoluto difere entre máquinas | Coleta oficial inteira numa só máquina, registrada no manifesto; o G1 deve ser reconferido nessa máquina antes da coleta (#207) | ⏳ Confirmar que a #210 foi coletada numa única máquina |
| **Conclusão** | Reprodutibilidade quebrada por fim de linha | Com `core.autocrlf=true`, o patch do OMB virava CRLF e o build falhava ("corrupt patch") | `.gitattributes` força LF em `Lab05/benchmark/**` | Baixo |

### 4.2 Ameaças previstas que ainda dependem da coleta oficial ⏳

| Tipo | Ameaça | O que verificar quando a #210/#211 forem entregues |
| --- | --- | --- |
| Interna | Efeito de ordem e deriva da máquina | Regressão do log do throughput na posição de execução (`ordem`) e por bloco; inclinação com IC contendo 0 |
| Interna | Efeito de bloco (sessões em dias diferentes) | Mediana por bloco em cada célula; incluir o bloco como covariável se houver diferença |
| Conclusão | Normalidade do log para escolher entre Welch e Mann-Whitney | Shapiro por célula; a escolha segue a regra pré-registrada no `plano_analise.md`, sem trocar de teste depois de ver p-valores |
| Conclusão | Execuções repetidas alteram o resultado | Análise de sensibilidade com e sem as execuções que precisaram de repetição |
| Construto | Latência do E2 sob a mesma carga relativa | Reportar a carga relativa (taxa ÷ capacidade) de cada broker junto da latência |

### 4.3 Verificação da correção do timestamp do RabbitMQ

Coleta `data/verificacao_e2/20261125T113906.033745Z`, com a imagem `5b1fa709-ts-ms`, 60 s
medidos e taxa fixa. A taxa de 1.069 msg/s é **a mesma do E2 16 KiB do piloto**, o que
permite comparar antes e depois diretamente.

| Execução | Taxa | p50 ponta a ponta | p99 ponta a ponta | p99 de publicação |
| --- | ---: | ---: | ---: | ---: |
| Piloto 19/11, RabbitMQ 16 KiB (r01–r03, imagem antiga) | 1.069 | **503–506 ms** | **994–998 ms** | 10–117 ms |
| `E2-rabbitmq-16k-v01` (corrigida) | 1.069 | 7 ms | 48 ms | 46 ms |
| `E2-rabbitmq-16k-v02` (corrigida) | 1.069 | 18 ms | 115 ms | 111 ms |
| `E2-rabbitmq-1k-v01` (corrigida) | 3.000 | 4 ms | 38 ms | 35 ms |
| `E2-rabbitmq-1k-v02` (corrigida) | 3.000 | 4 ms | 37 ms | 35 ms |
| `E2-kafka-1k-v01` (referência) | 3.000 | 2 ms | 4 ms | 3 ms |

**Conclusão:** confirmado. Com o tempo em milissegundos, o p50 do RabbitMQ caiu de cerca de
500 ms para 4–18 ms, e o p99 ponta a ponta passou a acompanhar o p99 de publicação, o que é
coerente porque o consumidor não acumula atraso (backlog de cerca de 0). No piloto, os cerca de
500 ms de p50 e os cerca de 995 ms de p99 eram **só o erro de arredondamento para o segundo**.
A diferença entre os brokers continua existindo (p99 de 4 ms no Kafka contra 37–115 ms no
RabbitMQ nestas execuções), mas agora é medida e cerca de 10–25× menor que a do piloto. Isto é
uma verificação de instrumento (n = 1–2, sem inferência), não um resultado da H2.

### 4.4 Revisão das 7 categorias e do GQM

- **7 categorias:** nenhuma mudança de classificação. O estudo continua aplicado, explicativo,
  quantitativo, experimental, transversal e controlado em laboratório. O **nível de evidência**
  recebe uma ressalva: a validade interna é alta *para o E1 corrigido e para a latência
  corrigida*; os dados do piloto de 19/11 não servem como evidência de nenhuma das duas.
- **GQM, Q1/M1 (throughput):** o construto agora corresponde à definição, ou seja, a
  contrapressão do broker, não a do controlador. Sugere-se reportar também
  `throughput_consumo_msg_s`, que mede o que de fato foi entregue.
- **GQM, Q2/M2 (latência):** a métrica só mede o que diz medir com o patch de timestamp em ms.
  Fica proibido comparar latência entre os brokers com dados coletados com a imagem
  `5b1fa709` (sem `-ts-ms`). O `manifesto.json` registra o ID da imagem usada.
- **Goodhart, na prática:** os dois defeitos (controlador adaptativo e timestamp em segundos)
  produziam números plausíveis e "limpos" (o E2 do RabbitMQ teve CV de 0% no p99). Uma métrica
  estável não é uma métrica válida, e por isso a revisão verificou o que gera cada número no
  código da ferramenta.

### 4.5 Revisão da análise (a fazer na PR da #211)

O checklist está em [`revisao_analise.md`](revisao_analise.md) e é preenchido na revisão da PR
do Lorran.
