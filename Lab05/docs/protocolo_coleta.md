# Protocolo de coleta — Kafka × RabbitMQ

## Ambiente de referência

O piloto é executado localmente, sem carga em serviços de terceiros. O ambiente registrado
em 18/11/2026 é:

| Item | Valor |
| --- | --- |
| CPU | AMD Ryzen 5 5600, 6 núcleos e 12 processadores lógicos |
| RAM | 16 GiB |
| SO | Windows 11 Pro 64 bits, build 26300 |
| WSL | 3.0.5.0, kernel 6.18.58.1 |
| Docker | Client 28.4.0, contexto `desktop-linux` |
| Docker Compose | 2.39.2 |

O coletor também grava esses valores, o commit Git e os *digests* efetivamente usados no
`manifesto.json` de cada coleta. Durante as medições, a máquina deve ficar na tomada, com
perfil de energia fixo e sem outras aplicações de uso intensivo.

## Brokers e limites

O arquivo `docker-compose.yml` usa as imagens oficiais `apache/kafka:4.4.0` e
`rabbitmq:4.4.1-management`. Cada broker recebe no máximo **4 vCPU e 4 GiB**. Apenas um
broker é iniciado por execução. O coletor sempre executa `docker compose down --volumes
--remove-orphans` antes e depois de cada medição, eliminando dados e estado residual.

- Kafka roda em nó único KRaft, uma partição, fator de replicação 1,
  `min.insync.replicas=1`, `acks=all` e produtor idempotente.
- RabbitMQ usa uma fila durável do tipo *quorum*, mensagens persistentes, confirmações do
  publicador e confirmação manual do consumidor pelo driver. O usuário isolado `lab05`
  é criado no início de cada execução; a conta `guest`, restrita a conexões locais pelo
  RabbitMQ, não é usada entre containers.

Em nó único nenhuma das tecnologias tolera a perda do nó; a equalização representa a
confirmação após persistência local. O experimento não afirma equivalência com clusters
replicados de produção.

## Ferramenta de carga

