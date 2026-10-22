"""Artefatos da parte C, derivados das mesmas tabelas numéricas publicadas."""
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.ticker import PercentFormatter
import numpy as np

from analises.graficos_a import inteiro, numero, salvar_figura
from analises.rq07 import NOTAS


def artefatos_rq07(tabelas, saida):
    pares = tabelas["rq07_concordancia"]
    pares = pares[pares.populacao == "pares_disponiveis"]
    dados = tabelas["rq07_matrizes"]
    figura, eixos = plt.subplots(1, 3, figsize=(8.2, 2.7), layout="constrained")
    maximo = max(int(dados.n.max()), 1)
    for eixo, (_, r) in zip(eixos, pares.iterrows()):
        m = dados[(dados.combinacao_a == r.combinacao_a) & (dados.combinacao_b == r.combinacao_b)]
        matriz = m.pivot(index="categoria_a", columns="categoria_b", values="n").reindex(
            index=NOTAS, columns=NOTAS).to_numpy()
        desenho = eixo.imshow(matriz, cmap="Blues", vmin=0, vmax=maximo)
        for i in range(4):
            for j in range(4):
                eixo.text(j, i, str(matriz[i, j]), ha="center", va="center", fontsize=9,
                          color="white" if matriz[i, j] > maximo / 2 else "#0b0b0b")
        eixo.set(xticks=range(4), yticks=range(4), xticklabels=list(NOTAS), yticklabels=list(NOTAS),
                 xlabel=r.combinacao_b, ylabel=r.combinacao_a,
                 title=f"n={r.n}; κ={numero(r.kappa_linear, 3)}")
        eixo.tick_params(labelsize=8)
        eixo.set_title(eixo.get_title(), fontsize=9)
    figura.colorbar(desenho, ax=list(eixos), shrink=.7, label="Projetos")
    salvar_figura(figura, saida / "rq07_transicoes")
    linhas = [r"% Gerado por analises.sprint3_c.", r"\begin{tabular}{llrrrrr}", r"\hline",
              r"Par & População & $n$ & Mudaram & \% & $\kappa_w$ & Sem par \\", r"\hline"]
    for _, r in tabelas["rq07_concordancia"].iterrows():
        populacao = "Por par" if r.populacao == "pares_disponiveis" else "Comum às três"
        linhas.append(f"{r.combinacao_a}--{r.combinacao_b} & {populacao} & {r.n} & {r.mudou} & "
                      f"{numero(100 * r.proporcao_mudou, 1)} & {numero(r.kappa_linear, 3)} & {r.n_excluidos} " + r"\\")
    linhas += [r"\hline", r"\end{tabular}"]
    (saida / "rq07_tabela.tex").write_text("\n".join(linhas) + "\n", encoding="utf-8", newline="\n")
    numeros = {}
    for _, r in pares.iterrows():
        prefixo = "labC" + r.combinacao_a.replace("1", "Um").replace("2", "Dois").replace("3", "Tres")
        prefixo += r.combinacao_b.replace("1", "Um").replace("2", "Dois").replace("3", "Tres")
        numeros.update({prefixo + "N": inteiro(r.n), prefixo + "Mudou": numero(100 * r.proporcao_mudou, 1),
                        prefixo + "Kappa": numero(r.kappa_linear, 3)})
    return numeros


