"""RQ3: análise descritiva, Wilcoxon exato e auditoria sem alterar os trials.

Execute no ambiente requirements-analysis.txt. As funções estatísticas e os
testes unitários usam apenas a biblioteca padrão. Não executa as soluções.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import importlib.metadata
import itertools
import json
import math
from pathlib import Path
import re
import statistics
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
METRICS = {
    "mean_complexity": ("Complexidade ciclomática média", "pontos"),
    "duplication_percent": ("Duplicação intrarquivo", "%"),
    "loc": ("Tamanho do código (SLOC)", "linhas"),
    "maintainability_index": ("Índice de manutenibilidade", "pontos (0–100)"),
}
PRIMARY = ("mean_complexity", "duplication_percent")
TREATMENTS = ("ia", "manual")
COLORS = {"ia": "#2878A0", "manual": "#C77731"}


def sha256(data):
    return hashlib.sha256(data).hexdigest()


def quantile(values, probability):
    """Interpolação linear, equivalente ao método inclusive/type 7."""
    values = sorted(values)
    if not values:
        return None
    index = (len(values) - 1) * probability
    lower, upper = math.floor(index), math.ceil(index)
    return values[lower] + (values[upper] - values[lower]) * (index - lower)


def describe(values):
    values = [v for v in values if v is not None]
    if not values:
        return dict(n=0, median=None, q1=None, q3=None, iqr=None)
    q1, q3 = quantile(values, .25), quantile(values, .75)
    return dict(n=len(values), median=statistics.median(values), q1=q1,
                q3=q3, iqr=q3 - q1)


def wilcoxon_two_sided(differences):
    """Distribuição exata por sinais, postos médios e zero_method='wilcox'.

    Diferenças arredondadas a oito casas antes do ranqueamento para evitar
    desempates artificiais de ponto flutuante. São no máximo três pares.
    """
    available = [round(d, 8) for d in differences if d is not None]
    nonzero = [d for d in available if d != 0]
    result = dict(n_pairs=len(available), n_effective=len(nonzero),
                  zero_differences=len(available) - len(nonzero),
                  statistic=None, w_plus=None, w_minus=None, p_value=None,
                  method="exact_sign_enumeration", alternative="two-sided")
    if not nonzero:
        result["status"] = "sem_diferencas_nao_nulas"
        return result
    absolute = sorted(abs(d) for d in nonzero)
    ranks = {}
    for value in set(absolute):
        positions = [i + 1 for i, x in enumerate(absolute) if x == value]
        ranks[value] = statistics.mean(positions)
    observed_ranks = [ranks[abs(d)] for d in nonzero]
    w_plus = sum(r for d, r in zip(nonzero, observed_ranks) if d > 0)
    total = sum(observed_ranks)
    observed = min(w_plus, total - w_plus)
    extreme = 0
    for signs in itertools.product((0, 1), repeat=len(nonzero)):
        positive = sum(r * sign for r, sign in zip(observed_ranks, signs))
        if min(positive, total - positive) <= observed:
            extreme += 1
    result.update(statistic=observed, w_plus=w_plus, w_minus=total - w_plus,
                  p_value=extreme / (2 ** len(nonzero)), status="calculado")
    return result


def holm(pvalues):
    """Família fixa de hipóteses. Testes indisponíveis permanecem nulos."""
    adjusted = {key: None for key in pvalues}
    ordered = sorted((p, key) for key, p in pvalues.items() if p is not None)
    maximum = 0.0
    for index, (p, key) in enumerate(ordered):
        maximum = max(maximum, (len(pvalues) - index) * p)
        adjusted[key] = min(1.0, maximum)
    return adjusted


def _number(value, name, integer=False, optional=False):
    if optional and value in (None, ""):
        return None
    try:
        result = float(value)
    except (TypeError, ValueError):
        raise ValueError(f"Valor inválido em {name}: {value!r}") from None
    if not math.isfinite(result) or result < 0 or (integer and not result.is_integer()):
        raise ValueError(f"Valor inválido em {name}: {value!r}")
    return int(result) if integer else result


def read_trials(trials_path, protocol_path):
    protocol = json.loads(Path(protocol_path).read_text(encoding="utf-8"))
    assignments = protocol["assignments"]
    expected = {(x["participant"], x["kata"]): x for x in assignments}
    participants = [x["id"] for x in protocol["participants"]]
    if len(participants) != 3 or len(expected) != 12 or len(assignments) != 12:
        raise ValueError("Esperados três participantes e 12 atribuições únicas.")
    for participant in participants:
        for treatment in TREATMENTS:
            if sum(x["participant"] == participant and x["treatment"] == treatment
                   for x in assignments) != 2:
                raise ValueError("Protocolo deve ter dois trials por tratamento e participante.")
    tests = {k["id"]: k["expected_tests"] for k in protocol["katas"]}
    with Path(trials_path).open(encoding="utf-8-sig", newline="") as stream:
        rows = list(csv.DictReader(stream))
    seen = set()
    required = {"participant", "kata", "treatment", "order", "commit_sha",
                "issue_number", "duration_seconds", "time_to_green_seconds",
                "censored", "total_tests", "passed_tests", "failed_tests",
                "success_rate", *METRICS}
    for row in rows:
        if not required.issubset(row):
            raise ValueError("CSV sem todas as colunas necessárias.")
        key = row["participant"], row["kata"]
        if key in seen or key not in expected:
            raise ValueError(f"Combinação duplicada ou desconhecida: {key}")
        seen.add(key)
        if row["treatment"] != expected[key]["treatment"]:
            raise ValueError(f"Tratamento divergente do protocolo: {key}")
        for field in ("order", "total_tests", "passed_tests", "failed_tests", "issue_number"):
            row[field] = _number(row[field], field, integer=True)
        if row["order"] != expected[key]["order"]:
            raise ValueError(f"Ordem divergente: {key}")
        if (row["total_tests"] != tests[key[1]] or
                row["passed_tests"] + row["failed_tests"] != row["total_tests"]):
            raise ValueError(f"Contagens de testes inconsistentes: {key}")
        row["success_rate"] = _number(row["success_rate"], "success_rate")
        if not math.isclose(row["success_rate"], 100 * row["passed_tests"] / row["total_tests"], abs_tol=.01):
            raise ValueError(f"Taxa de sucesso inconsistente: {key}")
        for field in METRICS:
            row[field] = _number(row[field], field, integer=field == "loc", optional=True)
            if field in ("duplication_percent", "maintainability_index") and row[field] is not None and row[field] > 100:
                raise ValueError(f"Métrica fora da escala: {key}/{field}")
        row["duration_seconds"] = _number(row["duration_seconds"], "duration_seconds")
        row["time_to_green_seconds"] = _number(row["time_to_green_seconds"], "time_to_green_seconds", optional=True)
        if row["censored"].lower() not in ("true", "false"):
            raise ValueError(f"Censura inválida: {key}")
        row["censored"] = row["censored"].lower() == "true"
        limit = protocol["timebox_seconds"]
        if row["duration_seconds"] > limit:
            raise ValueError(f"Duração acima do limite: {key}")
        if row["censored"] and (row["duration_seconds"] != limit or row["time_to_green_seconds"] is not None):
            raise ValueError(f"Registro censurado inconsistente: {key}")
        if not re.fullmatch(r"[0-9a-fA-F]{7,40}", row["commit_sha"]):
            raise ValueError(f"Commit ausente ou inválido: {key}")
    if seen != set(expected):
        raise ValueError("CSV não cobre as 12 atribuições do protocolo.")
    return sorted(rows, key=lambda r: (participants.index(r["participant"]), r["order"])), protocol


def git(repository, *args):
    result = subprocess.run(["git", "-c", f"safe.directory={repository.as_posix()}",
                             *args], cwd=repository, capture_output=True, check=False)
    if result.returncode:
        raise ValueError(result.stderr.decode("utf-8", errors="replace").strip())
    return result.stdout


def audit_sources(rows, repository):
    try:
        from .metrics import collect
    except ImportError:
        from metrics import collect
    records = []
    for row in rows:
        relative = f"Lab02/trials/{row['participant']}/{row['kata']}/solution.py"
        record = dict(participant=row["participant"], kata=row["kata"],
                      recorded_commit=row["commit_sha"], path=relative,
                      status="ok", differences=[])
        try:
            record["full_commit"] = git(repository, "rev-parse", f"{row['commit_sha']}^{{commit}}").decode().strip()
            source = git(repository, "show", f"{record['full_commit']}:{relative}")
            record["source_sha256"] = sha256(source)
            with tempfile.TemporaryDirectory(prefix="lab02-rq3-audit-") as temporary:
                saved = Path(temporary) / "solution.py"
                saved.write_bytes(source)
                measured = collect(str(saved))
            record["recomputed"] = measured
            for field in METRICS:
                original, calculated = row[field], measured[field]
                equal = (original is None and calculated is None) or (
                    original is not None and calculated is not None and
                    math.isclose(original, calculated, abs_tol=.005, rel_tol=0))
                if not equal:
                    record["differences"].append(dict(metric=field, recorded=original, recomputed=calculated))
            if record["differences"]:
                record["status"] = "divergent"
        except (ValueError, OSError, UnicodeError) as error:
            record.update(status="unavailable", error=str(error))
        records.append(record)
    return records


def summaries(rows, grouping):
    keys = sorted({tuple(row[column] for column in grouping) for row in rows})
    output = []
    for key in keys:
        group = [row for row in rows if tuple(row[column] for column in grouping) == key]
        for metric in METRICS:
            output.append(dict(zip(grouping, key)) | dict(metric=metric, **describe([r[metric] for r in group])))
    return output


def paired_results(rows, participants):
    pairs = []
    for metric in METRICS:
        for person in participants:
            conditions = {t: [r[metric] for r in rows if r["participant"] == person and r["treatment"] == t]
                          for t in TREATMENTS}
            complete = all(len(v) == 2 and all(x is not None for x in v) for v in conditions.values())
            pair = dict(participant=person, metric=metric, complete=complete)
            for treatment, values in conditions.items():
                pair[treatment] = statistics.median(values) if len(values) == 2 and all(x is not None for x in values) else None
            pair["difference_ia_minus_manual"] = round(pair["ia"] - pair["manual"], 8) if complete else None
            pairs.append(pair)
    tests = {}
    for metric in PRIMARY:
        differences = [r["difference_ia_minus_manual"] for r in pairs if r["metric"] == metric]
        tests[metric] = wilcoxon_two_sided(differences)
        tests[metric]["median_difference"] = describe(differences)["median"]
    corrected = holm({metric: tests[metric]["p_value"] for metric in PRIMARY})
    for metric in PRIMARY:
        tests[metric]["p_holm"] = corrected[metric]
        tests[metric]["reject_at_05"] = corrected[metric] < .05 if corrected[metric] is not None else None
    return pairs, tests


def analyze(rows, protocol):
    participants = [p["id"] for p in protocol["participants"]]
    pairs, tests = paired_results(rows, participants)
    sensitivity = []
    for person in participants:
        subset = [r for r in rows if r["participant"] != person]
        _, reduced_tests = paired_results(subset, [p for p in participants if p != person])
        sensitivity.append(dict(excluded_participant=person, summaries=summaries(subset, ["treatment"]), tests=reduced_tests))
    outliers = []
    for treatment in TREATMENTS:
        for metric in METRICS:
            group = [r for r in rows if r["treatment"] == treatment]
            stats = describe([r[metric] for r in group])
            if stats["n"]:
                lower, upper = stats["q1"] - 1.5 * stats["iqr"], stats["q3"] + 1.5 * stats["iqr"]
                for row in group:
                    if row[metric] is not None and not lower <= row[metric] <= upper:
                        outliers.append(dict(participant=row["participant"], kata=row["kata"], treatment=treatment,
                                             metric=metric, value=row[metric], lower=lower, upper=upper, retained=True))
    return dict(summary_by_treatment=summaries(rows, ["treatment"]),
                summary_by_participant=summaries(rows, ["participant", "treatment"]),
                summary_by_kata=summaries(rows, ["kata", "treatment"]),
                paired=pairs, tests=tests, sensitivity=sensitivity, outliers=outliers)


def draw_figures(rows, analysis, output):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import numpy as np
    import pandas as pd
    import seaborn as sns
    frame = pd.DataFrame(rows)
    sns.set_theme(style="whitegrid", font="DejaVu Sans", font_scale=.95)
    fig, axes = plt.subplots(2, 2, figsize=(10, 7))
    rng = np.random.default_rng(42)
    markers = {"pedro": "o", "diogo": "s", "lorran": "^"}
    for axis, metric in zip(axes.flat, METRICS):
        sns.boxplot(data=frame, x="treatment", y=metric, order=TREATMENTS,
                    color="#DCE5EA", showfliers=False, width=.45, ax=axis)
        for i, treatment in enumerate(TREATMENTS):
            for row in rows:
                if row["treatment"] == treatment and row[metric] is not None:
                    axis.scatter(i + rng.uniform(-.1, .1), row[metric], color=COLORS[treatment],
                                 marker=markers[row["participant"]], s=45, zorder=3)
        axis.set(title=METRICS[metric][0], xlabel="", ylabel=METRICS[metric][1])
        axis.set_xticks([0, 1], ["IA", "Manual"])
    fig.suptitle("RQ3 — Distribuições e valores dos 12 trials", fontsize=15)
    fig.text(.5, .012, "Cada ponto é um trial. Círculo: Pedro; quadrado: Diogo; triângulo: Lorran. Todos os valores foram mantidos.", ha="center", fontsize=9)
    fig.tight_layout(rect=(0, .04, 1, .95))
    fig.savefig(output / "rq3_distribuicoes.png", dpi=180)
    plt.close(fig)
    fig, axes = plt.subplots(1, 2, figsize=(10, 4))
    for axis, metric in zip(axes, PRIMARY):
        for record in analysis["paired"]:
            if record["metric"] == metric and record["complete"]:
                axis.plot([0, 1], [record["ia"], record["manual"]], marker=markers[record["participant"]], label=record["participant"].title())
        axis.set_xticks([0, 1], ["IA", "Manual"])
        axis.set(title=METRICS[metric][0], ylabel=METRICS[metric][1])
        axis.legend(fontsize=8)
    fig.suptitle("RQ3 — Medianas dos dois trials por condição e participante")
    fig.tight_layout(rect=(0, 0, 1, .92))
    fig.savefig(output / "rq3_pareados.png", dpi=180)
    plt.close(fig)
    fig, axes = plt.subplots(1, 2, figsize=(10, 4))
    for axis, metric in zip(axes, PRIMARY):
        for row in rows:
            if row[metric] is not None and row["loc"] is not None:
                axis.scatter(row["loc"], row[metric], color=COLORS[row["treatment"]], marker=markers[row["participant"]], s=50)
        axis.margins(.15)
        axis.set(title=METRICS[metric][0], xlabel="SLOC (linhas)", ylabel=METRICS[metric][1])
    fig.suptitle("RQ3 — Métricas em relação ao tamanho do código")
    fig.text(.5, .01, "Azul: IA; laranja: Manual. Círculo: Pedro; quadrado: Diogo; triângulo: Lorran. Sem ajuste causal por LOC.", ha="center", fontsize=9)
    fig.tight_layout(rect=(0, .05, 1, .92))
    fig.savefig(output / "rq3_loc.png", dpi=180)
    plt.close(fig)


def interpretation(analysis, audit, warnings):
    text = ["# RQ3 — Estrutura do código", "", "Fonte: trials preservados; comparação exploratória em três participantes.", "",
            "| Métrica | Tratamento | n | Mediana | Q1 | Q3 | IQR |", "|---|---|---:|---:|---:|---:|---:|"]
    def fmt(value):
        return "n.d." if value is None else f"{value:.3f}"
    for row in analysis["summary_by_treatment"]:
        text.append("| " + " | ".join([METRICS[row["metric"]][0], row["treatment"], str(row["n"]), *[fmt(row[k]) for k in ("median", "q1", "q3", "iqr")]]) + " |")
    text += ["", "## Inferência pareada", "", "Um par por participante, usando a mediana dos dois trials de cada condição. Diferença IA − Manual. Wilcoxon bilateral exato; diferenças zero removidas, empates com postos médios. Holm em uma família de duas hipóteses, alfa 0,05.", ""]
    for metric, test in analysis["tests"].items():
        text.append(f"- {METRICS[metric][0]}: W={fmt(test['statistic'])}; pares efetivos={test['n_effective']}; p={fmt(test['p_value'])}; p de Holm={fmt(test['p_holm'])}; diferença pareada mediana={fmt(test['median_difference'])}.")
    text += ["", "Não há rejeição das hipóteses nulas no nível adotado quando os valores ajustados são maiores que 0,05. Isso não demonstra equivalência nem ausência de efeito. Com três pares, a inferência tem poder muito baixo. Se todas as diferenças são zero, o teste fica indisponível.", "",
             "## Interpretação e LOC", "", "A mediana global por tratamento e a mediana das diferenças individuais respondem a perguntas distintas. Comparar os katas e os tamanhos evita atribuir automaticamente à IA diferenças de dificuldade ou verbosidade. O gráfico de LOC é descritivo, não uma regressão nem evidência de controle causal.", "",
             "A duplicação mede blocos literais de pelo menos três linhas significativas normalizadas dentro de cada arquivo. Não mede similaridade entre participantes e não é fornecida pelo Radon. O índice de manutenibilidade é complementar, não uma medida absoluta de qualidade.", "",
             "## Sensibilidade e auditoria", "", "sensitivity.csv repete os resumos excluindo cada participante por vez. Os testes desses cenários estão no JSON. Nenhuma exclusão modifica o conjunto principal. Valores além de 1,5 IQR são apenas sinalizados em outliers.csv e permanecem na análise.", "",
             f"Auditoria: {sum(a['status'] == 'ok' for a in audit)}/{len(audit)} soluções com métricas reproduzidas a partir dos commits."]
    if any(a["status"] != "ok" for a in audit):
        text.append("ATENÇÃO: há divergências na auditoria; os resultados usam os valores registrados e não estão liberados para conclusões finais até revisão.")
    text += ["", "## Ressalvas", ""] + ["- " + w for w in warnings]
    text += ["", "## Referências", "", "- Radon: https://radon.readthedocs.io/en/latest/intro.html", "- Wilcoxon: https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.wilcoxon.html", ""]
    return "\n".join(text)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--trials", type=Path, default=ROOT / "results/trials.csv")
    parser.add_argument("--protocol", type=Path, default=ROOT / "protocol.json")
    parser.add_argument("--output", type=Path, default=ROOT / "results/rq3")
    args = parser.parse_args()
    rows, protocol = read_trials(args.trials, args.protocol)
    analysis = analyze(rows, protocol)
    repository = ROOT.parent
    audit = audit_sources(rows, repository)
    warnings = ["Somente três participantes; pareamento controla participante, mas não a dificuldade dos diferentes katas.",
                "README registra início dos trials sem a baseline congelada prevista.",
                "As confirmações individuais de ambiente não estão todas documentadas."]
    for row in rows:
        if row["issue_number"] == 0:
            warnings.append(f"{row['participant']}/{row['kata']}: issue_number=0 no CSV original.")
        for metric in METRICS:
            if row[metric] is None:
                warnings.append(f"{row['participant']}/{row['kata']}: {metric} indisponível; não imputado.")
    analysis["audit"] = audit
    analysis["warnings"] = warnings
    analysis["release_status"] = "audited" if all(a["status"] == "ok" for a in audit) else "needs_review"
    analysis["provenance"] = {
        "schema_version": 1, "repository_commit": git(repository, "rev-parse", "HEAD").decode().strip(),
        "trials_sha256": sha256(args.trials.read_bytes()), "protocol_sha256": sha256(args.protocol.read_bytes()),
        "metrics_script_sha256": sha256((ROOT / "tools/metrics.py").read_bytes()),
        "analysis_script_sha256": sha256(Path(__file__).read_bytes()),
        "python": sys.version.split()[0],
        "packages": {name: importlib.metadata.version(name) for name in ("radon", "pandas", "numpy", "matplotlib", "seaborn")},
        "quantiles": "linear/type7", "alpha": .05, "difference": "IA - Manual",
        "source_policy": "CSV preservado; auditoria sobre git show commit:path, sem executar soluções",
    }
    import pandas as pd
    args.output.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(rows).to_csv(args.output / "individual.csv", index=False, lineterminator="\n")
    for key, filename in (("summary_by_treatment", "summary.csv"), ("summary_by_participant", "by_participant.csv"),
                          ("summary_by_kata", "by_kata.csv"), ("paired", "paired.csv")):
        pd.DataFrame(analysis[key]).to_csv(args.output / filename, index=False, lineterminator="\n")
    sensitivity = [dict(excluded_participant=s["excluded_participant"], **r) for s in analysis["sensitivity"] for r in s["summaries"]]
    pd.DataFrame(sensitivity).to_csv(args.output / "sensitivity.csv", index=False, lineterminator="\n")
    pd.DataFrame(analysis["outliers"], columns=["participant", "kata", "treatment", "metric", "value", "lower", "upper", "retained"]).to_csv(args.output / "outliers.csv", index=False, lineterminator="\n")
    (args.output / "analysis.json").write_text(json.dumps(analysis, ensure_ascii=False, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    (args.output / "interpretacao.md").write_text(interpretation(analysis, audit, warnings), encoding="utf-8")
    draw_figures(rows, analysis, args.output)
    print(json.dumps(dict(status=analysis["release_status"], trials=len(rows), audited=sum(a["status"] == "ok" for a in audit), tests=analysis["tests"]), ensure_ascii=False, indent=2))
    return 0 if analysis["release_status"] == "audited" else 2


if __name__ == "__main__":
    raise SystemExit(main())
