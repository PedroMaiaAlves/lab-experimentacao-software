"""RQ08: rework rate e comparação descritiva com CFR (b), sem nova coleta."""
from collections import defaultdict
import csv
import hashlib
import io
from zipfile import ZipFile

import numpy as np
import pandas as pd

from analises.entrada import caminhos, ler_json, sha256
from analises.rq01_04 import descrever
from metricas.cfr import calcular_cfr_b, explicar_release_corretiva
from metricas.rework import calcular_rework_rate
from pipeline.coleta_releases import filtrar_releases
from pipeline.dataset import normalizar_releases


def avaliar_releases(releases, comparacoes, commits, cfg):
    principais = filtrar_releases(normalizar_releases(releases), cfg)
    chave = lambda r: (r["full_name"], str(r["release_id"]))
    mapa = {chave(c): c for c in comparacoes}
    if len(mapa) != len(comparacoes):
        raise ValueError("comparações duplicadas")
    esperadas = {(r["full_name"], str(r["id"])) for r in principais}
    if len(esperadas) != len(principais) or set(mapa) != esperadas:
        raise ValueError("releases/comparações não têm cobertura exata")
    mensagens = defaultdict(list)
    for commit in commits:
        if chave(commit) not in esperadas:
            raise ValueError("commit sem release principal")
        mensagens[chave(commit)].append(commit.get("message", ""))
    linhas = []
    regras = cfg["heuristica_release"]
    for release in principais:
        k = release["full_name"], str(release["id"])
        comparacao, textos = mapa[k], mensagens[k]
        status = comparacao["status"]
        if status not in {"ok", "erro_404", "sem_anterior"}:
            raise ValueError(f"status desconhecido: {status}")
        if int(comparacao["commits_count"]) != len(textos):
            raise ValueError(f"contagem de commits divergente: {k}")
        evidencia = explicar_release_corretiva(comparacao.get("previous_tag_name"),
                                              release["tag_name"], textos, regras)
        vazios = sum(not isinstance(m, str) or not m.strip() for m in textos)
        motivo = status if status != "ok" else ("sem_commits" if not textos else
                                                "mensagem_ausente" if vazios else "")
        suficiente = not motivo if regras["usar_palavras_commits"] else status == "ok"
        positiva = evidencia["corretiva"]
        lacuna_cfr = (regras["usar_palavras_commits"] and
                      (status == "erro_404" or any(not m for m in textos)) and not positiva)
        linhas.append({"full_name": k[0], "release_id": k[1], "tag_name": release["tag_name"],
                       "published_at": release["published_at"], "status_comparacao": status,
                       "commits": len(textos), "mensagens_ausentes": vazios,
                       "criterio_patch": evidencia["criterio_patch"], "criterio_texto": evidencia["criterio_texto"],
                       "corretiva_heuristica": positiva, "evidencia_rework_suficiente": suficiente,
                       "motivo_ausencia": motivo if not suficiente else "",
                       "corretiva": positiva if suficiente else None, "lacuna_cfr_b": bool(lacuna_cfr)})
    return pd.DataFrame(linhas).sort_values(["full_name", "published_at", "release_id"]).reset_index(drop=True)


def carregar_releases(df, cfg, dataset="data/dataset.csv", amostra=None, pacote=None):
    _, amostra, pacote = caminhos(dataset, amostra, pacote)
    manifesto = ler_json(amostra.with_suffix(".manifest.json"))
    nomes = ("releases.csv", "comparacoes_releases.csv", "commits_entre_releases.csv")
    with ZipFile(pacote) as zipado:
        fontes = []
        for nome in nomes:
            with zipado.open(nome) as arquivo:
                resumo = hashlib.file_digest(arquivo, "sha256").hexdigest()
            if resumo != manifesto["fontes_sha256"][nome]:
                raise ValueError(f"hash divergente em {nome}")
        for nome in nomes[:2]:
            with zipado.open(nome) as arquivo:
                fontes.append(list(csv.DictReader(io.TextIOWrapper(arquivo, encoding="utf-8"))))
        with zipado.open(nomes[2]) as arquivo:
            commits = csv.DictReader(io.TextIOWrapper(arquivo, encoding="utf-8"))
            auditoria = avaliar_releases(*fontes, commits, cfg)
    contagens = auditoria.groupby("full_name").size()
    esperadas = df.set_index("full_name").releases_principais.astype(int)
    if set(contagens.index) != set(esperadas.index) or not np.array_equal(
            contagens.reindex(esperadas.index).to_numpy(), esperadas.to_numpy()):
        raise ValueError("contagens de releases divergem do dataset")
    return auditoria, sha256(pacote)


