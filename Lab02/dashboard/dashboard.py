"""
Dashboard de Visualização (v2) - Lab02 (Sprint 3)
Gera um conjunto de gráficos INDIVIDUAIS (um arquivo PNG por análise),
prontos para serem inseridos separadamente no relatório.

Cobre:
  RQ1 - Tempo até ficar verde (boxplot, violino, pareado, efeito de ordem)
  RQ2 - Sucesso dos testes e esforço com IA (dot plot + esforço x tempo)
  RQ3 - Estrutura do código (boxplots por métrica, correlação, dispersão,
        comparação por kata, sensibilidade por participante, radar normalizado)

Uso:
    python dashboard_v2.py --trials results\\trials.csv --output results\\graficos
    (opcional) --analysis results\\rq3\\analysis.json  -> usa p-valores já calculados

Sem --analysis, o script recalcula os testes de Wilcoxon pareados localmente
(mesma lógica: mediana dos 2 trials por participante/condição, teste exato
bilateral, correção de Holm) para poder anotar os gráficos de RQ3.
"""
import argparse
import itertools
import json
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns

sns.set_style("whitegrid")
plt.rcParams["figure.dpi"] = 150
plt.rcParams["savefig.dpi"] = 220
plt.rcParams["font.size"] = 11

TREATMENT_LABELS = {"ia": "IA", "manual": "Manual"}
PARTICIPANT_MARKERS = {"pedro": "o", "diogo": "s", "lorran": "^"}
PALETTE = {"IA": "#4C72B0", "Manual": "#DD8452"}
RQ3_METRICS = [
    ("mean_complexity", "Complexidade ciclomática média", "pontos"),
    ("duplication_percent", "Duplicação intrarquivo", "%"),
    ("loc", "Tamanho do código (SLOC)", "linhas"),
    ("maintainability_index", "Índice de manutenibilidade", "pontos (0-100)"),
]


# --------------------------------------------------------------------------
# Dados
# --------------------------------------------------------------------------
def load_trials(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path)
    df["treatment_label"] = df["treatment"].map(TREATMENT_LABELS)
    return df


def participant_medians(df: pd.DataFrame, value_col: str) -> pd.DataFrame:
    return df.groupby(["participant", "treatment"])[value_col].median().reset_index()


def wilcoxon_exact_two_sided(diffs):
    """Teste de postos sinalizados de Wilcoxon, exato, bilateral, sem dependências externas."""
    diffs = [d for d in diffs if d != 0]
    n = len(diffs)
    if n == 0:
        return None
    ranks = pd.Series([abs(d) for d in diffs]).rank(method="average").tolist()
    signs = [1 if d > 0 else -1 for d in diffs]
    w_plus = sum(r for r, s in zip(ranks, signs) if s > 0)
    total = sum(ranks)
    # enumerar todas as combinações de sinais para os postos observados
    count_le = 0
    count_total = 0
    for combo in itertools.product([1, -1], repeat=n):
        stat = sum(r for r, s in zip(ranks, combo) if s > 0)
        count_total += 1
        if abs(stat - total / 2) >= abs(w_plus - total / 2) - 1e-9:
            count_le += 1
    p = count_le / count_total
    return {"n_effective": n, "w_plus": w_plus, "p_value": min(p, 1.0)}


def compute_rq3_tests(df: pd.DataFrame) -> dict:
    """Recalcula (mediana IA-Manual por participante -> Wilcoxon + Holm) caso analysis.json não seja passado."""
    tests = {}
    raw_p = {}
    for metric, *_ in RQ3_METRICS:
        med = participant_medians(df, metric)
        piv = med.pivot(index="participant", columns="treatment", values=metric)
        piv = piv.dropna()
        diffs = (piv["ia"] - piv["manual"]).tolist()
        res = wilcoxon_exact_two_sided(diffs)
        raw_p[metric] = res["p_value"] if res else None
        tests[metric] = {
            "median_difference": float(np.median(diffs)) if diffs else None,
            "n_pairs": len(diffs),
            "p_value": res["p_value"] if res else None,
        }
    # Holm apenas nas métricas com p calculável (mesma família de 2 hipóteses do projeto: complexidade e duplicação)
    holm_family = [m for m in ["mean_complexity", "duplication_percent"] if raw_p.get(m) is not None]
    pvals = sorted(((raw_p[m], m) for m in holm_family))
    m = len(pvals)
    adj = {}
    running_max = 0.0
    for i, (p, name) in enumerate(pvals):
        val = min((m - i) * p, 1.0)
        running_max = max(running_max, val)
        adj[name] = running_max
    for name, val in adj.items():
        tests[name]["p_holm"] = val
    for metric, *_ in RQ3_METRICS:
        tests[metric].setdefault("p_holm", None)
    return tests


