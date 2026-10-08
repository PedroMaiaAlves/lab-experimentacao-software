"""Ponto de entrada único: python -m pipeline --config config.yaml"""
import argparse
import importlib
import logging
import os
import sys
from pathlib import Path

from pipeline.candidatos import salvar_candidatos, selecionar_candidatos
from pipeline.config import carregar_config
from pipeline.funil import executar_funil
from pipeline.http_client import GitHubClient
from pipeline.validacao_s01 import validar_artefatos_s01

log = logging.getLogger("pipeline")


def validar_tamanho_amostra(repos, meta):
    if len(repos) < meta:
        raise RuntimeError(
            f"amostra insuficiente: {len(repos)} repositórios aceitos; meta configurada: {meta}"
        )


def executar_etapas_de_coleta(client, cfg, repos):
    """Executa as etapas de B e C listadas em `etapas_coleta` (módulos com coletar())."""
    for nome in cfg.get("etapas_coleta", []):
        modulo = importlib.import_module(nome)
        log.info("executando etapa %s", nome)
        modulo.coletar(client, cfg, repos)


def executar_pipeline(client, cfg):
    """Executa todas as etapas na ordem e devolve a amostra aprovada pelo funil."""
    dados = Path(cfg["saida"]["dir_dados"])

    log.info("1/3 selecionando candidatos")
    candidatos = selecionar_candidatos(client, cfg)
    salvar_candidatos(candidatos, dados / "candidatos.csv")

    log.info("2/3 aplicando filtros e coletando metadados")
    repos = executar_funil(client, candidatos, cfg, dados)
    validar_tamanho_amostra(repos, cfg["selecao"]["meta_repositorios"])

    log.info("3/3 coletas de releases, tags, commits e workflow runs")
    executar_etapas_de_coleta(client, cfg, repos)
    validar_artefatos_s01(cfg, repos)
    return repos


def main(argv=None):
    ap = argparse.ArgumentParser(
        prog="python -m pipeline",
        description="Pipeline de mineração das métricas DORA (Lab03).")
    ap.add_argument("--config", default="config.yaml", help="caminho do config.yaml")
    ap.add_argument("--meta", type=int,
                    help="sobrescreve selecao.meta_repositorios (teste rápido, ex.: --meta 5)")
    ap.add_argument("-v", "--verbose", action="store_true", help="logs detalhados")
    args = ap.parse_args(argv)

    if args.meta is not None and args.meta <= 0:
        ap.error("--meta deve ser um inteiro positivo")

    logging.basicConfig(level=logging.DEBUG if args.verbose else logging.INFO,
                        format="%(asctime)s %(levelname)s %(name)s: %(message)s")

    token = os.environ.get("GITHUB_TOKEN")
    if not token:
        sys.exit("Erro: defina a variável de ambiente GITHUB_TOKEN (veja o README).")

    cfg = carregar_config(args.config)
    if args.meta is not None:
        cfg["selecao"]["meta_repositorios"] = args.meta

    client = GitHubClient(token, cache_dir=cfg["saida"]["dir_cache"])
    repos = executar_pipeline(client, cfg)
    log.info(
        "concluído: %d repositórios na amostra. Saídas em %s/",
        len(repos), cfg["saida"]["dir_dados"],
    )


if __name__ == "__main__":
    main()
