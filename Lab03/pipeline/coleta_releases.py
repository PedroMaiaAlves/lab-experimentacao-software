import logging
from pathlib import Path

import requests

from metricas.deployment_frequency import deployment_frequency
from pipeline.arquivos import abrir_csv
from pipeline.config import semanas_da_janela
from pipeline.janela import na_janela

log = logging.getLogger(__name__)
CAMPOS_RELEASES = ["full_name", "id", "tag_name", "target_commitish", "draft", "prerelease",
                   "published_at", "created_at", "html_url", "name", "body"]
CAMPOS_TAGS = ["full_name", "tag_name", "commit_sha", "commit_author_date", "status"]
CAMPOS_FREQUENCIA = ["full_name", "deployment_frequency", "releases_principais", "semanas_janela"]

_QUERY_TAGS = """
query($owner: String!, $name: String!, $cursor: String) {
  repository(owner: $owner, name: $name) {
    refs(refPrefix: "refs/tags/", first: 100, after: $cursor,
         orderBy: {field: TAG_COMMIT_DATE, direction: DESC}) {
      pageInfo { hasNextPage endCursor }
      nodes {
        name
        target {
          __typename
          ... on Commit { oid authoredDate }
          ... on Tag {
            target { ... on Commit { oid authoredDate } }
          }
        }
      }
    }
  }
}
"""


def filtrar_releases(releases, cfg, incluir_prereleases=False):
    return [release for release in releases if not release["draft"]
            and (incluir_prereleases or not release["prerelease"])
            and na_janela(release["published_at"], cfg)]


def coletar_releases(client, nome):
    releases = client.paginate(f"/repos/{nome}/releases", {"per_page": 100})
    return list({release["id"]: release for release in releases}.values())


def _dados_commit_tag(target):
    if not target:
        return None
    if target.get("__typename") == "Commit":
        return target
    if target.get("__typename") == "Tag":
        interno = target.get("target")
        if interno and interno.get("oid"):
            return interno
    return None


def _coletar_tags_graphql(client, nome):
    owner, repositorio = nome.split("/", 1)
    cursor = None
    while True:
        dados, _ = client.post_json("/graphql", {
            "query": _QUERY_TAGS,
            "variables": {"owner": owner, "name": repositorio, "cursor": cursor},
        })
        if dados.get("errors"):
            raise RuntimeError(f"GraphQL recusou a coleta de tags de {nome}: {dados['errors']}")
        refs = dados["data"]["repository"]["refs"]
        for node in refs["nodes"]:
            commit = _dados_commit_tag(node.get("target"))
            yield {
                "full_name": nome,
                "tag_name": node["name"],
                "commit_sha": commit.get("oid") if commit else None,
                "commit_author_date": commit.get("authoredDate") if commit else None,
                "status": "ok" if commit else "sem_commit",
            }
        pagina = refs["pageInfo"]
        if not pagina["hasNextPage"]:
            break
        cursor = pagina["endCursor"]


def _coletar_tags_rest(client, nome):
    datas = {}
    for tag in client.paginate(f"/repos/{nome}/tags", {"per_page": 100}):
        sha = tag["commit"]["sha"]
        if sha not in datas:
            try:
                commit, _ = client.get_json(f"/repos/{nome}/commits/{sha}")
                datas[sha] = (commit["commit"]["author"]["date"], "ok")
            except requests.HTTPError as erro:
                if erro.response is None or erro.response.status_code != 404:
                    raise
                datas[sha] = (None, "erro_404")
                log.warning("commit da tag indisponível: %s %s", nome, tag["name"])
        data, status = datas[sha]
        yield {"full_name": nome, "tag_name": tag["name"], "commit_sha": sha,
               "commit_author_date": data, "status": status}


def coletar_tags(client, nome):
    """Coleta tags em lotes GraphQL; clientes de teste/legados usam REST."""
    if hasattr(client, "post_json"):
        yield from _coletar_tags_graphql(client, nome)
    else:
        yield from _coletar_tags_rest(client, nome)


def coletar(client, cfg, repos):
    saida = Path(cfg["saida"]["dir_dados"])
    with abrir_csv(saida / "releases.csv", CAMPOS_RELEASES) as releases_csv, \
            abrir_csv(saida / "tags.csv", CAMPOS_TAGS) as tags_csv, \
            abrir_csv(saida / "deployment_frequency.csv", CAMPOS_FREQUENCIA) as frequencia_csv:
        for repo in repos:
            nome = repo["full_name"]
            releases = coletar_releases(client, nome)
            releases_csv.writerows({"full_name": nome, **{campo: release.get(campo)
                                   for campo in CAMPOS_RELEASES[1:]}} for release in releases)
            tags_csv.writerows(coletar_tags(client, nome))
            principais = filtrar_releases(releases, cfg)
            frequencia_csv.writerow({"full_name": nome, "releases_principais": len(principais),
                                     "semanas_janela": semanas_da_janela(cfg),
                                     "deployment_frequency": deployment_frequency(
                                         (release["published_at"] for release in principais), cfg)})
            log.info("%s: %d releases preservadas, %d na definição principal", nome,
                     len(releases), len(principais))
