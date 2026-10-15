"""Dataset da S02: uma linha por repositório, sem chamadas à API."""
import argparse
from collections import defaultdict
import csv
from datetime import datetime, timezone
import json
import logging
from pathlib import Path

from metricas.cfr import calcular_cfr_a, calcular_cfr_b, contar_conclusoes, explicar_release_corretiva
from metricas.deployment_frequency import deployment_frequency
from metricas.lead_time import calcular_lead_time, data_commit_valida
from metricas.recuperacao import calcular_tempo_recuperacao
from pipeline.coleta_releases import filtrar_releases
from pipeline.config import carregar_config
from pipeline.sprint2 import ler_csv, salvar_csv, sha256
from pipeline.coleta_runs import _salvar_json_atomico

log = logging.getLogger(__name__)
CAMPOS = [
    "full_name", "stars", "language", "default_branch", "created_at", "idade_dias", "contribuidores",
    "tipo_projeto", "releases_sao_entregas", "rotulo_disponivel", "heuristica_versao",
    "deployment_frequency", "deployment_frequency_prereleases", "deployment_frequency_tags",
    "lead_time_a_horas", "lead_time_b_horas", "cfr_a", "cfr_b", "tempo_recuperacao_horas",
    "releases_principais", "releases_com_prereleases", "tags_na_janela", "tags_sem_data",
    "releases_comparadas", "releases_sem_anterior", "releases_erro_404", "releases_sem_commits",
    "commits_data_invalida", "releases_sem_evidencia_textual", "cfr_b_disponivel",
    "releases_avaliadas", "releases_falharam", "releases_censuradas",
    "runs_total", "runs_validos", "runs_sucessos", "runs_falhas", "runs_ignorados",
    "episodios_total", "episodios_concluidos", "episodios_censurados", "proporcao_censurados",
    "intervalos_saturados", "intervalos_incompletos",
]


def normalizar_releases(linhas):
    return [{**r, "draft": str(r["draft"]).lower() == "true",
             "prerelease": str(r["prerelease"]).lower() == "true"} for r in linhas]


def calcular_linha(repo, releases, comparacoes, commits, tags, runs, cfg, rotulo=None, saturados=()):
    principais = sorted(filtrar_releases(releases, cfg), key=lambda r: (r["published_at"], str(r["id"])))
    com_pre = filtrar_releases(releases, cfg, incluir_prereleases=True)
    por_release = defaultdict(list)
    for commit in commits:
        por_release[str(commit["release_id"])].append(commit)
    mapa = {str(c["release_id"]): c for c in comparacoes}
    if len(mapa) != len(comparacoes):
        raise ValueError(f"comparações duplicadas: {repo['full_name']}")
    if set(mapa) != {str(r["id"]) for r in principais}:
        raise ValueError(f"comparações não cobrem as releases principais: {repo['full_name']}")
    if set(por_release) - set(mapa):
        raise ValueError(f"commits sem comparação: {repo['full_name']}")
    lead, classificadas, sem_texto, invalidos = [], [], 0, 0
    for release in principais:
        comparacao = mapa[str(release["id"])]
        itens = por_release[str(release["id"])]
        status = comparacao["status"]
        if status not in {"ok", "sem_anterior", "erro_404"}:
            raise ValueError(f"status desconhecido: {status}")
        if int(comparacao["commits_count"]) != len(itens):
            raise ValueError(f"contagem de commits divergente: {repo['full_name']}#{release['id']}")
        lead.append({**release, "status": status, "commits": itens})
        invalidos += sum(not data_commit_valida(release["published_at"], c["author_date"]) for c in itens)
        evidencia = explicar_release_corretiva(comparacao.get("previous_tag_name"), release["tag_name"],
                                              [c.get("message") for c in itens], cfg["heuristica_release"])
        texto_incompleto = (cfg["heuristica_release"]["usar_palavras_commits"] and
                            (status == "erro_404" or any(not c.get("message") for c in itens)))
        sem_texto += int(texto_incompleto and not evidencia["corretiva"])
        classificadas.append({**release, "corretiva": evidencia["corretiva"]})
    cfr_b = calcular_cfr_b(classificadas, cfg["janela_fim"], cfg["heuristica_release"]["janela_dias"])
    if sem_texto:
        cfr_b.update(cfr_b=None, releases_falharam=None)
    contagens = contar_conclusoes(runs)
    recuperacao = calcular_tempo_recuperacao(runs)
    datas_tags = [t["commit_author_date"] for t in tags if t.get("status") == "ok" and t.get("commit_author_date")]
    rotulo = rotulo or {}
    return {**repo, "tipo_projeto": rotulo.get("tipo_projeto"),
            "releases_sao_entregas": rotulo.get("releases_sao_entregas"),
            "rotulo_disponivel": bool(rotulo.get("tipo_projeto")),
            "heuristica_versao": cfg["heuristica_release"]["versao"],
            "deployment_frequency": deployment_frequency([r["published_at"] for r in principais], cfg),
            "deployment_frequency_prereleases": deployment_frequency([r["published_at"] for r in com_pre], cfg),
            "deployment_frequency_tags": deployment_frequency(datas_tags, cfg),
            **calcular_lead_time(lead, ignorar_invalidos=True), "cfr_a": calcular_cfr_a(runs), **cfr_b,
            "tempo_recuperacao_horas": recuperacao.mediana_horas,
            "releases_principais": len(principais), "releases_com_prereleases": len(com_pre),
            "tags_na_janela": sum(str(cfg["janela_inicio"]) <= d[:10] <= str(cfg["janela_fim"]) for d in datas_tags),
            "tags_sem_data": len(tags) - len(datas_tags),
            "releases_comparadas": sum(c["status"] == "ok" for c in comparacoes),
            "releases_sem_anterior": sum(c["status"] == "sem_anterior" for c in comparacoes),
            "releases_erro_404": sum(c["status"] == "erro_404" for c in comparacoes),
            "releases_sem_commits": sum(c["status"] == "ok" and int(c["commits_count"]) == 0 for c in comparacoes),
            "commits_data_invalida": invalidos, "releases_sem_evidencia_textual": sem_texto,
            "cfr_b_disponivel": not sem_texto, "runs_total": len(runs),
            "runs_validos": contagens["sucessos"] + contagens["falhas"],
            "runs_sucessos": contagens["sucessos"], "runs_falhas": contagens["falhas"],
            "runs_ignorados": contagens["ignoradas"], "episodios_total": recuperacao.episodios_total,
            "episodios_concluidos": len(recuperacao.episodios_horas),
            "episodios_censurados": recuperacao.episodios_censurados,
            "proporcao_censurados": recuperacao.proporcao_censurados,
            "intervalos_saturados": len(saturados),
            "intervalos_incompletos": sum(s["status"] == "incompleto" for s in saturados)}


