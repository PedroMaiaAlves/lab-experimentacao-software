# Resultados Estatísticos — Lab05S02 (Papel C: Lorran)

> **Status:** ⏳ **Aguardando coleta oficial validada (portão G3 / [#210](planejamento_s02.md)).**
> Os dados oficiais (`Lab05/data/oficial/<coleta>/`) ainda não foram entregues no repositório.

---

## 1. Por que ainda não há números inferenciais neste documento

De acordo com a revisão de método ([`metodo.md`](metodo.md), seção 4.4) e o checklist de revisão
([`revisao_analise.md`](revisao_analise.md)):

- O piloto de **19/11/2026** (`data/piloto/20261119T030115.153119Z/`) sofreu do artefato do
  `RateController` adaptativo no E1 e do arredondamento de timestamp em segundos no driver RabbitMQ
  do OMB no E2 (~500 ms no p50 e ~995 ms no p99 por construção).
- É **proibido** usar dados de `data/piloto/` ou `data/piloto_g1/` como evidência confirmatória de
  H1, H2 ou H3, ou gerar `data/analise/oficial_resumo.json` antes da coleta oficial validada pelo
  portão G3 com a imagem `lab05/openmessaging-benchmark:5b1fa709-ts-ms`.

Este documento será regenerado automaticamente assim que a coleta oficial da `#210` for concluída e
versionada em `Lab05/data/oficial/`.

---

## 2. Pipeline pré-registrado pronto e validado (`analisar.py`)

Toda a lógica exigida pela issue **#211** e pelo checklist [`revisao_analise.md`](revisao_analise.md)
já está implementada e coberta por testes em [`tests/test_analise.py`](../tests/test_analise.py):

1. **Validação de entrada (portão G3):** exige `validar.py` aprovado (`fase="completa"`), máquina
   única no manifesto, imagem OMB `5b1fa709-ts-ms`, e recusa diretórios de piloto/verificação.
2. **Descritiva por célula:** mediana, Q1/Q3, IQR, média geométrica, desvio-padrão, CV observado
   (comparado ao CV de referência da `#207`) e `n` válido para M1 (`throughput_msg_s`,
   `throughput_mib_s`, `throughput_consumo_msg_s`), M2 (`latencia_p50_ms`, `latencia_p99_ms`) e M4
   (`cpu_percent_medio`, `memoria_mib_media`). Falhas técnicas (`falha`, `bloqueada`,
   `interrompida`) são contabilizadas sem imputação.
3. **Hipóteses H1 e H2:** Shapiro-Wilk sobre `ln(Y)` em cada célula para escolher entre Welch-log e
   Mann-Whitney bicaudal conforme [`plano_analise.md`](plano_analise.md), com correção de
   **Holm-Bonferroni** nas 4 comparações principais (`E1` e `E2` × `1 KiB` e `16 KiB`).
4. **Hipótese H3 (interação broker × tamanho):** ANOVA Tipo III sobre `ln(Y)` e teste de permutação
   de Freedman-Lane (5.000 permutações, semente 42).
5. **Tamanho do efeito:** razão das médias geométricas (Kafka / RabbitMQ) com IC de 95% por
   bootstrap percentil (5.000 reamostragens, semente 42) e $\delta$ de Cliff com classificação de
   Romano.
6. **Checagens de validade (`metodo.md` §4.2):**
   - **Efeito de ordem:** regressão linear de `ln(Y)` na posição (`ordem`) geral e por bloco (`E1-B1`,
     `E1-B2`, `E2-B1`, `E2-B2`).
   - **Efeito de bloco:** comparação entre blocos por broker e modelo OLS ajustado por bloco.
   - **Sensibilidade às repetições:** comparação com e sem os IDs que precisaram de repetição técnica.
   - **Carga relativa no E2:** `taxa_alvo / mediana_E1` por broker e tamanho.
   - **Outliers:** marcados via regra de Tukey (`1,5 × IQR`) e **nunca removidos** das métricas.

---

## 3. Como gerar os resultados oficiais após a entrega da `#210`

Com a pasta oficial `Lab05/data/oficial/<coleta>/` disponível e validada:

```powershell
python Lab05/analisar.py --oficial
python -m pytest Lab05/tests -q
```

O comando `--oficial` valida o portão G3 com `validar.py`, grava
`Lab05/data/analise/oficial_resumo.json` e sobrescreve este `Lab05/docs/resultados.md` com todas
as tabelas e checagens oficiais preenchidas.
