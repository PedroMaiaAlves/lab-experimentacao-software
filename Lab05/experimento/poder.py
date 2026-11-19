"""Simulação de poder a priori (issue #197).

Antes do piloto não conhecemos a variabilidade entre execuções. Por isso simulamos
cenários de coeficiente de variação (CV) plausíveis para benchmarks de broker e
perguntamos: com n execuções por célula, qual a chance de detectar uma razão
Kafka/RabbitMQ de r, em cada tamanho de mensagem?

Modelo: métrica log-normal; log(Y) ~ N(mu_broker, sigma²), com sigma derivado do
CV (sigma = sqrt(ln(1 + CV²))). Testes: Welch sobre log e Mann-Whitney, bicaudais.
Como há várias comparações principais (H1 e H2, em 2 tamanhos), usamos Holm.
O pior caso do Holm (o menor p-valor contra alfa/m) é um limite conservador do
poder, então o nível efetivo é alfa/4.

Os números são provisórios: depois do piloto (#199), Lorran (#201) troca o CV
suposto pelo observado e confirma ou ajusta n.
"""

from __future__ import annotations

import numpy as np
from scipy import stats

ALFA = 0.05
COMPARACOES = 4  # H1 e H2, em 1 KiB e 16 KiB
ALFA_HOLM_PIOR_CASO = ALFA / COMPARACOES


def sigma_log(cv: float) -> float:
    return float(np.sqrt(np.log1p(cv**2)))


def poder(
    n: int,
    razao: float,
    cv: float,
    alfa: float = ALFA_HOLM_PIOR_CASO,
    repeticoes: int = 2000,
    semente: int = 42,
) -> dict[str, float]:
    rng = np.random.default_rng(semente)
    s = sigma_log(cv)
    a = rng.normal(np.log(razao), s, size=(repeticoes, n))
    b = rng.normal(0.0, s, size=(repeticoes, n))
    p_welch = stats.ttest_ind(a, b, axis=1, equal_var=False).pvalue
    p_mw = stats.mannwhitneyu(a, b, axis=1, alternative="two-sided", method="exact").pvalue
    return {
        "welch_log": float(np.mean(p_welch < alfa)),
        "mann_whitney": float(np.mean(p_mw < alfa)),
    }


def tabela(
    ns=(5, 8, 10, 15, 20),
    razoes=(1.05, 1.10, 1.20, 1.50),
    cvs=(0.05, 0.10, 0.20),
    repeticoes: int = 2000,
) -> list[dict]:
    linhas = []
    for cv in cvs:
        for razao in razoes:
            for n in ns:
                p = poder(n, razao, cv, repeticoes=repeticoes)
                linhas.append({"cv": cv, "razao": razao, "n": n, **p})
    return linhas


def menor_n(linhas: list[dict], cv: float, razao: float, alvo: float = 0.8, teste: str = "mann_whitney"):
    candidatos = [l["n"] for l in linhas if l["cv"] == cv and l["razao"] == razao and l[teste] >= alvo]
    return min(candidatos) if candidatos else None