def carregar_rotulos(caminho, amostra_sha256):
    if not Path(caminho).is_file():
        log.warning("consenso ainda indisponível; tipo_projeto ficará ausente")
        return {}
    atestado = Path(caminho).with_suffix(".manifest.json")
    if not atestado.is_file():
        log.warning("consenso sem vínculo com a amostra congelada; rótulos não serão utilizados")
        return {}
    origem = json.loads(atestado.read_text(encoding="utf-8"))
    if (origem.get("amostra_sha256") != amostra_sha256 or
            origem.get("consenso_sha256") != sha256(caminho) or
            origem.get("rotulagem_independente_confirmada") is not True or
            origem.get("origem_rotulagem") not in {"humana", "assistida_por_IA", "mista"}):
        raise ValueError("consenso sem integridade, proveniência ou vínculo válido com esta amostra")
    linhas = ler_csv(caminho)
    if any(not r.get("full_name") or not r.get("tipo_projeto") for r in linhas):
        raise ValueError("consenso possui chave ou tipo_projeto vazio")
    mapa = {r["full_name"]: r for r in linhas}
    if len(mapa) != len(linhas):
        raise ValueError("repositórios duplicados no consenso")
    return mapa


def grupos_csv(caminho, nomes):
    with Path(caminho).open(encoding="utf-8", newline="") as arquivo:
        leitor = csv.DictReader(arquivo)
        atual = next(leitor, None)
        for nome in nomes:
            grupo = []
            while atual is not None and atual["full_name"] == nome:
                grupo.append(atual)
                atual = next(leitor, None)
            yield grupo
        if atual is not None:
            raise ValueError(f"{caminho}: registros fora da ordem da amostra ou inesperados")


