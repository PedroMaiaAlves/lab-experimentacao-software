"""Cálculo dos episódios de falha e do tempo de recuperação da RQ04."""
from __future__ import annotations

from collections import defaultdict
from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from datetime import datetime
from statistics import median
from typing import Any

from metricas.cfr import classificar_conclusao


@dataclass(frozen=True)
class ResultadoRecuperacao:
    mediana_horas: float | None
    episodios_horas: tuple[float, ...]
    episodios_total: int
    episodios_censurados: int
    proporcao_censurados: float | None


def _data_hora(valor: str | None, campo: str) -> datetime:
    if not valor:
        raise ValueError(f"run válido sem {campo}")
    try:
        return datetime.fromisoformat(valor.replace("Z", "+00:00"))
    except ValueError as erro:
        raise ValueError(f"timestamp inválido em {campo}: {valor}") from erro


def calcular_tempo_recuperacao(
    runs: Iterable[Mapping[str, Any]],
) -> ResultadoRecuperacao:
    """Agrega episódios concluídos e censurados de todos os workflows."""
    por_workflow: dict[Any, list[Mapping[str, Any]]] = defaultdict(list)
    for run in runs:
        if run.get("workflow_id") is None:
            raise ValueError("run sem workflow_id")
        por_workflow[run["workflow_id"]].append(run)

    duracoes: list[float] = []
    censurados = 0
    for workflow_runs in por_workflow.values():
        ordenados = sorted(
            workflow_runs,
            key=lambda run: _data_hora(run.get("run_started_at"), "run_started_at"),
        )
        houve_sucesso = False
        inicio_falha: datetime | None = None

        for run in ordenados:
            classe = classificar_conclusao(run.get("conclusion"))
            if classe == "ignorar":
                continue
            inicio_run = _data_hora(run.get("run_started_at"), "run_started_at")

            if classe == "falha":
                if houve_sucesso and inicio_falha is None:
                    inicio_falha = inicio_run
                continue

            # Um sucesso encerra o episódio corrente e também habilita o próximo.
            if inicio_falha is not None:
                fim = _data_hora(run.get("updated_at"), "updated_at")
                horas = (fim - inicio_falha).total_seconds() / 3600
                if horas < 0:
                    raise ValueError("updated_at do sucesso anterior ao início da falha")
                duracoes.append(horas)
                inicio_falha = None
            houve_sucesso = True

        if inicio_falha is not None:
            censurados += 1

    total = len(duracoes) + censurados
    return ResultadoRecuperacao(
        mediana_horas=median(duracoes) if duracoes else None,
        episodios_horas=tuple(duracoes),
        episodios_total=total,
        episodios_censurados=censurados,
        proporcao_censurados=(censurados / total) if total else None,
    )
