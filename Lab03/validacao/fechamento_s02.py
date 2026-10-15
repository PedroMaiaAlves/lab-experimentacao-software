"""Prepara a amostra-ouro definitiva e consolida apenas evidências da mesma execução."""
import argparse
import csv
from datetime import datetime, timezone
import json
from pathlib import Path
import re

import pandas as pd

from pipeline.coleta_runs import _salvar_json_atomico
from pipeline.config import carregar_config
from pipeline.dataset import gerar_dataset
from pipeline.revisao_c import preparar_casos
from pipeline.sprint2 import salvar_csv, sha256
from scripts.validar_rotulos_b import validar_arquivo
from scripts.avaliar_heuristica import avaliar_linhas, registrar_resultado
from validacao.amostra_ouro import (
    COLS_LEITURA_RELEASES, adicionar_links, releases_principais_na_janela,
    sortear_releases, sortear_repositorios,
)
from validacao.artefatos_artigo import escapar, main as gerar_tabelas
from validacao.concordancia import AVALIADORES, ErroRotulos, _normalizar_chave, executar as concordancia, ler_rotulos


def preparar_amostra(cfg, amostra, saida):
    amostra, saida = Path(amostra), Path(saida)
    congelamento = json.loads(amostra.with_suffix(".manifest.json").read_text(encoding="utf-8"))
    if congelamento["amostra_sha256"] != sha256(amostra) or congelamento["repositorios"] < 300:
        raise ValueError("a amostra-ouro exige congelamento íntegro de pelo menos 300 repositórios")
    dados = Path(cfg["saida"]["dir_dados"])
    for campo in ("janela_inicio", "janela_fim"):
        if str(cfg[campo]) != congelamento[campo]:
            raise ValueError("janela diferente do congelamento")
    for nome in ("releases.csv", "comparacoes_releases.csv", "commits_entre_releases.csv"):
        if sha256(dados / nome) != congelamento["fontes_sha256"][nome]:
            raise ValueError(f"fonte alterada: {nome}")
    caminho_manifesto = saida / "manifesto.json"
    if caminho_manifesto.exists():
        anterior = json.loads(caminho_manifesto.read_text(encoding="utf-8"))
        if anterior["amostra_sha256"] != sha256(amostra):
            raise ValueError("não sobrescreva a amostra-ouro de outra execução")
        if any(anterior[c] != cfg["semente"] for c in ("semente_repos", "semente_releases")):
            raise ValueError("semente diferente da amostra-ouro registrada")
        for nome, esperado in anterior["artefatos_sha256"].items():
            if sha256(saida / nome) != esperado:
                raise ValueError(f"artefato da amostra-ouro alterado: {nome}")
        return anterior
    if saida.exists() and any(saida.iterdir()):
        raise ValueError("destino da amostra-ouro já contém arquivos sem manifesto")
    populacao = pd.read_csv(amostra, dtype=str, keep_default_na=False)
    if len(populacao) != congelamento["repositorios"] or populacao["full_name"].duplicated().any():
        raise ValueError("população divergente ou duplicada")
    repos = sortear_repositorios(populacao, 60, cfg["semente"])
    repos["repo_url"] = "https://github.com/" + repos["full_name"]
    releases = pd.read_csv(dados / "releases.csv", usecols=COLS_LEITURA_RELEASES, dtype=str, keep_default_na=False)
    principais = releases_principais_na_janela(releases, str(cfg["janela_inicio"]), str(cfg["janela_fim"]))
    escolhidas = sortear_releases(principais, list(repos["full_name"]), 5, cfg["semente"])
    if len(escolhidas) != 300 or not escolhidas.groupby("full_name").size().eq(5).all():
        raise ValueError("a amostra-ouro precisa de exatamente cinco releases de cada um dos 60 projetos")
    comparacoes = pd.read_csv(dados / "comparacoes_releases.csv", dtype=str, keep_default_na=False)
    escolhidas = adicionar_links(escolhidas, comparacoes)
    salvar_csv(saida / "repos_sorteados.csv", list(repos.columns), repos.to_dict("records"))
    salvar_csv(saida / "releases_sorteadas.csv", list(escolhidas.columns), escolhidas.to_dict("records"))
    casos = preparar_casos(saida / "releases_sorteadas.csv", dados / "releases.csv", dados / "commits_entre_releases.csv")
    _salvar_json_atomico(saida / "fontes_releases.json", {"casos": casos})
    manifesto = {"gerado_em": datetime.now(timezone.utc).isoformat(), "amostra_sha256": sha256(amostra),
                 "repositorios": 60, "releases": 300, "semente_repos": cfg["semente"],
                 "semente_releases": cfg["semente"], "avaliacoes_preenchidas": False,
                 "fontes_sha256": congelamento["fontes_sha256"],
                 "artefatos_sha256": {n: sha256(saida / n) for n in (
                     "repos_sorteados.csv", "releases_sorteadas.csv", "fontes_releases.json")}}
    _salvar_json_atomico(caminho_manifesto, manifesto)
    return manifesto


