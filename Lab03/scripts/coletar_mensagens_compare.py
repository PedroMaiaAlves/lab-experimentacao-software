"""Coleta assuntos dos commits dos links compare da amostra-ouro via patches públicos."""
from __future__ import annotations

import argparse
import csv
import re
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import pandas as pd
import requests

ASSUNTO = re.compile(r"^Subject: (?:\[PATCH[^]]*\]\s*)?(.*)$")


def coletar(linha: dict[str, str]) -> tuple[list[dict[str, str]], dict[str, str]]:
    url = str(linha.get("compare_url", "")).strip()
    base = {"full_name": linha["full_name"], "release_id": linha["release_id"]}
    if not url:
        return [], {**base, "status": "sem_compare_url", "mensagens": "0"}
    try:
        resposta = requests.get(
            url + ".patch", timeout=60,
            headers={"User-Agent": "lab-experimentacao-software-s02"},
        )
        resposta.raise_for_status()
        mensagens = []
        for texto in resposta.text.splitlines():
            achado = ASSUNTO.match(texto)
            if achado:
                mensagens.append({**base, "message": achado.group(1).strip()})
        return mensagens, {**base, "status": "ok", "mensagens": str(len(mensagens))}
    except requests.RequestException as erro:
        return [], {**base, "status": f"erro:{type(erro).__name__}", "mensagens": "0"}


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--amostra", default="data/amostra_ouro/releases_sorteadas.csv")
    parser.add_argument("--saida", default="data/commits_entre_releases_s02.csv")
    parser.add_argument("--status", default="data/coleta_mensagens_s02.csv")
    parser.add_argument("--workers", type=int, default=8)
    args = parser.parse_args(argv)
    amostra = pd.read_csv(args.amostra, dtype=str).fillna("").to_dict("records")
    mensagens, status = [], []
    with ThreadPoolExecutor(max_workers=args.workers) as executor:
        futuros = {executor.submit(coletar, linha): linha for linha in amostra}
        for futuro in as_completed(futuros):
            novas, situacao = futuro.result()
            mensagens.extend(novas)
            status.append(situacao)
    mensagens.sort(key=lambda x: (x["full_name"], x["release_id"], x["message"]))
    status.sort(key=lambda x: (x["full_name"], x["release_id"]))
    for caminho, linhas, campos in (
        (Path(args.saida), mensagens, ["full_name", "release_id", "message"]),
        (Path(args.status), status, ["full_name", "release_id", "status", "mensagens"]),
    ):
        caminho.parent.mkdir(parents=True, exist_ok=True)
        with caminho.open("w", newline="", encoding="utf-8") as arquivo:
            writer = csv.DictWriter(arquivo, fieldnames=campos)
            writer.writeheader()
            writer.writerows(linhas)
    erros = sum(item["status"] != "ok" for item in status)
    print(f"{len(mensagens)} mensagens; {len(status)} comparações; {erros} sem coleta")
    return 0 if not erros else 2


if __name__ == "__main__":
    raise SystemExit(main())
