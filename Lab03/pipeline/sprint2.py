"""Coleta retomável de C; não modifica os artefatos da Sprint 1 nem os rótulos."""
import argparse
from contextlib import contextmanager
import csv
from datetime import datetime, timezone
import hashlib
import json
import logging
import os
from pathlib import Path
import shutil

import requests

from pipeline.candidatos import carregar_candidatos, salvar_candidatos, selecionar_candidatos
from pipeline.coleta_commits import coletar as coletar_commits
from pipeline.coleta_releases import coletar as coletar_releases
from pipeline.coleta_runs import coletar as coletar_runs, _salvar_json_atomico
from pipeline.config import carregar_config
from pipeline.funil import coletar_metadados, contar_releases_janela, contar_runs_validos, usa_actions
from pipeline.http_client import GitHubClient
from pipeline.validacao_s01 import CSVS_OBRIGATORIOS, _validar_releases, _validar_runs, validar_artefatos_s01

log = logging.getLogger(__name__)
CAMPOS_META = ["full_name", "stars", "language", "default_branch", "created_at",
               "idade_dias", "contribuidores"]
ETAPAS = ("actions", "releases", "runs")


def sha256(caminho):
    resumo = hashlib.sha256()
    with Path(caminho).open("rb") as arquivo:
        for bloco in iter(lambda: arquivo.read(1024 * 1024), b""):
            resumo.update(bloco)
    return resumo.hexdigest()


def ler_csv(caminho):
    with Path(caminho).open(encoding="utf-8", newline="") as arquivo:
        return list(csv.DictReader(arquivo))


def salvar_csv(caminho, campos, linhas):
    caminho = Path(caminho)
    caminho.parent.mkdir(parents=True, exist_ok=True)
    temporario = caminho.with_suffix(caminho.suffix + ".tmp")
    with temporario.open("w", encoding="utf-8", newline="") as arquivo:
        writer = csv.DictWriter(arquivo, fieldnames=campos)
        writer.writeheader()
        writer.writerows(linhas)
    temporario.replace(caminho)


@contextmanager
def exclusividade(caminho):
    caminho = Path(caminho)
    caminho.parent.mkdir(parents=True, exist_ok=True)
    with caminho.open("a+b") as arquivo:
        arquivo.seek(0)
        if os.name == "nt":
            import msvcrt
            if caminho.stat().st_size == 0:
                arquivo.write(b"0")
                arquivo.flush()
            arquivo.seek(0)
            try:
                msvcrt.locking(arquivo.fileno(), msvcrt.LK_NBLCK, 1)
            except OSError as erro:
                raise RuntimeError("já existe uma coleta S02 em execução") from erro
        else:
            import fcntl
            try:
                fcntl.flock(arquivo, fcntl.LOCK_EX | fcntl.LOCK_NB)
            except OSError as erro:
                raise RuntimeError("já existe uma coleta S02 em execução") from erro
        try:
            yield
        finally:
            arquivo.seek(0)
            if os.name == "nt":
                msvcrt.locking(arquivo.fileno(), msvcrt.LK_UNLCK, 1)
            else:
                fcntl.flock(arquivo, fcntl.LOCK_UN)


def pasta_repo(dados, nome):
    return Path(dados) / "coletas" / nome.replace("/", "__")


def fontes_repo(dados, nome):
    pasta = pasta_repo(dados, nome)
    arquivos = [pasta / c for c in ("releases.csv", "comparacoes_releases.csv",
                                   "commits_entre_releases.csv", "tags.csv")]
    arquivos.append(pasta / "workflow_runs" / (nome.replace("/", "__") + ".json"))
    return {str(p.relative_to(pasta)).replace("\\", "/"): sha256(p) for p in arquivos}


def selecionar(client, cfg, candidatos, checkpoint, salvar):
    testes = (
        lambda c: usa_actions(client, c["full_name"]),
        lambda c: contar_releases_janela(client, c["full_name"], cfg,
                                        cfg["criterios"]["min_releases"]) >= cfg["criterios"]["min_releases"],
        lambda c: contar_runs_validos(client, c["full_name"], c["default_branch"], cfg,
                                      cfg["criterios"]["min_runs"]) >= cfg["criterios"]["min_runs"],
    )
    meta = cfg["selecao"]["meta_repositorios"]
    while checkpoint["proximo"] < len(candidatos) and len(checkpoint["repos"]) < meta:
        candidato = candidatos[checkpoint["proximo"]]
        descarte = None
        for etapa, teste in zip(ETAPAS, testes):
            try:
                aprovado = teste(candidato)
            except requests.HTTPError as erro:
                status = erro.response.status_code if erro.response is not None else None
                if status not in (404, 410):
                    raise
                descarte = {"full_name": candidato["full_name"], "etapa": etapa,
                            "motivo": f"erro_http_{status}"}
                break
            if not aprovado:
                descarte = {"full_name": candidato["full_name"], "etapa": etapa,
                            "motivo": {"actions": "sem_actions",
                                       "releases": f"menos_de_{cfg['criterios']['min_releases']}_releases",
                                       "runs": f"menos_de_{cfg['criterios']['min_runs']}_runs_validos"}[etapa]}
                break
        if descarte:
            checkpoint["descartes"].append(descarte)
        else:
            checkpoint["repos"].append(coletar_metadados(client, candidato, cfg))
        checkpoint["proximo"] += 1
        salvar(checkpoint)
        if checkpoint["proximo"] % 10 == 0:
            log.info("seleção: %d avaliados; %d/%d aprovados", checkpoint["proximo"],
                     len(checkpoint["repos"]), meta)
    if len(checkpoint["repos"]) < meta:
        raise RuntimeError("candidatos esgotados antes de atingir a meta; amplie a busca")
    return checkpoint["repos"]


