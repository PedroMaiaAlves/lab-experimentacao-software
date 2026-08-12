"""RQ01 — Sistemas populares são maduros/antigos?"""
import pandas as pd

from ._io import salvar_json

__all__ = ["analisar", "salvar_json"]


def analisar(df: pd.DataFrame) -> dict:
    return {
        "questao": "RQ01",
        "descricao": "Sistemas populares são maduros/antigos?",
        "metrica": "Idade do repositório em anos, a partir da data de criação",
        "idade_mediana_anos": round(float(df["Idade (anos)"].median()), 2),
        "idade_media_anos": round(float(df["Idade (anos)"].mean()), 2),
        "idade_minima_anos": round(float(df["Idade (anos)"].min()), 2),
        "idade_maxima_anos": round(float(df["Idade (anos)"].max()), 2),
        "total_repositorios": int(len(df)),
    }
