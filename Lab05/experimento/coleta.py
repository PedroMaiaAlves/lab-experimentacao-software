"""Orquestra o piloto reproduzível de Kafka e RabbitMQ."""

from __future__ import annotations

import csv
import ctypes
import json
import os
import platform
import re
import statistics
import subprocess
import threading
import time
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Protocol

from . import plano

RAIZ = Path(__file__).resolve().parents[1]
COMPOSE = RAIZ / "docker-compose.yml"
TEMPLATE = RAIZ / "benchmark" / "workloads" / "template.yaml"
IMAGENS = {
    "kafka": "apache/kafka:4.4.0",
    "rabbitmq": "rabbitmq:4.4.1-management",
}
CONTAINERS = {"kafka": "lab05-kafka", "rabbitmq": "lab05-rabbitmq"}


@dataclass
class Resultado:
    colecao_id: str
    ordem: int
    id_execucao: str
    experimento: str
    broker: str
    versao: str
    tamanho_bytes: int
    repeticao: int
    status: str
    inicio_utc: str
    fim_utc: str
    duracao_s: float
    aquecimento_s: int
    medicao_s: int
    taxa_alvo_msg_s: int | None = None
    throughput_msg_s: float | None = None
    throughput_mib_s: float | None = None
    latencia_p50_ms: float | None = None
    latencia_p99_ms: float | None = None
    cpu_percent_medio: float | None = None
    memoria_mib_media: float | None = None
    codigo_saida: int | None = None
    erro: str | None = None
    resultado_bruto: str | None = None
    stdout: str | None = None
    stderr: str | None = None
    comando: str | None = None


class Executor(Protocol):
    def executar(
        self, execucao: plano.Execucao, workload: Path, bruto: Path, stdout: Path, stderr: Path
    ) -> tuple[int, list[float], list[float], list[str]]: ...

    def limpar(self) -> None: ...

    def metadados(self) -> dict[str, Any]: ...


def agora_utc() -> datetime:
    return datetime.now(timezone.utc)


def iso(dt: datetime) -> str:
    return dt.isoformat(timespec="milliseconds").replace("+00:00", "Z")


def criar_diretorio_coleta(raiz: Path, instante: datetime | None = None) -> Path:
    instante = instante or agora_utc()
    colecao_id = instante.strftime("%Y%m%dT%H%M%S.%fZ")
    raiz.mkdir(parents=True, exist_ok=True)
    destino = raiz / colecao_id
    destino.mkdir(exist_ok=False)
    for nome in ("raw", "logs", "workloads"):
        (destino / nome).mkdir()
    return destino


def renderizar_workload(execucao: plano.Execucao, taxa_produtor: int, destino: Path) -> Path:
    texto = TEMPLATE.read_text(encoding="utf-8").format(
        experimento=execucao.experimento,
        broker=execucao.broker,
        tamanho_bytes=execucao.tamanho_bytes,
        taxa_produtor=taxa_produtor,
        aquecimento_s=execucao.aquecimento_s,
        medicao_s=execucao.medicao_s,
    )
    destino.write_text(texto, encoding="utf-8")
    return destino


def _media(valores: list[float]) -> float | None:
    return round(statistics.fmean(valores), 6) if valores else None


def interpretar_resultado_omb(caminho: Path, tamanho_bytes: int) -> dict[str, float]:
    dados = json.loads(caminho.read_text(encoding="utf-8"))
    taxas = [float(v) for v in dados.get("publishRate", [])]
    if not taxas:
        raise ValueError("OMB não produziu amostras de publishRate")
    throughput = statistics.fmean(taxas)
    return {
        "throughput_msg_s": round(throughput, 6),
        "throughput_mib_s": round(throughput * tamanho_bytes / 1024**2, 6),
        "latencia_p50_ms": float(dados.get("aggregatedEndToEndLatency50pct", 0.0)),
        "latencia_p99_ms": float(dados.get("aggregatedEndToEndLatency99pct", 0.0)),
    }


