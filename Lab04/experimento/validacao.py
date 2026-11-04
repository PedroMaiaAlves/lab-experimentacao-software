"""Conferência offline de proveniência, pareamento e reprodução da entrega."""

from __future__ import annotations

import csv
import json
from pathlib import Path

import numpy as np

from .dados import ROOT, ler_json, ler_pares, sha256


def exigir(condicao: bool, mensagem: str) -> None:
    if not condicao:
        raise ValueError(mensagem)


def validar_hashes(diretorio: Path, hashes: dict) -> None:
    for name, expected in hashes.items():
        path = (diretorio / name).resolve()
        exigir(path.is_relative_to(diretorio.resolve()), "Caminho de artefato fora do diretório.")
        exigir(path.is_file() and sha256(path) == expected, f"Artefato ausente ou modificado: {name}")


def validar_coleta(diretorio: Path) -> dict:
    manifest = ler_json(diretorio / "manifesto.json")
    exigir(manifest["status"] == "concluido", "Coleta incompleta não pode calibrar a simulação.")
    validar_hashes(diretorio, manifest["artefatos_sha256"])
    cfg = manifest["protocolo"]
    exigir(manifest["fonte"]["sha256"] == cfg["fonte_sha256"], "Fonte diverge do protocolo.")
    pares = ler_pares(diretorio / "pares_reais.csv")
    exigir(len(pares) == cfg["pares"] == manifest["pares_validos"], "Quantidade de pares incorreta.")
    with (diretorio / "pares_reais.csv").open(encoding="utf-8", newline="") as f:
        rows = list(csv.DictReader(f))
    exigir([int(r["par_id"]) for r in rows] == list(range(1, cfg["pares"] + 1)), "IDs fora de sequência.")
    ordens = [r["ordem"] for r in rows]
    exigir(ordens == manifest["ordens_planejadas"], "Ordem executada difere da planejada.")
    exigir(ordens.count("sem_cache->com_cache") == cfg["pares"] // 2
           and ordens.count("com_cache->sem_cache") == cfg["pares"] // 2, "Ordem não balanceada.")
    logs = [json.loads(line) for line in (diretorio / "medicoes.jsonl").read_text(encoding="utf-8").splitlines()]
    with (diretorio / "aquecimento.csv").open(encoding="utf-8", newline="") as f:
        warm = list(csv.DictReader(f))
    exigir(len(warm) == cfg["pares_aquecimento"], "Aquecimento incompleto.")
    quantidade_fontes = manifest["fonte"]["arquivos_python"]
    for fase, records in (("real", rows), ("aquecimento", warm)):
        for row in records:
            selected = [x for x in logs if x["fase"] == fase and x["par_id"] == int(row["par_id"])
                        and x["tentativa"] == int(row["tentativa"]) and x["status"] == "ok"]
            exigir(len(selected) == 2, "Par não possui duas medições bem-sucedidas no log.")
            exigir("->".join(x["condicao"] for x in selected) == row["ordem"], "Ordem diverge do log.")
            for measurement in selected:
                condition = measurement["condicao"]
                exigir(float(row[condition + "_s"]) == measurement["duracao_s"]
                       == measurement["duracao_ns"] / 1e9, "Tempo do CSV diverge da medição.")
                exigir(measurement["cache_antes"] == (quantidade_fontes if condition == "com_cache" else 0),
                       "Estado inicial do cache incorreto.")
                exigir(measurement["cache_depois"] == quantidade_fontes, "Cache final incompleto.")
                exigir(condition != "com_cache" or measurement["cache_reutilizado"], "Cache não reutilizado.")
                exigir(measurement["exit_code"] == 0, "Medição falhou.")
    return manifest


def validar_entrega(real: Path = ROOT / "data/real", simulado: Path = ROOT / "data/simulado") -> dict:
    from .simulacao import calibrar, gerar_pares

    manifest = validar_coleta(real)
    params = ler_json(simulado / "parametros.json")
    sim_manifest = ler_json(simulado / "manifesto.json")
    validar_hashes(simulado, sim_manifest["artefatos_sha256"])
    exigir(params["fonte"]["sha256"] == sha256(real / "pares_reais.csv"), "Simulação usa outra coleta.")
    exigir(params["fonte"]["manifesto_sha256"] == sha256(real / "manifesto.json"), "Manifesto da coleta mudou.")
    exigir(params["numpy"] == np.__version__, "Reprodução exata exige a versão registrada do NumPy.")
    calibrated = calibrar(ler_pares(real / "pares_reais.csv"))
    exigir(all(params[k] == v for k, v in calibrated.items()), "Calibração difere dos dados reais.")
    actual = ler_pares(simulado / "pares_simulados.csv")
    expected = gerar_pares(params, params["n_simulado"], params["semente"], params["delta_log_aplicado"])
    exigir(np.array_equal(actual, expected), "Simulação não reproduz exatamente os pares preservados.")
    exigir(sha256(ROOT / "docs/cenario.md") == params["cenario_previo_sha256"], "Cenário prévio foi modificado.")
    return {"status": "ok", "pares_reais": manifest["pares_validos"], "pares_simulados": len(actual),
            "aquecimento_separado": manifest["aquecimento_pares"], "reproducao_exata": True}


def main() -> None:
    print(json.dumps(validar_entrega(), ensure_ascii=False, indent=2))
