"""S02-A1: sorteio reprodutível da amostra-ouro e planilhas de rotulagem.

Não inclui a saída da heurística. As três planilhas são idênticas e saem em branco
nas colunas a preencher (tipo, entregas reais, corretiva).
"""
from __future__ import annotations

import argparse
import logging
from pathlib import Path

import pandas as pd

from pipeline.coleta_releases import filtrar_releases
from pipeline.config import carregar_config

log = logging.getLogger(__name__)

N_REPOSITORIOS = 60
N_RELEASES = 5
SEMENTE_REPOSITORIOS = 42
SEMENTE_RELEASES = 43

COLUNAS_RELEASES = [
    "full_name", "id", "tag_name", "html_url", "published_at", "draft", "prerelease",
]
COLUNAS_SORTEADAS = [
    "full_name", "release_id", "tag_name", "html_url", "published_at", "indice",
]
CAMPOS_ROTULO = [
    "full_name",
    "repo_html_url",
    "tipo_projeto",
    "entregas_reais",
]
for _i in range(1, N_RELEASES + 1):
    CAMPOS_ROTULO.extend([
        f"r{_i}_tag",
        f"r{_i}_html_url",
        f"r{_i}_corretiva",
    ])

TIPOS_PROJETO = (
    "biblioteca/framework",
    "aplicacao/servico",
    "ferramenta_cli",
    "outro",
)
ENTREGAS_REAIS = ("sim", "nao", "incerto")
CORRETIVA = ("sim", "nao")


def _bool(valor):
    if isinstance(valor, bool):
        return valor
    if valor is None or (isinstance(valor, float) and pd.isna(valor)):
        return False
    return str(valor).strip().lower() in {"true", "1", "yes", "sim"}


def caminho_amostra(dir_dados: Path) -> Path:
    final = dir_dados / "amostra_final.csv"
    if final.exists():
        return final
    return dir_dados / "metadados.csv"


def carregar_populacao(dir_dados: Path) -> pd.DataFrame:
    caminho = caminho_amostra(dir_dados)
    df = pd.read_csv(caminho)
    if "full_name" not in df.columns:
        raise ValueError(f"{caminho} precisa da coluna full_name")
    df = df.drop_duplicates(subset=["full_name"]).reset_index(drop=True)
    log.info("população para o sorteio: %s (%d repositórios)", caminho, len(df))
    if caminho.name != "amostra_final.csv":
        log.warning(
            "amostra_final.csv ausente; usando %s. Sorteie de novo quando C congelar a amostra.",
            caminho.name,
        )
    return df


def carregar_releases(dir_dados: Path) -> pd.DataFrame:
    caminho = dir_dados / "releases.csv"
    df = pd.read_csv(caminho, usecols=lambda c: c in COLUNAS_RELEASES)
    faltando = [c for c in COLUNAS_RELEASES if c not in df.columns]
    if faltando:
        raise ValueError(f"releases.csv sem colunas: {', '.join(faltando)}")
    return df


def releases_elegiveis(df: pd.DataFrame, cfg) -> pd.DataFrame:
    """Mesma definição principal de deploy: não draft, não pré-release, na janela."""
    registros = []
    for linha in df.to_dict("records"):
        registros.append({
            "full_name": linha["full_name"],
            "id": linha["id"],
            "tag_name": linha["tag_name"],
            "html_url": linha["html_url"],
            "published_at": linha["published_at"],
            "draft": _bool(linha["draft"]),
            "prerelease": _bool(linha["prerelease"]),
        })
    filtradas = filtrar_releases(registros, cfg, incluir_prereleases=False)
    return pd.DataFrame(filtradas)


def sortear_repositorios(populacao: pd.DataFrame, n=N_REPOSITORIOS, semente=SEMENTE_REPOSITORIOS):
    if len(populacao) < n:
        raise ValueError(
            f"população insuficiente para a amostra-ouro: {len(populacao)} < {n}"
        )
    return populacao.sample(n=n, random_state=semente).reset_index(drop=True)


