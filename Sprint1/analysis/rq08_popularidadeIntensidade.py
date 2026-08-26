"""RQ08 — Associação entre popularidade e intensidade de desenvolvimento."""

import pandas as pd

from ._io import salvar_json
from ._stats import arredondar, outliers_iqr, resumir, spearman

__all__ = ["analisar", "salvar_json"]

TAXAS = {
    "prs_por_ano": ("PRs por ano", "PRs aceitas"),
    "releases_por_ano": ("Releases por ano", "Total de releases"),
}


def _preparar(df: pd.DataFrame) -> pd.DataFrame:
    dados = df[["Nome", "Estrelas", "Idade (anos)", "PRs aceitas", "Total de releases"]].copy()
    idade = dados["Idade (anos)"]
    for coluna, origem in TAXAS.values():
        dados[coluna] = (dados[origem] / idade).where(idade > 0).round(4)
    return dados


def _quartis(dados: pd.DataFrame) -> list[dict]:
    dados = dados.sort_values(["Estrelas", "Nome"], kind="mergesort").reset_index(drop=True)
    dados["quartil"] = [i * 4 // len(dados) + 1 for i in range(len(dados))]
    return [{
        "quartil": f"Q{numero}", "repositorios": int(len(grupo)),
        "estrelas_minimo": int(grupo["Estrelas"].min()),
        "estrelas_mediana": arredondar(grupo["Estrelas"].median(), 2),
        "estrelas_maximo": int(grupo["Estrelas"].max()),
        "prs_por_ano_mediana": arredondar(grupo["PRs por ano"].median()),
        "releases_por_ano_mediana": arredondar(grupo["Releases por ano"].median()),
    } for numero, grupo in dados.groupby("quartil", sort=True)] if len(dados) else []


def _outliers(dados: pd.DataFrame, coluna: str) -> tuple[dict, pd.Series]:
    resumo, mascara = outliers_iqr(dados[coluna])
    extremos = dados.loc[mascara, ["Nome", "Estrelas", "Idade (anos)", coluna]]
    extremos = extremos.sort_values(coluna, ascending=False)
    resumo["repositorios"] = [
        {"repositorio": nome, "estrelas": int(estrelas),
         "idade_anos": arredondar(idade, 2), "valor": arredondar(valor)}
        for nome, estrelas, idade, valor in extremos.itertuples(index=False, name=None)
    ]
    return resumo, mascara


def _correlacoes(dados: pd.DataFrame) -> dict:
    return {f"estrelas_vs_{chave}": spearman(dados["Estrelas"], dados[coluna])
            for chave, (coluna, _) in TAXAS.items()}


def analisar(df: pd.DataFrame) -> dict:
    """Relaciona estrelas às taxas anuais de PRs mescladas e releases."""

    dados = _preparar(df)
    principal = dados[dados["Idade (anos)"] >= 1]
    sensibilidade = dados[dados["Idade (anos)"] > 0]
    prs_outliers, mascara_prs = _outliers(principal, "PRs por ano")
    releases_outliers, mascara_releases = _outliers(principal, "Releases por ano")

    return {
        "questao": "RQ08",
        "descricao": "Existe associação entre a popularidade dos repositórios e sua intensidade anual de desenvolvimento?",
        "metricas": {
            "popularidade": "Número de estrelas",
            "intensidade_prs": "PRs mescladas divididas pela idade arredondada em anos",
            "intensidade_releases": "Total de releases dividido pela idade arredondada em anos",
        },
        "criterios": {
            "idade_minima_analise_principal_anos": 1.0,
            "precisao_taxas_anuais_casas_decimais": 4,
            "correlacao": "Spearman calculada como correlação de Pearson entre ranks médios",
            "quartis_estrelas": "Ordenação crescente por Estrelas e Nome, seguida de divisão posicional determinística em Q1 a Q4",
            "outliers": "Critério de 1,5 vez o IQR, calculado por taxa anual",
            "politica_outliers": "Mantidos em todas as análises",
        },
        "amostra": {
            "total_repositorios": int(len(dados)),
            "analise_principal": int(len(principal)),
            "sensibilidade_idade_positiva": int(len(sensibilidade)),
            "idade_menor_1_ano": int((dados["Idade (anos)"] < 1).sum()),
            "idade_positiva_menor_1_ano": int(dados["Idade (anos)"].between(0, 1, inclusive="neither").sum()),
            "idade_nao_positiva": int((dados["Idade (anos)"] <= 0).sum()),
            "dados_ausentes": 0,
        },
        "taxas_anuais_analise_principal": {
            chave: resumir(principal[coluna]) for chave, (coluna, _) in TAXAS.items()
        },
        "correlacoes_spearman": {
            "principal_idade_maior_igual_1": _correlacoes(principal),
            "sensibilidade_todas_idades_positivas": _correlacoes(sensibilidade),
        },
        "resumo_por_quartil_estrelas": _quartis(principal),
        "outliers_iqr": {
            "prs_por_ano": prs_outliers,
            "releases_por_ano": releases_outliers,
            "uniao_repositorios_extremos": int((mascara_prs | mascara_releases).sum()),
            "extremos_em_ambas_metricas": int((mascara_prs & mascara_releases).sum()),
        },
        "total_repositorios": int(len(dados)),
    }
