"""Analisa tempo e sucesso dos trials do LAB02 por participante."""

import csv
import json
from itertools import product
from math import isfinite
from pathlib import Path
from statistics import median, quantiles


ROOT = Path(__file__).resolve().parents[1]


def read_trials(csv_path=ROOT / "results" / "trials.csv", protocol_path=ROOT / "protocol.json"):
    protocol = json.loads(Path(protocol_path).read_text(encoding="utf-8"))
    expected = {(item["participant"], item["kata"]): item for item in protocol["assignments"]}
    expected_tests = {item["id"]: item["expected_tests"] for item in protocol["katas"]}
    with Path(csv_path).open(encoding="utf-8", newline="") as source:
        rows = list(csv.DictReader(source))

    if len(rows) != len(expected):
        raise ValueError(f"Esperados {len(expected)} trials, encontrados {len(rows)}.")

    seen = set()
    for row in rows:
        key = row["participant"], row["kata"]
        if key in seen or key not in expected:
            raise ValueError(f"Trial duplicado ou não previsto: {key}.")
        seen.add(key)
        assignment = expected[key]
        if row["treatment"] != assignment["treatment"] or int(row["order"]) != assignment["order"]:
            raise ValueError(f"Tratamento ou ordem diverge do protocolo: {key}.")

        if row["censored"].lower() not in {"true", "false"}:
            raise ValueError(f"Indicador de censura inválido: {key}.")
        row["censored"] = row["censored"].lower() == "true"
        row["time"] = float(row["time_to_green_seconds"]) if row["time_to_green_seconds"] else None
        row["duration"] = float(row["duration_seconds"])
        row["rate"] = float(row["success_rate"])
        total, passed, failed = (int(row[field]) for field in ("total_tests", "passed_tests", "failed_tests"))
        if not all(isfinite(value) for value in (row["duration"], row["rate"])):
            raise ValueError(f"Métrica não finita: {key}.")
        if row["duration"] < 0 or total != expected_tests[key[1]] or passed + failed != total:
            raise ValueError(f"Contagem de testes ou taxa inconsistente: {key}.")
        if not 0 <= passed <= total or not 0 <= row["rate"] <= 100 or abs(row["rate"] - 100 * passed / total) > 0.01:
            raise ValueError(f"Contagem de testes ou taxa inconsistente: {key}.")
        if row["censored"]:
            if row["time"] is not None or row["duration"] != protocol["timebox_seconds"]:
                raise ValueError(f"Censura inconsistente: {key}.")
        elif row["time"] is None or not isfinite(row["time"]) or not 0 <= row["time"] <= protocol["timebox_seconds"] or row["time"] != row["duration"]:
            raise ValueError(f"Time-to-Green inconsistente: {key}.")

    if seen != set(expected):
        raise ValueError("O CSV não cobre todas as atribuições do protocolo.")
    return rows, protocol


def describe(values):
    q1, _, q3 = quantiles(values, n=4, method="inclusive")
    return {"median": median(values), "q1": q1, "q3": q3, "iqr": q3 - q1}


def wilcoxon_greater(differences):
    nonzero = [value for value in differences if value != 0]
    if not nonzero:
        return None

    indexed = sorted(enumerate(nonzero), key=lambda item: abs(item[1]))
    ranks = [0.0] * len(nonzero)
    start = 0
    while start < len(indexed):
        end = start + 1
        while end < len(indexed) and abs(indexed[end][1]) == abs(indexed[start][1]):
            end += 1
        for original_index, _ in indexed[start:end]:
            ranks[original_index] = (start + 1 + end) / 2
        start = end

    observed = sum(rank for rank, value in zip(ranks, nonzero) if value > 0)
    extreme = sum(
        sum(rank for rank, positive in zip(ranks, signs) if positive) >= observed
        for signs in product((False, True), repeat=len(ranks))
    )
    return {"n": len(ranks), "w_plus": observed, "p_one_sided": extreme / 2 ** len(ranks)}


def analyze(rows, protocol):
    if any(row["censored"] for row in rows):
        raise ValueError("Há trials censurados; o Wilcoxon sobre Time-to-Green não é adequado sem tratar a censura.")

    participants = [item["id"] for item in protocol["participants"]]
    pairs = {}
    for participant in participants:
        own = [row for row in rows if row["participant"] == participant]
        pairs[participant] = {}
        for treatment in ("ia", "manual"):
            selected = [row for row in own if row["treatment"] == treatment]
            if len(selected) != 2:
                raise ValueError(f"{participant}: esperados dois trials por tratamento.")
            pairs[participant][treatment] = {
                "time": median(row["time"] for row in selected),
                "rate": median(row["rate"] for row in selected),
            }

    time_differences = [pairs[name]["manual"]["time"] - pairs[name]["ia"]["time"] for name in participants]
    rate_differences = [pairs[name]["ia"]["rate"] - pairs[name]["manual"]["rate"] for name in participants]
    return {
        "trials": len(rows),
        "participants": len(participants),
        "rq1": {
            "ia_seconds": describe([row["time"] for row in rows if row["treatment"] == "ia"]),
            "manual_seconds": describe([row["time"] for row in rows if row["treatment"] == "manual"]),
            "paired_manual_minus_ia_seconds": dict(zip(participants, time_differences)),
            "median_paired_difference_seconds": median(time_differences),
            "wilcoxon": wilcoxon_greater(time_differences),
        },
        "rq2": {
            "ia_percent": describe([row["rate"] for row in rows if row["treatment"] == "ia"]),
            "manual_percent": describe([row["rate"] for row in rows if row["treatment"] == "manual"]),
            "paired_ia_minus_manual_points": dict(zip(participants, rate_differences)),
            "wilcoxon": wilcoxon_greater(rate_differences),
        },
    }


def main():
    rows, protocol = read_trials()
    print(json.dumps(analyze(rows, protocol), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