def sortear_releases_do_repositorio(
    elegiveis: pd.DataFrame,
    full_name: str,
    n=N_RELEASES,
    semente=SEMENTE_RELEASES,
):
    do_repo = elegiveis[elegiveis["full_name"] == full_name]
    if len(do_repo) < n:
        raise ValueError(
            f"{full_name} tem {len(do_repo)} releases elegíveis; precisa de {n}"
        )
    return do_repo.sample(n=n, random_state=semente).sort_values("published_at")


def montar_linha_rotulo(full_name: str, releases: pd.DataFrame) -> dict:
    linha = {
        "full_name": full_name,
        "repo_html_url": f"https://github.com/{full_name}",
        "tipo_projeto": "",
        "entregas_reais": "",
    }
    for indice, release in enumerate(releases.to_dict("records"), start=1):
        linha[f"r{indice}_tag"] = release["tag_name"]
        linha[f"r{indice}_html_url"] = release["html_url"]
        linha[f"r{indice}_corretiva"] = ""
    return linha


def gerar_amostra_ouro(dir_dados: Path, cfg, n_repos=N_REPOSITORIOS, n_releases=N_RELEASES):
    populacao = carregar_populacao(dir_dados)
    repos = sortear_repositorios(populacao, n=n_repos)
    elegiveis = releases_elegiveis(carregar_releases(dir_dados), cfg)

    linhas_rotulo = []
    linhas_sorteadas = []
    for full_name in repos["full_name"]:
        sorteadas = sortear_releases_do_repositorio(
            elegiveis, full_name, n=n_releases,
        )
        linhas_rotulo.append(montar_linha_rotulo(full_name, sorteadas))
        for indice, release in enumerate(sorteadas.to_dict("records"), start=1):
            linhas_sorteadas.append({
                "full_name": full_name,
                "release_id": release["id"],
                "tag_name": release["tag_name"],
                "html_url": release["html_url"],
                "published_at": release["published_at"],
                "indice": indice,
            })

    rotulos = pd.DataFrame(linhas_rotulo, columns=CAMPOS_ROTULO)
    sorteadas = pd.DataFrame(linhas_sorteadas, columns=COLUNAS_SORTEADAS)
    return repos, rotulos, sorteadas


def _confirmar_sem_heuristica(rotulos: pd.DataFrame):
    proibidas = [c for c in rotulos.columns if "heuri" in c.lower() or c.lower().startswith("cfr")]
    if proibidas:
        raise ValueError(f"planilha de rotulagem não pode incluir a heurística: {proibidas}")


def salvar_planilhas(dir_dados: Path, rotulos: pd.DataFrame, sorteadas: pd.DataFrame):
    _confirmar_sem_heuristica(rotulos)
    pasta = dir_dados / "rotulos"
    pasta.mkdir(parents=True, exist_ok=True)
    for avaliador in ("A", "B", "C"):
        destino = pasta / f"rotulos_{avaliador}.csv"
        rotulos.to_csv(destino, index=False, encoding="utf-8")
        log.info("gravado %s", destino)
    destino_sorteio = pasta / "releases_sorteadas.csv"
    sorteadas.to_csv(destino_sorteio, index=False, encoding="utf-8")
    log.info("gravado %s", destino_sorteio)


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Sorteia a amostra-ouro e gera as três planilhas de rotulagem.",
    )
    parser.add_argument("--config", default="config.yaml")
    args = parser.parse_args(argv)
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
    cfg = carregar_config(args.config)
    dir_dados = Path(cfg["saida"]["dir_dados"])
    _repos, rotulos, sorteadas = gerar_amostra_ouro(dir_dados, cfg)
    salvar_planilhas(dir_dados, rotulos, sorteadas)
    print(
        f"amostra-ouro: {len(rotulos)} repositórios, "
        f"{len(sorteadas)} releases; planilhas em {dir_dados / 'rotulos'}/"
    )


if __name__ == "__main__":
    main()
