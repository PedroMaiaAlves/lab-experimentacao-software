# Plano de Análise, Piloto e Simulação de Poder — Lab05S01 (Papel C: Lorran)

Este documento fecha os requisitos das issues **#200** (plano de análise e analisador) e **#201**
(análise descritiva do piloto e revisão de poder). Todos os cálculos são reproduzidos por:

```powershell
python Lab05/analisar.py --saida Lab05/data/analise/piloto_resumo.json
```

---

## 1. Plano de análise estatística (#200)

Todas as métricas principais (M1 throughput, M2 latência p50/p99 e M4 CPU/memória) estão em
**escala de razão** e são estritamente positivas. Como cada execução começa com containers e
volumes recriados em ordem randomizada, as amostras entre células são tratadas como
**independentes** (*between-runs*).

### 1.1 Tratamento de falhas e limpeza
- O analisador lê o `resultados.csv` gerado por `coletar.py` (P2).
- Apenas linhas com `status == "sucesso"` entram nos cálculos estatísticos.
- Execuções com `status` `falha`, `bloqueada` ou `interrompida` são contabilizadas em
  `contagens_status` e **nunca** convertidas em zero.
- Valores ausentes permanecem nulos (`None`), sem imputação e sem remoção manual de outliers.

### 1.2 Estatística descritiva
Para cada célula `(experimento, broker, tamanho_bytes)` e métrica (M1, M2 e M4):
- **Posição e dispersão robusta:** mediana, Q1, Q3 e IQR (`Q3 − Q1`).
- **Escala multiplicativa:** média geométrica ($\exp(\overline{\ln Y})$), variância e desvio
  padrão em escala logarítmica ($\sigma_{\log}$).
- **Variabilidade relativa:** desvio padrão amostral (`ddof=1`) e coeficiente de variação
  ($\text{CV} = s / \bar{y}$), usados na revisão do poder.
- **Visualização prevista (S02/S03):** boxplots com todos os pontos individuais por célula e
  gráficos de interação entre 1 KiB e 16 KiB.

### 1.3 Comparações principais (H1 e H2) e critério de escolha do teste
As quatro comparações principais (bicaudais, $\alpha = 0{,}05$) comparam **Kafka × RabbitMQ**
separadamente por tamanho de mensagem:
1. `E1` — `throughput_msg_s` em 1 KiB (H1)
2. `E1` — `throughput_msg_s` em 16 KiB (H1)
3. `E2` — `latencia_p99_ms` em 1 KiB (H2)
4. `E2` — `latencia_p99_ms` em 16 KiB (H2)

**Critério Welch vs. Mann-Whitney:**
- Aplicamos Shapiro-Wilk sobre $\ln(Y)$ em cada um dos dois brokers da célula.
- Se ambos os grupos tiverem $n \ge 3$ e $p_{\text{Shapiro}} \ge 0{,}05$, o teste primário é o
  **t de Welch sobre $\ln(Y)$** (equivalente a testar $\ln r = 0$ sem assumir variâncias iguais).
- Caso contrário (não normalidade em log ou $n < 3$), o teste primário é o **Mann-Whitney U**
  bicaudal (exato quando não há empates; assintótico caso contrário).
- Por transparência (e porque Shapiro tem baixo poder com $n$ pequeno), `analisar.py` reporta
  **ambos os testes** em todas as células.

### 1.4 Interação broker × tamanho da mensagem (H3)
Para testar se a razão Kafka/RabbitMQ muda entre 1 KiB e 16 KiB, definimos o contraste em escala
logarítmica:

$$\hat{\theta} = (\overline{\ln Y}_{K,16k} - \overline{\ln Y}_{R,16k}) - (\overline{\ln Y}_{K,1k} - \overline{\ln Y}_{R,1k}), \qquad \text{razão das razões} = e^{\hat{\theta}}$$

O analisador reporta dois testes complementares sobre $\ln(Y)$:
- **ANOVA fatorial 2×2 (Soma de Quadrados Tipo III via OLS/QR):** funciona inclusive com células
  desbalanceadas (como no piloto).