def load_rq3_tests(analysis_path: Path | None, df: pd.DataFrame) -> dict:
    if analysis_path and analysis_path.exists():
        data = json.loads(analysis_path.read_text(encoding="utf-8"))
        out = {}
        for metric, info in data.get("tests", {}).items():
            out[metric] = {
                "median_difference": info.get("median_difference"),
                "n_pairs": info.get("n_effective", info.get("n_pairs")),
                "p_value": info.get("p_value"),
                "p_holm": info.get("p_holm"),
            }
        for metric, *_ in RQ3_METRICS:
            out.setdefault(metric, {"median_difference": None, "n_pairs": None, "p_value": None, "p_holm": None})
        return out
    return compute_rq3_tests(df)


def scatter_by_participant(ax, df, x_col, y_col, x_order, jitter=0.05):
    x_pos = {label: i for i, label in enumerate(x_order)}
    rng = np.random.default_rng(42)
    for participant, marker in PARTICIPANT_MARKERS.items():
        sub = df[df["participant"] == participant]
        if sub.empty:
            continue
        xs = [x_pos[v] + rng.uniform(-jitter, jitter) for v in sub[x_col]]
        ax.scatter(xs, sub[y_col], marker=marker, s=75, color="black",
                   zorder=5, label=participant.capitalize())


def caption_note(fig, text):
    fig.text(0.5, -0.02, text, ha="center", fontsize=8.5, color="dimgray", wrap=True)


# --------------------------------------------------------------------------
# RQ1 — Tempo
# --------------------------------------------------------------------------
def fig_rq1_boxplot(df, outdir):
    fig, ax = plt.subplots(figsize=(6.5, 5))
    sns.boxplot(data=df, x="treatment_label", y="time_to_green_seconds",
                order=["IA", "Manual"], palette=PALETTE, ax=ax, width=0.5, showfliers=False)
    scatter_by_participant(ax, df, "treatment_label", "time_to_green_seconds", ["IA", "Manual"])
    ax.legend(title="Participante", fontsize=9, loc="upper left")
    ax.set_title("RQ1 — Tempo até ficar verde, por tratamento")
    ax.set_xlabel("")
    ax.set_ylabel("segundos")
    caption_note(fig, "Mediana Manual − IA = 952,8 s (≈15min53s); Wilcoxon unilateral exato p=0,125 (n=3 pares) — não significativo a 5%.")
    fig.savefig(outdir / "rq1_boxplot_tempo.png", bbox_inches="tight")
    plt.close(fig)


def fig_rq1_violin(df, outdir):
    fig, ax = plt.subplots(figsize=(6.5, 5))
    sns.violinplot(data=df, x="treatment_label", y="time_to_green_seconds",
                    order=["IA", "Manual"], palette=PALETTE, ax=ax, inner=None, cut=0)
    scatter_by_participant(ax, df, "treatment_label", "time_to_green_seconds", ["IA", "Manual"])
    ax.legend(title="Participante", fontsize=9, loc="upper left")
    ax.set_title("RQ1 — Forma da distribuição do tempo")
    ax.set_xlabel("")
    ax.set_ylabel("segundos")
    caption_note(fig, "Violino mostra a densidade estimada dos 6 trials por tratamento; pontos são os trials individuais.")
    fig.savefig(outdir / "rq1_violino_tempo.png", bbox_inches="tight")
    plt.close(fig)


def fig_rq1_paired(df, outdir):
    fig, ax = plt.subplots(figsize=(6.5, 5))
    med = participant_medians(df, "time_to_green_seconds")
    for participant, marker in PARTICIPANT_MARKERS.items():
        sub = med[med["participant"] == participant].set_index("treatment").reindex(["ia", "manual"])
        ax.plot(["IA", "Manual"], sub["time_to_green_seconds"], marker=marker,
                label=participant.capitalize(), linewidth=2, markersize=10)
    ax.set_title("RQ1 — Mediana por participante (2 trials por condição)")
    ax.set_ylabel("segundos")
    ax.legend(title="Participante", fontsize=9)
    caption_note(fig, "Cada linha liga a mediana IA à mediana Manual do mesmo participante — a unidade usada na inferência pareada.")
    fig.savefig(outdir / "rq1_pareado_participante.png", bbox_inches="tight")
    plt.close(fig)


