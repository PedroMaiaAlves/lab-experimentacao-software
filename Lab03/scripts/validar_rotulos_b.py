"""Valida formato, completude e revisão da rotulagem do integrante B."""
from __future__ import annotations

import argparse
import csv
from collections import Counter, defaultdict
from collections.abc import Iterable, Mapping
from pathlib import Path

import pandas as pd

CAMPOS_OBRIGATORIOS = (
    "full_name",
    "release_id",
    "tipo_projeto",
    "releases_sao_entregas",
    "corretiva",
)
CAMPOS_REVISAO = ("revisado_por", "revisao_confirmada")
VALORES_PERMITIDOS = {
    "tipo_projeto": {
        "biblioteca/framework", "aplicação/serviço", "ferramenta CLI", "outro"
    },
    "releases_sao_entregas": {"sim", "não", "incerto"},
    "corretiva": {"sim", "não"},
}


def validar_rotulos(
    linhas: Iterable[Mapping[str, str]],
    total_repositorios: int = 60,
    releases_por_repositorio: int = 5,
    exigir_revisao: bool = False,
) -> dict[str, int]:
    """Falha diante de rótulos incompletos, inválidos, duplicados ou inconsistentes."""
    registros = list(linhas)
    erros: list[str] = []
    esperadas = total_repositorios * releases_por_repositorio
    if len(registros) != esperadas:
        erros.append(f"esperadas {esperadas} linhas; encontradas {len(registros)}")

    chaves = []
    por_repo: dict[str, list[Mapping[str, str]]] = defaultdict(list)
    for numero, linha in enumerate(registros, start=2):
        campos_exigidos = CAMPOS_OBRIGATORIOS + (CAMPOS_REVISAO if exigir_revisao else ())
        ausentes = [campo for campo in campos_exigidos if campo not in linha]
        if ausentes:
            erros.append(f"linha {numero}: colunas ausentes: {', '.join(ausentes)}")
            continue
        vazios = [campo for campo in campos_exigidos
                  if not str(linha.get(campo, "")).strip()]
        if vazios:
            erros.append(f"linha {numero}: campos vazios: {', '.join(vazios)}")
            continue
        nome = str(linha["full_name"]).strip()
        release_id = str(linha["release_id"]).strip()
        chaves.append((nome, release_id))
        por_repo[nome].append(linha)
        for campo, permitidos in VALORES_PERMITIDOS.items():
            valor = str(linha[campo]).strip()
            if valor not in permitidos:
                erros.append(
                    f"linha {numero}: {campo}={valor!r}; esperado: {', '.join(sorted(permitidos))}"
                )
        if exigir_revisao and str(linha["revisao_confirmada"]).strip() != "sim":
            erros.append(f"linha {numero}: revisao_confirmada deve ser 'sim'")

    duplicadas = sorted(chave for chave, total in Counter(chaves).items() if total > 1)
    if duplicadas:
        erros.append("releases duplicadas: " + ", ".join(f"{n}#{r}" for n, r in duplicadas))
    if len(por_repo) != total_repositorios:
        erros.append(
            f"esperados {total_repositorios} repositórios; encontrados {len(por_repo)}"
        )
    contagens_invalidas = sorted(
        f"{nome} ({len(itens)})" for nome, itens in por_repo.items()
        if len(itens) != releases_por_repositorio
    )
    if contagens_invalidas:
        erros.append("quantidade de releases divergente: " + ", ".join(contagens_invalidas))

    for nome, itens in por_repo.items():
        for campo in ("tipo_projeto", "releases_sao_entregas"):
            valores = {str(item.get(campo, "")).strip() for item in itens}
            if len(valores) > 1:
                erros.append(f"{nome}: {campo} varia entre releases: {sorted(valores)}")

    if erros:
        raise ValueError("rotulagem B inválida:\n- " + "\n- ".join(erros))
    return {
        "repositorios": len(por_repo),
        "releases": len(registros),
        "releases_corretivas": sum(
            str(linha["corretiva"]).strip() == "sim" for linha in registros
        ),
        "revisoes_confirmadas": sum(
            str(linha.get("revisao_confirmada", "")).strip() == "sim"
            for linha in registros
        ),
    }


def validar_arquivo(caminho: str | Path, exigir_revisao: bool = False) -> dict[str, int]:
    caminho = Path(caminho)
    if caminho.suffix.lower() == ".xlsx":
        repos = pd.read_excel(caminho, sheet_name="repositorios", dtype=str).fillna("")
        releases = pd.read_excel(caminho, sheet_name="releases", dtype=str).fillna("")
        colunas_repos = {"full_name", "tipo_projeto", "releases_sao_entregas"}
        colunas_releases = {"full_name", "release_id", "corretiva"}
        if not colunas_repos.issubset(repos.columns) or not colunas_releases.issubset(releases.columns):
            raise ValueError("planilha B sem as colunas canônicas de A1")
        combinadas = releases.merge(
            repos[list(colunas_repos)], on="full_name", how="left", validate="many_to_one"
        )
        return validar_rotulos(combinadas.to_dict("records"), exigir_revisao=exigir_revisao)
    with caminho.open(newline="", encoding="utf-8") as arquivo:
        leitor = csv.DictReader(arquivo)
        return validar_rotulos(leitor, exigir_revisao=exigir_revisao)


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "arquivo", help="caminho de data/amostra_ouro/rotulos/rotulos_B.xlsx"
    )
    parser.add_argument(
        "--exigir-revisao",
        action="store_true",
        help="exige revisado_por preenchido e revisao_confirmada=sim em todas as linhas",
    )
    args = parser.parse_args(argv)
    try:
        resumo = validar_arquivo(args.arquivo, exigir_revisao=args.exigir_revisao)
    except (OSError, ValueError) as erro:
        parser.exit(1, f"Erro: {erro}\n")
    print(
        "Rotulagem B válida: "
        f"{resumo['repositorios']} repositórios, {resumo['releases']} releases, "
        f"{resumo['releases_corretivas']} corretivas, "
        f"{resumo['revisoes_confirmadas']} revisões confirmadas."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