def validar_avaliacoes(ouro):
    ouro = Path(ouro)
    repos = pd.read_csv(ouro / "repos_sorteados.csv", dtype=str, keep_default_na=False)
    releases = pd.read_csv(ouro / "releases_sorteadas.csv", dtype=str, keep_default_na=False)
    esperados = {"repositorios": set(repos["full_name"]),
                 "releases": set(_normalizar_chave(releases, ["full_name", "release_id"]))}
    documentos = []
    for avaliador in AVALIADORES:
        planilha = ouro / "rotulos" / f"rotulos_{avaliador}.xlsx"
        atestado = planilha.with_suffix(".manifest.json")
        if not planilha.is_file() or not atestado.is_file():
            raise ValueError(f"avaliação {avaliador} ainda sem planilha e proveniência")
        doc = json.loads(atestado.read_text(encoding="utf-8"))
        if (doc.get("avaliador") != avaliador or doc.get("arquivo_sha256") != sha256(planilha) or
                doc.get("itens_sha256") != sha256(ouro / "releases_sorteadas.csv") or
                doc.get("repos_sha256") != sha256(ouro / "repos_sorteados.csv") or
                doc.get("origem") not in {"humana", "assistida_por_IA"} or
                doc.get("avaliacao_concluida") is not True or not doc.get("id_avaliacao") or
                doc.get("rotulos_outros_lidos") is not False or doc.get("saida_heuristica_lida") is not False):
            raise ValueError(f"proveniência inválida da avaliação {avaliador}")
        validar_arquivo(planilha)
        documentos.append(doc)
    if len({d["id_avaliacao"] for d in documentos}) != len(AVALIADORES):
        raise ValueError("as três avaliações precisam de execuções/avaliadores independentes distintos")
    dados = ler_rotulos(ouro / "rotulos")
    for av in AVALIADORES:
        for aba, chaves in (("repositorios", ["full_name"]), ("releases", ["full_name", "release_id"])):
            if set(_normalizar_chave(dados[av][aba], chaves)) != esperados[aba]:
                raise ErroRotulos(f"{av}: itens diferentes da amostra-ouro definitiva em {aba}")
    return documentos


def consolidar_validacao(cfg, amostra, ouro, artigo, tipo_desempate):
    documentos = validar_avaliacoes(ouro)
    if concordancia(ouro, artigo / "kappa_s02.tex", tipo_desempate):
        return {"qualificada": False, "consenso_concluido": False,
                "pendencias": ["resolver casos 1-1-1 registrados em casos_divergentes.csv"]}
    origens = {d["origem"] for d in documentos}
    origem = next(iter(origens)) if len(origens) == 1 else "mista"
    atestado = {"amostra_sha256": sha256(amostra), "origem_rotulagem": origem,
                "rotulagem_independente_confirmada": True,
                "avaliacoes_sha256": {av: sha256(ouro / "rotulos" / f"rotulos_{av}.xlsx") for av in AVALIADORES}}
    for nome in ("consenso_repos.csv", "consenso_releases.csv"):
        caminho = ouro / nome
        _salvar_json_atomico(caminho.with_suffix(".manifest.json"), {**atestado, "consenso_sha256": sha256(caminho)})
    dados = Path(cfg["saida"]["dir_dados"])
    consenso = pd.read_csv(ouro / "consenso_releases.csv", dtype=str, keep_default_na=False).to_dict("records")
    chaves = {(r["full_name"], r["release_id"]) for r in consenso}
    def selecionadas(nome):
        with (dados / nome).open(encoding="utf-8", newline="") as arquivo:
            return [r for r in csv.DictReader(arquivo) if (r["full_name"], r["release_id"]) in chaves]
    auditoria, metricas = avaliar_linhas(consenso, selecionadas("comparacoes_releases.csv"),
                                       selecionadas("commits_entre_releases.csv"), cfg["heuristica_release"])
    versao = cfg["heuristica_release"]["versao"]
    if not re.fullmatch(r"[A-Za-z0-9_.-]+", versao):
        raise ValueError("versão da heurística inválida para o registro de artefatos")
    registro = {"regras": cfg["heuristica_release"], "consenso_sha256": sha256(ouro / "consenso_releases.csv")}
    caminho_registro = ouro / f"avaliacao_{versao}.manifest.json"
    if caminho_registro.exists() and json.loads(caminho_registro.read_text(encoding="utf-8")) != registro:
        raise ValueError("não sobrescreva uma avaliação com regras ou consenso diferentes; registre nova versão")
    salvar_csv(ouro / f"avaliacao_{versao}.csv", list(auditoria[0]), auditoria)
    _salvar_json_atomico(caminho_registro, registro)
    doc = ouro / "heuristica_versoes.md"
    if not doc.exists():
        doc.write_text("# Heurística na amostra definitiva da S02\n\n"
                       "Refinamento e avaliação na mesma amostra; não é teste de generalização.\n\n"
                       "<!-- resultados:start -->\n<!-- resultados:end -->\n", encoding="utf-8")
    registrar_resultado(ouro / "heuristica_metricas.csv", doc, versao, metricas, cfg["heuristica_release"])
    qualificada = metricas["f1"] >= 0.70
    return {"qualificada": qualificada, "consenso_concluido": True, "origem_rotulagem": origem,
            "versao": versao, "metricas": metricas,
            "pendencias": [] if qualificada else ["refinar e registrar nova versão da heurística até F1 >= 0,70"]}


