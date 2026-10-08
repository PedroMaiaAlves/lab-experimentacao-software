import csv
import logging
from collections import defaultdict
from pathlib import Path
from urllib.parse import quote

import requests

from metricas.lead_time import calcular_lead_time
from pipeline.arquivos import abrir_csv
from pipeline.janela import na_janela

log = logging.getLogger(__name__)
CAMPOS_COMPARACOES = ["full_name", "release_id", "tag_name", "published_at",
                      "previous_tag_name", "status", "commits_count"]
CAMPOS_COMMITS = ["full_name", "release_id", "tag_name", "published_at",
                  "previous_tag_name", "sha", "author_date"]
CAMPOS_METRICAS = ["full_name", "lead_time_a_horas", "lead_time_b_horas", "releases_comparadas",
                   "releases_sem_anterior", "releases_erro_404", "releases_sem_commits"]


def coletar_commits(client, nome, releases, cfg, incluir_prereleases=False):
    historico = sorted((release for release in releases if not release["draft"]
                       and release["published_at"]
                       and (incluir_prereleases or not release["prerelease"])),
                      key=lambda release: (release["published_at"], release["id"]))
    comparacoes = []
    for indice, release in enumerate(historico):
        if not na_janela(release["published_at"], cfg):
            continue
        anterior = historico[indice - 1]["tag_name"] if indice else None
        registro = {"release_id": release["id"], "tag_name": release["tag_name"],
                    "published_at": release["published_at"], "previous_tag_name": anterior,
                    "status": "ok" if anterior is not None else "sem_anterior", "commits": []}
        if anterior is not None:
            caminho = f"/repos/{nome}/compare/{quote(anterior, safe='')}...{quote(release['tag_name'], safe='')}"
            try:
                commits = client.paginate(caminho, {"per_page": 100}, chave="commits")
                unicos = {commit["sha"]: {"sha": commit["sha"],
                          "author_date": commit["commit"]["author"]["date"]} for commit in commits}
                registro["commits"] = list(unicos.values())
            except requests.HTTPError as erro:
                if erro.response is None or erro.response.status_code != 404:
                    raise
                registro["status"] = "erro_404"
                log.warning("comparação indisponível: %s %s...%s", nome, anterior, release["tag_name"])
        comparacoes.append(registro)
    return comparacoes


def _ler_releases(caminho):
    por_repo = defaultdict(list)
    with caminho.open(newline="", encoding="utf-8") as arquivo:
        for release in csv.DictReader(arquivo):
            for campo in ("draft", "prerelease"):
                release[campo] = release[campo] == "True"
            release["id"] = int(release["id"])
            por_repo[release["full_name"]].append(release)
    return por_repo


def coletar(client, cfg, repos):
    saida = Path(cfg["saida"]["dir_dados"])
    releases = _ler_releases(saida / "releases.csv")
    with abrir_csv(saida / "comparacoes_releases.csv", CAMPOS_COMPARACOES) as comparacoes_csv, \
            abrir_csv(saida / "commits_entre_releases.csv", CAMPOS_COMMITS) as commits_csv, \
            abrir_csv(saida / "lead_time.csv", CAMPOS_METRICAS) as metricas_csv:
        for repo in repos:
            nome = repo["full_name"]
            comparacoes = coletar_commits(client, nome, releases[nome], cfg)
            for comparacao in comparacoes:
                dados = {"full_name": nome, **{campo: comparacao[campo]
                         for campo in CAMPOS_COMPARACOES[1:-1]}}
                comparacoes_csv.writerow({**dados, "commits_count": len(comparacao["commits"])})
                commits_csv.writerows({**{campo: dados[campo] for campo in CAMPOS_COMMITS[:5]},
                                       **commit} for commit in comparacao["commits"])
            contagens = {"releases_comparadas": sum(c["status"] == "ok" for c in comparacoes),
                         "releases_sem_anterior": sum(c["status"] == "sem_anterior" for c in comparacoes),
                         "releases_erro_404": sum(c["status"] == "erro_404" for c in comparacoes),
                         "releases_sem_commits": sum(c["status"] == "ok" and not c["commits"] for c in comparacoes)}
            metricas_csv.writerow({"full_name": nome, **calcular_lead_time(comparacoes), **contagens})
            log.info("%s: %d comparações, %d ignoradas por 404", nome,
                     contagens["releases_comparadas"], contagens["releases_erro_404"])
