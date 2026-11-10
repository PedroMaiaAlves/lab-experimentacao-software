# Evidências de Diogo — Lab04S02, Q2

## Escopo

- **#186:** `experimento/q2.py`, `simular_q2.py`, `tests/test_q2.py` e
  `data/s02/q2_resultados.csv` + `q2_manifesto.json`.
- **#187:** `experimento/q2_interpretacao.py`, `interpretar_q2.py`,
  `tests/test_q2_interpretacao.py` e `data/s02/q2_interpretacao.json`.

O `monte_carlo.py` de Pedro não foi alterado, pois o `validar_q1` confere seu hash.

## Configuração de Q2

- Diferenças `log(sem) − log(com)` normais, desvio calibrado `0,18309179292385067`.
- 30 pares, 10.000 repetições por razão, testes bicaudais, `alpha = 0,05`.
- Razões 1,00; 1,02; 1,05; 1,10; 1,15; 1,20; 1,25 (`delta = log(razão)`), fixadas na issue.
- Semente derivada de 42: `SeedSequence([42, 2])`, independente dos fluxos da Q1.
  Q3 deve usar a mesma política com a chave 3.

## Resultados

| Razão | Poder t (IC 95%) | Poder Wilcoxon (IC 95%) | Só t rejeita | Só Wilcoxon rejeita | McNemar p | Maior poder |
| --- | --- | --- | --- | --- | --- | --- |
| 1,00 (H0) | 4,98% (4,57–5,42) | 4,97% (4,56–5,41) | 92 | 91 | 1,00 | sem diferença |
| 1,02 | 8,52% (7,99–9,08) | 8,16% (7,64–8,71) | 146 | 110 | 0,029 | t |
| 1,05 | 29,51% (28,62–30,41) | 28,04% (27,17–28,93) | 362 | 215 | 9,9e-10 | t |
| 1,10 | 78,73% (77,92–79,52) | 77,50% (76,67–78,31) | 291 | 168 | 1,0e-08 | t |
| 1,15 | 98,06% (97,77–98,31) | 97,67% (97,36–97,95) | 57 | 18 | 7,2e-06 | t |
| 1,20 | 99,97% (99,91–99,99) | 99,95% (99,88–99,98) | 3 | 1 | 0,63 | sem diferença |
| 1,25 | 100% (99,96–100) | 100% (99,96–100) | 0 | 0 | 1,00 | sem diferença |

## Interpretação

Poder é a proporção de amostras simuladas em que o teste rejeita H0 quando o efeito
existe. Não é um p-valor (que se refere a uma única amostra) nem o tamanho do efeito
(que é a razão definida em cada linha). Em 1,00 a taxa é o erro tipo I, perto dos 5%,
como na Q1.

Sob normalidade, o t pareado teve poder maior em 1,02; 1,05; 1,10 e 1,15, com no máximo
1,5 ponto percentual de vantagem. É o esperado: o t é ótimo para dados normais, e a
eficiência relativa assintótica do Wilcoxon nesse caso é 3/π ≈ 0,955. Em 1,20 e 1,25 os
dois chegam perto de 100% e não há diferença detectável. Com 30 pares, os dois testes
só passam de 80% de poder a partir da razão 1,15.

Os testes são aplicados às mesmas amostras. Por isso a comparação usa o teste exato de
McNemar sobre as amostras em que só um deles rejeita, e não a sobreposição dos
intervalos de Wilson, que ignora esse pareamento.

## Limitações e incerteza de Monte Carlo

- Com 10.000 repetições, o erro padrão de uma taxa é no máximo 0,5 p.p., e os intervalos
  de Wilson de 95% têm meia-largura de até cerca de 1 p.p.
- Os resultados valem para diferenças normais, independentes, com o desvio calibrado e
  n = 30. Com caudas pesadas (Q3) ou outro n, a ordem dos testes pode mudar.
- Nas razões maiores o poder satura em 100%, e a comparação perde informação.
- A simulação descreve o comportamento dos testes, não o efeito real do cache.

## Validação

- **Regeneração idêntica:** `validar_q2` e `validar_interpretacao` regeneram em memória e
  conferem os bytes, a origem e os hashes do código.
- **SciPy direto:** `interpretar_q2.py --scipy` refaz as 140.000 decisões com
  `scipy.stats.ttest_1samp` e `scipy.stats.wilcoxon(method="exact")`, chamadas uma por
  amostra: **0 divergências** em relação ao cálculo em lote (cerca de 1 min).
- **Testes:** 75 passando no Lab04.

## Uso no dashboard (G4, Lorran)

```python
from experimento.q2_interpretacao import ler_texto_q2

q2 = ler_texto_q2()      # lê o JSON preservado, sem simular
q2["texto"]              # 4 frases para a seção de poder
q2["limitacoes"]         # lista de limitações
q2["comparacao"]         # poder, IC, discordâncias e McNemar por razão
```

As curvas do G4 devem ler `data/s02/q2_resultados.csv` (`ler_resultados`).

## Reproduzir

```powershell
.\Lab04\.venv\Scripts\python.exe Lab04/simular_q2.py --validar
.\Lab04\.venv\Scripts\python.exe Lab04/interpretar_q2.py --validar
.\Lab04\.venv\Scripts\python.exe Lab04/interpretar_q2.py --scipy
.\Lab04\.venv\Scripts\python.exe -m pytest -c Lab04/pytest.ini Lab04/tests -q
```