def analisar(df, auditoria, cfg):
    grupos = {nome: grupo for nome, grupo in auditoria.groupby("full_name")}
    linhas = []
    for _, repo in df.sort_values("full_name").iterrows():
        grupo = grupos[repo.full_name]
        flags = [{"corretiva": None if r.lacuna_cfr_b else r.corretiva_heuristica}
                 for r in grupo.itertuples()]
        conservador = calcular_rework_rate([{"corretiva": r.corretiva} for r in grupo.itertuples()])
        cfr = calcular_cfr_b([{"id": r.release_id, "published_at": r.published_at,
                              "corretiva": r.corretiva_heuristica} for r in grupo.itertuples()],
                            cfg["janela_fim"], cfg["heuristica_release"]["janela_dias"])
        if grupo.lacuna_cfr_b.any():
            cfr["cfr_b"] = None
        observado = cfr["cfr_b"]
        if ((observado is None) != pd.isna(repo.cfr_b) or
                (observado is not None and not np.isclose(observado, repo.cfr_b, rtol=1e-12, atol=1e-12))):
            raise ValueError(f"CFR (b) recalculado diverge do dataset: {repo.full_name}")
        linhas.append({"full_name": repo.full_name, **calcular_rework_rate(flags),
                       "rework_conservador": conservador["rework_rate"],
                       "releases_sem_evidencia_completa": conservador["releases_sem_evidencia"],
                       "limite_inferior_conservador": conservador["rework_limite_inferior"],
                       "limite_superior_conservador": conservador["rework_limite_superior"],
                       "cfr_b": observado, "releases_avaliadas_cfr_b": cfr["releases_avaliadas"],
                       "releases_censuradas_cfr_b": cfr["releases_censuradas"],
                       "releases_falharam_cfr_b": cfr["releases_falharam"] if observado is not None else None})
    projetos = pd.DataFrame(linhas)
    pares = projetos.dropna(subset=["rework_rate", "cfr_b"])[["full_name", "rework_rate", "cfr_b"]].copy()
    pares["diferenca_rework_menos_cfr_b"] = pares.rework_rate - pares.cfr_b
    resumos = pd.DataFrame([{"metrica": coluna, "n_total": len(projetos),
                             "n_ausentes": int(projetos[coluna].isna().sum()), **descrever(projetos[coluna])}
                            for coluna in ("rework_rate", "cfr_b", "rework_conservador")])
    total = int(projetos.releases_total.sum())
    corretivas = int(projetos.releases_corretivas.sum())
    ausentes = int(projetos.releases_sem_evidencia.sum())
    sem_evidencia = int(projetos.releases_sem_evidencia_completa.sum())
    corretivas_completas = int(auditoria.corretiva.eq(True).sum())
    cobertura = {"repositorios": len(projetos), "releases_total": total,
                 "corretivas_heuristica": corretivas, "releases_sem_evidencia": ausentes,
                 "rework_agregado": corretivas / total if total and not ausentes else None,
                 "limite_inferior_agregado": corretivas / total if total else None,
                 "limite_superior_agregado": (corretivas + ausentes) / total if total else None,
                 "releases_sem_evidencia_completa": sem_evidencia,
                 "limite_inferior_conservador": corretivas_completas / total if total else None,
                 "limite_superior_conservador": (corretivas_completas + sem_evidencia) / total if total else None,
                 "repositorios_pareados": len(pares)}
    return {"rq08_repositorios": projetos, "rq08_releases": auditoria,
            "rq08_resumo": resumos, "rq08_comparacao": pares,
            "rq08_cobertura": pd.DataFrame([cobertura])}
