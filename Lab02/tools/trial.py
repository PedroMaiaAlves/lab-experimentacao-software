"""Inicia, verifica e finaliza trials do LAB02 sem fabricar medições."""

from __future__ import annotations

import argparse
import ast
import csv
import importlib.util
import io
import json
import shutil
import subprocess
import sys
import unittest
from datetime import datetime, timezone
from pathlib import Path
from types import ModuleType
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
PROTOCOL_PATH = ROOT / "protocol.json"
STATE_DIR = ROOT / "results" / ".state"
CSV_PATH = ROOT / "results" / "trials.csv"

RESULT_FIELDS = [
    "participant",
    "kata",
    "treatment",
    "order",
    "started_at",
    "ended_at",
    "duration_seconds",
    "time_to_green_seconds",
    "censored",
    "total_tests",
    "passed_tests",
    "failed_tests",
    "success_rate",
    "loc",
    "mean_complexity",
    "duplication_percent",
    "maintainability_index",
    "assistant",
    "assistant_plan",
    "assistant_model",
    "prompt_count",
    "commit_sha",
    "issue_number",
]


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def iso(moment: datetime) -> str:
    return moment.isoformat(timespec="seconds")


def load_protocol() -> dict[str, Any]:
    try:
        return json.loads(PROTOCOL_PATH.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise SystemExit(f"Protocolo não encontrado: {PROTOCOL_PATH}") from exc
    except json.JSONDecodeError as exc:
        raise SystemExit(f"Protocolo JSON inválido: {exc}") from exc


def assignment(protocol: dict[str, Any], participant: str, kata: str) -> dict[str, Any]:
    matches = [
        item
        for item in protocol.get("assignments", [])
        if item.get("participant") == participant and item.get("kata") == kata
    ]
    if len(matches) != 1:
        raise SystemExit(f"Combinação não prevista no protocolo: {participant}/{kata}")
    return matches[0]


def trial_paths(participant: str, kata: str) -> tuple[Path, Path, Path, Path]:
    kata_dir = ROOT / "katas" / kata
    solution = ROOT / "trials" / participant / kata / "solution.py"
    state = STATE_DIR / f"{participant}-{kata}.json"
    acceptance = kata_dir / "acceptance.py"
    return kata_dir, solution, state, acceptance


def load_module(path: Path, name: str) -> ModuleType:
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Não foi possível carregar {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def count_declared_tests(test_path: Path) -> int:
    tree = ast.parse(test_path.read_text(encoding="utf-8"))
    return sum(
        1
        for node in ast.walk(tree)
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        and node.name.startswith("test_")
    )


def run_tests(solution_path: Path, test_path: Path) -> dict[str, Any]:
    """Executa testes de aceitação e preserva falhas de carga como defeitos."""
    expected = count_declared_tests(test_path)
    module_name = f"acceptance_{solution_path.parent.parent.name}_{solution_path.parent.name}"
    sys.modules.pop("solution", None)
    sys.modules.pop(module_name, None)

    try:
        load_module(solution_path, "solution")
        acceptance_module = load_module(test_path, module_name)
        suite = unittest.defaultTestLoader.loadTestsFromModule(acceptance_module)
        stream = io.StringIO()
        result = unittest.TextTestRunner(stream=stream, verbosity=2).run(suite)
        failed = len(result.failures) + len(result.errors)
        total = result.testsRun
        return {
            "total": total,
            "failed": failed,
            "passed": max(total - failed, 0),
            "green": result.wasSuccessful() and total == expected,
            "output": stream.getvalue(),
        }
    except Exception as exc:  # o erro faz parte do resultado do participante
        return {
            "total": expected,
            "failed": expected,
            "passed": 0,
            "green": False,
            "output": f"Solução ou testes não puderam ser carregados: {type(exc).__name__}: {exc}\n",
        }
    finally:
        sys.modules.pop("solution", None)
        sys.modules.pop(module_name, None)


def collect_metrics(solution_path: Path) -> dict[str, Any]:
    metrics_path = ROOT / "tools" / "metrics.py"
    if not metrics_path.exists():
        return {
            "loc": "",
            "mean_complexity": "",
            "duplication_percent": "",
            "maintainability_index": "",
        }
    module = load_module(metrics_path, "lab02_metrics")
    values = module.collect(solution_path)
    return {
        "loc": values.get("loc", ""),
        "mean_complexity": values.get("mean_complexity", ""),
        "duplication_percent": values.get("duplication_percent", ""),
        "maintainability_index": values.get("maintainability_index", ""),
    }


def git_sha(reference: str = "HEAD") -> str:
    repository = ROOT.parent
    completed = subprocess.run(
        [
            "git",
            "-c",
            f"safe.directory={repository.as_posix()}",
            "rev-parse",
            "--short",
            reference,
        ],
        cwd=repository,
        capture_output=True,
        text=True,
        check=False,
    )
    if completed.returncode != 0:
        raise SystemExit(f"Não foi possível resolver o commit {reference}: {completed.stderr.strip()}")
    return completed.stdout.strip()


def _ensure_csv() -> None:
    CSV_PATH.parent.mkdir(parents=True, exist_ok=True)
    if not CSV_PATH.exists():
        with CSV_PATH.open("w", encoding="utf-8", newline="") as handle:
            csv.DictWriter(handle, fieldnames=RESULT_FIELDS).writeheader()
        return

    with CSV_PATH.open(encoding="utf-8", newline="") as handle:
        reader = csv.reader(handle)
        header = next(reader, [])
    if header != RESULT_FIELDS:
        raise SystemExit("Cabeçalho de results/trials.csv diverge do contrato documentado.")


def read_results() -> list[dict[str, str]]:
    _ensure_csv()
    with CSV_PATH.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def append_result(row: dict[str, Any]) -> None:
    existing = read_results()
    if any(
        item["participant"] == str(row["participant"])
        and item["kata"] == str(row["kata"])
        for item in existing
    ):
        raise SystemExit(
            f"Resultado já registrado para {row['participant']}/{row['kata']}."
        )

    with CSV_PATH.open("a", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=RESULT_FIELDS)
        writer.writerow({field: row.get(field, "") for field in RESULT_FIELDS})


def replace_results(rows: list[dict[str, str]]) -> None:
    _ensure_csv()
    temporary = CSV_PATH.with_suffix(".tmp")
    with temporary.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=RESULT_FIELDS)
        writer.writeheader()
        writer.writerows(rows)
    temporary.replace(CSV_PATH)


def _protocol_errors(protocol: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    participants = [item.get("id") for item in protocol.get("participants", [])]
    katas = [item.get("id") for item in protocol.get("katas", [])]
    assignments = protocol.get("assignments", [])

    if len(participants) != 3 or len(set(participants)) != 3:
        errors.append("o protocolo deve possuir 3 participantes únicos")
    if len(katas) != 4 or len(set(katas)) != 4:
        errors.append("o protocolo deve possuir 4 katas únicos")
    if protocol.get("timebox_seconds") != 2100:
        errors.append("o time-box deve ser 2100 segundos")
    if len(assignments) != 12:
        errors.append(f"esperadas 12 atribuições, encontradas {len(assignments)}")

    combinations = [(item.get("participant"), item.get("kata")) for item in assignments]
    if len(combinations) != len(set(combinations)):
        errors.append("há combinações participante/kata duplicadas")

    for item in assignments:
        if item.get("participant") not in participants:
            errors.append(f"participante desconhecido em atribuição: {item.get('participant')}")
        if item.get("kata") not in katas:
            errors.append(f"kata desconhecido em atribuição: {item.get('kata')}")
        if item.get("treatment") not in {"ia", "manual"}:
            errors.append(f"tratamento inválido: {item.get('treatment')}")

    for participant in participants:
        own = [item for item in assignments if item.get("participant") == participant]
        if len(own) != 4:
            errors.append(f"{participant}: esperado 4 trials, encontrado {len(own)}")
            continue
        if {item.get("order") for item in own} != {1, 2, 3, 4}:
            errors.append(f"{participant}: ordem deve conter 1, 2, 3 e 4")
        treatments = [item.get("treatment") for item in own]
        if treatments.count("ia") != 2 or treatments.count("manual") != 2:
            errors.append(f"{participant}: tratamentos não estão distribuídos em 2/2")

    if sum(item.get("treatment") == "ia" for item in assignments) != 6:
        errors.append("o protocolo deve possuir 6 trials com IA")
    if sum(item.get("treatment") == "manual" for item in assignments) != 6:
        errors.append("o protocolo deve possuir 6 trials manuais")

    for kata in katas:
        treatments = {
            item.get("treatment") for item in assignments if item.get("kata") == kata
        }
        if treatments != {"ia", "manual"}:
            errors.append(f"{kata}: deve aparecer nos dois tratamentos")
    return errors


def validate(_: argparse.Namespace | None = None) -> None:
    protocol = load_protocol()
    errors = _protocol_errors(protocol)

    for kata in protocol.get("katas", []):
        kata_dir = ROOT / "katas" / kata["id"]
        for filename in ("README.md", "stub.py", "acceptance.py"):
            if not (kata_dir / filename).exists():
                errors.append(f"arquivo ausente: {kata_dir / filename}")
        stub = kata_dir / "stub.py"
        acceptance = kata_dir / "acceptance.py"
        if stub.exists() and acceptance.exists():
            result = run_tests(stub, acceptance)
            if result["total"] != kata.get("expected_tests"):
                errors.append(
                    f"{kata['id']}: esperado {kata.get('expected_tests')} testes, "
                    f"encontrado {result['total']}"
                )
            if result["green"]:
                errors.append(f"{kata['id']}: o stub não deveria passar nos testes")

    if not (ROOT / "tools" / "metrics.py").exists():
        errors.append("arquivo ausente: Lab02/tools/metrics.py (handoff de Diogo)")

    pending_handoffs = (
        (ROOT / "requirements.txt", "handoff de Diogo"),
        (ROOT / "docs" / "ambiente.md", "handoff de Diogo"),
        (ROOT / "docs" / "catalogo_katas.md", "handoff de Lorran"),
        (ROOT / "tools" / "create_issues.py", "handoff de Lorran"),
    )
    for path, owner in pending_handoffs:
        if not path.exists():
            errors.append(f"arquivo ausente: {path.relative_to(ROOT)} ({owner})")

    try:
        _ensure_csv()
    except SystemExit as exc:
        errors.append(str(exc))

    if errors:
        raise SystemExit("Pacote experimental incompleto:\n- " + "\n- ".join(errors))
    print("Protocolo válido: 3 participantes, 12 trials, 6 IA e 6 manuais.")
    print("Quatro katas e ferramenta de métricas disponíveis; stubs falham como esperado.")


def start(args: argparse.Namespace) -> None:
    protocol = load_protocol()
    item = assignment(protocol, args.participant, args.kata)
    kata_dir, solution, state, _ = trial_paths(args.participant, args.kata)

    active = list(STATE_DIR.glob(f"{args.participant}-*.json")) if STATE_DIR.exists() else []
    if active:
        raise SystemExit(f"{args.participant} já possui um trial em andamento: {active[0].stem}")
    if state.exists():
        raise SystemExit("Já existe um trial em andamento para essa combinação.")
    if not (kata_dir / "stub.py").exists() or not (kata_dir / "acceptance.py").exists():
        raise SystemExit(f"Kata incompleto: {kata_dir}")
    if solution.exists() and not args.force:
        raise SystemExit(f"A solução já existe: {solution}. Use --force somente antes do trial.")

    assistant = protocol.get("assistant", {})
    if item["treatment"] == "ia" and not assistant.get("model_verified_at"):
        raise SystemExit(
            "Preencha assistant.model_verified_at em protocol.json após confirmar "
            "o mesmo modelo para os três participantes."
        )

    solution.parent.mkdir(parents=True, exist_ok=True)
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(kata_dir / "stub.py", solution)
    started_at = utc_now()
    state.write_text(
        json.dumps(
            {
                "participant": args.participant,
                "kata": args.kata,
                "treatment": item["treatment"],
                "order": item["order"],
                "started_at": iso(started_at),
                "issue_number": args.issue,
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )

    deadline = datetime.fromtimestamp(
        started_at.timestamp() + protocol["timebox_seconds"], tz=timezone.utc
    )
    print(f"TRIAL INICIADO: {args.participant} / {args.kata} / {item['treatment']}")
    print(f"Especificação: {kata_dir / 'README.md'}")
    print(f"Solução: {solution}")
    print(f"Início UTC: {iso(started_at)}")
    print(f"Deadline UTC: {iso(deadline)}")


def _finalize(
    protocol: dict[str, Any],
    item: dict[str, Any],
    state_data: dict[str, Any],
    solution: Path,
    state: Path,
    test_result: dict[str, Any],
    ended_at: datetime,
    prompts: int,
) -> None:
    started_at = datetime.fromisoformat(state_data["started_at"])
    elapsed = max(0.0, (ended_at - started_at).total_seconds())
    timebox = protocol["timebox_seconds"]
    green = bool(test_result["green"]) and elapsed <= timebox
    censored = not green
    duration = round(elapsed, 3) if green else timebox
    total = int(test_result["total"])
    passed = int(test_result["passed"])
    metrics = collect_metrics(solution)
    assistant = protocol.get("assistant", {})

    row: dict[str, Any] = {
        "participant": state_data["participant"],
        "kata": state_data["kata"],
        "treatment": item["treatment"],
        "order": item["order"],
        "started_at": state_data["started_at"],
        "ended_at": iso(ended_at),
        "duration_seconds": duration,
        "time_to_green_seconds": duration if green else "",
        "censored": str(censored).lower(),
        "total_tests": total,
        "passed_tests": passed,
        "failed_tests": int(test_result["failed"]),
        "success_rate": round((passed / total) * 100, 2) if total else 0.0,
        **metrics,
        "assistant": assistant.get("name", "") if item["treatment"] == "ia" else "",
        "assistant_plan": assistant.get("plan", "") if item["treatment"] == "ia" else "",
        "assistant_model": assistant.get("model", "") if item["treatment"] == "ia" else "",
        "prompt_count": prompts if item["treatment"] == "ia" else 0,
        "commit_sha": "PENDING",
        "issue_number": state_data["issue_number"],
    }
    append_result(row)
    state.unlink()
    status = "verde" if green else "censurado"
    print(f"TRIAL FINALIZADO: {status} em {duration}s")
    print(f"Resultado gravado em: {CSV_PATH}")
    print("Após o commit da solução, execute link-commit para registrar o hash.")


def conclude(args: argparse.Namespace, explicit_finish: bool) -> None:
    if args.prompts < 0:
        raise SystemExit("A quantidade de prompts não pode ser negativa.")

    protocol = load_protocol()
    item = assignment(protocol, args.participant, args.kata)
    _, solution, state, acceptance = trial_paths(args.participant, args.kata)
    if not state.exists():
        raise SystemExit("Nenhum trial em andamento. Execute start primeiro.")
    if not solution.exists():
        raise SystemExit(f"Solução do trial não encontrada: {solution}")

    state_data = json.loads(state.read_text(encoding="utf-8"))
    started_at = datetime.fromisoformat(state_data["started_at"])
    ended_at = utc_now()
    elapsed = max(0.0, (ended_at - started_at).total_seconds())
    test_result = run_tests(solution, acceptance)
    print(test_result["output"], end="")

    if test_result["green"] and elapsed <= protocol["timebox_seconds"]:
        _finalize(
            protocol, item, state_data, solution, state, test_result, ended_at, args.prompts
        )
        return
    if elapsed >= protocol["timebox_seconds"]:
        _finalize(
            protocol, item, state_data, solution, state, test_result, ended_at, args.prompts
        )
        return

    remaining = round(protocol["timebox_seconds"] - elapsed, 1)
    command = "finish" if explicit_finish else "check"
    raise SystemExit(
        f"Trial ainda vermelho; faltam {remaining}s. Continue e rode {command} novamente."
    )


def link_commit(args: argparse.Namespace) -> None:
    commit = git_sha(args.commit)
    rows = read_results()
    matches = [
        row
        for row in rows
        if row["participant"] == args.participant and row["kata"] == args.kata
    ]
    if len(matches) != 1:
        raise SystemExit(
            f"Esperado um resultado para {args.participant}/{args.kata}; encontrado {len(matches)}."
        )
    if matches[0]["commit_sha"] not in {"", "PENDING"} and not args.force:
        raise SystemExit("O resultado já possui commit. Use --force somente para corrigir evidência.")
    matches[0]["commit_sha"] = commit
    replace_results(rows)
    print(f"Commit {commit} vinculado a {args.participant}/{args.kata}.")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)

    validate_parser = commands.add_parser("validate", help="valida o pacote da Sprint 01")
    validate_parser.set_defaults(handler=validate)

    start_parser = commands.add_parser("start", help="inicia um trial")
    start_parser.add_argument("participant")
    start_parser.add_argument("kata")
    start_parser.add_argument("--issue", type=int, required=True)
    start_parser.add_argument("--force", action="store_true")
    start_parser.set_defaults(handler=start)

    for command, explicit in (("check", False), ("finish", True)):
        current = commands.add_parser(command)
        current.add_argument("participant")
        current.add_argument("kata")
        current.add_argument("--prompts", type=int, default=0)
        current.set_defaults(
            handler=lambda args, flag=explicit: conclude(args, explicit_finish=flag)
        )

    commit_parser = commands.add_parser("link-commit", help="vincula o commit da solução")
    commit_parser.add_argument("participant")
    commit_parser.add_argument("kata")
    commit_parser.add_argument("--commit", default="HEAD")
    commit_parser.add_argument("--force", action="store_true")
    commit_parser.set_defaults(handler=link_commit)
    return parser


def main() -> None:
    args = build_parser().parse_args()
    args.handler(args)


if __name__ == "__main__":
    main()
