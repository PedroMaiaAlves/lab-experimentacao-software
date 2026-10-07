"""Cria milestones, labels e as Issues do grupo a partir de scripts/issues.csv.

Pré-requisitos: GitHub CLI (gh) instalado e autenticado:
    gh auth login
    gh auth refresh -s project        # permissão para adicionar ao GitHub Projects

Uso (rode UMA vez; comece com --dry-run para conferir):
    python scripts/criar_issues.py --dry-run
    python scripts/criar_issues.py
"""
import argparse
import csv
import subprocess

REPO = "SEU-USUARIO/SEU-REPOSITORIO"          # AJUSTE
PROJETO = "Lab03 DORA"                         # título EXATO do GitHub Projects (AJUSTE)
USUARIOS = {"A": "usuario-github-a",           # AJUSTE: login do GitHub de cada integrante
            "B": "usuario-github-b",
            "C": "usuario-github-c"}
MILESTONES = {"S01": "Lab03S01", "S02": "Lab03S02", "S03": "Lab03S03", "FIN": "Entrega final"}
CORES_LABEL = {"Código": "1f6feb", "Teste": "2da44e", "Escrita": "bf8700",
               "Dados": "8250df", "Validação": "cf222e", "Infra": "6e7781"}


def gh(args, dry):
    print("$ gh " + " ".join(f'"{a}"' if " " in a else a for a in args)[:200])
    if not dry:
        subprocess.run(["gh", *args], check=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true", help="só mostra os comandos")
    dry = ap.parse_args().dry_run

    for titulo in MILESTONES.values():
        gh(["api", f"repos/{REPO}/milestones", "-f", f"title={titulo}"], dry)
    for nome, cor in CORES_LABEL.items():
        gh(["label", "create", nome, "--color", cor, "--repo", REPO, "--force"], dry)

    with open("scripts/issues.csv", newline="", encoding="utf-8-sig") as f:
        for linha in csv.DictReader(f):
            gh(["issue", "create", "--repo", REPO,
                "--title", f"[{linha['id']}] {linha['titulo']}",
                "--body", linha["descricao"],
                "--assignee", USUARIOS[linha["resp"]],
                "--label", linha["tipo"],
                "--milestone", MILESTONES[linha["sprint"]],
                "--project", PROJETO], dry)


if __name__ == "__main__":
    main()
