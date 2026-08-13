"""RQ05 — Sistemas populares são escritos nas linguagens mais populares?"""
import pandas as pd

from ._io import salvar_json
from .constants import FONTE_OCTOVERSE_2025, LINGUAGENS_POPULARES_OCTOVERSE

__all__ = ["analisar", "salvar_json"]


def analisar(df: pd.DataFrame) -> dict:
    contagem = df["Linguagem"].value_counts()
    percentual_top10 = float(df["Linguagem"].isin(LINGUAGENS_POPULARES_OCTOVERSE).mean()) * 100

    return {
        "questao": "RQ05",
        "descricao": "Sistemas populares são escritos nas linguagens mais populares?",
        "metrica": (
            "Linguagem primária de cada repositório, comparada ao ranking de linguagens "
            "mais populares do GitHub Octoverse 2025"
        ),
        "fonte_ranking": FONTE_OCTOVERSE_2025,
        "criterio_ranking": "Número de contribuidores mensais em agosto de 2025",
        "ranking_referencia_octoverse": LINGUAGENS_POPULARES_OCTOVERSE,
        "distribuicao_linguagens": contagem.to_dict(),
        "percentual_no_top10_octoverse": round(percentual_top10, 1),
        "total_repositorios": int(len(df)),
    }
