"""Validação dos artefatos produzidos pelo pipeline integrado da Lab03S01."""
from __future__ import annotations

import csv
import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

from metricas.cfr import classificar_conclusao
from pipeline.janela import na_janela

CSVS_OBRIGATORIOS = (
    "candidatos.csv",
    "funil.csv",
    "descartes.csv",
    "metadados.csv",
    "releases.csv",
    "tags.csv",
    "comparacoes_releases.csv",
    "commits_entre_releases.csv",
    "lead_time.csv",
    "deployment_frequency.csv",
    "runs_saturados.csv",
)

RESUMOS_POR_REPOSITORIO = (
    "metadados.csv",
    "lead_time.csv",
    "deployment_frequency.csv",
)


def _ler_csv(caminho: Path) -> list[dict[str, str]]:
    with caminho.open(newline="", encoding="utf-8") as arquivo:
        return list(csv.DictReader(arquivo))


def _validar_resumo(
    caminho: Path, esperados: set[str], erros: list[str]
) -> None:
    nomes = [linha.get("full_name", "") for linha in _ler_csv(caminho)]
    contagens = Counter(nomes)
    duplicados = sorted(nome for nome, total in contagens.items() if nome and total > 1)
    encontrados = set(nomes) - {""}
    faltantes = sorted(esperados - encontrados)
    extras = sorted(encontrados - esperados)
    if faltantes:
        erros.append(f"{caminho.name}: repositórios ausentes: {', '.join(faltantes)}")
    if extras:
        erros.append(f"{caminho.name}: repositórios inesperados: {', '.join(extras)}")
    if duplicados:
        erros.append(f"{caminho.name}: repositórios duplicados: {', '.join(duplicados)}")


def _validar_releases(
    caminho: Path, esperados: set[str], cfg: dict[str, Any], erros: list[str]
) -> None:
    totais: dict[str, int] = defaultdict(int)
    for release in _ler_csv(caminho):
        nome = release.get("full_name", "")
        if nome not in esperados:
            continue
        principal = (
            release.get("draft", "").lower() == "false"
            and release.get("prerelease", "").lower() == "false"
            and na_janela(release.get("published_at"), cfg)
        )
        totais[nome] += int(principal)

    minimo = cfg["criterios"]["min_releases"]
    insuficientes = sorted(
        f"{nome} ({totais[nome]})" for nome in esperados if totais[nome] < minimo
    )
    if insuficientes:
        erros.append(
            f"releases.csv: menos de {minimo} releases principais: "
            + ", ".join(insuficientes)
        )


def _validar_runs(
    diretorio: Path,
    repos: list[dict[str, Any]],
    cfg: dict[str, Any],
    erros: list[str],
) -> None:
    minimo = cfg["criterios"]["min_runs"]
    for repo in repos:
        nome = repo["full_name"]
        caminho = diretorio / "workflow_runs" / (nome.replace("/", "__") + ".json")
        if not caminho.is_file():
            erros.append(f"workflow runs ausentes para {nome}: {caminho.name}")
            continue
        try:
            dados = json.loads(caminho.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            erros.append(f"workflow runs inválidos para {nome}: {exc}")
            continue

        if dados.get("full_name") != nome:
            erros.append(f"workflow runs de {nome}: full_name divergente")
        if dados.get("default_branch") != repo.get("default_branch"):
            erros.append(f"workflow runs de {nome}: default_branch divergente")
        if dados.get("janela_inicio") != cfg["janela_inicio"].isoformat() or dados.get(
            "janela_fim"
        ) != cfg["janela_fim"].isoformat():
            erros.append(f"workflow runs de {nome}: janela divergente do config")
        if dados.get("complete") is not True:
            erros.append(f"workflow runs de {nome}: coleta marcada como incompleta")

        runs = dados.get("workflow_runs")
        if not isinstance(runs, list):
            erros.append(f"workflow runs de {nome}: workflow_runs não é uma lista")
            continue
        validos = sum(
            classificar_conclusao(run.get("conclusion")) != "ignorar"
            for run in runs
            if isinstance(run, dict)
        )
        if validos < minimo:
            erros.append(f"workflow runs de {nome}: {validos} válidos; mínimo {minimo}")


def validar_artefatos_s01(
    cfg: dict[str, Any], repos: list[dict[str, Any]]
) -> dict[str, int]:
    """Falha se a execução não comprovar uma amostra completa e coerente."""
    diretorio = Path(cfg["saida"]["dir_dados"])
    erros: list[str] = []
    nomes = [repo["full_name"] for repo in repos]
    esperados = set(nomes)
    if len(esperados) != len(nomes):
        erros.append("a amostra contém repositórios duplicados")

    ausentes = [nome for nome in CSVS_OBRIGATORIOS if not (diretorio / nome).is_file()]
    if ausentes:
        erros.append("arquivos obrigatórios ausentes: " + ", ".join(ausentes))

    for nome in RESUMOS_POR_REPOSITORIO:
        caminho = diretorio / nome
        if caminho.is_file():
            _validar_resumo(caminho, esperados, erros)

    releases = diretorio / "releases.csv"
    if releases.is_file():
        _validar_releases(releases, esperados, cfg, erros)

    funil = diretorio / "funil.csv"
    if funil.is_file():
        finais = [linha for linha in _ler_csv(funil) if linha.get("etapa") == "amostra_final"]
        if len(finais) != 1 or finais[0].get("restaram") != str(len(esperados)):
            erros.append("funil.csv: amostra_final não corresponde à amostra coletada")

    saturados = diretorio / "runs_saturados.csv"
    if saturados.is_file():
        incompletos = [
            linha for linha in _ler_csv(saturados) if linha.get("status") == "incompleto"
        ]
        if incompletos:
            erros.append(
                f"runs_saturados.csv: {len(incompletos)} intervalo(s) diário(s) incompleto(s)"
            )

    _validar_runs(diretorio, repos, cfg, erros)
    if erros:
        detalhes = "\n- ".join(erros)
        raise RuntimeError(f"validação final da Lab03S01 falhou:\n- {detalhes}")
    return {"repositorios": len(esperados), "arquivos_csv": len(CSVS_OBRIGATORIOS)}
