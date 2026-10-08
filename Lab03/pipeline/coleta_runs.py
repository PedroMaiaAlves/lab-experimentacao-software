"""Coleta de workflow runs do default branch, subdividida por mês."""
from __future__ import annotations

import csv
import json
import os
import re
import tempfile
from datetime import date, timedelta
from pathlib import Path
from typing import Any

from pipeline.janela import meses_da_janela

LIMITE_CONSULTA = 1000
CAMPOS_RUN = (
    "id", "workflow_id", "name", "conclusion", "run_started_at", "updated_at", "created_at"
)
_PROXIMA = re.compile(r'<([^>]+)>;\s*rel="next"')


def _params(branch: str, inicio: date, fim: date) -> dict[str, Any]:
    return {
        "branch": branch,
        "event": "push",
        "created": f"{inicio.isoformat()}..{fim.isoformat()}",
        "per_page": 100,
    }


def _paginar_a_partir_da_primeira(client, dados, headers) -> list[dict[str, Any]]:
    runs = list(dados.get("workflow_runs", []))
    proxima = _PROXIMA.search(headers.get("link", ""))
    url = proxima.group(1) if proxima else None
    while url:
        pagina, cabecalhos = client.get_json(url)
        runs.extend(pagina.get("workflow_runs", []))
        proxima = _PROXIMA.search(cabecalhos.get("link", ""))
        url = proxima.group(1) if proxima else None
    return runs


def _coletar_intervalo(client, nome: str, branch: str, inicio: date, fim: date):
    caminho = f"/repos/{nome}/actions/runs"
    dados, headers = client.get_json(caminho, _params(branch, inicio, fim))
    total = int(dados.get("total_count", 0))

    if total >= LIMITE_CONSULTA and inicio < fim:
        meio = inicio + timedelta(days=(fim - inicio).days // 2)
        esquerda, sat_esq, completa_esq = _coletar_intervalo(
            client, nome, branch, inicio, meio
        )
        direita, sat_dir, completa_dir = _coletar_intervalo(
            client, nome, branch, meio + timedelta(days=1), fim
        )
        registro = {
            "full_name": nome,
            "inicio": inicio.isoformat(),
            "fim": fim.isoformat(),
            "total_count": total,
            "status": "subdividido",
        }
        return esquerda + direita, [registro, *sat_esq, *sat_dir], completa_esq and completa_dir

    runs = _paginar_a_partir_da_primeira(client, dados, headers)
    if total >= LIMITE_CONSULTA:
        registro = {
            "full_name": nome,
            "inicio": inicio.isoformat(),
            "fim": fim.isoformat(),
            "total_count": total,
            "status": "incompleto",
        }
        return runs, [registro], False
    return runs, [], True


def _normalizar_run(run: dict[str, Any]) -> dict[str, Any]:
    return {campo: run.get(campo) for campo in CAMPOS_RUN}


def coletar_runs_repositorio(client, repo: dict[str, Any], cfg: dict[str, Any]) -> dict[str, Any]:
    """Coleta e normaliza todos os runs de um repositório na janela configurada."""
    nome = repo["full_name"]
    branch = repo["default_branch"]
    por_id: dict[Any, dict[str, Any]] = {}
    saturados: list[dict[str, Any]] = []
    completa = True

    for inicio, fim in meses_da_janela(cfg):
        runs, registros, intervalo_completo = _coletar_intervalo(
            client, nome, branch, inicio, fim
        )
        for run in runs:
            if run.get("id") is not None:
                por_id.setdefault(run["id"], _normalizar_run(run))
        saturados.extend(registros)
        completa = completa and intervalo_completo

    runs_ordenados = sorted(
        por_id.values(), key=lambda run: (run.get("created_at") or "", run["id"])
    )
    return {
        "full_name": nome,
        "default_branch": branch,
        "janela_inicio": cfg["janela_inicio"].isoformat(),
        "janela_fim": cfg["janela_fim"].isoformat(),
        "complete": completa,
        "saturated_intervals": saturados,
        "workflow_runs": runs_ordenados,
    }


def _salvar_json_atomico(caminho: Path, dados: dict[str, Any]) -> None:
    caminho.parent.mkdir(parents=True, exist_ok=True)
    temporario = None
    try:
        with tempfile.NamedTemporaryFile(
            "w", encoding="utf-8", dir=caminho.parent, delete=False
        ) as f:
            temporario = Path(f.name)
            json.dump(dados, f, ensure_ascii=False, indent=2)
            f.flush()
            os.fsync(f.fileno())
        os.replace(temporario, caminho)
    finally:
        if temporario is not None and temporario.exists():
            temporario.unlink()


def _nome_arquivo(full_name: str) -> str:
    return full_name.replace("/", "__") + ".json"


def coletar(client, cfg: dict[str, Any], repos: list[dict[str, Any]]):
    """Entrada usada por ``python -m pipeline``; grava JSONs e relatório de saturação."""
    dir_dados = Path(cfg["saida"]["dir_dados"])
    dir_runs = dir_dados / "workflow_runs"
    resultados = []
    saturados = []
    for repo in repos:
        resultado = coletar_runs_repositorio(client, repo, cfg)
        _salvar_json_atomico(dir_runs / _nome_arquivo(repo["full_name"]), resultado)
        resultados.append(resultado)
        saturados.extend(resultado["saturated_intervals"])

    dir_dados.mkdir(parents=True, exist_ok=True)
    with open(dir_dados / "runs_saturados.csv", "w", newline="", encoding="utf-8") as f:
        campos = ["full_name", "inicio", "fim", "total_count", "status"]
        escritor = csv.DictWriter(f, fieldnames=campos)
        escritor.writeheader()
        escritor.writerows(saturados)
    return resultados