def fig_rq1_order_effect(df, outdir):
    fig, ax = plt.subplots(figsize=(7, 5))
    for treatment, color in PALETTE.items():
        key = "ia" if treatment == "IA" else "manual"
        sub = df[df["treatment"] == key]
        ax.scatter(sub["order"], sub["time_to_green_seconds"], color=color, s=70, label=treatment)
    ax.set_xticks(sorted(df["order"].unique()))
    ax.set_title("RQ1 — Tempo em função da ordem do trial na sessão")
    ax.set_xlabel("Ordem do trial (1º ao 4º da sessão)")
    ax.set_ylabel("segundos")
    ax.legend(title="Tratamento")
    caption_note(fig, "Verifica visualmente efeito de aprendizado/fadiga ao longo da sessão — não é um teste formal.")
    fig.savefig(outdir / "rq1_efeito_ordem.png", bbox_inches="tight")
    plt.close(fig)


# --------------------------------------------------------------------------
# RQ2 — Sucesso e esforço
# --------------------------------------------------------------------------
def fig_rq2_success_dotplot(df, outdir):
    fig, ax = plt.subplots(figsize=(6, 4.5))
    summary = df.groupby("treatment_label")["success_rate"].agg(["mean", "min", "max"]).reindex(["IA", "Manual"])
    for i, (label, row) in enumerate(summary.iterrows()):
        ax.errorbar(row["mean"], i, xerr=[[row["mean"] - row["min"]], [row["max"] - row["mean"]]],
                    fmt="o", color=PALETTE[label], markersize=14, capsize=6, linewidth=2)
    ax.set_yticks(range(len(summary)))
    ax.set_yticklabels(summary.index)
    ax.set_xlim(90, 105)
    ax.set_xlabel("% de testes aprovados")
    ax.set_title("RQ2 — Taxa de sucesso dos testes (efeito teto)")
    for i, (label, row) in enumerate(summary.iterrows()):
        ax.annotate(f"{row['mean']:.0f}% (min={row['min']:.0f}, max={row['max']:.0f})",
                    (row["mean"], i), textcoords="offset points", xytext=(0, 14), ha="center", fontsize=9)
    caption_note(fig, "As 6 execuções de cada tratamento aprovaram 100% dos 8 testes de aceitação — sem variância a explorar (efeito teto).")
    fig.savefig(outdir / "rq2_taxa_sucesso.png", bbox_inches="tight")
    plt.close(fig)


def fig_rq2_effort(df, outdir):
    ia = df[df["treatment"] == "ia"]
    fig, ax = plt.subplots(figsize=(6.5, 5))
    for participant, marker in PARTICIPANT_MARKERS.items():
        sub = ia[ia["participant"] == participant]
        ax.scatter(sub["prompt_count"], sub["time_to_green_seconds"], marker=marker,
                   s=100, color=PALETTE["IA"], edgecolor="black", label=participant.capitalize())
    if ia["prompt_count"].nunique() > 1:
        coef = np.polyfit(ia["prompt_count"], ia["time_to_green_seconds"], 1)
        xs = np.linspace(ia["prompt_count"].min(), ia["prompt_count"].max(), 20)
        ax.plot(xs, np.polyval(coef, xs), "--", color="gray", linewidth=1.5)
    ax.set_title("RQ2 (esforço) — Nº de prompts vs. tempo até ficar verde (trials com IA)")
    ax.set_xlabel("Número de prompts ao assistente")
    ax.set_ylabel("segundos até ficar verde")
    ax.legend(title="Participante", fontsize=9)
    caption_note(fig, "Explora se mais interações com o assistente se associam a tempos maiores/menores nos 6 trials de IA.")
    fig.savefig(outdir / "rq2_esforco_prompts.png", bbox_inches="tight")
    plt.close(fig)


