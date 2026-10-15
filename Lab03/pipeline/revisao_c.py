"""Fontes da revisão assistida de C, sem ler rótulos ou previsões de A/B."""
import argparse
import base64
from collections import defaultdict
import csv
from datetime import datetime, timezone
import json
import os
from pathlib import Path

import requests

from pipeline.coleta_runs import _salvar_json_atomico
from pipeline.http_client import GitHubClient
from pipeline.sprint2 import ler_csv, salvar_csv, sha256


def preparar_casos(amostra, releases, commits):
    sorteadas = ler_csv(amostra)
    chaves = [(r["full_name"], str(r["release_id"])) for r in sorteadas]
    if len(chaves) != len(set(chaves)):
        raise ValueError("a amostra contém releases duplicadas")
    notas, mensagens = {}, defaultdict(list)
    esperadas = set(chaves)
    with Path(releases).open(encoding="utf-8", newline="") as arquivo:
        for release in csv.DictReader(arquivo):
            chave = release["full_name"], str(release["id"])
            if chave in esperadas:
                notas[chave] = release
    if set(notas) != esperadas:
        raise ValueError("há release sorteada sem notas na fonte fornecida")
    if commits and Path(commits).exists():
        with Path(commits).open(encoding="utf-8", newline="") as arquivo:
            for commit in csv.DictReader(arquivo):
                chave = commit["full_name"], str(commit["release_id"])
                if chave in esperadas and commit.get("message"):
                    mensagens[chave].append(commit["message"])
    return [{**item, "name": notas[chave].get("name", ""),
             "body": notas[chave].get("body", ""), "mensagens_commits": mensagens[chave],
             "origem_notas": f"https://api.github.com/repos/{item['full_name']}/releases/{item['release_id']}"}
            for item, chave in zip(sorteadas, chaves)]


def coletar_documentacao(client, nomes, destino):
    destino = Path(destino)
    destino.mkdir(parents=True, exist_ok=True)
    for nome in sorted(set(nomes)):
        caminho = destino / (nome.replace("/", "__") + ".json")
        if caminho.exists():
            continue
        repo, _ = client.get_json(f"/repos/{nome}")
        if repo.get("private"):
            raise ValueError("a revisão foi limitada a repositórios públicos")
        readme, indisponivel = "", False
        try:
            resposta, _ = client.get_json(f"/repos/{nome}/readme")
            if resposta.get("encoding") != "base64":
                raise ValueError("README sem codificação base64 esperada")
            readme = base64.b64decode(resposta["content"]).decode("utf-8", errors="replace")
        except requests.HTTPError as erro:
            if erro.response is None or erro.response.status_code != 404:
                raise
            indisponivel = True
        _salvar_json_atomico(caminho, {"full_name": nome, "description": repo.get("description"),
                                     "html_url": repo["html_url"], "readme": readme,
                                     "readme_indisponivel": indisponivel,
                                     "origem": f"https://api.github.com/repos/{nome}/readme"})
        print(f"documentação: {nome}", flush=True)


def preparar(amostra, releases, commits, saida):
    casos = preparar_casos(amostra, releases, commits)
    destino = Path(saida)
    destino.mkdir(parents=True, exist_ok=True)
    fontes = {"amostra": str(amostra), "amostra_sha256": sha256(amostra),
              "releases": str(releases), "releases_sha256": sha256(releases)}
    if commits and Path(commits).exists():
        fontes.update(commits=str(commits), commits_sha256=sha256(commits))
    manifesto = {"gerado_em": datetime.now(timezone.utc).isoformat(),
                 "avaliador": "C", "origem_avaliacao": "assistida_por_IA",
                 "avaliacao_humana_declarada": False, "estado": "provisoria_aguarda_amostra_definitiva",
                 "repositorios": len({r["full_name"] for r in casos}), "releases": len(casos),
                 "fontes": fontes, "rotulos_de_outros_avaliadores_lidos": False,
                 "saida_heuristica_lida": False}
    _salvar_json_atomico(destino / "fontes_releases.json", {"casos": casos})
    _salvar_json_atomico(destino / "manifesto.json", manifesto)
    return casos


