"""Coleta repositórios populares do GitHub e gera os resultados das RQs."""

import argparse
import json
import os
from pathlib import Path

import pandas as pd
import requests
from dotenv import load_dotenv

from analysis import MODULOS_RQ
from github_collector.client import GRAPHQL_URL
from github_collector.schema import GRAPHQL_QUERY
from utils import montar_dataframe


TOTAL_REPOSITORIOS_PADRAO = 1_000
TAMANHO_PAGINA = 50

BASE_DIR = Path(__file__).resolve().parent

DATA_RAW_DIR = BASE_DIR / "data" / "raw"
DATA_RQ_DIR = BASE_DIR / "data" / "rq"

ARQUIVO_SAIDA = DATA_RAW_DIR / "repositorios_graphql.json"
ARQUIVO_CSV = DATA_RAW_DIR / "repositorios_populares.csv"
ARQUIVO_CSV_COMPLETO = DATA_RAW_DIR / "repositorios_populares_completo.csv"


def carregar_token() -> str:
    """Lê GITHUB_TOKEN do .env de Sprint1 ou da raiz do repositório."""

    load_dotenv(BASE_DIR / ".env")
    load_dotenv(BASE_DIR.parent / ".env")

    token = os.getenv("GITHUB_TOKEN", "").strip()

    if not token:
        raise RuntimeError(
            "Configure GITHUB_TOKEN no arquivo .env."
        )

    return token


def montar_query_string(linguagem: str = "Todas") -> str:
    """
    Monta a query do GitHub usada para buscar os repositórios.

    O critério principal continua sendo estrelas em ordem decrescente.
    """

    partes = [
        "stars:>0",
        "is:public",
    ]

    if linguagem and linguagem != "Todas":
        partes.append(f"language:{linguagem}")

    partes.append("sort:stars-desc")

    return " ".join(partes)


def coletar_repositorios(
    token: str,
    linguagem: str = "Todas",
    quantidade: int = TOTAL_REPOSITORIOS_PADRAO,
) -> list[dict]:
    """Consulta páginas via cursor até completar a quantidade solicitada."""

    repositorios = []
    nomes_coletados = set()
    cursores_vistos = set()
    cursor = None

    with requests.Session() as sessao:
        sessao.headers["Authorization"] = f"Bearer {token}"

        while len(repositorios) < quantidade:
            restante = quantidade - len(repositorios)

            variaveis = {
                "queryString": montar_query_string(linguagem),
                "first": min(
                    TAMANHO_PAGINA,
                    restante,
                ),
                "after": cursor,
            }

            resposta = sessao.post(
                GRAPHQL_URL,
                json={
                    "query": GRAPHQL_QUERY,
                    "variables": variaveis,
                },
                timeout=30,
            )

            resposta.raise_for_status()

            payload = resposta.json()

            if payload.get("errors"):
                raise RuntimeError(
                    payload["errors"][0]["message"]
                )

            busca = payload["data"]["search"]

            pagina = [
                edge["node"]
                for edge in busca["edges"]
                if edge.get("node") is not None
            ]

            if not pagina:
                raise RuntimeError(
                    "O GitHub retornou uma página vazia antes de completar "
                    f"os {quantidade} repositórios."
                )

            for repositorio in pagina:
                nome = repositorio["nameWithOwner"]

                if nome in nomes_coletados:
                    continue

                nomes_coletados.add(nome)
                repositorios.append(repositorio)

            print(
                f"Coletados: {len(repositorios)}/{quantidade}"
            )

            if len(repositorios) >= quantidade:
                break

            page_info = busca["pageInfo"]

            if not page_info["hasNextPage"]:
                raise RuntimeError(
                    "A busca terminou antes de completar "
                    f"{quantidade} repositórios únicos; "
                    f"foram coletados {len(repositorios)}."
                )

            proximo_cursor = page_info["endCursor"]

            if (
                not proximo_cursor
                or proximo_cursor in cursores_vistos
            ):
                raise RuntimeError(
                    "A paginação não avançou: o GitHub retornou "
                    "um cursor ausente ou repetido."
                )

            cursores_vistos.add(proximo_cursor)
            cursor = proximo_cursor

    return repositorios


def exibir_repositorios(
    repositorios: list[dict],
) -> None:
    """Exibe os principais valores recebidos da API."""

    print(
        "\nPos | Repositório                          | "
        "Estrelas   | Linguagem"
    )
    print("-" * 76)

    for posicao, repositorio in enumerate(
        repositorios,
        start=1,
    ):
        linguagem = repositorio.get("primaryLanguage")

        nome_linguagem = (
            linguagem["name"]
            if linguagem
            else "Não definida"
        )

        print(
            f"{posicao:>3} | "
            f"{repositorio['nameWithOwner'][:36]:<36} | "
            f"{repositorio['stargazerCount']:>10} | "
            f"{nome_linguagem}"
        )