def salvar_funil(dados, candidatos, checkpoint):
    avaliados = checkpoint["proximo"]
    linhas = [{"etapa": "candidatos_na_busca", "entraram": len(candidatos),
               "descartados": "", "restaram": len(candidatos), "motivo_descarte": ""},
              {"etapa": "candidatos_avaliados", "entraram": avaliados, "descartados": "",
               "restaram": avaliados, "motivo_descarte": "parou ao atingir a meta"}]
    restantes = avaliados
    for etapa in ETAPAS:
        descartados = sum(r["etapa"] == etapa for r in checkpoint["descartes"])
        linhas.append({"etapa": etapa, "entraram": restantes, "descartados": descartados,
                       "restaram": restantes - descartados, "motivo_descarte": "ver descartes.csv"})
        restantes -= descartados
    linhas.append({"etapa": "amostra_final", "entraram": "", "descartados": "",
                   "restaram": len(checkpoint["repos"]), "motivo_descarte": ""})
    salvar_csv(dados / "funil.csv", list(linhas[0]), linhas)
    salvar_csv(dados / "descartes.csv", ["full_name", "etapa", "motivo"], checkpoint["descartes"])
    salvar_csv(dados / "metadados.csv", CAMPOS_META, checkpoint["repos"])


def reunir_coletas(dados, repos):
    for nome in CSVS_OBRIGATORIOS:
        if nome in {"candidatos.csv", "funil.csv", "descartes.csv", "metadados.csv"}:
            continue
        primeiro = pasta_repo(dados, repos[0]["full_name"]) / nome
        with primeiro.open(encoding="utf-8", newline="") as arquivo:
            campos = next(csv.reader(arquivo))

        def linhas():
            for repo in repos:
                with (pasta_repo(dados, repo["full_name"]) / nome).open(encoding="utf-8", newline="") as arquivo:
                    leitor = csv.DictReader(arquivo)
                    if leitor.fieldnames != campos:
                        raise ValueError(f"schema divergente em {repo['full_name']}/{nome}")
                    yield from leitor
        salvar_csv(dados / nome, campos, linhas())
    destino = dados / "workflow_runs"
    destino.mkdir(exist_ok=True)
    for repo in repos:
        nome = repo["full_name"].replace("/", "__") + ".json"
        shutil.copyfile(pasta_repo(dados, repo["full_name"]) / "workflow_runs" / nome, destino / nome)


def congelar(cfg, repos, destino):
    destino = Path(destino)
    if len(repos) < max(300, cfg["selecao"]["meta_repositorios"]):
        raise ValueError("o congelamento exige pelo menos 300 repositórios validados")
    validar_artefatos_s01(cfg, repos)
    if destino.exists():
        if ler_csv(destino) != ler_csv(Path(cfg["saida"]["dir_dados"]) / "metadados.csv"):
            raise ValueError("amostra já congelada é diferente; não será sobrescrita")
    else:
        salvar_csv(destino, CAMPOS_META, repos)
    manifesto = {"congelado_em": datetime.now(timezone.utc).isoformat(),
                 "repositorios": len(repos), "amostra_sha256": sha256(destino),
                 "janela_inicio": str(cfg["janela_inicio"]), "janela_fim": str(cfg["janela_fim"]),
                 "semente": cfg["semente"], "diretorio_dados": str(Path(cfg["saida"]["dir_dados"]).resolve()),
                 "fontes_sha256": {nome: sha256(Path(cfg["saida"]["dir_dados"]) / nome)
                                   for nome in CSVS_OBRIGATORIOS},
                 "fontes_repos_sha256": {r["full_name"]: fontes_repo(cfg["saida"]["dir_dados"], r["full_name"])
                                          for r in repos}}
    caminho_manifesto = destino.with_suffix(".manifest.json")
    if caminho_manifesto.exists():
        anterior = json.loads(caminho_manifesto.read_text(encoding="utf-8"))
        for campo in ("amostra_sha256", "janela_inicio", "janela_fim", "fontes_sha256", "fontes_repos_sha256"):
            if anterior[campo] != manifesto[campo]:
                raise ValueError("fontes divergem do congelamento anterior")
        return anterior
    _salvar_json_atomico(caminho_manifesto, manifesto)
    return manifesto


