# Planejamento — Lab05S02

**Entrega da sprint (enunciado):** coleta completa, dados validados e versionados, análise
(descritiva, testes e tamanho do efeito) e ameaças à validade.

## 1. Ponto de partida: o que o piloto mostrou

Piloto: `data/piloto/20261119T030115.153119Z/` (24 tentativas, 23 com sucesso, 1 falha), com
resumo em `data/analise/piloto_resumo.json`.

| Célula | Throughput mediano | CV do throughput | p99 mediano | CV do p99 |
| --- | ---: | ---: | ---: | ---: |
| E1 Kafka 1 KiB | 22.381 msg/s | **128%** | 2.285 ms | 130% |
| E1 RabbitMQ 1 KiB | 12.572 msg/s (n = 2) | 2% | 2.192 ms | 10% |
| E1 Kafka 16 KiB | 2.129 msg/s | **98%** | 4.759 ms | 92% |
| E1 RabbitMQ 16 KiB | 2.701 msg/s | **52%** | 1.659 ms | 23% |
| E2 Kafka 1 KiB | 6.320 msg/s (taxa fixa) | 0% | 8 ms | 24% |
| E2 RabbitMQ 1 KiB | 6.315 msg/s (taxa fixa) | 7% | **2.657 ms** | 48% |
| E2 Kafka 16 KiB | 1.069 msg/s (taxa fixa) | 0% | 3 ms | 118% |
| E2 RabbitMQ 16 KiB | 1.070 msg/s (taxa fixa) | 0% | 995 ms | 0% |

**O que isso significa para a sprint:**

1. **O E1 não está estável.** A regra de revisão da #197 (`metodo.md`, seção 2.4) previa CV
   de até 10%, com teto de 20 execuções por célula. Com CV entre 50% e 130%, nem 20 execuções
   dão poder suficiente, e a variância indica problema de instrumentação, não do broker. Por
   exemplo, a média geométrica do Kafka 1 KiB (1.434 msg/s) está muito abaixo da mediana
   (22.381 msg/s), o que sugere uma execução quase parada.
2. **O E2 está estável na taxa**, porque a taxa é imposta. Mesmo assim, o p99 do RabbitMQ
   (cerca de 1 a 2,6 s a 50% da carga) precisa ser explicado: pode ser fila acumulada, efeito
   do *publisher confirm* em lote ou a configuração do consumidor. Isso é uma ameaça de
   construto.
3. **A direção dos efeitos já aparece** (Kafka cerca de 1,8× em 1 KiB; RabbitMQ cerca de 1,3×
   em 16 KiB; p99 do E2 de 2 a 3 ordens de grandeza menor no Kafka), mas são números de
   piloto, sem inferência.

Por isso a sprint é organizada em **portões**: a coleta completa só começa quando o E1
estiver estável. Isso evita gastar horas de coleta em dados que não servem para o teste.

## 2. Fases e portões

```
Fase 0 ─ Estabilizar E1 (Diogo, #209) ── Portão G1: CV ≤ 20% em mini-piloto de 5 execuções/célula
   │
Fase 1 ─ Protocolo final e pré-registro do n (Pedro, #207) ── Portão G2: n e regras congelados no main
   │      (em paralelo: Lorran prepara análise e gráficos sobre o piloto, L3/L4)
Fase 2 ─ Coleta completa + validação + versionamento (Pedro, P4)  ── Portão G3: validar.py sem erros
   │
Fase 3 ─ Análise completa (Lorran, L3/L4) + ameaças revisadas com evidência (Diogo, D4)
```

| Portão | Critério objetivo | Se falhar |
| --- | --- | --- |
| **G1** | No mini-piloto do E1 (5 execuções por célula), CV do throughput ≤ 20% em todas as células e nenhuma execução com throughput < 10% da mediana da célula | Investigar mais um ciclo. Se não resolver até a metade da sprint, aplicar o plano B (seção 5) |
| **G2** | `metodo.md` atualizado com n final, critérios de exclusão e de repetição, e commit no `main` **antes** do primeiro dado oficial | Nenhuma coleta oficial começa |
| **G3** | `validar.py` aprovado: todas as células com n válido, sem duplicatas, hashes conferidos e falhas registradas | Repetir só as execuções faltantes, na ordem do plano |

## 3. Issues da sprint

Milestone `Lab05S02`; labels `lab05` e `sprint-02`. O fluxo e o limite de uma issue em
andamento por pessoa continuam como na S01.

### P3 (#207) — [Lab05S02][Pedro] Protocolo final: n revisado, regras de exclusão e pré-registro
**Depende de:** #209 (portão G1).
- [ ] Rodar `experimento/poder.py` com o CV do mini-piloto estabilizado (troca o CV suposto pelo observado), para throughput e p99.
- [ ] Fixar o n por célula (alvo: 80% de poder para razão 1,20 com Holm; teto de 20) e registrar a justificativa em `metodo.md`, seção 2.4.
- [ ] Definir as regras antes da coleta: o que é falha, quando repetir (a execução inteira, na mesma posição do plano), critério de exclusão (só falha técnica registrada, nunca "valor estranho") e tratamento de outliers (reportar, não remover).
- [ ] Regenerar `data/plano/plano_E1.csv` e `plano_E2.csv` com o n final (`planejar.py`) e separar em **blocos** (sessões de coleta), com o bloco registrado como variável.
- [ ] Commit no `main` antes do primeiro dado oficial (portão G2).

