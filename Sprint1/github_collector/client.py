"""Cliente responsável por consultar a API GraphQL do GitHub.

Este módulo só fala com a API e devolve dados crus (lista de dicts).
A conversão para tabela fica a cargo de `utils.dataframe.montar_dataframe`,
e a análise de cada RQ fica a cargo do pacote `analysis`.
"""
import time

import requests

from .schema import GRAPHQL_QUERY

GRAPHQL_URL = "https://api.github.com/graphql"


def coletar_repositorios(token: str, linguagem: str, quantidade: int, progresso=None) -> list:
    """Coleta os N repositórios com mais estrelas do GitHub via GraphQL.

    Args:
        token: GitHub Personal Access Token.
        linguagem: filtro de linguagem ("Todas" para não filtrar).
        quantidade: número total de repositórios a coletar (top-N por estrelas).
        progresso: objeto opcional do Streamlit (st.progress) para feedback visual.

    Returns:
        Lista de nós (dicts) crus, exatamente como retornados pela API.
    """
    query_string = "stars:>1 sort:stars-desc"
    if linguagem != "Todas":
        query_string += f" language:{linguagem}"

    headers = {"Authorization": f"Bearer {token}"}
    registros = []
    cursor = None
    restante = quantidade

    while restante > 0:
        lote = min(50, restante)
        variables = {"queryString": query_string, "first": lote, "after": cursor}
        resp = requests.post(
            GRAPHQL_URL,
            json={"query": GRAPHQL_QUERY, "variables": variables},
            headers=headers,
            timeout=30,
        )
        resp.raise_for_status()
        payload = resp.json()

        if "errors" in payload:
            raise RuntimeError(payload["errors"][0].get("message", "Erro desconhecido na API GraphQL."))

        data = payload["data"]["search"]
        for edge in data["edges"]:
            registros.append(edge["node"])

        restante -= lote
        if progresso is not None:
            progresso.progress(
                min(1.0, len(registros) / quantidade),
                text=f"{len(registros)}/{quantidade} repositórios coletados...",
            )

        if not data["pageInfo"]["hasNextPage"]:
            break
        cursor = data["pageInfo"]["endCursor"]
        time.sleep(0.3)  # evita rate limit secundário

    return registros
