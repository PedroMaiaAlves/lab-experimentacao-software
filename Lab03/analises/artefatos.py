"""Figuras e tabelas do artigo, derivadas dos mesmos resultados dos CSVs."""
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from analises.comum import METRICAS
from analises.rq06 import FATORES

ROTULOS_FATORES = {"tipo_projeto": "Tipo do projeto", "contribuidores_quartil": "Contribuidores (quartis)",
                   "linguagem_grupo": "Linguagem"}
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


def efeitos(tabela):
    fig, eixo = plt.subplots(figsize=(9, 2.7), layout="constrained")
    matriz = tabela.pivot(index="fator", columns="metrica", values="efeito").reindex(index=FATORES, columns=METRICAS)
    # Valores assinados de Cliff são preservados se um fator passar a ter apenas dois grupos.
    negativo = bool((matriz < 0).any().any())
    mapa = eixo.imshow(matriz.to_numpy(float), cmap="RdBu_r" if negativo else "YlGnBu",
                      vmin=-1 if negativo else 0, vmax=1)
    eixo.set_xticks(range(len(METRICAS)), [v[0].replace(" ", "\n", 1) for v in METRICAS.values()])
    eixo.set_yticks(range(len(FATORES)), [ROTULOS_FATORES[f] for f in FATORES])
    for i, fator in enumerate(FATORES):
        for j, metrica in enumerate(METRICAS):
            r = tabela[(tabela.fator == fator) & (tabela.metrica == metrica)].iloc[0]
            texto = "n/a" if not np.isfinite(r.efeito) else f"{r.efeito:.3f}" + ("*" if r.p_holm < .05 else "")
            eixo.text(j, i, texto, ha="center", va="center", color="white" if abs(r.efeito) > .55 else "black")
    fig.colorbar(mapa, ax=eixo, label="Tamanho de efeito (ε²; δ se dois grupos)", shrink=.85)
    eixo.set_title("RQ06 · * p ajustado por Holm < 0,05")
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


def gerar_tabelas(rq05, rq06, destino):
    destino = Path(destino)
    linhas = [r"% Gerado por analises.sprint3_b", r"\begin{tabular}{lrrrr}", r"\hline",
              r"Proxy & $n$ & $\rho$ [IC 95\%] & $p$ Spearman & $p$ perm./Holm \\", r"\hline"]
    for _, r in rq05.iterrows():
        intervalo = f"{numero(r.rho)} [{numero(r.ic95_inferior)}; {numero(r.ic95_superior)}]"
        linhas.append(f"{METRICAS[r.variante][0]} & {int(r['n'])} & {intervalo} & "
                      f"{p_formatado(r.p_spearman)} & {p_formatado(r.p_permutacao_holm)} " + r"\\")
    linhas += [r"\hline", r"\end{tabular}"]
    (destino / "rq05_tabela.tex").write_text("\n".join(linhas)+"\n", encoding="utf-8", newline="\n")
    linhas = [r"% Gerado por analises.sprint3_b", r"\begin{tabular}{llrrr}", r"\hline",
              r"Fator & Métrica & $n$ & $p$ Holm & $\varepsilon^2$ / $\delta$ \\", r"\hline"]
    for _, r in rq06.iterrows():
        linhas.append(f"{ROTULOS_FATORES[r.fator]} & {METRICAS[r.metrica][0]} & {int(r['n'])} & "
                      f"{p_formatado(r.p_holm)} & {numero(r.efeito)} " + r"\\")
    linhas += [r"\hline", r"\end{tabular}"]
    (destino / "rq06_tabela.tex").write_text("\n".join(linhas)+"\n", encoding="utf-8", newline="\n")
    significativas = [linha for linha, (_, r) in zip(linhas[5:-2], rq06.iterrows()) if r.p_holm < .05]
    (destino / "rq06_significativos.tex").write_text("\n".join(linhas[:5] + significativas + linhas[-2:])+"\n", encoding="utf-8", newline="\n")
