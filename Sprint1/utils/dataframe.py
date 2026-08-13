"""Conversão dos dados crus da API GraphQL em uma tabela (DataFrame)."""
from datetime import datetime, timezone

import pandas as pd


def montar_dataframe(registros: list) -> pd.DataFrame:
    """Transforma a lista de nós retornados pela API GraphQL em um DataFrame
    com as colunas usadas pelas análises de RQ01 a RQ07."""
    agora = datetime.now(timezone.utc)
    linhas = []
    for node in registros:
        criado_em = datetime.fromisoformat(node["createdAt"].replace("Z", "+00:00"))
        ultimo_push_em = (
            datetime.fromisoformat(node["pushedAt"].replace("Z", "+00:00"))
            if node["pushedAt"] else criado_em
        )
        issues_abertas = node["openIssues"]["totalCount"]
        issues_fechadas = node["closedIssues"]["totalCount"]
        total_issues = issues_abertas + issues_fechadas

        linhas.append({
            "Nome": node["nameWithOwner"],
            "URL": node["url"],
            "Estrelas": node["stargazerCount"],
            "Linguagem": node["primaryLanguage"]["name"] if node["primaryLanguage"] else "Não definida",
            "Idade (anos)": round((agora - criado_em).days / 365.25, 2),
            "PRs aceitas": node["pullRequests"]["totalCount"],
            "Total de releases": node["releases"]["totalCount"],
            "Dias desde última atualização": round(
                max(0.0, (agora - ultimo_push_em).total_seconds() / 86_400),
                4,
            ),
            "Issues abertas": issues_abertas,
            "Issues fechadas": issues_fechadas,
            "% issues fechadas": round(100 * issues_fechadas / total_issues, 1) if total_issues > 0 else None,
        })
    return pd.DataFrame(linhas)
