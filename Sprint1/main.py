"""Coleta os 1.000 repositórios e gera os resultados das RQ01 a RQ07."""

import argparse
import json
import os
from pathlib import Path

import requests
from dotenv import load_dotenv

from analysis import MODULOS_RQ
from github_collector.client import GRAPHQL_URL
from github_collector.schema import GRAPHQL_QUERY
from utils import montar_dataframe


TOTAL_REPOSITORIOS = 1_000
TAMANHO_PAGINA = 50
BASE_DIR = Path(__file__).resolve().parent
ARQUIVO_SAIDA = BASE_DIR / "data" / "raw" / "repositorios_graphql.json"
ARQUIVO_CSV = BASE_DIR / "data" / "raw" / "repositorios_populares.csv"
DIRETORIO_RQS = BASE_DIR / "data" / "rq"


def carregar_token() -> str:
    """Lê GITHUB_TOKEN do .env de Sprint1 ou da raiz do repositório."""

    load_dotenv(BASE_DIR / ".env")
    load_dotenv(BASE_DIR.parent / ".env")
    token = os.getenv("GITHUB_TOKEN", "").strip()
    if not token:
        raise RuntimeError("Configure GITHUB_TOKEN no arquivo .env.")
    return token


def coletar_repositorios(token: str) -> list[dict]:
    """Consulta páginas via cursor até completar 1.000 repositórios únicos."""

    repositorios = []
    nomes_coletados = set()
    cursores_vistos = set()
    cursor = None

    with requests.Session() as sessao:
        sessao.headers["Authorization"] = f"Bearer {token}"

        while len(repositorios) < TOTAL_REPOSITORIOS:
            variaveis = {
                "queryString": "stars:>0 is:public sort:stars-desc",
                "first": min(
                    TAMANHO_PAGINA,
                    TOTAL_REPOSITORIOS - len(repositorios),
                ),
                "after": cursor,
            }
            resposta = sessao.post(
                GRAPHQL_URL,
                json={"query": GRAPHQL_QUERY, "variables": variaveis},
                timeout=30,
            )
            resposta.raise_for_status()
            payload = resposta.json()

            if payload.get("errors"):
                raise RuntimeError(payload["errors"][0]["message"])

            busca = payload["data"]["search"]
            pagina = [
                edge["node"]
                for edge in busca["edges"]
                if edge.get("node") is not None
            ]
            if not pagina:
                raise RuntimeError(
                    "O GitHub retornou uma página vazia antes de completar "
                    f"os {TOTAL_REPOSITORIOS} repositórios."
                )

            for repositorio in pagina:
                nome = repositorio["nameWithOwner"]
                if nome in nomes_coletados:
                    continue
                nomes_coletados.add(nome)
                repositorios.append(repositorio)

            print(f"Coletados: {len(repositorios)}/{TOTAL_REPOSITORIOS}")

            if len(repositorios) >= TOTAL_REPOSITORIOS:
                break

            page_info = busca["pageInfo"]
            if not page_info["hasNextPage"]:
                raise RuntimeError(
                    "A busca terminou antes de completar "
                    f"{TOTAL_REPOSITORIOS} repositórios únicos; "
                    f"foram coletados {len(repositorios)}."
                )

            proximo_cursor = page_info["endCursor"]
            if not proximo_cursor or proximo_cursor in cursores_vistos:
                raise RuntimeError(
                    "A paginação não avançou: o GitHub retornou um cursor "
                    "ausente ou repetido."
                )
            cursores_vistos.add(proximo_cursor)
            cursor = proximo_cursor

    return repositorios


def exibir_repositorios(repositorios: list[dict]) -> None:
    """Exibe os valores principais recebidos da API."""

    print("\nPos | Repositório                          | Estrelas   | Linguagem")
    print("-" * 76)
    for posicao, repositorio in enumerate(repositorios, start=1):
        linguagem = repositorio.get("primaryLanguage")
        nome_linguagem = linguagem["name"] if linguagem else "Não definida"
        print(
            f"{posicao:>3} | "
            f"{repositorio['nameWithOwner'][:36]:<36} | "
            f"{repositorio['stargazerCount']:>10} | "
            f"{nome_linguagem}"
        )


def salvar_json(repositorios: list[dict]) -> None:
    ARQUIVO_SAIDA.parent.mkdir(parents=True, exist_ok=True)
    ARQUIVO_SAIDA.write_text(
        json.dumps(repositorios, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(f"\nJSON salvo em: {ARQUIVO_SAIDA}")


def salvar_csv(dataframe) -> None:
    """Exporta o dataset normalizado para CSV quando solicitado."""

    ARQUIVO_CSV.parent.mkdir(parents=True, exist_ok=True)
    dataframe.to_csv(ARQUIVO_CSV, index=False, encoding="utf-8")
    print(f"CSV salvo em: {ARQUIVO_CSV}")


def salvar_resultados_rqs(dataframe) -> None:
    """Executa cada análise e salva um JSON por questão de pesquisa."""

    DIRETORIO_RQS.mkdir(parents=True, exist_ok=True)

    for nome, modulo in MODULOS_RQ.items():
        resultado = modulo.analisar(dataframe)
        caminho = DIRETORIO_RQS / f"{nome}.json"
        modulo.salvar_json(resultado, str(caminho))
        print(f"Resultado salvo: {caminho.name}")


def criar_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Coleta os 1.000 repositórios públicos com mais estrelas do GitHub "
            "e gera os resultados das RQ01 a RQ07."
        )
    )
    parser.add_argument(
        "--csv",
        action="store_true",
        help=(
            "também exporta o dataset normalizado para "
            "data/raw/repositorios_populares.csv"
        ),
    )
    return parser


def main(exportar_csv: bool = False) -> None:
    try:
        repositorios = coletar_repositorios(carregar_token())
        exibir_repositorios(repositorios)
        salvar_json(repositorios)
        dataframe = montar_dataframe(repositorios)
        if exportar_csv:
            salvar_csv(dataframe)
        salvar_resultados_rqs(dataframe)
    except (requests.RequestException, RuntimeError, KeyError) as erro:
        raise SystemExit(f"Erro: {erro}") from erro


if __name__ == "__main__":
    argumentos = criar_parser().parse_args()
    main(exportar_csv=argumentos.csv)