def taxas_e2(resultados_e1: list[Resultado]) -> dict[int, int]:
    saida: dict[int, int] = {}
    for tamanho in plano.TAMANHOS_BYTES:
        medianas = []
        for broker in plano.BROKERS:
            valores = [
                r.throughput_msg_s
                for r in resultados_e1
                if r.status == "sucesso"
                and r.broker == broker
                and r.tamanho_bytes == tamanho
                and r.throughput_msg_s is not None
            ]
            if valores:
                medianas.append(statistics.median(valores))
        if len(medianas) == len(plano.BROKERS):
            saida[tamanho] = max(1, int(min(medianas) * 0.5))
    return saida


def _memoria_total_bytes() -> int | None:
    if os.name == "nt":
        class EstadoMemoria(ctypes.Structure):
            _fields_ = [
                ("dwLength", ctypes.c_ulong),
                ("dwMemoryLoad", ctypes.c_ulong),
                ("ullTotalPhys", ctypes.c_ulonglong),
                ("ullAvailPhys", ctypes.c_ulonglong),
                ("ullTotalPageFile", ctypes.c_ulonglong),
                ("ullAvailPageFile", ctypes.c_ulonglong),
                ("ullTotalVirtual", ctypes.c_ulonglong),
                ("ullAvailVirtual", ctypes.c_ulonglong),
                ("ullAvailExtendedVirtual", ctypes.c_ulonglong),
            ]

        estado = EstadoMemoria()
        estado.dwLength = ctypes.sizeof(EstadoMemoria)
        if ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(estado)):
            return int(estado.ullTotalPhys)
    return None


def _comando_curto(args: list[str], timeout: int = 20) -> str | None:
    try:
        proc = subprocess.run(args, capture_output=True, text=True, timeout=timeout, check=False)
        return proc.stdout.strip() or proc.stderr.strip() or None
    except (OSError, subprocess.SubprocessError):
        return None


def metadados_ambiente() -> dict[str, Any]:
    return {
        "so": platform.platform(),
        "cpu": platform.processor(),
        "processadores_logicos": os.cpu_count(),
        "memoria_total_bytes": _memoria_total_bytes(),
        "python": platform.python_version(),
        "docker": _comando_curto(["docker", "version", "--format", "{{json .}}"]),
        "docker_compose": _comando_curto(["docker", "compose", "version", "--short"]),
        "git_commit": _comando_curto(["git", "rev-parse", "HEAD"]),
    }


def _converter_mib(valor: str) -> float:
    correspondencia = re.fullmatch(r"\s*([0-9.]+)\s*([KMGT]?i?B)\s*", valor, re.IGNORECASE)
    if not correspondencia:
        raise ValueError(f"memória inválida: {valor}")
    numero = float(correspondencia.group(1))
    unidade = correspondencia.group(2).lower()
    fatores = {"b": 1 / 1024**2, "kb": 1 / 1024, "kib": 1 / 1024, "mb": 1, "mib": 1,
               "gb": 1024, "gib": 1024, "tb": 1024**2, "tib": 1024**2}
    return numero * fatores[unidade]


def interpretar_stats(texto: str) -> tuple[float, float]:
    cpu, memoria = texto.strip().split("|", maxsplit=1)
    usada = memoria.split("/", maxsplit=1)[0]
    return float(cpu.strip().removesuffix("%")), _converter_mib(usada)


