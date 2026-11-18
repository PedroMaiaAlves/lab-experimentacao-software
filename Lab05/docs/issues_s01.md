# Issues da Lab05S01 — cadastradas (#196–#201)

**Diogo:** `DiogoBrunoro` · **Pedro:** `PedroMaiaAlves` · **Lorran:** `LorranX`.

Configuração comum: milestone `Lab05S01`; labels `lab05` e `sprint-01`. O fluxo é
`Backlog → Ready → In Progress → In Review → Done`, com no máximo uma issue em andamento por
pessoa. D1/P1/L1… são códigos deste documento. Depois do cadastro, use os números reais
(`#NUMERO`) nos commits e nas PRs.

## D1 (#196) — [Lab05S01][Diogo] Proposta: software, critérios, GQM e hipóteses
**Assignee:** `DiogoBrunoro` · **Dependências:** nenhuma.
- [x] Evidências dos três critérios com fonte e data (seção 1 de `proposta.md`).
- [x] Pergunta de pesquisa, caminho e GQM (objetivo de Basili, perguntas, métricas, entidade, atributo e escala).
- [x] Hipóteses bicaudais e expectativa registrada antes da coleta.
- [ ] Revisão por outro integrante.

## D2 (#197) — [Lab05S01][Diogo] 7 categorias, design do experimento e ameaças à validade
**Assignee:** `DiogoBrunoro` · **Dependências:** D1.
- [x] Primeira versão das 7 categorias, com justificativa.
- [x] Variáveis, design fatorial 2×2 e randomização com semente 42.
- [x] Ameaças à validade dos 4 tipos, com mitigação.
- [ ] Ajustar o tamanho amostral depois do piloto (P2 e L2).

## P1 (#198) — [Lab05S01][Pedro] Ambiente Docker reproduzível para Kafka e RabbitMQ
**Assignee:** `PedroMaiaAlves` · **Dependências:** D1.
- [ ] `docker-compose.yml` com Kafka 4.4.0 (KRaft) e RabbitMQ 4.4.1, nas versões e com os limites da proposta (4 vCPU, 4 GiB).
- [ ] Durabilidade equalizada (`acks=all` / *publisher confirms* + *quorum queue*).
- [ ] Escolha da ferramenta de carga (OpenMessaging Benchmark ou nativas), com justificativa.
- [ ] `docs/protocolo_coleta.md` com ambiente (CPU, RAM, SO, versão do Docker) e comandos.

## P2 (#199) — [Lab05S01][Pedro] Coletor e coleta piloto
**Assignee:** `PedroMaiaAlves` · **Dependências:** P1.
- [ ] `coletar.py`: ordem aleatória (semente 42), containers recriados por execução, aquecimento descartado e saída CSV/JSON com metadados.
- [ ] Piloto com 3 execuções por célula (E1 e E2) em `data/piloto/`, sem sobrescrever.
- [ ] Falhas preservadas e registradas; testes do coletor.

## L1 (#200) — [Lab05S01][Lorran] Plano de análise e esqueleto do analisador
**Assignee:** `LorranX` · **Dependências:** D1.
- [ ] `docs/plano_analise.md`: descritiva, critério Welch/Mann-Whitney, ANOVA ou permutação para a interação, Holm, razão geométrica com bootstrap e δ de Cliff.
- [ ] `analisar.py` lendo o formato de saída de P2, com testes.

## L2 (#201) — [Lab05S01][Lorran] Análise do piloto, poder e primeira estimativa de impacto
**Assignee:** `LorranX` · **Dependências:** P2 e L1.
- [ ] Descritiva do piloto e variância por célula.
- [ ] Simulação de poder (reaproveitando o Lab04) para confirmar ou ajustar as 10 execuções por célula.
- [ ] `docs/impacto.md`: fontes públicas (Docker Hub, Fortune 100) e o método de conversão para CPU-hora.
