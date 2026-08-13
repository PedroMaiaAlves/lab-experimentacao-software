"""RQ06 — Sistemas populares possuem alto percentual de issues fechadas?"""

import pandas as pd

from ._io import salvar_json

__all__ = ["analisar", "salvar_json"]


def analisar(df: pd.DataFrame) -> dict:
    """Resume o percentual de issues fechadas entre repositórios com issues."""

    percentuais = df["% issues fechadas"]
    percentuais_validos = percentuais.dropna()

    if percentuais_validos.empty:
        mediana = media = minimo = maximo = None
    else:
        mediana = round(float(percentuais_validos.median()), 2)
        media = round(float(percentuais_validos.mean()), 2)
        minimo = round(float(percentuais_validos.min()), 2)
        maximo = round(float(percentuais_validos.max()), 2)

    return {
        "questao": "RQ06",
        "descricao": (
            "Sistemas populares possuem um alto percentual de issues fechadas?"
        ),
        "metrica": "Percentual de issues fechadas sobre o total de issues",
        "percentual_issues_fechadas_mediana": mediana,
        "percentual_issues_fechadas_media": media,
        "percentual_issues_fechadas_minimo": minimo,
        "percentual_issues_fechadas_maximo": maximo,
        "repositorios_com_issues": int(percentuais_validos.count()),
        "repositorios_sem_issues": int(percentuais.isna().sum()),
        "total_repositorios": int(len(df)),
    }