# --------------------------------------------------------------------------
# RQ3 — Estrutura do código
# --------------------------------------------------------------------------
def fig_rq3_metric_boxplot(df, outdir, metric, title, ylabel, tests):
    fig, ax = plt.subplots(figsize=(6, 5))
    sns.boxplot(data=df, x="treatment_label", y=metric, order=["IA", "Manual"],
                palette=PALETTE, ax=ax, width=0.5, showfliers=False)
    scatter_by_participant(ax, df, "treatment_label", metric, ["IA", "Manual"])
    ax.legend(title="Participante", fontsize=9, loc="upper right", bbox_to_anchor=(1.32, 1.02))
    ax.set_title(f"RQ3 — {title}")
    ax.set_xlabel("")
    ax.set_ylabel(ylabel)
    info = tests.get(metric, {})
    if info.get("p_holm") is not None:
        note = (f"Diferença pareada mediana (IA−Manual) = {info['median_difference']:.2f}; "
                f"Wilcoxon exato bilateral, n={info['n_pairs']} pares, p={info['p_value']:.3f}, "
                f"p de Holm={info['p_holm']:.3f}.")
    else:
        note = "Sem teste inferencial calculado para esta métrica na família de Holm do projeto."
    caption_note(fig, note)
    fname = {"mean_complexity": "rq3_boxplot_complexidade.png",
             "duplication_percent": "rq3_boxplot_duplicacao.png",
             "loc": "rq3_boxplot_sloc.png",
             "maintainability_index": "rq3_boxplot_manutenibilidade.png"}[metric]
    fig.savefig(outdir / fname, bbox_inches="tight")
    plt.close(fig)


def fig_rq3_correlation(df, outdir):
    cols = ["mean_complexity", "duplication_percent", "loc", "maintainability_index", "time_to_green_seconds"]
    labels = ["Complexidade", "Duplicação", "SLOC", "Manutenibilidade", "Tempo"]
    corr = df[cols].corr(method="spearman")
    fig, ax = plt.subplots(figsize=(6.5, 5.5))
    sns.heatmap(corr, annot=True, fmt=".2f", cmap="vlag", center=0, ax=ax,
                xticklabels=labels, yticklabels=labels, vmin=-1, vmax=1, square=True, cbar_kws={"label": "ρ de Spearman"})
    ax.set_title("RQ3 — Correlação entre métricas (12 trials, todos os tratamentos)")
    caption_note(fig, "Correlação de Spearman calculada sobre os 12 trials, sem separar por tratamento — descritiva, não causal.")
    fig.savefig(outdir / "rq3_correlacao_heatmap.png", bbox_inches="tight")
    plt.close(fig)


def fig_rq3_scatter_complexity_sloc(df, outdir):
    fig, ax = plt.subplots(figsize=(7, 5.5))
    for treatment_key, label in TREATMENT_LABELS.items():
        sub = df[df["treatment"] == treatment_key]
        for participant, marker in PARTICIPANT_MARKERS.items():
            p_sub = sub[sub["participant"] == participant]
            ax.scatter(p_sub["loc"], p_sub["mean_complexity"], color=PALETTE[label],
                       marker=marker, s=100, edgecolor="black", zorder=5)
        if len(sub) > 1:
            coef = np.polyfit(sub["loc"], sub["mean_complexity"], 1)
            xs = np.linspace(sub["loc"].min(), sub["loc"].max(), 20)
            ax.plot(xs, np.polyval(coef, xs), color=PALETTE[label], linestyle="--", label=f"Tendência {label}")
    handles = [plt.Line2D([0], [0], color=PALETTE["IA"], linestyle="--", label="Tendência IA"),
               plt.Line2D([0], [0], color=PALETTE["Manual"], linestyle="--", label="Tendência Manual")]
    handles += [plt.Line2D([0], [0], marker=m, color="black", linestyle="", label=p.capitalize())
                for p, m in PARTICIPANT_MARKERS.items()]
    ax.legend(handles=handles, fontsize=8.5, loc="upper left")
    ax.set_title("RQ3 — Complexidade ciclomática em função do tamanho do código")
    ax.set_xlabel("SLOC (linhas)")
    ax.set_ylabel("Complexidade ciclomática média")
    caption_note(fig, "Cor = tratamento; forma = participante. Sem ajuste causal — ilustra se soluções maiores tendem a ser mais complexas.")
    fig.savefig(outdir / "rq3_dispersao_complexidade_sloc.png", bbox_inches="tight")
    plt.close(fig)


