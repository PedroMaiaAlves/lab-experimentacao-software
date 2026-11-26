# Lab05 — Kafka × RabbitMQ: throughput e latência em produção simulada

Experimento controlado que compara dois *message brokers* em operação real, ambos
nas versões mantidas e rodando no ambiente do grupo (Docker, nó único):

- **Apache Kafka 4.4.0**, em modo KRaft;
- **RabbitMQ 4.4.1**, com *quorum queue*.

**Pergunta de pesquisa:** com a mesma garantia de durabilidade e o mesmo hardware, qual
broker entrega mais mensagens por segundo e qual tem menor latência de cauda (p99)? Essa
diferença depende do tamanho da mensagem?

| Documento | Conteúdo | Responsável |
| --- | --- | --- |
| [docs/proposta.md](docs/proposta.md) | Critérios do software, GQM, 7 categorias, hipóteses, design, ameaças e plano de análise | Diogo |
| [docs/metodo.md](docs/metodo.md), `planejar.py`, `experimento/`, `data/plano/` | 7 categorias, design 2×2 randomizado, poder a priori e ameaças (#197) | Diogo |
| [docs/issues_s01.md](docs/issues_s01.md) | Divisão de tarefas e issues da S01 | Diogo |
| `docs/protocolo_coleta.md`, `coletar.py`, `validar.py`, `data/piloto/` | Ambiente, piloto e coleta oficial validada | Pedro |
| `analisar.py`, `docs/plano_analise.md`, `docs/impacto.md` | Descritiva, testes, efeito e impacto | Lorran |

## Divisão (papéis da seção 6 do enunciado)

| Papel | Integrante | GitHub |
| --- | --- | --- |
| A — Planejamento e Método | Diogo | `DiogoBrunoro` |
| B — Instrumentação e Operação | Pedro Maia | `PedroMaiaAlves` |
| C — Análise e Impacto | Lorran | `LorranX` |

Ética: toda a carga roda localmente, em containers do próprio grupo. Não há teste de carga
em sistema de terceiros nem coleta de dados pessoais.
