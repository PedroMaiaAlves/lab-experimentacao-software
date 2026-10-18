"""Figuras e tabelas do artigo, derivadas dos mesmos resultados dos CSVs."""

from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt

import numpy as np

from analises.comum import METRICAS

CORES = ("#177e89", "#b64835")

def dispersao(df, resumo):
    fig, eixos = plt.subplots(1, 2, figsize=(9, 3.4), layout="constrained")
    for eixo, variante, cor in zip(eixos, ("cfr_a", "cfr_b"), CORES):
        pares = df[["deployment_frequency", variante]].dropna()
        positivos = pares.deployment_frequency > 0
        eixo.scatter(pares.deployment_frequency, pares[variante], s=19, alpha=.60, color=cor, linewidths=0)
        # A coleta principal sempre tem >=5 releases; para outras entradas, preservar zero.
        eixo.set_xscale("log" if positivos.all() else "symlog", **({} if positivos.all() else {"linthresh": .1}))
        r = resumo.set_index("variante").loc[variante]
        eixo.set(title=f"{METRICAS[variante][0]} · n={int(r['n'])} · ρ={r.rho:.3f}",
                 xlabel="Releases por semana", ylabel="Taxa de falha", ylim=(-.03, 1.03))
        eixo.grid(alpha=.18)
    return fig

def salvar_figura(figura, destino):
    destino = Path(destino)
    figura.savefig(destino.with_suffix(".png"), dpi=180, metadata={"Software": "LAB03"})
    figura.savefig(destino.with_suffix(".pdf"), metadata={"Creator": "LAB03", "CreationDate": None, "ModDate": None})
    plt.close(figura)

def numero(valor, digitos=3):
    if not np.isfinite(valor):
        return "--"
    return f"{valor:.{digitos}f}".replace(".", ",")

def p_formatado(valor):
    if not np.isfinite(valor):
        return "--"
    if 0 < valor < .0001:
        mantissa, expoente = f"{valor:.2e}".split("e")
        return "$" + mantissa.replace(".", ",") + r"\times 10^{" + str(int(expoente)) + "}$"
    return numero(valor, 4)
