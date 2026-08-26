"""RQ08 — Repositórios mais antigos apresentam maior proporção de issues fechadas?"""

import pandas as pd

from ._io import salvar_json

__all__ = ["analisar", "salvar_json"]


def analisar(df: pd.DataFrame) -> dict:
    """
    Analisa a relação entre idade do repositório e percentual de issues fechadas.

    Repositórios que nunca tiveram issues possuem percentual de issues fechadas
    como NaN e são excluídos da análise de correlação e das estatísticas por faixa.
    """

    colunas_necessarias = [
        "Idade (anos)",
        "% issues fechadas",
    ]

    for coluna in colunas_necessarias:
        if coluna not in df.columns:
            raise ValueError(
                f"Coluna necessária para a RQ08 não encontrada: '{coluna}'"
            )

    dados = df[colunas_necessarias].copy()

    dados["Idade (anos)"] = pd.to_numeric(
        dados["Idade (anos)"],
        errors="coerce",
    )

    dados["% issues fechadas"] = pd.to_numeric(
        dados["% issues fechadas"],
        errors="coerce",
    )

    total_repositorios = len(dados)

    dados_validos = dados.dropna(
        subset=["Idade (anos)", "% issues fechadas"]
    ).copy()

    repositorios_sem_issues = int(
        dados["% issues fechadas"].isna().sum()
    )

    repositorios_com_issues = int(len(dados_validos))

    if dados_validos.empty:
        return {
            "questao": "RQ08",
            "descricao": (
                "Repositórios mais antigos apresentam maior proporção "
                "de issues fechadas?"
            ),
            "metrica": (
                "Correlação de Spearman entre idade do repositório e "
                "percentual de issues fechadas"
            ),
            "hipotese_informal": (
                "Espera-se que repositórios mais antigos apresentem maior "
                "percentual mediano de issues fechadas, por possuírem processos "
                "de manutenção mais consolidados."
            ),
            "total_repositorios": total_repositorios,
            "repositorios_com_issues": repositorios_com_issues,
            "repositorios_sem_issues": repositorios_sem_issues,
            "correlacao_spearman": None,
            "interpretacao_correlacao": "Dados insuficientes.",
            "resumo_por_faixa_etaria": [],
        }

    # ---------------------------------------------------------
    # Correlação de Spearman
    # ---------------------------------------------------------
    correlacao = dados_validos["Idade (anos)"].corr(
        dados_validos["% issues fechadas"],
        method="spearman",
    )

    if pd.isna(correlacao):
        correlacao = None
        interpretacao = "Não foi possível calcular a correlação."
    else:
        correlacao = round(float(correlacao), 4)

        if correlacao > 0.7:
            interpretacao = "Correlação positiva forte."
        elif correlacao > 0.3:
            interpretacao = "Correlação positiva moderada."
        elif correlacao > 0.0:
            interpretacao = "Correlação positiva fraca."
        elif correlacao < -0.7:
            interpretacao = "Correlação negativa forte."
        elif correlacao < -0.3:
            interpretacao = "Correlação negativa moderada."
        elif correlacao < 0.0:
            interpretacao = "Correlação negativa fraca."
        else:
            interpretacao = "Ausência de correlação monotônica relevante."

    # ---------------------------------------------------------
    # Faixas de idade
    # ---------------------------------------------------------
    def classificar_faixa(idade: float) -> str:
        if idade <= 2:
            return "0–2 anos"
        elif idade <= 5:
            return ">2–5 anos"
        elif idade <= 10:
            return ">5–10 anos"
        elif idade <= 15:
            return ">10–15 anos"
        else:
            return ">15 anos"

    dados_validos["Faixa de idade"] = dados_validos["Idade (anos)"].apply(
        classificar_faixa
    )

    ordem_faixas = [
        "0–2 anos",
        ">2–5 anos",
        ">5–10 anos",
        ">10–15 anos",
        ">15 anos",
    ]

    resumo = (
        dados_validos
        .groupby("Faixa de idade", observed=True)
        .agg(
            Quantidade_repositorios=("% issues fechadas", "size"),
            Mediana_issues_fechadas=("% issues fechadas", "median"),
            Q1_issues_fechadas=(
                "% issues fechadas",
                lambda x: x.quantile(0.25),
            ),
            Q3_issues_fechadas=(
                "% issues fechadas",
                lambda x: x.quantile(0.75),
            ),
        )
        .reindex(ordem_faixas)
        .dropna(subset=["Quantidade_repositorios"])
        .reset_index()
    )

    resumo["IQR_issues_fechadas"] = (
        resumo["Q3_issues_fechadas"]
        - resumo["Q1_issues_fechadas"]
    )

    resumo["Quantidade_repositorios"] = (
        resumo["Quantidade_repositorios"]
        .astype(int)
    )

    for coluna in [
        "Mediana_issues_fechadas",
        "Q1_issues_fechadas",
        "Q3_issues_fechadas",
        "IQR_issues_fechadas",
    ]:
        resumo[coluna] = resumo[coluna].astype(float).round(2)

    return {
        "questao": "RQ08",
        "descricao": (
            "Repositórios mais antigos apresentam maior proporção "
            "de issues fechadas?"
        ),
        "metrica": (
            "Idade em anos, percentual de issues fechadas, correlação de "
            "Spearman e mediana/IQR do percentual de issues fechadas por faixa de idade"
        ),
        "hipotese_informal": (
            "Espera-se que repositórios mais antigos apresentem maior "
            "percentual mediano de issues fechadas, por possuírem processos "
            "de manutenção mais consolidados."
        ),
        "total_repositorios": total_repositorios,
        "repositorios_com_issues": repositorios_com_issues,
        "repositorios_sem_issues": repositorios_sem_issues,
        "correlacao_spearman": correlacao,
        "interpretacao_correlacao": interpretacao,
        "idade_mediana_repositorios_com_issues": round(
            float(dados_validos["Idade (anos)"].median()),
            2,
        ),
        "percentual_issues_fechadas_mediana": round(
            float(dados_validos["% issues fechadas"].median()),
            2,
        ),
        "resumo_por_faixa_etaria": resumo.to_dict(
            orient="records"
        ),
    }