def fig_rq3_by_kata(df, outdir, metric="loc", title="Tamanho do código (SLOC)", ylabel="linhas"):
    med = df.groupby(["kata", "treatment"])[metric].median().reset_index()
    katas = sorted(med["kata"].unique())
    fig, ax = plt.subplots(figsize=(7, 5))
    x = np.arange(len(katas))
    for treatment_key, label in TREATMENT_LABELS.items():
        sub = med[med["treatment"] == treatment_key].set_index("kata").reindex(katas)
        ax.plot(x, sub[metric], marker="o", markersize=10, linewidth=2, color=PALETTE[label], label=label)
    ax.set_xticks(x)
    ax.set_xticklabels(katas)
    ax.set_title(f"RQ3 — {title} por kata (mediana entre participantes)")
    ax.set_xlabel("Kata")
    ax.set_ylabel(ylabel)
    ax.legend(title="Tratamento")
    caption_note(fig, "Cada kata foi resolvido por participantes diferentes em IA e em Manual — compara dificuldade intrínseca do kata, não pareamento por pessoa.")
    fig.savefig(outdir / "rq3_por_kata_sloc.png", bbox_inches="tight")
    plt.close(fig)


def fig_rq3_sensitivity(df, outdir):
    participants = sorted(df["participant"].unique())
    metric = "mean_complexity"
    rows = []
    for excluded in participants:
        sub = df[df["participant"] != excluded]
        med = sub.groupby("treatment")[metric].median()
        rows.append({"excluded": excluded, "ia": med.get("ia"), "manual": med.get("manual")})
    sens = pd.DataFrame(rows)
    full_ia = df[df["treatment"] == "ia"][metric].median()
    full_manual = df[df["treatment"] == "manual"][metric].median()

    fig, ax = plt.subplots(figsize=(7, 5))
    y = np.arange(len(sens))
    ax.hlines(y, sens["manual"], sens["ia"], color="gray", linewidth=2, zorder=1)
    ax.scatter(sens["ia"], y, color=PALETTE["IA"], s=120, label="Mediana IA", zorder=3)
    ax.scatter(sens["manual"], y, color=PALETTE["Manual"], s=120, label="Mediana Manual", zorder=3)
    ax.axvline(full_ia, color=PALETTE["IA"], linestyle=":", linewidth=1, alpha=0.7)
    ax.axvline(full_manual, color=PALETTE["Manual"], linestyle=":", linewidth=1, alpha=0.7)
    ax.set_yticks(y)
    ax.set_yticklabels([f"sem {p.capitalize()}" for p in sens["excluded"]])
    ax.set_xlabel("Complexidade ciclomática média (mediana)")
    ax.set_title("RQ3 — Sensibilidade: mediana excluindo um participante por vez")
    ax.set_ylim(-0.6, len(sens) - 0.4)
    ax.legend(fontsize=9, loc="lower right")
    caption_note(fig, "Linhas pontilhadas verticais marcam a mediana com os 3 participantes (referência). Nenhuma exclusão muda o conjunto principal de conclusões.")
    fig.savefig(outdir / "rq3_sensibilidade.png", bbox_inches="tight")
    plt.close(fig)


def fig_rq3_radar(df, outdir):
    labels = [m[1].replace(" ", "\n") for m in RQ3_METRICS]
    ia_vals, manual_vals = [], []
    for metric, *_ in RQ3_METRICS:
        vals = df[metric]
        vmin, vmax = vals.min(), vals.max()
        norm = lambda v: 0.5 if vmax == vmin else (v - vmin) / (vmax - vmin)
        ia_vals.append(norm(df[df["treatment"] == "ia"][metric].median()))
        manual_vals.append(norm(df[df["treatment"] == "manual"][metric].median()))

    n = len(labels)
    angles = np.linspace(0, 2 * np.pi, n, endpoint=False).tolist()
    ia_vals += ia_vals[:1]
    manual_vals += manual_vals[:1]
    angles += angles[:1]

    fig, ax = plt.subplots(figsize=(6.5, 6.5), subplot_kw={"projection": "polar"})
    ax.plot(angles, ia_vals, color=PALETTE["IA"], linewidth=2, label="IA")
    ax.fill(angles, ia_vals, color=PALETTE["IA"], alpha=0.15)
    ax.plot(angles, manual_vals, color=PALETTE["Manual"], linewidth=2, label="Manual")
    ax.fill(angles, manual_vals, color=PALETTE["Manual"], alpha=0.15)
    ax.set_xticks(angles[:-1])
    ax.set_xticklabels(labels, fontsize=9)
    ax.set_yticklabels([])
    ax.set_title("RQ3 — Visão geral normalizada (medianas min-max por métrica)", pad=25)
    ax.legend(loc="upper right", bbox_to_anchor=(1.25, 1.1))
    caption_note(fig, "Eixos normalizados 0-1 pelo min-max de cada métrica nos 12 trials. Atenção: em Complexidade, Duplicação e SLOC, mais para fora "
                       "é geralmente indesejável; em Manutenibilidade, mais para fora é melhor. Não interprete a área do polígono como um escore único.")
    fig.savefig(outdir / "rq3_radar_normalizado.png", bbox_inches="tight")
    plt.close(fig)