def salvar_json(repositorios: list[dict]) -> None:
    """Salva os dados brutos coletados."""

    DATA_RAW_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    ARQUIVO_SAIDA.write_text(
        json.dumps(
            repositorios,
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )

    print(
        f"\nJSON bruto salvo em: {ARQUIVO_SAIDA}"
    )


def salvar_csv(dataframe: pd.DataFrame) -> None:
    """Exporta o dataset normalizado para CSV."""

    DATA_RAW_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    dataframe.to_csv(
        ARQUIVO_CSV,
        index=False,
        encoding="utf-8",
    )

    print(
        f"CSV normalizado salvo em: {ARQUIVO_CSV}"
    )


def executar_analises(
    dataframe: pd.DataFrame,
) -> dict:
    """
    Executa todas as RQs registradas em MODULOS_RQ.

    Cada resultado é salvo em data/rq/.
    """

    DATA_RQ_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    resultados = {}

    for nome, modulo in MODULOS_RQ.items():
        resultado = modulo.analisar(dataframe)

        caminho = DATA_RQ_DIR / f"{nome}.json"

        modulo.salvar_json(
            resultado,
            str(caminho),
        )

        resultados[nome] = resultado

        print(
            f"Resultado salvo: {caminho.name}"
        )

    return resultados


def construir_csv_completo(
    dataframe: pd.DataFrame,
    resultados_rq: dict,
) -> pd.DataFrame:
    """
    Reproduz a lógica do CSV completo do app.py.

    Adiciona às linhas do dataset:
    - informação do Top 10 Octoverse;
    - métricas agregadas da RQ07;
    - métricas gerais das demais RQs;
    - métricas da RQ10.
    """

    df_completo = dataframe.copy()

    # ---------------------------------------------------------
    # RQ05 — Top 10 Octoverse
    # ---------------------------------------------------------

    rq05 = resultados_rq.get(
        "rq05_linguagem",
        {},
    )

    top10 = set(
        rq05.get(
            "ranking_referencia_octoverse",
            [],
        )
    )

    if top10:
        df_completo[
            "Linguagem no Top 10 Octoverse"
        ] = (
            df_completo["Linguagem"]
            .isin(top10)
        )

    # ---------------------------------------------------------
    # RQ07 — métricas agregadas por linguagem
    # ---------------------------------------------------------

    rq07 = resultados_rq.get(
        "rq07_cruzamento",
        {},
    )

    resumo_linguagem = pd.DataFrame(
        rq07.get(
            "resumo_por_linguagem",
            [],
        )
    )

    if not resumo_linguagem.empty:

        resumo_linguagem = resumo_linguagem.rename(
            columns={
                "PRs_aceitas_mediana":
                    "PRs aceitas (mediana da linguagem)",

                "Releases_mediana":
                    "Releases (mediana da linguagem)",

                "Dias_desde_atualizacao_mediana":
                    "Dias desde atualização (mediana da linguagem)",
            }
        )

        # Colunas que já podem existir no dataset original
        # não devem gerar conflito no merge.
        colunas_merge = [
            coluna
            for coluna in resumo_linguagem.columns
            if coluna != "Linguagem"
        ]

        df_completo = df_completo.merge(
            resumo_linguagem[
                ["Linguagem"] + colunas_merge
            ],
            on="Linguagem",
            how="left",
        )

    # ---------------------------------------------------------
    # RQs individuais
    # ---------------------------------------------------------

    rq01 = resultados_rq.get(
        "rq01_idade",
        {},
    )

    rq02 = resultados_rq.get(
        "rq02_pr_aceitos",
        {},
    )

    rq03 = resultados_rq.get(
        "rq03_releases",
        {},
    )

    rq04 = resultados_rq.get(
        "rq04_ultima_atualizacao",
        {},
    )

    rq06 = resultados_rq.get(
        "rq06_issues_fechadas",
        {},
    )

    rq10 = resultados_rq.get(
        "rq10_idade_issues",
        {},
    )

    if "idade_mediana_anos" in rq01:
        df_completo[
            "Idade mediana geral (anos)"
        ] = rq01["idade_mediana_anos"]

    if "prs_aceitas_mediana" in rq02:
        df_completo[
            "PRs aceitas mediana geral"
        ] = rq02["prs_aceitas_mediana"]

    if "releases_mediana" in rq03:
        df_completo[
            "Releases mediana geral"
        ] = rq03["releases_mediana"]

    if "dias_desde_atualizacao_mediana" in rq04:
        df_completo[
            "Dias desde atualização mediana geral"
        ] = rq04[
            "dias_desde_atualizacao_mediana"
        ]

    if "percentual_issues_fechadas_mediana" in rq06:
        df_completo[
            "% issues fechadas mediana geral"
        ] = rq06[
            "percentual_issues_fechadas_mediana"
        ]

    if "percentual_no_top10_octoverse" in rq05:
        df_completo[
            "% no Top 10 Octoverse (geral)"
        ] = rq05[
            "percentual_no_top10_octoverse"
        ]

    if "correlacao_spearman" in rq10:
        df_completo[
            "RQ10 - Correlação Spearman idade x issues fechadas"
        ] = rq10[
            "correlacao_spearman"
        ]

    if "repositorios_com_issues" in rq10:
        df_completo[
            "RQ10 - Repositórios com issues"
        ] = rq10[
            "repositorios_com_issues"
        ]

    if "repositorios_sem_issues" in rq10:
        df_completo[
            "RQ10 - Repositórios sem issues"
        ] = rq10[
            "repositorios_sem_issues"
        ]

    return df_completo


def salvar_csv_completo(
    dataframe: pd.DataFrame,
    resultados_rq: dict,
) -> None:
    """Gera o CSV completo com todas as métricas."""

    df_completo = construir_csv_completo(
        dataframe,
        resultados_rq,
    )

    DATA_RAW_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    df_completo.to_csv(
        ARQUIVO_CSV_COMPLETO,
        index=False,
        encoding="utf-8",
    )

    print(
        f"CSV completo salvo em: {ARQUIVO_CSV_COMPLETO}"
    )


def criar_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Coleta repositórios públicos populares do GitHub "
            "e gera os resultados de todas as RQs."
        )
    )

    parser.add_argument(
        "--repos",
        type=int,
        default=TOTAL_REPOSITORIOS_PADRAO,
        help=(
            "Quantidade de repositórios a coletar "
            "(padrão: 1000)."
        ),
    )

    parser.add_argument(
        "--linguagem",
        default="Todas",
        help=(
            "Filtra a coleta por linguagem. "
            "Exemplo: Python, Java, Go. "
            "Padrão: Todas."
        ),
    )

    parser.add_argument(
        "--csv",
        action="store_true",
        help=(
            "Exporta o dataset normalizado para "
            "data/raw/repositorios_populares.csv."
        ),
    )

    parser.add_argument(
        "--csv-completo",
        action="store_true",
        help=(
            "Exporta o dataset com todas as métricas das RQs "
            "para data/raw/repositorios_populares_completo.csv."
        ),
    )

    return parser