Foi escolhido o [OpenMessaging Benchmark](https://github.com/openmessaging/benchmark),
fixado no commit `5b1fa70951a323da26bd587174b58bb2c65b0b5c`. Ele usa a mesma instrumentação e o mesmo
formato de métricas para Kafka e RabbitMQ, evitando comparar cálculos diferentes das
ferramentas nativas. O driver RabbitMQ habilita *publisher confirms* e suporta filas
*quorum*; o driver Kafka usa `acks=all`.

Como o OMB original expressa duração apenas em minutos, a imagem aplica o patch versionado
`benchmark/omb-seconds.patch`. Ele acrescenta campos em segundos sem mudar o comportamento
dos campos originais. Assim são cumpridos exatamente 30 s de aquecimento descartado e 60 s
de medição. O mesmo patch encerra explicitamente a JVM depois de `worker.close()`, evitando
que threads não daemon da revisão fixada mantenham o container ativo após o JSON ser gravado.

## Comandos

Validar sem iniciar containers:

```powershell
docker compose -f Lab05/docker-compose.yml config
python -m pytest Lab05/tests
```

Construir a ferramenta e baixar as imagens, depois dos primeiros commits:

```powershell
docker compose -f Lab05/docker-compose.yml build omb
docker compose -f Lab05/docker-compose.yml pull kafka rabbitmq
```

Executar o piloto completo:

```powershell
python Lab05/coletar.py --piloto
```

São 24 tentativas: 2 experimentos × 2 brokers × 2 tamanhos × 3 repetições. E1 usa taxa
máxima. Para cada tamanho, E2 usa 50% do menor throughput mediano observado entre os dois
brokers em E1. Cada tentativa recria containers e volumes, descarta o aquecimento e grava
resultado, recursos, metadados e logs, inclusive quando falha.

## Estabilização do E1 — portão G1 (#209)

Responsável: Diogo. Relatórios do portão em `data/analise/g1_*.json`, gerados por
`python Lab05/portao_g1.py <resultados.csv> [<repetições.csv>]`.

**Critério (definido antes, em `planejamento_s02.md`):** em cada célula do E1, CV do throughput
entre execuções ≤ 20%; nenhuma execução com colapso (intervalo de 10 s abaixo de 10% do maior
intervalo da própria execução); nenhuma execução abaixo de 10% da mediana da célula; pelo menos
3 sucessos por célula.

### Diagnóstico

O piloto de 19/11 (`data/piloto/20261119T030115.153119Z`) reprovou nas 4 células, com CV de
52% a 128%. Pelos JSON brutos do OMB, as execuções do Kafka publicavam dezenas de milhares de
msg/s e, depois de um pico de latência de publicação (13,6 s no `E1-kafka-1k-r02`), caíam para
cerca de 1 msg/s até o fim da medição.

**Causa:** `producerRate: 0` no workload. Na revisão do OMB usada
(`5b1fa70951a323da26bd587174b58bb2c65b0b5c`), esse valor liga `findMaximumSustainableRate`,
que roda durante **toda** a medição e chama o `RateController` a cada 3 s. Quando o atraso
passa de 1.000 mensagens, a nova taxa é `min(taxa real, esperado − atraso)`, que vai a quase
zero depois de um único pico, e o fator de rampa cai para 1%. O E1 media a dinâmica do
controlador, não o broker. Isso é uma ameaça de **construto**, não só de variância.

### Correções aplicadas (uma de cada vez)

| # | Correção | Arquivo |
| --- | --- | --- |
| 1 | E1 com taxa-alvo **fixa e inalcançável** (`TAXA_E1_ABERTA = 1.000.000` msg/s): sem controlador adaptativo; o limite vem da contrapressão do broker | `experimento/plano.py`, `experimento/coleta.py` |
| 2 | Métricas de estabilidade por execução (`cv_intervalos`, `intervalo_min_rel`, `colapso`) e `throughput_consumo_msg_s` | `experimento/coleta.py` |
| 3 | Patch e arquivos do OMB forçados a LF (`.gitattributes`): com `core.autocrlf=true`, o `git apply` do build falhava com "corrupt patch" | `.gitattributes` |
| 4 | Healthcheck do RabbitMQ: `check_port_connectivity` no lugar de `ping`, que responde antes de o listener AMQP abrir (causa das duas falhas de `E1-rabbitmq-1k-r02`) | `docker-compose.yml` |
| 5 | O coletor impede a suspensão do Windows durante a coleta (`SetThreadExecutionState`) | `experimento/coleta.py`, `coletar.py` |
| 6 | Modo `--repetir-falhas`: repete a execução inteira numa coleta nova ligada à original (`origem.json`), sem sobrescrever | `coletar.py` |
| 7 | Mini-pilotos do G1 gravados em `data/piloto_g1/`, para não serem lidos como piloto completo pelo `analisar.py` | `coletar.py` |

### Ciclos do mini-piloto (5 execuções por célula, só E1)

Máquina dos ciclos: Windows 11 Home, 16 processadores lógicos, Docker Desktop 28.4.0 com
7,6 GiB para a VM. **Não é a máquina do piloto de 19/11** (ver "Ambiente de referência"). A
coleta oficial precisa rodar inteira numa única máquina.

| Célula E1 | Piloto 19/11 (`producerRate: 0`, 60 s) | Ciclo 1 (taxa aberta, 60 s) | Ciclo 2 (taxa aberta, 120 s) |
| --- | --- | --- | --- |
| Kafka 1 KiB | 22.381 msg/s · CV 128% · 2 colapsos | 129.146 msg/s · CV **16%** | 125.147 msg/s · CV **20,3%** |
| Kafka 16 KiB | 2.129 msg/s · CV 98% · 2 colapsos | 8.509 msg/s · CV **27%** | 7.508 msg/s · CV **30%** |
| RabbitMQ 1 KiB | 12.572 msg/s · n = 2 | 8.913 msg/s · CV **15%** (n = 4) | 8.665 msg/s · CV **4%** |
| RabbitMQ 16 KiB | 2.701 msg/s · CV 52% | 4.284 msg/s · CV **20,4%** | 3.411 msg/s · CV **11%** |
| **Portão G1** | reprovado (4/4) | reprovado (2/4) | **reprovado (2/4, só Kafka)** |

Coletas: ciclo 1 em `data/piloto_g1/20261125T024110.282507Z` (1 falha de partida do RabbitMQ,
antes da correção 4); ciclo 2 em `data/piloto_g1/20261125T032412.920068Z`, mais as repetições
em `data/piloto_g1/20261125T105810.056929Z`. No ciclo 2, a máquina **suspendeu** durante a
execução 12. As execuções 12 a 14 falharam com timeout negativo (salto de relógio), foram
preservadas como falha e repetidas com sucesso (correções 5 e 6).

### O que resta e interpretação

- **Nenhum colapso** em nenhuma execução depois da correção 1. O problema do piloto está
  resolvido.
- O controlador do OMB **escondia** cerca de 6× do throughput do Kafka 1 KiB (22 mil → cerca
  de 125 mil msg/s).
- **RabbitMQ estável** com 120 s (CV de 4% e 11%).
- O **Kafka** continua oscilando dentro de cada execução (CV entre intervalos de 20% a 43%) e
  entre execuções. Dobrar a medição não reduziu o CV (16% → 20%; 27% → 30%), então não é ruído
  que se resolve medindo mais. A CPU do broker fica em 90–150% de um teto de 400%, ou seja, o
  Kafka **não está limitado por CPU**. As hipóteses que sobram são I/O de disco (cerca de
  178 MB/s no 16 KiB, sobre o disco virtual do WSL2 e a *page cache* da VM) e o cliente OMB
  (limitado a 2 vCPU) como teto no 1 KiB. A medição está *correta* (sem artefato do
  controlador); o que varia é o ambiente sob o Kafka.

### Poder com o CV observado (Mann-Whitney, α = 0,0125, Holm)

| CV | razão 1,2 | razão 1,5 | razão 2,0 |
| --- | --- | --- | --- |
| 20% | n = 20: 60% | n = 10: 93% | n = 5: 88% |
| 30% | n = 20: 27% | n = 15: 84% | n = 10: 98% |

As razões Kafka/RabbitMQ observadas no E1 são cerca de **14×** (1 KiB) e cerca de **2,2×**
(16 KiB). Com CV de 30%, **n = 10–15 por célula** detecta razões a partir de 1,5–2,0 com
poder ≥ 84%, mas não detecta diferenças de 20%.

### Decisão final da #207 (desvio do G1)

O critério de 20% **não foi alterado** depois de ver os dados. O protocolo mantém E1 com taxa
aberta e 120 s, aceita a reprovação do G1 nas células Kafka como limitação e fixa **n = 20**,
o teto previsto. No pior caso observado (Kafka 16 KiB, CV 30,34%), n=20 fornece somente cerca
de 24–25% de poder para razão 1,20; não se afirma que o alvo de 80% foi alcançado. A decisão e
a ausência de CV estabilizado do p99 estão detalhadas em `metodo.md`, seção 2.4.

## Pré-registro da coleta oficial — portão G2 (#207)

A fonte estruturada do protocolo é `data/plano/protocolo_oficial.json`. Ela congela n,
sementes, blocos, durações, tolerâncias de integridade e fingerprints de imagens. Os CSVs
`plano_E1.csv` e `plano_E2.csv` são as listas executáveis.

| Imagem | Fingerprint congelado |
| --- | --- |
| `apache/kafka:4.4.0` | `apache/kafka@sha256:833b867a9585a141da455dc2b57431c65cbccb27f11c91f694444cca9f777e0f` |
| `rabbitmq:4.4.1-management` | `rabbitmq@sha256:61f90c401a5b5ed2486771973ea92ad66046471eacab9c9149f1a6e091c91677` |
| `lab05/openmessaging-benchmark:5b1fa709-ts-ms` | `sha256:b8475ccc9922bc4f60049271e2d1de9b3bccbb3622f13aaac593e12339999fd6` |

### Ordem e blocos

1. Executar `E1-B1` e `E1-B2`, nessa ordem, com 40 IDs por bloco e 120 s medidos.
2. Validar todos os 80 IDs de E1 e calcular, por tamanho, 50% do menor throughput mediano
   entre os brokers. Congelar essas duas taxas no manifesto oficial.
3. Executar `E2-B1` e `E2-B2`, nessa ordem, com 40 IDs por bloco e 60 s medidos.

Cada bloco contém exatamente 10 execuções de cada combinação broker × tamanho. A ordem
global e a posição dentro do bloco não podem ser alteradas durante a coleta.

### Comandos da coleta oficial

Criar a raiz da coleta, sem executar medições:

```powershell
python Lab05/coletar.py --oficial --iniciar
```

Executar cada bloco na ordem pré-registrada, sempre informando o caminho impresso pelo
comando anterior e declarando o desvio explicitamente:

```powershell
python Lab05/coletar.py --oficial --coleta Lab05/data/oficial/<coleta> --bloco E1-B1 --desvio "nenhum"
python Lab05/coletar.py --oficial --coleta Lab05/data/oficial/<coleta> --bloco E1-B2 --desvio "nenhum"
python Lab05/validar.py Lab05/data/oficial/<coleta> --fase E1
python Lab05/coletar.py --oficial --coleta Lab05/data/oficial/<coleta> --bloco E2-B1 --desvio "nenhum"
python Lab05/coletar.py --oficial --coleta Lab05/data/oficial/<coleta> --bloco E2-B2 --desvio "nenhum"
python Lab05/validar.py Lab05/data/oficial/<coleta>
```

Se um bloco terminar com falha técnica, repetir somente os IDs ainda sem sucesso:

```powershell
python Lab05/coletar.py --oficial --coleta Lab05/data/oficial/<coleta> --bloco E1-B1 --desvio "repetição de falha técnica registrada" --repetir-falhas-oficial
```

O coletor recusa blocos fora de ordem, mudança de máquina ou imagem e E2 antes de todos os
80 IDs de E1 terem sucesso. Uma interrupção pode ser retomada repetindo o comando do bloco;
IDs já tentados não são executados novamente sem `--repetir-falhas-oficial`.

### Falhas, repetições, exclusões e outliers

- Falha técnica é erro de inicialização, timeout, código de saída não zero, interrupção, bruto
  ausente ou bruto inválido. A causa deve constar no resultado e no manifesto.
- Somente IDs sem tentativa bem-sucedida são repetidos. A execução inteira volta na mesma
  posição lógica (`bloco`, `ordem`, `ordem_no_bloco`), com novo número de tentativa e novos
  arquivos. Tentativas anteriores nunca são apagadas ou sobrescritas.
- Somente tentativas com falha técnica registrada são excluídas das métricas. Mais de um
  sucesso para o mesmo ID reprova a validação.
- Valores extremos tecnicamente válidos são preservados e reportados; “valor estranho” não é
  critério de exclusão nem de repetição.

### Registro obrigatório por bloco

O início e o fim, a identificação da máquina, o plano de energia/estado AC, a temperatura
quando disponível e qualquer desvio devem ser registrados. A execução futura acrescentará
uma linha por bloco nesta seção; declarar explicitamente `nenhum` quando não houver desvio.

| Coleta | Bloco | Início/fim (America/Sao_Paulo) | Máquina | Energia/temperatura | Desvio |
| --- | --- | --- | --- | --- | --- |