def gerar_dataset(cfg, amostra, consenso, saida, relato=None):
    amostra, saida = Path(amostra), Path(saida)
    manifesto = json.loads(amostra.with_suffix(".manifest.json").read_text(encoding="utf-8"))
    if manifesto["amostra_sha256"] != sha256(amostra):
        raise ValueError("amostra alterada depois do congelamento")
    for campo in ("janela_inicio", "janela_fim"):
        if manifesto[campo] != str(cfg[campo]):
            raise ValueError("janela diferente do congelamento")
    dados = Path(cfg["saida"]["dir_dados"])
    for nome, esperado in manifesto["fontes_sha256"].items():
        if sha256(dados / nome) != esperado:
            raise ValueError(f"fonte alterada depois do congelamento: {nome}")
    repos = ler_csv(amostra)
    if len(repos) != manifesto["repositorios"] or len({r["full_name"] for r in repos}) != len(repos):
        raise ValueError("amostra duplicada ou divergente do manifesto")
    rotulos = carregar_rotulos(consenso, manifesto["amostra_sha256"])
    linhas = []
    nomes = [repo["full_name"] for repo in repos]
    arquivos = ["releases.csv", "comparacoes_releases.csv", "commits_entre_releases.csv", "tags.csv"]
    grupos = [grupos_csv(dados / nome, nomes) for nome in arquivos]
    for repo, *fontes in zip(repos, *grupos, strict=True):
        run_path = dados / "workflow_runs" / (repo["full_name"].replace("/", "__") + ".json")
        if sha256(run_path) != manifesto["fontes_repos_sha256"][repo["full_name"]]["workflow_runs/" + run_path.name]:
            raise ValueError(f"workflow runs alterados: {repo['full_name']}")
        origem_runs = json.loads(run_path.read_text(encoding="utf-8"))
        if origem_runs.get("complete") is not True:
            raise ValueError(f"workflow runs incompletos: {repo['full_name']}")
        fontes[0] = normalizar_releases(fontes[0])
        linhas.append(calcular_linha(repo, *fontes, origem_runs["workflow_runs"], cfg,
                                    rotulos.get(repo["full_name"]), origem_runs["saturated_intervals"]))
    salvar_csv(saida, CAMPOS, linhas)
    resumo = {"gerado_em": datetime.now(timezone.utc).isoformat(), "repositorios": len(linhas),
              "dataset_sha256": sha256(saida), "amostra_sha256": sha256(amostra),
              "heuristica": cfg["heuristica_release"],
              "consenso_sha256": sha256(consenso) if rotulos else None,
              "consenso_utilizado": bool(rotulos),
              "repositorios_sem_tipo": sum(not r["rotulo_disponivel"] for r in linhas),
              "cfr_b_indisponiveis": sum(not r["cfr_b_disponivel"] for r in linhas),
              "totais": {c: sum(r[c] for r in linhas) for c in (
                  "releases_principais", "releases_erro_404", "commits_data_invalida",
                  "releases_censuradas", "runs_total", "runs_validos", "runs_ignorados",
                  "episodios_total", "episodios_censurados", "intervalos_saturados", "intervalos_incompletos")}}
    funil = dados / "funil.csv"
    resumo["funil"] = ler_csv(funil) if funil.exists() else []
    _salvar_json_atomico(saida.with_suffix(".manifest.json"), resumo)
    if relato:
        gerar_relato(resumo, cfg, relato)
    return resumo


def gerar_relato(resumo, cfg, caminho):
    totais = resumo["totais"]
    texto = (f"A execução concluída reuniu {resumo['repositorios']} repositórios, na janela de "
             f"{cfg['janela_inicio']} a {cfg['janela_fim']}. Foram contabilizados "
             f"{totais['releases_principais']} releases principais, {totais['runs_validos']} runs válidos "
             f"e {totais['runs_ignorados']} runs ignorados. Houve {totais['releases_erro_404']} "
             f"comparações com erro 404 e {totais['commits_data_invalida']} relações release/commit "
             f"com data inválida. No CFR (b), {totais['releases_censuradas']} releases foram censuradas. "
             f"Dos {totais['episodios_total']} episódios de falha, {totais['episodios_censurados']} "
             f"permaneceram censurados. Foram registrados {totais['intervalos_saturados']} intervalos "
             f"saturados (incluindo subdivisões), com {totais['intervalos_incompletos']} incompletos. "
             f"O tipo do projeto permanece ausente em {resumo['repositorios_sem_tipo']} repositórios "
             f"não cobertos pelo consenso, sem imputação automática. O CFR (b) ficou indisponível "
             f"em {resumo['cfr_b_indisponiveis']} repositórios por evidência textual insuficiente.\n")
    caminho = Path(caminho)
    caminho.parent.mkdir(parents=True, exist_ok=True)
    caminho.write_text(texto, encoding="utf-8")


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", default="config_s02.yaml")
    parser.add_argument("--amostra", default="data/amostra_final.csv")
    parser.add_argument("--consenso", default="data/amostra_ouro/consenso_repos.csv")
    parser.add_argument("--saida", default="data/dataset.csv")
    parser.add_argument("--relato", default="docs/artigo/tabelas/coleta_s02.tex")
    args = parser.parse_args(argv)
    logging.basicConfig(level=logging.INFO)
    resumo = gerar_dataset(carregar_config(args.config), args.amostra, args.consenso, args.saida, args.relato)
    print(json.dumps(resumo, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
