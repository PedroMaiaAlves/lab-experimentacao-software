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
  publicador e confirmação manual do consumidor pelo driver.

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
de medição.

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