class DockerExecutor:
    def __init__(self, diretorio_coleta: Path):
        self.diretorio_coleta = diretorio_coleta
        self.base = ["docker", "compose", "-f", str(COMPOSE)]

    def _run(self, args: list[str], *, timeout: int = 180, check: bool = True) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            args, cwd=RAIZ.parent, capture_output=True, text=True, timeout=timeout, check=check
        )

    def limpar(self) -> None:
        self._run(self.base + ["down", "--volumes", "--remove-orphans", "--timeout", "10"], check=False)

    def _subir(self, broker: str) -> None:
        self._run(self.base + ["--profile", broker, "up", "-d", "--wait", broker], timeout=240)

    def _stats(self, broker: str) -> tuple[float, float] | None:
        proc = self._run(
            ["docker", "stats", "--no-stream", "--format", "{{.CPUPerc}}|{{.MemUsage}}", CONTAINERS[broker]],
            timeout=15,
            check=False,
        )
        if proc.returncode or not proc.stdout.strip():
            return None
        return interpretar_stats(proc.stdout.splitlines()[0])

    def executar(
        self, execucao: plano.Execucao, workload: Path, bruto: Path, stdout: Path, stderr: Path
    ) -> tuple[int, list[float], list[float], list[str]]:
        self.limpar()
        self._subir(execucao.broker)
        relativo = self.diretorio_coleta.name
        comando = self.base + [
            "--profile", "benchmark", "run", "--rm",
            "-v", f"{self.diretorio_coleta.parent.resolve()}:/resultados",
            "omb",
            "--drivers", f"/workspace/drivers/{execucao.broker}.yaml",
            "--output", f"/resultados/{relativo}/raw/{bruto.name}",
            f"/resultados/{relativo}/workloads/{workload.name}",
        ]
        cpus: list[float] = []
        memorias: list[float] = []
        with stdout.open("w", encoding="utf-8") as out, stderr.open("w", encoding="utf-8") as err:
            proc = subprocess.Popen(comando, cwd=RAIZ.parent, stdout=out, stderr=err, text=True)
            inicio_benchmark = time.monotonic()
            limite = inicio_benchmark + execucao.aquecimento_s + execucao.medicao_s + 240
            while proc.poll() is None:
                agora = time.monotonic()
                if agora > limite:
                    proc.kill()
                    err.write("\nColetor: tempo limite excedido.\n")
                    break
                amostra = self._stats(execucao.broker)
                # O aquecimento também é descartado das métricas de recursos.
                if amostra and agora - inicio_benchmark >= execucao.aquecimento_s:
                    cpus.append(amostra[0])
                    memorias.append(amostra[1])
                time.sleep(1)
            codigo = proc.wait(timeout=30)
        return codigo, cpus, memorias, comando

    def metadados(self) -> dict[str, Any]:
        digests = {}
        for broker, imagem in IMAGENS.items():
            digests[broker] = _comando_curto(
                ["docker", "image", "inspect", imagem, "--format", "{{index .RepoDigests 0}}"]
            )
        digests["omb"] = _comando_curto(
            ["docker", "image", "inspect", "lab05/openmessaging-benchmark:5b1fa709", "--format", "{{.Id}}"]
        )
        return {"ambiente": metadados_ambiente(), "imagens": digests}


