"""RQ04 — Sistemas populares são atualizados com frequência?"""

import pandas as pd

from ._io import salvar_json

__all__ = ["analisar", "salvar_json"]


def analisar(df: pd.DataFrame) -> dict:
    """Resume os dias decorridos desde o último push (pushedAt)."""

    dias = df["Dias desde última atualização"]
    return {
        "questao": "RQ04",
        "descricao": "Sistemas populares são atualizados com frequência?",
        "metrica": "Dias decimais desde o último push no repositório (pushedAt)",
        "dias_desde_atualizacao_mediana": round(float(dias.median()), 4),
        "dias_desde_atualizacao_media": round(float(dias.mean()), 4),
        "dias_desde_atualizacao_minimo": round(float(dias.min()), 4),
        "dias_desde_atualizacao_maximo": round(float(dias.max()), 4),
        "total_repositorios": int(len(df)),
    }
