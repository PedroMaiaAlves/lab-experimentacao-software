"""RQ09 — Colaboração e publicação de releases."""

import pandas as pd

from ._io import salvar_json
from ._stats import arredondar, outliers_iqr, resumir, spearman

__all__ = ["analisar", "salvar_json"]


def analisar(df: pd.DataFrame) -> dict:
    """Relaciona as intensidades anuais de PRs mescladas e releases."""

    dados = df[["Nome", "Idade (anos)", "PRs aceitas", "Total de releases"]].copy()
    colunas_numericas = ["Idade (anos)", "PRs aceitas", "Total de releases"]
    dados[colunas_numericas] = dados[colunas_numericas].apply(
        pd.to_numeric, errors="coerce"
    ).replace([float("inf"), float("-inf")], pd.NA)

    idade = dados["Idade (anos)"]
    contagens_validas = (dados["PRs aceitas"] >= 0) & (dados["Total de releases"] >= 0)
    dados["PRs por ano"] = (dados["PRs aceitas"] / idade).where(
        (idade > 0) & contagens_validas
    ).round(4)
    dados["Releases por ano"] = (dados["Total de releases"] / idade).where(
        (idade > 0) & contagens_validas
    ).round(4)

    principal = dados[dados["Idade (anos)"] >= 1].dropna(
        subset=["PRs por ano", "Releases por ano"]
    ).copy()
    correlacao = spearman(principal["PRs por ano"], principal["Releases por ano"])

    rho = correlacao["rho"]
    if rho is None:
        interpretacao = "Dados insuficientes para calcular a associação."
    else:
        absoluto = abs(rho)
        intensidade = (
            "desprezível" if absoluto < 0.1 else
            "fraca" if absoluto < 0.3 else
            "moderada" if absoluto < 0.5 else
            "forte"
        )
        direcao = "positiva" if rho > 0 else "negativa" if rho < 0 else "sem direção"
        interpretacao = f"Associação monotônica {direcao} {intensidade}."

    ordenados = principal.sort_values(
        ["PRs por ano", "Nome"], kind="mergesort"
    ).reset_index(drop=True)
    if ordenados.empty:
        quartis = []
    else:
        ordenados["quartil"] = [
            indice * 4 // len(ordenados) + 1 for indice in range(len(ordenados))
        ]
        nomes_faixas = {
            1: "Q1 — menor intensidade",
            2: "Q2",
            3: "Q3",
            4: "Q4 — maior intensidade",
        }
        quartis = [
            {
                "faixa": nomes_faixas[numero],
                "repositorios": int(len(grupo)),
                "prs_por_ano_minimo": arredondar(grupo["PRs por ano"].min()),
                "prs_por_ano_mediana": arredondar(grupo["PRs por ano"].median()),
                "prs_por_ano_maximo": arredondar(grupo["PRs por ano"].max()),
                "releases_por_ano_mediana": arredondar(
                    grupo["Releases por ano"].median()
                ),
            }
            for numero, grupo in ordenados.groupby("quartil", sort=True)
        ]

    prs_outliers, mascara_prs = outliers_iqr(principal["PRs por ano"])
    releases_outliers, mascara_releases = outliers_iqr(
        principal["Releases por ano"]
    )

    return {
        "questao": "RQ09",
        "descricao": (
            "Repositórios com maior intensidade de pull requests mescladas também "
            "apresentam maior intensidade de releases?"
        ),
        "metricas": {
            "intensidade_prs": "PRs mescladas divididas pela idade do repositório em anos",
            "intensidade_releases": "Releases acumuladas divididas pela idade do repositório em anos",
        },
        "hipotese_informal": (
            "Espera-se uma associação positiva entre a intensidade anual de PRs "
            "mescladas e a intensidade anual de releases."
        ),
        "criterios": {
            "idade_minima_analise_anos": 1.0,
            "precisao_taxas_anuais_casas_decimais": 4,
            "correlacao": "Spearman calculada como correlação de Pearson entre ranks médios",
            "quartis_prs": (
                "Ordenação crescente por PRs por ano e Nome, seguida de divisão "
                "posicional determinística em Q1 a Q4"
            ),
            "outliers": "Critério de 1,5 vez o IQR, calculado por taxa anual",
            "politica_outliers": "Mantidos na correlação e nas faixas",
        },
        "amostra": {
            "total_repositorios": int(len(dados)),
            "analise_principal": int(len(principal)),
            "excluidos_idade_menor_1_ano": int((idade < 1).sum()),
            "excluidos_dados_ausentes_ou_invalidos": int(
                len(dados) - len(principal) - (idade < 1).sum()
            ),
        },
        "taxas_anuais_analise_principal": {
            "prs_por_ano": resumir(principal["PRs por ano"]),
            "releases_por_ano": resumir(principal["Releases por ano"]),
        },
        "correlacao_spearman": correlacao,
        "interpretacao_correlacao": interpretacao,
        "resumo_por_quartil_prs": quartis,
        "outliers_iqr": {
            "prs_por_ano": prs_outliers,
            "releases_por_ano": releases_outliers,
            "uniao_repositorios_extremos": int((mascara_prs | mascara_releases).sum()),
            "extremos_em_ambas_metricas": int((mascara_prs & mascara_releases).sum()),
        },
        "total_repositorios": int(len(dados)),
    }