- **Teste de permutação de Freedman-Lane (5.000 permutações, semente 42):** ajusta o modelo
  aditivo sem interação, permuta os resíduos e recalcula a estatística $F$ da interação. Evita o
  erro de permutação ingênua, que inflaria o erro tipo I diante de efeitos principais grandes.

### 1.5 Correção para múltiplas comparações (Holm)
Aplicamos **Holm-Bonferroni** sobre a família das 4 comparações principais (H1 e H2 em 1 KiB e
16 KiB), com $\alpha = 0{,}05$, gerando p-valores ajustados para o teste recomendado, para Welch
e para Mann-Whitney. Os dois testes de interação (H3) são reportados à parte.

### 1.6 Tamanho do efeito
Para cada comparação principal reportamos duas medidas complementares:
- **Razão das médias geométricas** ($r = \exp(\overline{\ln Y}_K - \overline{\ln Y}_R)$) com
  **IC 95% por bootstrap percentil** (5.000 reamostragens independentes por grupo, semente 42).
- **$\delta$ de Cliff** (não paramétrico, invariante a transformações monótonas), classificado
  pelas faixas de Romano et al.: desprezível ($|\delta| < 0{,}147$), pequeno ($< 0{,}33$),
  médio ($< 0{,}474$) e grande ($\ge 0{,}474$).

---

## 2. Descritiva do piloto e variância por célula (#201)

A coleta piloto oficial concluída é `data/piloto/20261119T030115.153119Z/resultados.csv`
(4 tentativas anteriores interrompidas foram preservadas em `data/piloto/` como evidência).
Das **24 execuções planejadas**, **23 terminaram com sucesso** e **1 falhou**
(`E1-rabbitmq-1k-r02`, erro de inicialização no `docker compose up --wait`). As taxas fixas
calculadas automaticamente para o E2 foram **6.285 msg/s** (1 KiB) e **1.064 msg/s** (16 KiB).

### 2.1 Métricas principais por célula (M1 em E1; M2 em E2)

| Exp | Métrica | Broker | Tam | n | Mediana | IQR | Média geom. | CV | $\sigma_{\log}$ |
| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| E1 | throughput (msg/s) | Kafka | 1 KiB | 3 | 22.380,60 | 49.453,15 | 1.433,52 | 128,3% | 6,092 |
| E1 | throughput (msg/s) | RabbitMQ | 1 KiB | 2 | 12.571,68 | 166,47 | 12.570,58 | 1,9% | 0,019 |
| E1 | throughput (msg/s) | Kafka | 16 KiB | 3 | 2.129,33 | 2.073,23 | 673,72 | 98,0% | 2,599 |
| E1 | throughput (msg/s) | RabbitMQ | 16 KiB | 3 | 2.700,48 | 1.250,81 | 2.181,12 | 51,8% | 0,629 |
| E2 | latência p99 (ms) | Kafka | 1 KiB | 3 | 8,00 | 2,00 | 8,51 | 24,0% | 0,232 |
| E2 | latência p99 (ms) | RabbitMQ | 1 KiB | 3 | 2.657,01 | 1.039,01 | 2.051,82 | 48,0% | 0,592 |
| E2 | latência p99 (ms) | Kafka | 16 KiB | 3 | 3,00 | 9,50 | 5,83 | 117,5% | 1,150 |
| E2 | latência p99 (ms) | RabbitMQ | 16 KiB | 3 | 995,00 | 2,00 | 995,67 | 0,2% | 0,002 |

### 2.2 Recursos por célula (M4 — medianas)

| Exp | Broker | 1 KiB — CPU (%) | 1 KiB — RAM (MiB) | 16 KiB — CPU (%) | 16 KiB — RAM (MiB) |
| --- | --- | ---: | ---: | ---: | ---: |
| E1 | Kafka | 126,56 | 3.290,33 | 191,62 | 3.309,15 |
| E1 | RabbitMQ | 243,61 | 195,47 | 182,19 | 210,99 |
| E2 | Kafka | 165,29 | 1.001,70 | 121,15 | 1.115,56 |
| E2 | RabbitMQ | 170,37 | 176,35 | 105,18 | 176,66 |

