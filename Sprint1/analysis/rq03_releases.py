"""RQ03 — Sistemas populares lançam releases com frequência?"""
import pandas as pd

from ._io import salvar_json

__all__ = ["analisar", "salvar_json"]


def analisar(df: pd.DataFrame) -> dict:
    return {
        "questao": "RQ03",
        "descricao": "Sistemas populares lançam releases com frequência?",
        "metrica": "Total de releases do repositório",
        "releases_mediana": float(df["Total de releases"].median()),
        "releases_media": round(float(df["Total de releases"].mean()), 2),
        "releases_maxima": int(df["Total de releases"].max()),
        "total_repositorios": int(len(df)),
    }
