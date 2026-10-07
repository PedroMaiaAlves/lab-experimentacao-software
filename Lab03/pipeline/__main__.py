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

try:  # cliente de C (S01-C1); enquanto não existir, usa o provisório
    from pipeline.http_client import GitHubClient
except ImportError:
    from pipeline.http_client_provisorio import GitHubClient

log = logging.getLogger("pipeline")


def executar_etapas_de_coleta(client, cfg, repos):
    """Executa as etapas de B e C listadas em `etapas_coleta` (módulos com coletar())."""
    for nome in cfg.get("etapas_coleta", []):
        try:
            modulo = importlib.import_module(nome)
        except ModuleNotFoundError as e:
            if e.name == nome:  # o módulo em si não existe ainda
                log.warning("etapa %s ainda não implementada; pulando", nome)
                continue
            raise
        log.info("executando etapa %s", nome)
        modulo.coletar(client, cfg, repos)


def main(argv=None):
    ap = argparse.ArgumentParser(
        prog="python -m pipeline",
        description="Pipeline de mineração das métricas DORA (Lab03).")
    ap.add_argument("--config", default="config.yaml", help="caminho do config.yaml")
    ap.add_argument("--meta", type=int,
                    help="sobrescreve selecao.meta_repositorios (teste rápido, ex.: --meta 5)")
    ap.add_argument("-v", "--verbose", action="store_true", help="logs detalhados")
    args = ap.parse_args(argv)

    logging.basicConfig(level=logging.DEBUG if args.verbose else logging.INFO,
                        format="%(asctime)s %(levelname)s %(name)s: %(message)s")

    token = os.environ.get("GITHUB_TOKEN")
    if not token:
        sys.exit("Erro: defina a variável de ambiente GITHUB_TOKEN (veja o README).")

    cfg = carregar_config(args.config)
    if args.meta:
        cfg["selecao"]["meta_repositorios"] = args.meta

    dados = Path(cfg["saida"]["dir_dados"])
    client = GitHubClient(token, cache_dir=cfg["saida"]["dir_cache"])

    log.info("1/3 selecionando candidatos")
    candidatos = selecionar_candidatos(client, cfg)
    salvar_candidatos(candidatos, dados / "candidatos.csv")

    log.info("2/3 aplicando filtros e coletando metadados")
    repos = executar_funil(client, candidatos, cfg, dados)

    log.info("3/3 coletas de releases e workflow runs")
    executar_etapas_de_coleta(client, cfg, repos)

    log.info("concluído: %d repositórios na amostra. Saídas em %s/", len(repos), dados)


if __name__ == "__main__":
    main()
