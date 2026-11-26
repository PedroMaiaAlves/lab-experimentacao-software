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

Para o protocolo oficial (#207), o módulo também produz a simulação com os CVs
observados no mini-piloto estabilizado. O CV corrigido de p99 ainda não existe
para as quatro células; essa ausência é registrada, não estimada.
"""

from __future__ import annotations

import numpy as np
from scipy import stats

ALFA = 0.05
COMPARACOES = 4  # H1 e H2, em 1 KiB e 16 KiB
ALFA_HOLM_PIOR_CASO = ALFA / COMPARACOES

CVS_THROUGHPUT_OBSERVADOS = {
    ("kafka", 1024): 0.2010,
    ("kafka", 16384): 0.3034,
    ("rabbitmq", 1024): 0.0374,
    ("rabbitmq", 16384): 0.1118,
}


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


def tabela_observada(
    ns=(5, 8, 10, 15, 20),
    razao: float = 1.20,
    repeticoes: int = 10_000,
) -> list[dict]:
    """Poder com os CVs válidos disponíveis para o pré-registro da #207."""
    linhas: list[dict] = []
    for (broker, tamanho), cv in CVS_THROUGHPUT_OBSERVADOS.items():
        for n in ns:
            estimativa = poder(n, razao, cv, repeticoes=repeticoes)
            linhas.append(
                {
                    "metrica": "throughput_msg_s",
                    "broker": broker,
                    "tamanho_bytes": tamanho,
                    "cv": cv,
                    "razao": razao,
                    "n": n,
                    "status": "calculado",
                    **estimativa,
                }
            )

    # A correção do timestamp do RabbitMQ invalidou o p99 do piloto antigo. A
    # verificação corrigida tem só 1–2 observações e nenhuma para Kafka 16 KiB.
    # Não se apresenta esse conjunto incompleto como CV estabilizado.
    for broker in ("kafka", "rabbitmq"):
        for tamanho in (1024, 16384):
            linhas.append(
                {
                    "metrica": "latencia_p99_ms",
                    "broker": broker,
                    "tamanho_bytes": tamanho,
                    "cv": "",
                    "razao": razao,
                    "n": 20,
                    "status": "cv_indisponivel",
                    "welch_log": "",
                    "mann_whitney": "",
                }
            )
    return linhas
