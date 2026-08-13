"""RQ07 — Relação entre linguagem, contribuição, releases e atualização."""

import pandas as pd

from ._io import salvar_json
from .constants import FONTE_OCTOVERSE_2025, LINGUAGENS_POPULARES_OCTOVERSE

__all__ = ["analisar", "salvar_json"]


def analisar(df: pd.DataFrame) -> dict:
    """Agrupa as medianas das RQs 02, 03 e 04 por linguagem primária."""

    resumo = (
        df.groupby("Linguagem", dropna=False)
        .agg(
            Quantidade_repositorios=("Nome", "size"),
            PRs_aceitas_mediana=("PRs aceitas", "median"),
            Releases_mediana=("Total de releases", "median"),
            Dias_desde_atualizacao_mediana=(
                "Dias desde última atualização",
                "median",
            ),
        )
        .reset_index()
        .sort_values(
            ["Quantidade_repositorios", "Linguagem"],
            ascending=[False, True],
        )
    )

    resumo["No_top10_octoverse"] = resumo["Linguagem"].isin(
        LINGUAGENS_POPULARES_OCTOVERSE
    )

    colunas_inteiras = ["Quantidade_repositorios"]
    colunas_decimais = [
        "PRs_aceitas_mediana",
        "Releases_mediana",
        "Dias_desde_atualizacao_mediana",
    ]
    resumo[colunas_inteiras] = resumo[colunas_inteiras].astype(int)
    resumo[colunas_decimais] = resumo[colunas_decimais].astype(float).round(2)

    return {
        "questao": "RQ07",
        "descricao": (
            "Sistemas escritos em linguagens mais populares recebem mais "
            "contribuição externa, lançam mais releases e são atualizados "
            "com mais frequência?"
        ),
        "metrica": "Medianas das RQs 02, 03 e 04 por linguagem primária",
        "fonte_linguagens_populares": FONTE_OCTOVERSE_2025,
        "ranking_referencia_octoverse": LINGUAGENS_POPULARES_OCTOVERSE,
        "resumo_por_linguagem": resumo.to_dict(orient="records"),
        "total_linguagens": int(len(resumo)),
        "total_repositorios": int(len(df)),
    }
