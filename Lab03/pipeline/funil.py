"""S01-A3: filtros em cascata, funil de seleção e metadados dos repositórios."""
import csv
import logging
import re
from datetime import date
from pathlib import Path

import requests

from metricas.cfr import classificar_conclusao
from pipeline.coleta_runs import coletar_runs_repositorio
from pipeline.janela import na_janela

log = logging.getLogger(__name__)

_ULTIMA_PAGINA = re.compile(r'[?&]page=(\d+)[^>]*>;\s*rel="last"')


# ---------- testes de cada etapa do funil ----------
def usa_actions(client, nome):
    dados, _ = client.get_json(f"/repos/{nome}/actions/workflows", {"per_page": 1})
    return dados["total_count"] > 0


def contar_releases_janela(client, nome, cfg, parar_em):
    """Conta releases principais publicadas na janela; para ao atingir ``parar_em``."""
    n = 0
    for rel in client.paginate(f"/repos/{nome}/releases", {"per_page": 100}):
        if rel.get("draft") or rel.get("prerelease") or not na_janela(rel.get("published_at"), cfg):
            continue
        n += 1
        if n >= parar_em:
            break
    return n


def contar_runs_validos(client, nome, branch, cfg, parar_em):
    """Conta localmente as conclusions válidas dos runs coletados mês a mês."""
    resultado = coletar_runs_repositorio(
        client, {"full_name": nome, "default_branch": branch}, cfg
    )
    return sum(
        classificar_conclusao(run.get("conclusion")) != "ignorar"
        for run in resultado["workflow_runs"]
    )


# ---------- metadados ----------
def contar_contribuidores(client, nome):
    """Lê a última página de /contributors?per_page=1 (1 contribuidor por página)."""
    try:
        dados, headers = client.get_json(f"/repos/{nome}/contributors",
                                         {"per_page": 1, "anon": "true"})
    except requests.HTTPError as e:
        log.warning("contribuidores indisponíveis para %s: %s", nome, e)
        return None
    m = _ULTIMA_PAGINA.search(headers.get("link", ""))
    if m:
        return int(m.group(1))
    return len(dados) if dados else 0


def coletar_metadados(client, cand, cfg):
    criado = date.fromisoformat(cand["created_at"][:10])
    return {
        "full_name": cand["full_name"],
        "stars": int(cand["stars"]),
        "language": cand["language"],
        "default_branch": cand["default_branch"],
        "created_at": criado.isoformat(),
        "idade_dias": (cfg["janela_fim"] - criado).days,
        "contribuidores": contar_contribuidores(client, cand["full_name"]),
    }


# ---------- funil ----------
def _salvar_csv(caminho, campos, linhas):
    with open(caminho, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=campos)
        w.writeheader()
        w.writerows(linhas)


def executar_funil(client, candidatos, cfg, saida="data"):
    """Aplica as etapas até atingir a meta; grava funil.csv, descartes.csv e metadados.csv."""
    saida = Path(saida)
    saida.mkdir(parents=True, exist_ok=True)
    crit = cfg["criterios"]
    meta = cfg["selecao"]["meta_repositorios"]
    min_rel, min_runs = crit["min_releases"], crit["min_runs"]

    etapas = [
        ("actions", "sem_actions",
         lambda c: usa_actions(client, c["full_name"])),
        ("releases", f"menos_de_{min_rel}_releases",
         lambda c: contar_releases_janela(client, c["full_name"], cfg, min_rel) >= min_rel),
        ("runs", f"menos_de_{min_runs}_runs_validos",
         lambda c: contar_runs_validos(client, c["full_name"], c["default_branch"], cfg, min_runs) >= min_runs),
    ]
    contagem = {nome: {"entraram": 0, "descartados": 0, "motivo": motivo} for nome, motivo, _ in etapas}
    descartes, aceitos, metadados = [], [], []
    avaliados = 0

    for cand in candidatos:
        if len(aceitos) >= meta:
            break
        avaliados += 1
        nome = cand["full_name"]
        for etapa, motivo, teste in etapas:
            contagem[etapa]["entraram"] += 1
            try:
                ok = teste(cand)
            except requests.HTTPError as e:
                status = e.response.status_code if e.response is not None else "x"
                ok, motivo = False, f"erro_http_{status}"
            if not ok:
                contagem[etapa]["descartados"] += 1
                descartes.append({"full_name": nome, "etapa": etapa, "motivo": motivo})
                break
        else:
            aceitos.append(cand)
            metadados.append(coletar_metadados(client, cand, cfg))
        if avaliados % 10 == 0:
            log.info("avaliados %d | aceitos %d/%d", avaliados, len(aceitos), meta)

    linhas = [
        {"etapa": "candidatos_na_busca", "entraram": len(candidatos), "descartados": "",
         "restaram": len(candidatos), "motivo_descarte": ""},
        {"etapa": "candidatos_avaliados", "entraram": avaliados, "descartados": "",
         "restaram": avaliados, "motivo_descarte": "parou ao atingir a meta"},
    ]
    for etapa, info in contagem.items():
        linhas.append({"etapa": etapa, "entraram": info["entraram"],
                       "descartados": info["descartados"],
                       "restaram": info["entraram"] - info["descartados"],
                       "motivo_descarte": info["motivo"]})
    linhas.append({"etapa": "amostra_final", "entraram": "", "descartados": "",
                   "restaram": len(aceitos), "motivo_descarte": ""})

    _salvar_csv(saida / "funil.csv",
                ["etapa", "entraram", "descartados", "restaram", "motivo_descarte"], linhas)
    _salvar_csv(saida / "descartes.csv", ["full_name", "etapa", "motivo"], descartes)
    _salvar_csv(saida / "metadados.csv",
                ["full_name", "stars", "language", "default_branch", "created_at",
                 "idade_dias", "contribuidores"], metadados)
    log.info("funil: %d avaliados -> %d aceitos", avaliados, len(aceitos))
    return aceitos
