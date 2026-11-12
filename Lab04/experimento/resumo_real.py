"""Resumo dos pares reais: efeito e incerteza, separados do poder simulado."""

import numpy as np
from scipy import stats

from .analise import analisar_pares
from .dados import validar_pares


def resumir_reais(pares: np.ndarray, alpha: float = 0.05) -> dict:
    pares = validar_pares(pares)
    resultados = analisar_pares(pares, alpha)
    diferencas = np.log(pares[:, 0]) - np.log(pares[:, 1])
    media = float(diferencas.mean())
    erro = float(stats.sem(diferencas))
    intervalo = None
    if resultados["t_pareado"]["p_valor"] is not None:
        limites = stats.t.interval(1 - alpha, len(pares) - 1, loc=media, scale=erro)
        intervalo = [float(np.exp(limite)) for limite in limites]
    return {
        "n_pares": len(pares), "resultados": resultados,
        "media_sem_cache_s": float(pares[:, 0].mean()), "media_com_cache_s": float(pares[:, 1].mean()),
        "media_diferencas_log": media, "razao_geometrica": float(np.exp(media)),
        "ic95_razao_t": intervalo,
        "limites": "O IC t depende das diferenças e da independência; esta coleta mede bytecode local, não todo build.",
    }
