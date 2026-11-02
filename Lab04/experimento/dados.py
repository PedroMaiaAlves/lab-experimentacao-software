"""Contratos de dados compartilhados, independentes do dashboard."""

from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
COLUNAS_TEMPOS = ("sem_cache_s", "com_cache_s")


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def ler_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def salvar_json(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + "\n", encoding="utf-8", newline="\n")


def validar_pares(pares: np.ndarray) -> np.ndarray:
    a = np.asarray(pares, dtype=float)
    if a.ndim != 2 or a.shape[1] != 2 or a.shape[0] < 2:
        raise ValueError("Esperada matriz n x 2, com pelo menos dois pares completos.")
    if not np.isfinite(a).all() or (a <= 0).any():
        raise ValueError("Tempos devem ser positivos e finitos; não remover pares silenciosamente.")
    return a


def ler_pares(path: Path) -> np.ndarray:
    with path.open(encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        if not {"par_id", *COLUNAS_TEMPOS}.issubset(reader.fieldnames or []):
            raise ValueError("CSV não atende ao contrato de pares.")
        rows = list(reader)
    ids = [r["par_id"] for r in rows]
    if any(not x.strip() for x in ids) or len(set(ids)) != len(ids):
        raise ValueError("par_id deve ser preenchido e único.")
    return validar_pares([[float(r[k]) for k in COLUNAS_TEMPOS] for r in rows])


def salvar_pares(path: Path, pares: np.ndarray) -> None:
    a = validar_pares(pares)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f, lineterminator="\n")
        writer.writerow(["par_id", *COLUNAS_TEMPOS])
        for i, (sem, com) in enumerate(a, 1):
            writer.writerow([i, repr(float(sem)), repr(float(com))])