def relatar_validacao(ouro, artigo, resultado):
    if not resultado.get("metricas"):
        return
    linhas = pd.read_csv(ouro / "kappa_fleiss.csv", keep_default_na=False).to_dict("records")
    metodo = {"humana": "humana", "assistida_por_IA": "assistida por IA", "mista": "mista"}[resultado["origem_rotulagem"]]
    m = resultado["metricas"]
    texto = (f"A rotulagem da amostra definitiva é {metodo}, com três avaliações de 60 projetos e 300 releases. "
             f"A heurística {escapar(resultado['versao'])} obteve precisão {m['precisao']:.3f}, recall {m['recall']:.3f} "
             f"e F1 {m['f1']:.3f}; VP={m['tp']}, FP={m['fp']}, FN={m['fn']} e VN={m['tn']}.\n"
             "\\input{tabelas/kappa_s02}\n")
    if not resultado["qualificada"]:
        texto += "O F1 ainda não atingiu a meta de 0,70; o refinamento permanece pendente.\n"
    for r in linhas:
        if r["kappa"] == "":
            texto += f"Kappa indefinido por ausência de variação na dimensão {r['dimensao'].replace('_', ' ')}.\n"
    (artigo / "validacao_s02.tex").write_text(texto, encoding="utf-8")


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--config", default="config_s02.yaml")
    ap.add_argument("--amostra", default="data/amostra_final.csv")
    ap.add_argument("--ouro", default="data/amostra_ouro_s02")
    ap.add_argument("--consenso", help="CSV de consenso com manifesto válido para a amostra")
    ap.add_argument("--dataset", default="data/dataset.csv")
    ap.add_argument("--artigo", default="docs/artigo/tabelas")
    ap.add_argument("--validar-avaliacoes", action="store_true")
    ap.add_argument("--tipo-desempate", choices=["reuniao", "adjudicacao_IA"], default="reuniao")
    a = ap.parse_args(argv)
    cfg = carregar_config(a.config)
    ouro, artigo = Path(a.ouro), Path(a.artigo)
    artigo.mkdir(parents=True, exist_ok=True)
    amostra_ouro = preparar_amostra(cfg, a.amostra, ouro)
    caminho_estado = ouro / "fechamento.json"
    anterior = json.loads(caminho_estado.read_text(encoding="utf-8")) if caminho_estado.exists() else {}
    verificar = a.validar_avaliacoes or anterior.get("concluido") is True
    tipo_desempate = a.tipo_desempate if a.validar_avaliacoes else anterior.get("tipo_desempate", a.tipo_desempate)
    _salvar_json_atomico(ouro / "fechamento.json", {"concluido": False, "estado": "em_validacao"})
    consenso = a.consenso or ouro / "consenso_repos.csv"
    validacao = {"qualificada": False, "pendencias": ["validar três avaliações independentes da amostra definitiva",
                 "gerar consenso e kappas com proveniência", "avaliar/refinar heurística até F1 >= 0,70"]}
    if verificar:
        (artigo / "validacao_s02.tex").write_text("A validação da amostra-ouro está em atualização.\n", encoding="utf-8")
        validacao = consolidar_validacao(cfg, a.amostra, ouro, artigo, tipo_desempate)
        consenso = ouro / "consenso_repos.csv" if validacao["consenso_concluido"] else None
        relatar_validacao(ouro, artigo, validacao)
    resumo = gerar_dataset(cfg, a.amostra, consenso, a.dataset, artigo / "coleta_s02.tex")
    gerar_tabelas(["--config", a.config, "--dados", cfg["saida"]["dir_dados"], "--saida", str(artigo)])
    estado = {"atualizado_em": datetime.now(timezone.utc).isoformat(),
              "coleta_congelada": resumo["repositorios"], "amostra_sha256": resumo["amostra_sha256"],
              "dataset_sha256": resumo["dataset_sha256"], "amostra_ouro": amostra_ouro["artefatos_sha256"],
              "consenso_utilizado": resumo["consenso_utilizado"],
              "tipo_desempate": tipo_desempate,
              "validacao": validacao, "concluido": validacao["qualificada"], "pendencias": validacao["pendencias"]}
    _salvar_json_atomico(ouro / "fechamento.json", estado)
    print(json.dumps(estado, ensure_ascii=False, indent=2))
    return 0 if not verificar or estado["concluido"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
