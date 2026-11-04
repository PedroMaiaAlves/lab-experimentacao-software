"""Medição real de compileall; preparação e verificações fora do cronômetro."""

from __future__ import annotations

import argparse
import csv
from datetime import datetime, timezone
import importlib.util
import json
import os
from pathlib import Path
import platform
import random
import shutil
import struct
import subprocess
import sys
import tarfile
import time
import urllib.request
import uuid

from .dados import ROOT, ler_json, salvar_json, sha256

CONDICOES = ("sem_cache", "com_cache")
CAMPOS = ["par_id", "ordem", "sem_cache_s", "com_cache_s", "tentativa",
          "sem_cache_inicio_utc", "com_cache_inicio_utc"]


def agora() -> str:
    return datetime.now(timezone.utc).isoformat()


def ordens_balanceadas(n: int, seed: int) -> list[tuple[str, str]]:
    if n < 2 or n % 2:
        raise ValueError("Número de pares oficiais deve ser positivo e par.")
    ordens = [CONDICOES] * (n // 2) + [CONDICOES[::-1]] * (n // 2)
    random.Random(seed).shuffle(ordens)
    return ordens


def registrar(path: Path, event: dict) -> None:
    with path.open("a", encoding="utf-8", newline="\n") as f:
        f.write(json.dumps(event, ensure_ascii=False, allow_nan=False) + "\n")


def preparar_fonte(cfg: dict, destino: Path) -> tuple[Path, dict]:
    cache = ROOT / ".cache"
    cache.mkdir(exist_ok=True)
    archive = cache / "django-5.2.8.tar.gz"
    url_final = cfg["fonte_url"]
    if not archive.exists():
        with urllib.request.urlopen(cfg["fonte_url"], timeout=60) as response:
            content = response.read()
            url_final = response.url
        archive.write_bytes(content)
    if sha256(archive) != cfg["fonte_sha256"]:
        raise ValueError("SHA-256 da fonte difere do protocolo; coleta interrompida.")
    # Uma extração nova por sessão impede reutilizar uma árvore modificada.
    extraction = cache / ("fonte_" + uuid.uuid4().hex)
    extraction.mkdir()
    with tarfile.open(archive) as tf:
        prefix = cfg["subdiretorio"] + "/"
        members = [m for m in tf.getmembers() if m.name.startswith(prefix)]
        if not members or any(not (m.isfile() or m.isdir()) for m in members):
            raise ValueError("Árvore-fonte ausente ou contém links inesperados.")
        tf.extractall(extraction, members=members, filter="data")
    source = extraction / cfg["subdiretorio"]
    files = sorted(source.rglob("*.py"))
    if not files:
        raise ValueError("Nenhum arquivo Python na fonte.")
    with (destino / "arquivos_fonte.csv").open("w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f, lineterminator="\n")
        writer.writerow(["caminho", "sha256"])
        writer.writerows((p.relative_to(source).as_posix(), sha256(p)) for p in files)
    return source, {
        "url": cfg["fonte_url"], "url_resolvida_download": url_final,
        "sha256": sha256(archive), "checksum_url": cfg["checksum_url"],
        "verificacao": "SHA-256 conferido com valor oficial fixado; assinatura PGP não verificada",
        "arquivos_python": len(files), "diretorio_local": str(source),
        "inventario_sha256": sha256(destino / "arquivos_fonte.csv"),
    }


class Medidor:
    def __init__(self, source: Path, cache_root: Path, timeout: int = 120):
        self.source = source.resolve()
        self.cache_root = cache_root.resolve()
        if self.source == self.cache_root or not self.source.is_relative_to(self.cache_root):
            raise ValueError("Fonte deve estar dentro da área isolada de cache.")
        self.files = sorted(self.source.rglob("*.py"))
        if not self.files:
            raise ValueError("Fonte sem arquivos .py.")
        self.pycs = [Path(importlib.util.cache_from_source(str(p), optimization="")) for p in self.files]
        self.command = [sys.executable, "-I", "-m", "compileall", "-q", "-j", "1",
                        "--invalidation-mode", "timestamp", "-o", "0", str(self.source)]
        self.timeout = timeout

    def limpar_cache(self) -> None:
        # Verificação de contenção antes de cada remoção recursiva.
        for path in self.source.rglob("__pycache__"):
            target = path.resolve()
            if not target.is_relative_to(self.source) or target == self.source or path.is_symlink():
                raise ValueError("Diretório de cache fora da fonte isolada.")
            shutil.rmtree(target)
        if any(self.source.rglob("*.pyc")):
            raise ValueError("Restaram arquivos .pyc inesperados após a limpeza.")

    def snapshot_cache(self) -> dict:
        return {str(p): (p.stat().st_size, p.stat().st_mtime_ns) for p in self.pycs if p.exists()}

    def conferir_cache(self) -> None:
        for source, pyc in zip(self.files, self.pycs):
            with pyc.open("rb") as f:
                header = f.read(16)
            if len(header) != 16:
                raise ValueError("Cabeçalho .pyc incompleto.")
            magic, flags, timestamp, size = struct.unpack("<4sIII", header)
            st = source.stat()
            if (magic != importlib.util.MAGIC_NUMBER or flags != 0
                    or timestamp != (int(st.st_mtime) & 0xffffffff)
                    or size != (st.st_size & 0xffffffff)):
                raise ValueError("Cache não corresponde à fonte/interpreter/timestamp.")

    def executar(self):
        return subprocess.run(self.command, capture_output=True, text=True,
                              encoding="utf-8", errors="replace", timeout=self.timeout,
                              check=True)

    def medir(self, condicao: str) -> dict:
        if condicao not in CONDICOES:
            raise ValueError("Condição desconhecida.")
        self.limpar_cache()
        if condicao == "com_cache":
            self.executar()  # Preenchimento fora da medição.
            self.conferir_cache()
        before = self.snapshot_cache()
        expected = len(self.files) if condicao == "com_cache" else 0
        if len(before) != expected:
            raise ValueError("Estado inicial do cache inválido.")
        inicio = agora()
        start = time.perf_counter_ns()
        process = self.executar()
        elapsed_ns = time.perf_counter_ns() - start
        fim = agora()
        if elapsed_ns <= 0:
            raise ValueError("Duração não positiva.")
        self.conferir_cache()
        after = self.snapshot_cache()
        if condicao == "com_cache" and before != after:
            raise ValueError("Execução com cache reescreveu bytecode; par inválido.")
        return {
            "condicao": condicao, "inicio_utc": inicio, "fim_utc": fim,
            "duracao_ns": elapsed_ns, "duracao_s": elapsed_ns / 1e9,
            "cache_antes": len(before), "cache_depois": len(after),
            "cache_reutilizado": condicao == "com_cache" and before == after,
            "exit_code": process.returncode, "stdout": process.stdout, "stderr": process.stderr,
        }


def coletar_par(medidor: Medidor, ordem: tuple, par_id: int, fase: str,
                destino: Path, max_tentativas: int) -> dict:
    for tentativa in range(1, max_tentativas + 1):
        measurements = {}
        for posicao, condicao in enumerate(ordem, 1):
            context = {"fase": fase, "par_id": par_id, "tentativa": tentativa, "posicao": posicao}
            try:
                result = medidor.medir(condicao)
            except (OSError, ValueError, subprocess.SubprocessError) as exc:
                failure = {**context, "condicao": condicao, "instante_utc": agora(),
                           "erro": type(exc).__name__, "mensagem": str(exc),
                           "stdout": str(getattr(exc, "stdout", "")),
                           "stderr": str(getattr(exc, "stderr", "")),
                           "acao": "descartar a tentativa inteira e repetir o par"}
                registrar(destino / "falhas.jsonl", failure)
                registrar(destino / "medicoes.jsonl", {**failure, "status": "falha"})
                break
            registrar(destino / "medicoes.jsonl", {**context, **result, "status": "ok"})
            measurements[condicao] = result
        if len(measurements) == 2:
            return {
                "par_id": par_id, "ordem": "->".join(ordem), "tentativa": tentativa,
                **{f"{c}_s": measurements[c]["duracao_s"] for c in CONDICOES},
                **{f"{c}_inicio_utc": measurements[c]["inicio_utc"] for c in CONDICOES},
            }
    raise RuntimeError(f"Par {par_id} ({fase}) falhou {max_tentativas} vezes; sessão incompleta preservada.")


def coletar(destino: Path) -> dict:
    cfg = ler_json(ROOT / "protocolo.json")
    if platform.python_version() != cfg["python"] or platform.python_implementation() != "CPython":
        raise ValueError(f"Coleta exige CPython {cfg['python']}; atual: {platform.python_version()}.")
    destino.mkdir(parents=True, exist_ok=False)  # Nunca sobrescrever coleta anterior.
    official_orders = ordens_balanceadas(cfg["pares"], cfg["semente"])
    files = [ROOT / "protocolo.json", ROOT / "docs/cenario.md", *sorted((ROOT / "experimento").glob("*.py"))]
    manifest = {
        "status": "em_andamento", "inicio_utc": agora(), "protocolo": cfg,
        "registro_previo": {p.relative_to(ROOT).as_posix(): sha256(p) for p in files},
        "ambiente": {"python": platform.python_version(), "implementacao": platform.python_implementation(),
                     "executavel": sys.executable, "sistema": platform.platform(),
                     "arquitetura": platform.machine(), "processador": platform.processor(),
                     "cpus_logicas": os.cpu_count(), "relogio": vars(time.get_clock_info("perf_counter"))},
        "ordens_planejadas": ["->".join(x) for x in official_orders],
        "aquecimento_pares": cfg["pares_aquecimento"],
        "limites": ["Uma máquina, uma versão do projeto, repetições temporais.",
                    "Cache de disco, antivírus e carga do SO não controlados.",
                    "Somente compilação bytecode; não é o build completo do Django."],
    }
    manifest_path = destino / "manifesto.json"
    salvar_json(manifest_path, manifest)
    for name in ("medicoes.jsonl", "falhas.jsonl"):
        (destino / name).touch()
    try:
        source, manifest["fonte"] = preparar_fonte(cfg, destino)
        medidor = Medidor(source, ROOT / ".cache", cfg["timeout_s"])
        manifest["comando"] = medidor.command
        salvar_json(manifest_path, manifest)
        phases = [("aquecimento", [CONDICOES if i % 2 == 0 else CONDICOES[::-1]
                                  for i in range(cfg["pares_aquecimento"])]),
                  ("real", official_orders)]
        for fase, ordens in phases:
            filename = "pares_reais.csv" if fase == "real" else "aquecimento.csv"
            with (destino / filename).open("w", encoding="utf-8", newline="") as f:
                writer = csv.DictWriter(f, fieldnames=CAMPOS, lineterminator="\n")
                writer.writeheader()
                f.flush()
                for i, ordem in enumerate(ordens, 1):
                    row = coletar_par(medidor, ordem, i, fase, destino, cfg["max_tentativas_por_par"])
                    writer.writerow(row)
                    f.flush()
                    print(f"{fase} {i}/{len(ordens)}: sem={row['sem_cache_s']:.6f}s com={row['com_cache_s']:.6f}s", flush=True)
        # Confere integridade dos fontes depois de todas as medições.
        with (destino / "arquivos_fonte.csv").open(encoding="utf-8", newline="") as f:
            if any(sha256(source / r["caminho"]) != r["sha256"] for r in csv.DictReader(f)):
                raise ValueError("Fonte mudou durante a coleta.")
        manifest["status"] = "concluido"
        manifest["pares_validos"] = cfg["pares"]
    except BaseException as exc:
        manifest["status"] = "incompleto"
        manifest["erro_final"] = f"{type(exc).__name__}: {exc}"
        raise
    finally:
        manifest["fim_utc"] = agora()
        manifest["artefatos_sha256"] = {p.name: sha256(p) for p in sorted(destino.iterdir())
                                        if p.is_file() and p.name != "manifesto.json"}
        salvar_json(manifest_path, manifest)
    return manifest


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--saida", type=Path, default=ROOT / "data/real",
                        help="Diretório novo. Recusa sobrescrever uma coleta existente.")
    args = parser.parse_args()
    manifest = coletar(args.saida.resolve())
    print(f"Coleta {manifest['status']}: {manifest['pares_validos']} pares válidos em {args.saida}")
