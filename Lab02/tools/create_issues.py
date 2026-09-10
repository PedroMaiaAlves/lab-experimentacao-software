"""Gera as Issues dos trials da Sprint 02 sem publicá-las por padrão."""

from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path
from typing import Any, Sequence


ROOT = Path(__file__).resolve().parents[1]
PROTOCOL_PATH = ROOT / "protocol.json"


def load_protocol(path: str | Path = PROTOCOL_PATH) -> dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def build_issues(protocol: dict[str, Any]) -> list[dict[str, str]]:
    participants = {item["id"]: item for item in protocol.get("participants", [])}
    katas = {item["id"]: item for item in protocol.get("katas", [])}
    assignments = protocol.get("assignments", [])
    if len(assignments) != 12:
        raise ValueError(f"O protocolo deve conter 12 atribuições, não {len(assignments)}.")

    issues = []
    for item in assignments:
        try:
            participant = participants[item["participant"]]
            kata = katas[item["kata"]]
        except KeyError as exc:
            raise ValueError(f"Atribuição referencia identificador desconhecido: {exc.args[0]}") from exc

        treatment = item.get("treatment")
        if treatment not in {"ia", "manual"}:
            raise ValueError(f"Tratamento inválido: {treatment}")
        treatment_label = "IA" if treatment == "ia" else "Manual"
        order = item.get("order")
        title = (
            f"[Lab02S02][{participant['name']}][{order:02d}] "
            f"{kata['name']} — {treatment_label}"
        )
        body = f"""## Objetivo

Executar o trial de {kata['name']} no tratamento {treatment_label}, seguindo o protocolo congelado do LAB02.

## Configuração

- Participante: {participant['name']} (`{participant['id']}`)
- Kata: {kata['name']} (`{kata['id']}`)
- Tratamento: {treatment_label}
- Ordem do participante: {order}
- Time-box: {protocol['timebox_seconds']} segundos

## Critérios de aceite

- [ ] Branch criada diretamente do baseline congelado
- [ ] Recursos permitidos e tratamento conferidos antes do início
- [ ] Trial encerrado no primeiro verde ou ao atingir o time-box
- [ ] Resultado preservado, inclusive se censurado
- [ ] Commit da solução vinculado pela ferramenta de trials
- [ ] Evidências e URLs consultadas registradas nesta Issue

## Evidências

- Branch:
- Commit:
- Início UTC:
- Fim UTC:
- URLs consultadas:
- Observações:
"""
        issues.append({"title": title, "body": body, "assignee": participant["github"]})

    titles = [issue["title"] for issue in issues]
    if len(titles) != len(set(titles)):
        raise ValueError("O protocolo gerou títulos de Issue duplicados.")
    return issues


def print_preview(issues: list[dict[str, str]]) -> None:
    for issue in issues:
        print(f"[PRÉVIA] {issue['title']}")
        print(f"Responsável: {issue['assignee']}")
        print(issue["body"].rstrip())
        print("---")
    print(f"Prévia concluída: {len(issues)} Issues; nada foi publicado.")


def existing_titles(repository: str | None = None) -> set[str]:
    command = ["gh", "issue", "list", "--state", "all", "--limit", "500", "--json", "title"]
    if repository:
        command.extend(["--repo", repository])
    completed = subprocess.run(command, capture_output=True, text=True, check=True)
    return {item["title"] for item in json.loads(completed.stdout)}


def publish_issues(
    issues: list[dict[str, str]],
    repository: str | None = None,
    project: str | None = None,
) -> None:
    published = 0
    skipped = 0
    known_titles = existing_titles(repository)
    for issue in issues:
        if issue["title"] in known_titles:
            print(f"Ignorada por título existente: {issue['title']}")
            skipped += 1
            continue

        command = [
            "gh",
            "issue",
            "create",
            "--title",
            issue["title"],
            "--body",
            issue["body"],
            "--assignee",
            issue["assignee"],
        ]
        if repository:
            command.extend(["--repo", repository])
        if project:
            command.extend(["--project", project])
        subprocess.run(command, check=True)
        known_titles.add(issue["title"])
        published += 1
    print(f"Publicação concluída: {published} criadas, {skipped} ignoradas.")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--protocol", default=str(PROTOCOL_PATH))
    parser.add_argument("--repo", help="repositório OWNER/REPO usado com --apply")
    parser.add_argument("--project", help="Project ao qual adicionar as Issues com --apply")
    parser.add_argument("--apply", action="store_true", help="publica as Issues no GitHub")
    return parser


def main(argv: Sequence[str] | None = None) -> None:
    args = build_parser().parse_args(argv)
    issues = build_issues(load_protocol(args.protocol))
    if args.apply:
        publish_issues(issues, args.repo, args.project)
    else:
        print_preview(issues)


if __name__ == "__main__":
    main()
