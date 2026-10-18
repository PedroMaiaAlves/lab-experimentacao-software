"""Figuras e tabelas LaTeX da parte A, derivadas dos mesmos resultados dos CSVs."""
from pathlib import Path
import re

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter, LogLocator, NullFormatter
import numpy as np

from analises.rq01_04 import METRICAS
from metricas.classificacao import DIAS_MES, HORAS_DIA, HORAS_SEMANA, UM_POR_MES_EM_SEMANAS

# Paleta de referência validada (dataviz): três séries categóricas e tinta neutra.
SERIES = ("#2a78d6", "#eb6834", "#1baf7a")
TINTA, TINTA_SECUNDARIA, TINTA_MUDA = "#0b0b0b", "#52514e", "#898781"
GRADE, EIXO, SUPERFICIE = "#e1e0d9", "#c3c2b7", "#ffffff"

# (título, colunas, rótulos curtos, eixo, escala, cortes da classificação DORA)
PAINEIS = (
    ("RQ01 · Frequência de entrega", ("deployment_frequency", "deployment_frequency_prereleases",
                                      "deployment_frequency_tags"),
     ("Releases", "Com pré-\nreleases", "Tags"), "Entregas por semana", "log",
     ((7, "Elite ≥ 7"), (1, "High ≥ 1"), (UM_POR_MES_EM_SEMANAS, "Medium ≥ 1/mês"))),
    ("RQ02 · Lead time", ("lead_time_a_horas", "lead_time_b_horas"),
     ("(a) por release", "(b) por commit"), "Horas", "log",
     ((HORAS_DIA, "Elite < 1 dia"), (HORAS_SEMANA, "High < 1 semana"), (DIAS_MES * HORAS_DIA, "Medium < 30 dias"))),
    ("RQ03 · Taxa de falha das mudanças", ("cfr_a", "cfr_b"),
     ("(a) runs de CI", "(b) releases"), "Proporção", "linear",
     ((.15, "Elite ≤ 0,15"), (.30, "High ≤ 0,30"), (.45, "Medium ≤ 0,45"))),
    ("RQ04 · Tempo de recuperação", ("tempo_recuperacao_horas", "episodios"),
     ("Mediana por\nprojeto", "Episódios\nconcluídos"), "Horas", "log",
     ((1, "Elite < 1 h"), (HORAS_DIA, "High < 1 dia"), (HORAS_SEMANA, "Medium < 1 semana"))),
)


def numero(valor, casas=3):
    """Número no formato brasileiro (1.234,567); ausente vira '--'."""
    if valor is None or not np.isfinite(valor):
        return "--"
    return f"{valor:,.{casas}f}".replace(",", "\0").replace(".", ",").replace("\0", ".")


def inteiro(valor):
    return numero(valor, 0)


def por_unidade(valor, unidade):
    if unidade == "horas":
        return numero(valor, 2 if abs(valor) < 100 else 1) if np.isfinite(valor) else "--"
    return numero(valor, 3)


def p_formatado(valor):
    if valor is None or not np.isfinite(valor):
        return "--"
    if 0 < valor < 1e-4:
        mantissa, expoente = f"{valor:.2e}".split("e")
        return "$" + mantissa.replace(".", ",") + r"\times 10^{" + str(int(expoente)) + "}$"
    return numero(valor, 4)


def _rotulo_eixo(valor, _):
    if valor <= 0:
        return "0"
    casas = max(0, -int(np.floor(np.log10(valor)))) if valor < 1 else 0
    return numero(valor, casas)


def _estilo(eixo):
    eixo.set_facecolor(SUPERFICIE)
    for lado in ("top", "right"):
        eixo.spines[lado].set_visible(False)
    for lado in ("left", "bottom"):
        eixo.spines[lado].set_color(EIXO)
        eixo.spines[lado].set_linewidth(.8)
    eixo.tick_params(colors=TINTA_SECUNDARIA, labelsize=8, length=3, width=.6)
    eixo.grid(axis="y", color=GRADE, linewidth=.6)
    eixo.set_axisbelow(True)


LIMITE_PONTOS = 500  # acima disso (episódios), só a cauda além de P95 é desenhada


def _caixas(eixo, series, rng):
    # Bigodes por percentis: 1,5 IQR em escala linear se estende até o mínimo em escala log.
    caixas = eixo.boxplot(series, widths=.42, patch_artist=True, showfliers=False,
                          whis=(5, 95), medianprops=dict(color=TINTA, linewidth=1.6),
                          whiskerprops=dict(color=TINTA_SECUNDARIA, linewidth=.9),
                          capprops=dict(color=TINTA_SECUNDARIA, linewidth=.9))
    for indice, (caixa, valores) in enumerate(zip(caixas["boxes"], series)):
        cor = SERIES[indice]
        caixa.set(facecolor=cor + "1f", edgecolor=cor, linewidth=1.4)
        if len(valores) > LIMITE_PONTOS:
            p5, p95 = np.percentile(valores, [5, 95])
            valores = valores[(valores < p5) | (valores > p95)]
        deslocamento = rng.uniform(-.17, .17, len(valores))
        eixo.scatter(indice + 1 + deslocamento, valores, s=7, color=cor, alpha=.45,
                     linewidths=0, zorder=3)


