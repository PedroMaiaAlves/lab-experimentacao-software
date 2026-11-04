"""D1: t pareado e Wilcoxon pareado sobre os log-tempos, com decisão e interpretação."""

from __future__ import annotations

import numpy as np
from scipy import stats

from experimento.dados import validar_pares

ALTERNATIVA = "two-sided"
HIPOTESES = {
    "t_pareado": {
        "H0": "a média populacional de log(sem cache) − log(com cache) é zero",
        "H1": "essa média é diferente de zero (bicaudal)",
    },
    "wilcoxon": {
        "H0": "as diferenças log(sem) − log(com) são simétricas em torno de zero (mediana zero)",
        "H1": "as diferenças não são simétricas em torno de zero (bicaudal)",
    },
}
NOMES = {"t_pareado": "t pareado", "wilcoxon": "Wilcoxon pareado"}


def _fmt(valor: float) -> str:
    return format(valor, ".3g").replace(".", ",")


def _indisponivel(chave: str, n: int, alpha: float, metodo: str, motivo: str) -> dict:
    # Nunca inventar zero: estatística e p-valor ficam None, com o motivo explícito.
    return {
        "estatistica": None, "p_valor": None, "metodo": metodo, "n_pares": n, "alpha": alpha,
        "alternativa": ALTERNATIVA, "hipoteses": HIPOTESES[chave], "decisao": "indisponível",
        "motivo": motivo,
        "interpretacao": f"O {NOMES[chave]} não foi calculado: {motivo}",
    }


def _interpretar(chave: str, p: float, alpha: float) -> str:
    nome = NOMES[chave]
    if p < alpha:
        return (
            f"Com p = {_fmt(p)} < α = {_fmt(alpha)}, o {nome} rejeita H0 ({HIPOTESES[chave]['H0']}). "
            "O p-valor é a probabilidade, supondo H0 verdadeira, de observar uma estatística tão ou mais "
            "extrema que a obtida; não é a probabilidade de H0 ser verdadeira nem mede o tamanho do efeito."
        )
    return (
        f"Com p = {_fmt(p)} ≥ α = {_fmt(alpha)}, o {nome} não rejeita H0 ({HIPOTESES[chave]['H0']}). "
        "Não rejeitar H0 não prova que os tempos são iguais: a amostra apenas não trouxe evidência "
        "suficiente contra H0 neste nível de significância."
    )


def teste_t_pareado(pares: np.ndarray, alpha: float = 0.05) -> dict:
    a = validar_pares(pares)
    logs = np.log(a)
    d = logs[:, 0] - logs[:, 1]
    n = d.size
    metodo = "t de Student pareado sobre log-tempos (distribuição t com n−1 gl)"
    # Tolerância relativa: diferenças constantes podem deixar resíduo de ponto flutuante.
    if d.std(ddof=1) <= 1e-12 * max(1.0, abs(d.mean())):
        return _indisponivel("t_pareado", n, alpha, metodo,
                             "diferenças constantes têm desvio padrão zero, então t é indefinido.")
    r = stats.ttest_rel(logs[:, 0], logs[:, 1], alternative=ALTERNATIVA)
    p = float(r.pvalue)
    return {
        "estatistica": float(r.statistic), "p_valor": p, "metodo": metodo, "n_pares": n,
        "gl": n - 1, "alpha": alpha, "alternativa": ALTERNATIVA, "hipoteses": HIPOTESES["t_pareado"],
        "decisao": "rejeitar H0" if p < alpha else "não rejeitar H0",
        "interpretacao": _interpretar("t_pareado", p, alpha),
    }


def teste_wilcoxon(pares: np.ndarray, alpha: float = 0.05) -> dict:
    a = validar_pares(pares)
    d = np.log(a[:, 0]) - np.log(a[:, 1])
    n = d.size
    nz = d[d != 0]
    zeros = int(n - nz.size)
    empates = bool(np.unique(np.abs(nz)).size < nz.size)
    if nz.size == 0:
        return _indisponivel("wilcoxon", n, alpha, "Wilcoxon pareado",
                             "todas as diferenças são zero, então não há postos com sinal.")
    if zeros or empates:
        # Distribuição exata não vale com empates/zeros: zeros descartados e variância corrigida.
        metodo = (f"Wilcoxon pareado, aproximação normal sem correção de continuidade "
                  f"({zeros} zero(s) descartado(s), empates={'sim' if empates else 'não'})")
        r = stats.wilcoxon(d, zero_method="wilcox", correction=False, alternative=ALTERNATIVA, method="approx")
    else:
        metodo = "Wilcoxon pareado exato: distribuição de min(W+, W−) sob H0"
        r = stats.wilcoxon(d, alternative=ALTERNATIVA, method="exact")
    p = float(r.pvalue)
    return {
        "estatistica": float(r.statistic), "p_valor": p, "metodo": metodo, "n_pares": n,
        "n_efetivo": int(nz.size), "zeros": zeros, "empates": empates,
        "alpha": alpha, "alternativa": ALTERNATIVA, "hipoteses": HIPOTESES["wilcoxon"],
        "decisao": "rejeitar H0" if p < alpha else "não rejeitar H0",
        "interpretacao": _interpretar("wilcoxon", p, alpha),
    }


def analisar_pares(pares: np.ndarray, alpha: float = 0.05) -> dict:
    """Aplica os dois testes à mesma amostra pareada; pares inválidos geram erro."""
    if not 0 < alpha < 1:
        raise ValueError("alpha deve estar entre 0 e 1.")
    return {"t_pareado": teste_t_pareado(pares, alpha), "wilcoxon": teste_wilcoxon(pares, alpha)}