### D4 (#208) — [Lab05S02][Diogo] Ameaças à validade revisadas com evidência e revisão do método
**Depende de:** P4 e L3.
- [ ] Revisar a tabela de ameaças de `metodo.md` com o que aconteceu de fato: variância do piloto e causa encontrada, falhas da coleta, efeito de bloco e de ordem (tendência do throughput pela posição) e o p99 alto do RabbitMQ no E2.
- [ ] Para cada ameaça: evidência observada, mitigação aplicada e risco residual.
- [ ] Revisar as 7 categorias e o GQM diante do que foi coletado (por exemplo, se a latência do E2 mede o que diz medir).
- [ ] Revisar o código de análise (PR de L3) contra as hipóteses H1–H3 pré-registradas, sem análise nova escolhida depois de ver os dados.

### D3 (#209) — [Lab05S02][Diogo] Estabilizar a medição do E1 (portão G1)
**Depende de:** nada; é a primeira tarefa da sprint.
- [ ] Diagnosticar a variância do E1 com os logs do piloto: execuções quase paradas, *rate limiter* adaptativo do OMB (`producerRate` máximo), aquecimento curto para a JVM do Kafka, disco (volume no OneDrive/WSL2 versus volume Docker nativo), *throttling* térmico e energia.
- [ ] Testar as correções uma de cada vez, registrando o resultado de cada tentativa em `protocolo_coleta.md`. Candidatas: aquecimento maior, taxa máxima fixa alta em vez de adaptativa, volume Docker fora do OneDrive, intervalo de resfriamento entre execuções.
- [ ] Investigar a falha do `E1-rabbitmq-1k-r02` e o p99 de cerca de 2,6 s do RabbitMQ no E2.
- [ ] Mini-piloto do E1 com 5 execuções por célula em `data/piloto/` (sem sobrescrever) e CV por célula enviado ao Pedro (#207).

### P4 (#210) — [Lab05S02][Pedro] Coleta completa, validação e versionamento (portão G3)
**Depende de:** #207 (portão G2).
- [ ] Rodar o plano oficial (E1 e depois E2, com a taxa do E2 calculada a partir do E1 oficial) em `data/oficial/<coleta>/`, na ordem do plano e por blocos.
- [ ] Criar `validar.py`: n por célula, IDs únicos e iguais aos do plano, status, faixas plausíveis, hashes SHA-256 de `resultados.csv` e dos brutos gravados no manifesto, e digest das imagens igual ao do protocolo.
- [ ] Repetir só as execuções que falharam, conforme a regra de D3. Todas as tentativas ficam preservadas.
- [ ] Registrar no `protocolo_coleta.md` o horário dos blocos, a máquina, a temperatura ou energia e qualquer desvio do protocolo.

### L3 (#211) — [Lab05S02][Lorran] Análise estatística completa
**Depende de:** P4 (portão G3). O código pode ser preparado antes, sobre o piloto.
- [ ] Descritiva por célula: mediana, IQR, média geométrica, CV e n válido.
- [ ] H1 e H2 em cada tamanho: Welch sobre log, ou Mann-Whitney se a normalidade do log falhar (critério do `plano_analise.md`), com correção de Holm.
- [ ] H3 (interação broker × tamanho): ANOVA sobre o log ou teste de permutação.
- [ ] Tamanho do efeito: razão geométrica com IC de 95% por bootstrap (semente 42) e δ de Cliff.
- [ ] Checagens: efeito de ordem e de bloco (regressão do log da métrica na posição) e sensibilidade com e sem execuções repetidas.
- [ ] Resultados em `data/analise/oficial_resumo.json` e `docs/resultados.md`, com testes do analisador.

### L4 (#212) — [Lab05S02][Lorran] Visualizações e base do dashboard
**Depende de:** L3. Pode começar com o piloto.
- [ ] Gráficos: boxplots com pontos por célula (throughput e p99), *forest plot* das razões geométricas com IC e gráfico de interação (tamanho × broker).
- [ ] Gráfico de throughput pela ordem de execução, para mostrar o efeito de ordem (alimenta D4).
- [ ] Esqueleto do dashboard Streamlit reaproveitando o Lab04 (seções: cenário, dados, testes e efeito), deixando o impacto para a S03.

## 4. Sequência e esforço estimado

| Ordem | Issue | Duração estimada | Observação |
| --- | --- | --- | --- |
| 1 | #209 (Diogo) | 2 a 3 sessões | Cada mini-piloto do E1 com 5 × 4 execuções leva cerca de 40 min |
| 1 (paralelo) | L3/L4 sobre o piloto | — | Código pronto antes dos dados oficiais |
| 2 | #207 (Pedro) | 1 sessão | Bloqueia a coleta |
| 3 | P4 | 2 noites | Com n = 20: 160 execuções × cerca de 2 min ≈ 5,5 h, em 2 blocos |
| 4 | L3/L4 com dados oficiais | 1 a 2 sessões | — |
| 4 (paralelo) | D4 | 1 sessão | Revisa a PR de L3 |

## 5. Riscos da sprint e plano B

| Risco | Plano B |
| --- | --- |
| O E1 não estabiliza (G1 falha) | Trocar o E1 por **throughput a taxas fixas crescentes** (por exemplo, 25%, 50%, 75% e 100% da capacidade estimada), medindo a taxa sustentada e a latência em cada degrau. A taxa imposta já se mostrou estável no E2. Diogo atualiza o design em `metodo.md` antes da coleta. |
| A coleta não cabe no tempo | Reduzir n até o mínimo que ainda dá 80% de poder para razão 1,50 e declarar isso como limitação de conclusão. |
| Coleta em dias diferentes cria efeito de dia | Blocos registrados, com a ordem aleatória já espalhando as células entre os blocos. L3 testa o efeito de bloco. |
| Atualização do Docker ou de imagem no meio da coleta | Fixar digests no compose; `validar.py` recusa digest diferente. |
