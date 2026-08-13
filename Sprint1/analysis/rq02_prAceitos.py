"""RQ02 — Sistemas populares recebem muita contribuição externa?"""

import pandas as pd

from ._io import salvar_json

__all__ = ["analisar", "salvar_json"]


def analisar(df: pd.DataFrame) -> dict:
    """Resume o total de pull requests aceitas (estado MERGED)."""

    prs_aceitas = df["PRs aceitas"]
    return {
        "questao": "RQ02",
        "descricao": "Sistemas populares recebem muita contribuição externa?",
        "metrica": "Total de pull requests aceitas (estado MERGED)",
        "prs_aceitas_mediana": float(prs_aceitas.median()),
        "prs_aceitas_media": round(float(prs_aceitas.mean()), 2),
        "prs_aceitas_maxima": int(prs_aceitas.max()),
        "total_repositorios": int(len(df)),
    }