class Coletor:
    def __init__(self, diretorio: Path, executor: Executor):
        self.diretorio = diretorio
        self.executor = executor
        self.csv = diretorio / "resultados.csv"
        self.manifesto = diretorio / "manifesto.json"
        self.resultados: list[Resultado] = []
        self.metadados = executor.metadados()
        with self.csv.open("x", newline="", encoding="utf-8") as arquivo:
            csv.DictWriter(arquivo, fieldnames=list(Resultado.__dataclass_fields__)).writeheader()

    def _salvar(self, resultado: Resultado) -> None:
        self.resultados.append(resultado)
        with self.csv.open("a", newline="", encoding="utf-8") as arquivo:
            csv.DictWriter(arquivo, fieldnames=list(Resultado.__dataclass_fields__)).writerow(asdict(resultado))
        self._manifesto("em_andamento")

    def _manifesto(self, status: str) -> None:
        contagens: dict[str, int] = {}
        for resultado in self.resultados:
            contagens[resultado.status] = contagens.get(resultado.status, 0) + 1
        dados = {
            "schema": 1,
            "colecao_id": self.diretorio.name,
            "status": status,
            "semente": plano.SEMENTE,
            "execucoes_por_celula": 3,
            "planejadas": 24,
            "registradas": len(self.resultados),
            "contagens": contagens,
            "fixas": plano.FIXAS,
            **self.metadados,
        }
        temporario = self.manifesto.with_suffix(".json.tmp")
        temporario.write_text(json.dumps(dados, ensure_ascii=False, indent=2), encoding="utf-8")
        temporario.replace(self.manifesto)

    def _bloqueada(self, execucao: plano.Execucao, motivo: str) -> Resultado:
        instante = agora_utc()
        return Resultado(
            colecao_id=self.diretorio.name,
            ordem=execucao.ordem,
            id_execucao=execucao.id_execucao,
            experimento=execucao.experimento,
            broker=execucao.broker,
            versao=execucao.versao,
            tamanho_bytes=execucao.tamanho_bytes,
            repeticao=execucao.repeticao,
            status="bloqueada",
            inicio_utc=iso(instante), fim_utc=iso(instante), duracao_s=0.0,
            aquecimento_s=execucao.aquecimento_s, medicao_s=execucao.medicao_s, erro=motivo,
        )

    def executar_uma(self, execucao: plano.Execucao, taxa: int) -> Resultado:
        inicio = agora_utc()
        bruto = self.diretorio / "raw" / f"{execucao.id_execucao}.json"
        stdout = self.diretorio / "logs" / f"{execucao.id_execucao}.stdout.log"
        stderr = self.diretorio / "logs" / f"{execucao.id_execucao}.stderr.log"
        workload = renderizar_workload(
            execucao, taxa, self.diretorio / "workloads" / f"{execucao.id_execucao}.yaml"
        )
        status, erro, codigo = "falha", None, None
        cpus: list[float] = []
        memorias: list[float] = []
        comando: list[str] = []
        metricas: dict[str, float] = {}
        try:
            codigo, cpus, memorias, comando = self.executor.executar(
                execucao, workload, bruto, stdout, stderr
            )
            if codigo != 0:
                raise RuntimeError(f"OMB terminou com código {codigo}")
            if not bruto.exists():
                raise RuntimeError("OMB não criou o JSON de resultado")
            metricas = interpretar_resultado_omb(bruto, execucao.tamanho_bytes)
            status = "sucesso"
        except KeyboardInterrupt:
            status, erro = "interrompida", "coleta interrompida pelo usuário"
            raise
        except Exception as exc:  # a falha vira dado e as outras células continuam
            erro = f"{type(exc).__name__}: {exc}"
        finally:
            self.executor.limpar()
            fim = agora_utc()
            resultado = Resultado(
                colecao_id=self.diretorio.name,
                ordem=execucao.ordem,
                id_execucao=execucao.id_execucao,
                experimento=execucao.experimento,
                broker=execucao.broker,
                versao=execucao.versao,
                tamanho_bytes=execucao.tamanho_bytes,
                repeticao=execucao.repeticao,
                status=status,
                inicio_utc=iso(inicio), fim_utc=iso(fim),
                duracao_s=round((fim - inicio).total_seconds(), 3),
                aquecimento_s=execucao.aquecimento_s, medicao_s=execucao.medicao_s,
                taxa_alvo_msg_s=taxa if taxa > 0 else None,
                cpu_percent_medio=_media(cpus), memoria_mib_media=_media(memorias),
                codigo_saida=codigo, erro=erro,
                resultado_bruto=str(bruto.relative_to(self.diretorio)) if bruto.exists() else None,
                stdout=str(stdout.relative_to(self.diretorio)) if stdout.exists() else None,
                stderr=str(stderr.relative_to(self.diretorio)) if stderr.exists() else None,
                comando=json.dumps(comando, ensure_ascii=False) if comando else None,
                **metricas,
            )
            self._salvar(resultado)
        return resultado

    def piloto(self) -> list[Resultado]:
        self._manifesto("em_andamento")
        interrompida = False
        try:
            for execucao in plano.gerar_plano("E1", 3):
                self.executar_uma(execucao, 0)
            alvos = taxas_e2(self.resultados)
            for execucao in plano.gerar_plano("E2", 3):
                if execucao.tamanho_bytes not in alvos:
                    self._salvar(self._bloqueada(execucao, "E1 sem sucesso nos dois brokers para este tamanho"))
                    continue
                self.executar_uma(execucao, alvos[execucao.tamanho_bytes])
        except KeyboardInterrupt:
            interrompida = True
        finally:
            self.executor.limpar()
            self._manifesto("interrompida" if interrompida else "concluida")
        return self.resultados