# --------------------------------------------------------------------------
# Índice para o relatório
# --------------------------------------------------------------------------
def write_index(outdir: Path):
    entries = [
        ("rq1_boxplot_tempo.png", "RQ1 - Boxplot do tempo até ficar verde, por tratamento"),
        ("rq1_violino_tempo.png", "RQ1 - Distribuição (violino) do tempo por tratamento"),
        ("rq1_pareado_participante.png", "RQ1 - Mediana pareada por participante (IA -> Manual)"),
        ("rq1_efeito_ordem.png", "RQ1 - Tempo em função da ordem do trial na sessão"),
        ("rq2_taxa_sucesso.png", "RQ2 - Taxa de sucesso dos testes (efeito teto, com min/máx)"),
        ("rq2_esforco_prompts.png", "RQ2 - Nº de prompts vs. tempo, apenas trials de IA"),
        ("rq3_boxplot_complexidade.png", "RQ3 - Complexidade ciclomática média por tratamento"),
        ("rq3_boxplot_duplicacao.png", "RQ3 - Duplicação intra-arquivo por tratamento"),
        ("rq3_boxplot_sloc.png", "RQ3 - Tamanho do código (SLOC) por tratamento"),
        ("rq3_boxplot_manutenibilidade.png", "RQ3 - Índice de manutenibilidade por tratamento"),
        ("rq3_correlacao_heatmap.png", "RQ3 - Mapa de correlação (Spearman) entre métricas"),
        ("rq3_dispersao_complexidade_sloc.png", "RQ3 - Complexidade vs. SLOC, com tendência por tratamento"),
        ("rq3_por_kata_sloc.png", "RQ3 - SLOC mediano por kata e tratamento (dificuldade intrínseca)"),
        ("rq3_sensibilidade.png", "RQ3 - Sensibilidade da mediana ao excluir cada participante"),
        ("rq3_radar_normalizado.png", "RQ3 - Visão geral normalizada das 4 métricas (IA vs. Manual)"),
    ]
    lines = ["# Índice de gráficos — Lab02 Sprint 3", "", "| Arquivo | Descrição |", "|---|---|"]
    for fname, desc in entries:
        lines.append(f"| `{fname}` | {desc} |")
    (outdir / "README.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--trials", default="trials.csv")
    parser.add_argument("--analysis", default=None, help="Caminho para analysis.json (opcional; se omitido, recalcula os testes)")
    parser.add_argument("--output", default="output/graficos")
    args = parser.parse_args()

    df = load_trials(Path(args.trials))
    outdir = Path(args.output)
    outdir.mkdir(parents=True, exist_ok=True)

    tests = load_rq3_tests(Path(args.analysis) if args.analysis else None, df)

    fig_rq1_boxplot(df, outdir)
    fig_rq1_violin(df, outdir)
    fig_rq1_paired(df, outdir)
    fig_rq1_order_effect(df, outdir)

    fig_rq2_success_dotplot(df, outdir)
    fig_rq2_effort(df, outdir)

    for metric, title, ylabel in RQ3_METRICS:
        fig_rq3_metric_boxplot(df, outdir, metric, title, ylabel, tests)
    fig_rq3_correlation(df, outdir)
    fig_rq3_scatter_complexity_sloc(df, outdir)
    fig_rq3_by_kata(df, outdir)
    fig_rq3_sensitivity(df, outdir)
    fig_rq3_radar(df, outdir)

    write_index(outdir)
    print(f"{len(list(outdir.glob('*.png')))} gráficos gerados em: {outdir.resolve()}")
    print(f"Índice: {(outdir / 'README.md').resolve()}")


if __name__ == "__main__":
    main()