def figura_rework(tabelas):
    projetos, pares = tabelas["rq08_repositorios"], tabelas["rq08_comparacao"]
    figura, eixos = plt.subplots(1, 2, figsize=(8.2, 3.1), layout="constrained")
    for coluna, cor, nome in (("rework_rate", "#2a78d6", "Rework rate"), ("cfr_b", "#eb6834", "CFR (b)")):
        valores = np.sort(projetos[coluna].dropna().to_numpy())
        if len(valores):
            eixos[0].step(valores, np.arange(1, len(valores) + 1) / len(valores), where="post",
                          color=cor, label=f"{nome} (n={len(valores)})")
    eixos[0].set(xlabel="Proporção", ylabel="Fração acumulada dos projetos", title="Casos completos por indicador")
    eixos[0].legend(frameon=False, fontsize=8)
    eixos[0].yaxis.set_major_formatter(PercentFormatter(1))
    eixos[1].scatter(pares.cfr_b, pares.rework_rate, s=13, color="#2a78d6", alpha=.55, linewidths=0)
    eixos[1].plot([0, 1], [0, 1], color="#898781", linestyle="--", linewidth=.8)
    eixos[1].set(xlabel="CFR (b)", ylabel="Rework rate", title=f"Mesmos projetos (n={len(pares)})", ylim=(0, 1))
    for eixo in eixos:
        eixo.set_xlim(0, 1)
        eixo.xaxis.set_major_formatter(PercentFormatter(1))
        eixo.spines[["top", "right"]].set_visible(False)
        eixo.grid(alpha=.15)
        eixo.tick_params(labelsize=8)
    eixos[1].yaxis.set_major_formatter(PercentFormatter(1))
    return figura


def escrever_artefatos(tabelas, saida):
    saida = Path(saida)
    salvar_figura(figura_rework(tabelas), saida / "rq08_rework_cfr")
    resumo = tabelas["rq08_resumo"].set_index("metrica")
    cobertura = tabelas["rq08_cobertura"].iloc[0]
    pares = tabelas["rq08_comparacao"]
    linhas = [r"% Gerado por analises.sprint3_c; não edite à mão.",
              r"\begin{tabular}{lrrrr}", r"\hline",
              r"Indicador & $n$ & Ausentes & Mediana (\%) & Q1--Q3 (\%) \\", r"\hline"]
    for coluna, nome in (("rework_rate", "Rework rate"), ("cfr_b", "CFR (b)"),
                        ("rework_conservador", "Rework (evidência completa)")):
        r = resumo.loc[coluna]
        linhas.append(f"{nome} & {inteiro(r['n'])} & {inteiro(r.n_ausentes)} & "
                      f"{numero(100 * r.mediana, 1)} & {numero(100 * r.q1, 1)}--{numero(100 * r.q3, 1)} " + r"\\")
    linhas += [r"\hline", r"\end{tabular}"]
    (saida / "rq08_tabela.tex").write_text("\n".join(linhas) + "\n", encoding="utf-8", newline="\n")
    numeros = {"labCReworkN": inteiro(resumo.loc["rework_rate", "n"]),
               "labCReworkAusentes": inteiro(resumo.loc["rework_rate", "n_ausentes"]),
               "labCReworkMediana": numero(100 * resumo.loc["rework_rate", "mediana"], 1),
               "labCReworkTotal": inteiro(cobertura.releases_total),
               "labCReworkCorretivas": inteiro(cobertura.corretivas_heuristica),
               "labCReworkSemEvidencia": inteiro(cobertura.releases_sem_evidencia_completa),
               "labCReworkLimInf": numero(100 * cobertura.limite_inferior_conservador, 2),
               "labCReworkLimSup": numero(100 * cobertura.limite_superior_conservador, 2),
               "labCReworkConservadorN": inteiro(resumo.loc["rework_conservador", "n"]),
               "labCReworkConservadorMediana": numero(100 * resumo.loc["rework_conservador", "mediana"], 1),
               "labCReworkPareados": inteiro(len(pares)),
               "labCReworkDifMediana": numero(100 * pares.diferenca_rework_menos_cfr_b.median(), 1),
               "labCReworkMaior": inteiro((pares.rework_rate > pares.cfr_b).sum())}
    if "rq07_concordancia" in tabelas:
        numeros.update(artefatos_rq07(tabelas, saida))
    texto = "% Gerado por analises.sprint3_c; não edite à mão.\n"
    texto += "".join(f"\\newcommand{{\\{nome}}}{{{valor}}}\n" for nome, valor in numeros.items())
    (saida / "numeros_c.tex").write_text(texto, encoding="utf-8", newline="\n")
