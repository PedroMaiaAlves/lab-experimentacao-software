"""Change failure rate usando workflow runs como proxy de falha."""
from __future__ import annotations

from collections.abc import Iterable, Mapping
from typing import Any, Literal

SUCESSOS = frozenset({"success"})
FALHAS = frozenset({"failure", "timed_out", "startup_failure"})
IGNORADAS = frozenset({
    "cancelled", "skipped", "neutral", "action_required", "stale", None, ""
})

Classificacao = Literal["sucesso", "falha", "ignorar"]


def classificar_conclusao(conclusao: str | None) -> Classificacao:
    """Classifica uma conclusion; valores novos/desconhecidos são ignorados."""
    if conclusao in SUCESSOS:
        return "sucesso"
    if conclusao in FALHAS:
        return "falha"
    return "ignorar"


def contar_conclusoes(runs: Iterable[Mapping[str, Any]]) -> dict[str, int]:
    contagens = {"sucessos": 0, "falhas": 0, "ignoradas": 0}
    for run in runs:
        classe = classificar_conclusao(run.get("conclusion"))
        contagens[{"sucesso": "sucessos", "falha": "falhas", "ignorar": "ignoradas"}[classe]] += 1
    return contagens


def calcular_cfr_a(runs: Iterable[Mapping[str, Any]]) -> float | None:
    """Calcula falhas / (falhas + sucessos), ou None sem observações válidas."""
    contagens = contar_conclusoes(runs)
    validas = contagens["falhas"] + contagens["sucessos"]
    if validas == 0:
        return None
    return contagens["falhas"] / validas