def exportar_avaliacao(diretorio):
    diretorio = Path(diretorio)
    fontes = diretorio / "fontes_releases.json"
    casos = json.loads(fontes.read_text(encoding="utf-8"))["casos"]
    avaliacao = json.loads((diretorio / "avaliacao_c.json").read_text(encoding="utf-8"))
    repos = json.loads((diretorio / "avaliacao_repos_c.json").read_text(encoding="utf-8"))
    for documento in (avaliacao, repos):
        if documento["origem"] != "assistida_por_IA" or documento["avaliacao_humana_declarada"] is not False:
            raise ValueError("a revisão C deve preservar sua origem assistida por IA")
    if avaliacao["fontes_sha256"] != sha256(fontes):
        raise ValueError("fontes diferentes das usadas na avaliação")
    itens = avaliacao["releases"]
    if len(itens) != len(casos) or sorted(r[0] for r in itens) != list(range(len(casos))):
        raise ValueError("cada release precisa de exatamente uma avaliação")
    nomes = {c["full_name"] for c in casos}
    tipos = {"biblioteca/framework", "aplicação/serviço", "ferramenta CLI", "outro"}
    escopos = {"completa", "parcial", "ambigua", "insuficiente"}
    mapa, linhas_repos = {}, []
    for nome, tipo, entregas, motivo, escopo in repos["repositorios"]:
        if nome in mapa or tipo not in tipos or entregas not in {"sim", "não", "incerto"}:
            raise ValueError("avaliação de repositório inválida ou duplicada")
        if not motivo.strip() or escopo not in escopos:
            raise ValueError("repositório sem justificativa ou escopo válido")
        doc = diretorio / "documentacao" / (nome.replace("/", "__") + ".json")
        mapa[nome] = {"full_name": nome, "tipo_projeto": tipo, "releases_sao_entregas": entregas,
                      "justificativa": motivo, "escopo_evidencia": escopo,
                      "origem": "assistida_por_IA", "avaliacao_humana_declarada": False,
                      "fonte": f"https://github.com/{nome}", "documentacao_sha256": sha256(doc)}
        linhas_repos.append(mapa[nome])
    if set(mapa) != nomes:
        raise ValueError("avaliações não cobrem exatamente os repositórios das fontes")
    linhas = []
    for indice, corretiva, motivo, escopo in sorted(itens):
        if corretiva not in {"sim", "não", None} or not motivo.strip() or escopo not in escopos:
            raise ValueError("avaliação de release inválida")
        if (corretiva is None) != (escopo == "insuficiente"):
            raise ValueError("evidência insuficiente deve permanecer sem rótulo")
        caso = casos[indice]
        repo = mapa[caso["full_name"]]
        linhas.append({"full_name": caso["full_name"], "release_id": caso["release_id"],
                       "tag_name": caso["tag_name"], "published_at": caso["published_at"],
                       "tipo_projeto": repo["tipo_projeto"], "releases_sao_entregas": repo["releases_sao_entregas"],
                       "corretiva": corretiva, "justificativa": motivo, "escopo_evidencia": escopo,
                       "origem": "assistida_por_IA", "avaliacao_humana_declarada": False,
                       "revisao_confirmada": "não", "release_url": caso["release_url"],
                       "compare_url": caso["compare_url"], "origem_notas": caso["origem_notas"]})
    if not linhas:
        raise ValueError("não há avaliações para exportar")
    salvar_csv(diretorio / "rotulos_repos_C.csv", list(linhas_repos[0]), linhas_repos)
    salvar_csv(diretorio / "rotulos_releases_C.csv", list(linhas[0]), linhas)
    manifesto = json.loads((diretorio / "manifesto.json").read_text(encoding="utf-8"))
    manifesto.update(releases_examinadas=len(linhas),
                     releases_sem_rotulo=sum(r["corretiva"] is None for r in linhas),
                     escopos={e: sum(r["escopo_evidencia"] == e for r in linhas) for e in sorted(escopos)},
                     revisao_independente_definitiva=False,
                     artefatos_sha256={p.name: sha256(p) for p in (
                         fontes, diretorio / "avaliacao_c.json", diretorio / "avaliacao_repos_c.json",
                         diretorio / "rotulos_repos_C.csv", diretorio / "rotulos_releases_C.csv")})
    _salvar_json_atomico(diretorio / "manifesto.json", manifesto)
    return manifesto


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--amostra", default="data/amostra_ouro/releases_sorteadas.csv")
    parser.add_argument("--releases", default="data/releases.csv")
    parser.add_argument("--commits", default="data/commits_entre_releases_s02.csv")
    parser.add_argument("--saida", default="data/revisao_c_provisoria")
    parser.add_argument("--documentacao", action="store_true")
    parser.add_argument("--exportar", action="store_true", help="valida avaliações explícitas e exporta CSVs")
    args = parser.parse_args(argv)
    if args.exportar:
        print(json.dumps(exportar_avaliacao(args.saida), ensure_ascii=False, indent=2))
        return
    casos = preparar(args.amostra, args.releases, args.commits, args.saida)
    if args.documentacao:
        token = os.environ.get("GITHUB_TOKEN")
        if not token:
            parser.error("defina GITHUB_TOKEN para consultar a documentação pública")
        client = GitHubClient(token, cache_dir="cache/revisao_c")
        coletar_documentacao(client, [r["full_name"] for r in casos], Path(args.saida) / "documentacao")
    print(f"Fontes preparadas: {len(casos)} releases; nenhum rótulo gerado automaticamente.")


if __name__ == "__main__":
    main()