def _cortes(eixo, cortes):
    for valor, texto in cortes:
        eixo.axhline(valor, color=TINTA_MUDA, linewidth=.7, linestyle=(0, (4, 3)), zorder=1)
        eixo.annotate(texto, xy=(1, valor), xycoords=("axes fraction", "data"), xytext=(3, 0),
                      textcoords="offset points", va="center", ha="left", fontsize=6.5,
                      color=TINTA_SECUNDARIA)


def distribuicoes(df, episodios, semente=42):
    """Boxplots das RQ01 a RQ04 com os cortes da classificação DORA de referência."""
    rng = np.random.default_rng(semente)
    figura, eixos = plt.subplots(2, 2, figsize=(9, 6.6), layout="constrained")
    figura.get_layout_engine().set(w_pad=.12, h_pad=.08)
    for eixo, (titulo, colunas, rotulos, nome_eixo, escala, cortes) in zip(eixos.flat, PAINEIS):
        _estilo(eixo)
        series = [episodios.horas.to_numpy(float) if c == "episodios" else df[c].dropna().to_numpy(float)
                  for c in colunas]
        _caixas(eixo, series, rng)
        if escala == "log":
            eixo.set_yscale("log")
            eixo.yaxis.set_major_locator(LogLocator(base=10, numticks=12))
            eixo.yaxis.set_major_formatter(FuncFormatter(_rotulo_eixo))
            eixo.yaxis.set_minor_formatter(NullFormatter())
        else:
            eixo.set_ylim(-.03, 1.03)
            eixo.yaxis.set_major_formatter(FuncFormatter(lambda v, _: numero(v, 1)))
        _cortes(eixo, cortes)
        ns = [f"n={inteiro(len(s))}" for s in series]
        eixo.set_xticks(range(1, len(rotulos) + 1), [f"{r}\n{n}" for r, n in zip(rotulos, ns)])
        eixo.set_title(titulo, loc="left", fontsize=9.5, color=TINTA, pad=6)
        eixo.set_ylabel(nome_eixo, fontsize=8, color=TINTA_SECUNDARIA)
    return figura


def salvar_figura(figura, destino):
    destino = Path(destino)
    figura.savefig(destino.with_suffix(".png"), dpi=180, facecolor=SUPERFICIE, metadata={"Software": "LAB03"})
    figura.savefig(destino.with_suffix(".pdf"), facecolor=SUPERFICIE,
                   metadata={"Creator": "LAB03", "CreationDate": None, "ModDate": None})
    plt.close(figura)


def _escrever(destino, linhas):
    Path(destino).write_text("\n".join(linhas) + "\n", encoding="utf-8", newline="\n")


def sinal_tex(texto):
    """Sinal negativo em modo matemático; '--' (ausente ou intervalo) não é alterado."""
    return re.sub(r"(?:^|(?<= ))-(?=\d)", "$-$", texto)


UNIDADES_TEX = {"releases/semana": "por semana", "tags/semana": "por semana", "horas": "horas",
                "proporção": "proporção"}
PARES_TEX = {"deployment_frequency_prereleases": "Com pré-releases $-$ releases",
             "deployment_frequency_tags": "Tags $-$ releases",
             "lead_time_a_horas": "Lead time (a) $-$ (b), horas",
             "cfr_a": "CFR (a) $-$ CFR (b)"}


def tabela_descritivas(descritivas, destino):
    linhas = [r"% Gerado por analises.sprint3_a; não edite à mão.", r"\begin{tabular}{lllrrrr}", r"\hline",
              r"RQ & Métrica & Unidade & $n$ & Mediana & Q1--Q3 & IQR \\", r"\hline"]
    anterior = None
    for _, r in descritivas.iterrows():
        if anterior and r.rq != anterior:
            linhas.append(r"\hline")
        anterior = r.rq
        f = lambda v: por_unidade(v, r.unidade)
        linhas.append(sinal_tex(f"{r.rq} & {r.rotulo} & {UNIDADES_TEX[r.unidade]} & {inteiro(r['n'])} & "
                                f"{f(r.mediana)} & {f(r.q1)}--{f(r.q3)} & {f(r.iqr)} ") + r"\\")
    linhas += [r"\hline", r"\end{tabular}"]
    _escrever(destino, linhas)


def tabela_pareadas(pareadas, destino):
    linhas = [r"% Gerado por analises.sprint3_a; não edite à mão.", r"\begin{tabular}{lrrrrrrr}", r"\hline",
              r"Diferença $x-y$ & $n$ & $x>y$ & $x=y$ & $x<y$ & Mediana & $r$ & $p$ Holm \\", r"\hline"]
    for _, r in pareadas.iterrows():
        unidade = METRICAS[r.x][2]
        linhas.append(sinal_tex(f"{PARES_TEX[r.x]} & {inteiro(r['n'])} & {inteiro(r.n_x_maior)} & "
                                f"{inteiro(r.n_iguais)} & {inteiro(r.n_x_menor)} & "
                                f"{por_unidade(r.mediana_diferenca, unidade)} & "
                                f"{numero(r.efeito_rank_biserial)} & {p_formatado(r.p_holm)} ") + r"\\")
    linhas += [r"\hline", r"\end{tabular}"]
    _escrever(destino, linhas)


def tabela_numeros(numeros, destino):
    """Macros LaTeX para os números citados no texto, sempre a partir dos CSVs."""
    linhas = [r"% Gerado por analises.sprint3_a; não edite à mão."]
    linhas += [rf"\newcommand{{\{nome}}}{{{sinal_tex(valor)}}}" for nome, valor in numeros.items()]
    _escrever(destino, linhas)