### 2.3 Diagnóstico do piloto (não é conclusão final)
1. **Estabilidade operacional em E1 (alerta crítico para S02):** duas execuções do Kafka em
   saturação travaram com throughput quase nulo (`E1-kafka-1k-r02` = `1,33 msg/s` e
   `E1-kafka-16k-r02` = `34,35 msg/s` após pausa de ~15 s registrada no JSON bruto). Sem esses
   travamentos, o Kafka alcançou `22.381`–`98.908 msg/s` (1 KiB) e `2.129`–`4.181 msg/s` (16 KiB).
   O fenômeno explica o CV acima de 98% e precisa ser investigado na instrumentação (ex.:
   pressão de memória JVM perto do limite de 4 GiB, onde a RAM do Kafka ficou em ~3,3–3,4 GiB)
   antes da coleta completa.
2. **Latência em E2:** sob taxa fixa, o Kafka apresentou latência p99 duas ordens de grandeza
   menor que o RabbitMQ (`8 ms` vs. `2.657 ms` em 1 KiB; `3 ms` vs. `995 ms` em 16 KiB;
   $\delta = -1{,}00$ nos dois tamanhos). Esse padrão contraria parcialmente nossa expectativa
   informal inicial (que supunha RabbitMQ competitivo em latência sob carga moderada), mas
   aguarda a coleta completa com $n$ adequado para inferência confirmatória.
3. **Uso de memória:** o Kafka consumiu de ~6× (E2) a ~16× (E1) mais RAM que o RabbitMQ.

---

## 3. Simulação de poder sobre o piloto e decisão de *n* (#201)

Seguindo exatamente a regra de revisão de `docs/metodo.md` (seção 2.4), rodamos a função
`experimento.poder.poder` (2.000 repetições, semente 42, nível conservador de Holm
$\alpha/4 = 0{,}0125$) usando o **maior CV observado** em cada par de comparação do piloto:

| Comparação | CV máx. piloto | Razão 1,20 (n=10 / 15 / 20) | Razão 1,50 (n=10 / 15 / 20) | Razão 2,00 (n=10 / 15 / 20) |
| --- | ---: | :---: | :---: | :---: |
| E1 throughput 1 KiB | 128,3% | 2,1% / 2,4% / 2,9% | 5,4% / 8,3% / 11,0% | 14,9% / 26,0% / 36,3% |
| E1 throughput 16 KiB | 98,0% | 1,9% / 3,1% / 3,1% | 6,7% / 10,9% / 15,6% | 19,9% / 38,2% / 51,8% |
| E2 latência p99 1 KiB | 48,0% | 4,1% / 7,4% / 9,4% | 23,5% / 41,8% / 57,8% | 72,7% / 91,2% / 98,3% |
| E2 latência p99 16 KiB | 117,5% | 1,8% / 2,7% / 3,6% | 5,9% / 8,9% / 11,6% | 15,1% / 29,3% / 40,7% |

*(Valores reportados para Welch sobre log; Mann-Whitney ficou entre 0 e 3 p.p. abaixo em todos os
cenários — detalhes completos em `data/analise/piloto_resumo.json`.)*

### Recomendação de tamanho amostral para a coleta completa (S02)
- **Pela regra de `docs/metodo.md`:** como o CV excedeu 10% nas quatro comparações principais e
  nenhuma atinge 80% de poder para razão `1,20` até `n = 20`, a aplicação literal da regra eleva
  o tamanho amostral ao teto de **`n = 20` execuções por célula** (80 execuções por experimento).
- **Recomendação prática ao trio antes de congelar o plano final (D2 / P2):**
  1. **Prioridade 1 (instrumentação):** investigar os dois travamentos do Kafka em E1 (RAM
     próxima do teto de 4 GiB) e a falha de subida do RabbitMQ. Com CV > 98%, aumentar `n` de 10
     para 20 não resolve o poder para diferenças pequenas ou médias.
  2. **Prioridade 2 (tamanho amostral):** mesmo sem os travamentos de E1, o p99 em E2 teve CV de
     48% (1 KiB). Adotar **`n = 15` a `20` por célula** garante >89% de poder para diferenças de
     2× (com CV de 48%) e margem de segurança caso ocorra 1 falha eventual de container. Para o
     efeito observado em E2 (~170× a ~240×), tanto `n = 10` quanto `n = 20` atingem poder ~100%.