def main(
    quantidade: int = TOTAL_REPOSITORIOS_PADRAO,
    linguagem: str = "Todas",
    exportar_csv: bool = False,
    exportar_csv_completo: bool = False,
) -> None:
    if quantidade < 1:
        raise SystemExit(
            "A quantidade de repositórios deve ser maior que zero."
        )

    if quantidade > 1_000:
        raise SystemExit(
            "A quantidade máxima permitida é 1000."
        )

    try:
        token = carregar_token()

        print(
            "=================================================="
        )
        print(
            " GitHub Popular Repositories - Laboratório"
        )
        print(
            "=================================================="
        )
        print(
            f"Quantidade: {quantidade}"
        )
        print(
            f"Linguagem: {linguagem}"
        )
        print(
            "Critério: estrelas em ordem decrescente"
        )
        print(
            "=================================================="
        )

        repositorios = coletar_repositorios(
            token=token,
            linguagem=linguagem,
            quantidade=quantidade,
        )

        exibir_repositorios(repositorios)

        salvar_json(repositorios)

        dataframe = montar_dataframe(
            repositorios
        )

        print(
            "\nDataset normalizado:"
        )
        print(
            f"Linhas: {len(dataframe)}"
        )
        print(
            f"Colunas: {len(dataframe.columns)}"
        )

        resultados_rq = executar_analises(
            dataframe
        )

        if exportar_csv:
            salvar_csv(dataframe)

        if exportar_csv_completo:
            salvar_csv_completo(
                dataframe,
                resultados_rq,
            )

        print(
            "\n=================================================="
        )
        print(
            "Processamento concluído com sucesso."
        )
        print(
            "=================================================="
        )

    except (
        requests.RequestException,
        RuntimeError,
        KeyError,
        ValueError,
    ) as erro:
        raise SystemExit(
            f"Erro: {erro}"
        ) from erro


if __name__ == "__main__":
    argumentos = criar_parser().parse_args()

    main(
        quantidade=argumentos.repos,
        linguagem=argumentos.linguagem,
        exportar_csv=argumentos.csv,
        exportar_csv_completo=argumentos.csv_completo,
    )