def executar(client, cfg, origem_candidatos, congelada, limite=None):
    dados = Path(cfg["saida"]["dir_dados"])
    if dados.resolve() == Path("data").resolve():
        raise ValueError("use uma saída separada da S01, por exemplo data/s02")
    dados.mkdir(parents=True, exist_ok=True)
    with exclusividade(dados / "coleta.lock"):
        snapshot = dados / "candidatos.csv"
        if not snapshot.exists():
            candidatos = (carregar_candidatos(origem_candidatos) if origem_candidatos
                          else selecionar_candidatos(client, cfg))
            nomes = [c["full_name"].lower() for c in candidatos]
            if len(set(nomes)) != len(nomes):
                raise ValueError("snapshot de candidatos contém duplicatas")
            salvar_candidatos(candidatos, snapshot)
        candidatos = carregar_candidatos(snapshot)
        contrato = {"janela_inicio": str(cfg["janela_inicio"]), "janela_fim": str(cfg["janela_fim"]),
                    "semente": cfg["semente"], "criterios": cfg["criterios"],
                    "meta": cfg["selecao"]["meta_repositorios"], "candidatos_sha256": sha256(snapshot)}
        caminho = dados / "checkpoint.json"
        checkpoint = (json.loads(caminho.read_text(encoding="utf-8")) if caminho.exists()
                      else {"contrato": contrato, "proximo": 0, "repos": [], "descartes": [], "coletados": []})
        if checkpoint["contrato"] != contrato:
            raise ValueError("configuração diverge do checkpoint; não misture execuções")
        salvar = lambda estado: _salvar_json_atomico(caminho, estado)
        repos = selecionar(client, cfg, candidatos, checkpoint, salvar)
        salvar_funil(dados, candidatos, checkpoint)
        nesta_execucao = 0
        for repo in repos:
            nome = repo["full_name"]
            if nome in checkpoint["coletados"]:
                continue
            pasta = pasta_repo(dados, nome)
            local = {**cfg, "saida": {**cfg["saida"], "dir_dados": str(pasta)}}
            log.info("coletando %s (%d/%d)", nome, len(checkpoint["coletados"]) + 1, len(repos))
            for coletar in (coletar_releases, coletar_commits, coletar_runs):
                coletar(client, local, [repo])
            erros = []
            _validar_releases(pasta / "releases.csv", {nome}, cfg, erros)
            _validar_runs(pasta, [repo], cfg, erros)
            if erros:
                raise RuntimeError("coleta não qualificada: " + "; ".join(erros))
            checkpoint["coletados"].append(nome)
            salvar(checkpoint)
            nesta_execucao += 1
            if limite and nesta_execucao >= limite:
                return checkpoint
        reunir_coletas(dados, repos)
        congelar(cfg, repos, congelada)
        log.info("amostra congelada: %d repositórios em %s", len(repos), congelada)
        return checkpoint


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", default="config_s02.yaml")
    parser.add_argument("--candidatos", help="reutiliza um snapshot de busca, preservando ordem e proveniência")
    parser.add_argument("--congelada", default="data/amostra_final.csv")
    parser.add_argument("--consenso", help="consenso com manifesto; por padrão, usa o diretório da amostra-ouro")
    parser.add_argument("--ouro", default="data/amostra_ouro_s02")
    parser.add_argument("--dataset", default="data/dataset.csv")
    parser.add_argument("--limite-coletas", type=int, help="piloto: para após N coletas, sem congelar")
    args = parser.parse_args(argv)
    if args.limite_coletas is not None and args.limite_coletas < 1:
        parser.error("--limite-coletas deve ser positivo")
    cfg = carregar_config(args.config)
    if cfg["selecao"]["meta_repositorios"] < 300:
        parser.error("S02 exige meta de pelo menos 300 repositórios")
    token = os.environ.get("GITHUB_TOKEN")
    if not token:
        parser.error("defina GITHUB_TOKEN antes de coletar")
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
    client = GitHubClient(token, cache_dir=cfg["saida"]["dir_cache"])
    from pipeline.observabilidade_s02 import observar_http
    observar_http(client, Path(cfg["saida"]["dir_cache"]) / "http_metricas.json")
    executar(client, cfg, args.candidatos, args.congelada, args.limite_coletas)
    if Path(args.congelada).exists() and not args.limite_coletas:
        from validacao.fechamento_s02 import main as fechar
        argumentos = ["--config", args.config, "--amostra", args.congelada,
                      "--ouro", args.ouro, "--dataset", args.dataset]
        if args.consenso:
            argumentos.extend(["--consenso", args.consenso])
        fechar(argumentos)


if __name__ == "__main__":
    main()
