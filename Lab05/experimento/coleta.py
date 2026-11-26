"""Orquestra o piloto reproduzível de Kafka e RabbitMQ."""

from __future__ import annotations

import csv
import ctypes
import hashlib
import json
import os
import platform
import re
import statistics
import subprocess
import threading
import time
from contextlib import contextmanager
from dataclasses import asdict, dataclass, replace
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Protocol
from zoneinfo import ZoneInfo

from . import plano

RAIZ = Path(__file__).resolve().parents[1]
COMPOSE = RAIZ / "docker-compose.yml"
TEMPLATE = RAIZ / "benchmark" / "workloads" / "template.yaml"
PROTOCOLO_OFICIAL = RAIZ / "data" / "plano" / "protocolo_oficial.json"
PROTOCOLO_COLETA_MD = RAIZ / "docs" / "protocolo_coleta.md"
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
    bloco: str
    ordem_no_bloco: int
    tentativa: int
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
    throughput_consumo_msg_s: float | None = None
    cv_intervalos: float | None = None
    intervalo_min_rel: float | None = None
    colapso: bool | None = None
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


@contextmanager
def sem_suspensao():
    """Impede que o Windows suspenda durante a coleta (#209).

    No mini-piloto de 25/11 a máquina suspendeu no meio da execução 12; três
    execuções ficaram horas paradas e falharam com timeout negativo (salto de
    relógio). SetThreadExecutionState vale só enquanto o processo roda.
    """
    if os.name != "nt":
        yield
        return
    ES_CONTINUOUS, ES_SYSTEM_REQUIRED = 0x80000000, 0x00000001
    kernel = ctypes.windll.kernel32
    kernel.SetThreadExecutionState(ES_CONTINUOUS | ES_SYSTEM_REQUIRED)
    try:
        yield
    finally:
        kernel.SetThreadExecutionState(ES_CONTINUOUS)


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


def sha256_arquivo(caminho: Path) -> str:
    digest = hashlib.sha256()
    with caminho.open("rb") as arquivo:
        for bloco in iter(lambda: arquivo.read(1024 * 1024), b""):
            digest.update(bloco)
    return digest.hexdigest()


def _opcional(texto: str, conversor):
    return conversor(texto) if texto not in ("", None) else None


def carregar_resultados(caminho: Path) -> list[Resultado]:
    if not caminho.exists():
        return []
    inteiros = {
        "ordem", "tamanho_bytes", "repeticao", "ordem_no_bloco", "tentativa",
        "aquecimento_s", "medicao_s", "taxa_alvo_msg_s", "codigo_saida",
    }
    flutuantes = {
        "duracao_s", "throughput_msg_s", "throughput_mib_s", "latencia_p50_ms",
        "latencia_p99_ms", "throughput_consumo_msg_s", "cv_intervalos",
        "intervalo_min_rel", "cpu_percent_medio", "memoria_mib_media",
    }
    saida = []
    with caminho.open(encoding="utf-8") as arquivo:
        for linha in csv.DictReader(arquivo):
            dados: dict[str, Any] = {}
            for campo in Resultado.__dataclass_fields__:
                texto = linha.get(campo, "")
                if campo in inteiros:
                    dados[campo] = _opcional(texto, int)
                elif campo in flutuantes:
                    dados[campo] = _opcional(texto, float)
                elif campo == "colapso":
                    dados[campo] = None if texto == "" else texto.lower() == "true"
                else:
                    dados[campo] = texto or None
            dados["bloco"] = dados["bloco"] or f"{dados['experimento']}-B1"
            dados["ordem_no_bloco"] = dados["ordem_no_bloco"] or dados["ordem"]
            dados["tentativa"] = dados["tentativa"] or 1
            saida.append(Resultado(**dados))
    return saida


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
    consumo = [float(v) for v in dados.get("consumeRate", [])]
    return {
        "throughput_msg_s": round(throughput, 6),
        "throughput_mib_s": round(throughput * tamanho_bytes / 1024**2, 6),
        "latencia_p50_ms": float(dados.get("aggregatedEndToEndLatency50pct", 0.0)),
        "latencia_p99_ms": float(dados.get("aggregatedEndToEndLatency99pct", 0.0)),
        "throughput_consumo_msg_s": round(statistics.fmean(consumo), 6) if consumo else None,
        **estabilidade_intervalos(taxas),
    }


def estabilidade_intervalos(taxas: list[float]) -> dict[str, Any]:
    """Estabilidade dentro de uma execução, a partir das taxas por intervalo (10 s no OMB).

    `colapso` marca a assinatura do problema do piloto: algum intervalo abaixo de
    G1_FRACAO_COLAPSO do MAIOR intervalo da própria execução (ex.: 50k msg/s caindo
    a 1 msg/s). A referência é o máximo, e não a mediana, porque quando a execução
    passa mais da metade do tempo colapsada a mediana já é o valor colapsado.
    """
    referencia = max(taxas)
    if referencia <= 0:
        return {"cv_intervalos": None, "intervalo_min_rel": 0.0, "colapso": True}
    cv = statistics.pstdev(taxas) / statistics.fmean(taxas) if len(taxas) > 1 else 0.0
    minimo_rel = min(taxas) / referencia
    return {
        "cv_intervalos": round(cv, 6),
        "intervalo_min_rel": round(minimo_rel, 6),
        "colapso": minimo_rel < plano.G1_FRACAO_COLAPSO,
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


def metadados_energia() -> dict[str, Any]:
    dados: dict[str, Any] = {
        "plano_energia": _comando_curto(["powercfg", "/getactivescheme"]) if os.name == "nt" else None,
        "fonte": None,
        "bateria_percentual": None,
    }
    if os.name != "nt":
        return dados

    class EstadoEnergia(ctypes.Structure):
        _fields_ = [
            ("ACLineStatus", ctypes.c_ubyte),
            ("BatteryFlag", ctypes.c_ubyte),
            ("BatteryLifePercent", ctypes.c_ubyte),
            ("SystemStatusFlag", ctypes.c_ubyte),
            ("BatteryLifeTime", ctypes.c_ulong),
            ("BatteryFullLifeTime", ctypes.c_ulong),
        ]

    estado = EstadoEnergia()
    if ctypes.windll.kernel32.GetSystemPowerStatus(ctypes.byref(estado)):
        dados["fonte"] = {0: "bateria", 1: "tomada"}.get(estado.ACLineStatus, "desconhecida")
        if estado.BatteryLifePercent != 255:
            dados["bateria_percentual"] = int(estado.BatteryLifePercent)
    return dados


def carregar_plano_oficial(experimento: str) -> list[plano.Execucao]:
    caminho = RAIZ / "data" / "plano" / f"plano_{experimento}.csv"
    execucoes = []
    with caminho.open(encoding="utf-8") as arquivo:
        for r in csv.DictReader(arquivo):
            execucoes.append(
                plano.Execucao(
                    bloco=r["bloco"], ordem=int(r["ordem"]),
                    ordem_no_bloco=int(r["ordem_no_bloco"]), id_execucao=r["id_execucao"],
                    experimento=r["experimento"], broker=r["broker"], versao=r["versao"],
                    tamanho_bytes=int(r["tamanho_bytes"]), repeticao=int(r["repeticao"]),
                    aquecimento_s=int(r["aquecimento_s"]), medicao_s=int(r["medicao_s"]),
                )
            )
    return execucoes


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
        self.todos_perfis = ["--profile", "kafka", "--profile", "rabbitmq", "--profile", "benchmark"]

    def _run(self, args: list[str], *, timeout: int = 180, check: bool = True) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            args, cwd=RAIZ.parent, capture_output=True, text=True, timeout=timeout, check=check
        )

    def limpar(self) -> None:
        # O Compose ignora serviços de perfis inativos até mesmo no `down`.
        self._run(
            self.base + self.todos_perfis
            + ["down", "--volumes", "--remove-orphans", "--timeout", "10"],
            check=False,
        )

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
            ["docker", "image", "inspect", "lab05/openmessaging-benchmark:5b1fa709-ts-ms", "--format", "{{.Id}}"]
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
            bloco=execucao.bloco,
            ordem_no_bloco=execucao.ordem_no_bloco,
            tentativa=1,
            status="bloqueada",
            inicio_utc=iso(instante), fim_utc=iso(instante), duracao_s=0.0,
            aquecimento_s=execucao.aquecimento_s, medicao_s=execucao.medicao_s, erro=motivo,
        )

    def executar_uma(
        self, execucao: plano.Execucao, taxa: int, tentativa: int = 1,
        nomear_tentativa: bool = False,
    ) -> Resultado:
        inicio = agora_utc()
        sufixo = f"-t{tentativa:02d}" if nomear_tentativa or tentativa > 1 else ""
        nome_tentativa = f"{execucao.id_execucao}{sufixo}"
        bruto = self.diretorio / "raw" / f"{nome_tentativa}.json"
        stdout = self.diretorio / "logs" / f"{nome_tentativa}.stdout.log"
        stderr = self.diretorio / "logs" / f"{nome_tentativa}.stderr.log"
        workload = renderizar_workload(
            execucao, taxa, self.diretorio / "workloads" / f"{nome_tentativa}.yaml"
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
                bloco=execucao.bloco,
                ordem_no_bloco=execucao.ordem_no_bloco,
                tentativa=tentativa,
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
                self.executar_uma(execucao, plano.TAXA_E1_ABERTA)
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

    def repetir(self, execucoes: list[plano.Execucao], origem: str) -> list[Resultado]:
        """Repete execuções que falharam numa coleta anterior, sem tocar nela."""
        (self.diretorio / "origem.json").write_text(
            json.dumps({"repete_falhas_de": origem, "ids": [e.id_execucao for e in execucoes]},
                       ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        self._manifesto("em_andamento")
        interrompida = False
        try:
            for execucao in execucoes:
                taxa = plano.TAXA_E1_ABERTA if execucao.experimento == "E1" else 0
                if execucao.experimento != "E1":
                    raise ValueError("repetição automática só cobre E1; E2 depende da taxa calculada")
                self.executar_uma(execucao, taxa)
        except KeyboardInterrupt:
            interrompida = True
        finally:
            self.executor.limpar()
            self._manifesto("interrompida" if interrompida else "concluida")
        return self.resultados

    def mini_piloto_e1(self, repeticoes: int = 5, medicao_s: int | None = None) -> list[Resultado]:
        """Só E1, com taxa aberta, para verificar o portão G1 (#209).

        `medicao_s` permite testar outra duração sem mudar o plano oficial.
        """
        self._manifesto("em_andamento")
        interrompida = False
        try:
            for execucao in plano.gerar_plano("E1", repeticoes):
                if medicao_s is not None:
                    execucao = replace(execucao, medicao_s=medicao_s)
                self.executar_uma(execucao, plano.TAXA_E1_ABERTA)
        except KeyboardInterrupt:
            interrompida = True
        finally:
            self.executor.limpar()
            self._manifesto("interrompida" if interrompida else "concluida")
        return self.resultados


class ColetorOficial(Coletor):
    """Coleta oficial retomável, orientada pelos CSVs congelados no portão G2."""

    def __init__(
        self,
        diretorio: Path,
        executor: Executor,
        protocolo: Path = PROTOCOLO_OFICIAL,
        documento_protocolo: Path = PROTOCOLO_COLETA_MD,
    ):
        self.diretorio = diretorio
        self.executor = executor
        self.csv = diretorio / "resultados.csv"
        self.manifesto = diretorio / "manifesto.json"
        self.documento_protocolo = documento_protocolo
        self.protocolo = json.loads(protocolo.read_text(encoding="utf-8"))
        self.execucoes = {
            e.id_execucao: e
            for exp in plano.EXPERIMENTOS
            for e in carregar_plano_oficial(exp)
        }
        if len(self.execucoes) != 160:
            raise ValueError("os planos oficiais devem conter 160 IDs únicos")

        for nome in ("raw", "logs", "workloads"):
            (diretorio / nome).mkdir(parents=True, exist_ok=True)
        if self.csv.exists():
            self.resultados = carregar_resultados(self.csv)
        else:
            self.resultados = []
            with self.csv.open("x", newline="", encoding="utf-8") as arquivo:
                csv.DictWriter(arquivo, fieldnames=list(Resultado.__dataclass_fields__)).writeheader()

        anterior = {}
        if self.manifesto.exists():
            anterior = json.loads(self.manifesto.read_text(encoding="utf-8"))
            if anterior.get("schema") != 2:
                raise ValueError("manifesto existente não usa o schema oficial 2")
        self.sessoes: list[dict[str, Any]] = list(anterior.get("blocos", []))
        self.taxas_oficiais_e2: dict[int, int] = {
            int(k): int(v) for k, v in anterior.get("taxas_e2", {}).items()
        }
        self.metadados = executor.metadados()
        self._validar_ambiente(anterior)
        self._manifesto(anterior.get("status", "iniciada"))

    def _validar_ambiente(self, anterior: dict[str, Any]) -> None:
        esperadas = {
            nome: dados["fingerprint"]
            for nome, dados in self.protocolo["imagens"].items()
        }
        atuais = self.metadados.get("imagens", {})
        divergencias = [
            f"{nome}: esperado {esperado}, obtido {atuais.get(nome)}"
            for nome, esperado in esperadas.items()
            if atuais.get(nome) != esperado
        ]
        if divergencias:
            raise RuntimeError("fingerprint de imagem divergente: " + "; ".join(divergencias))

        ambiente_anterior = anterior.get("ambiente")
        if ambiente_anterior:
            atual = self.metadados.get("ambiente", {})
            chaves = ("so", "cpu", "processadores_logicos", "memoria_total_bytes")
            diferentes = [c for c in chaves if ambiente_anterior.get(c) != atual.get(c)]
            if diferentes:
                raise RuntimeError("a coleta oficial deve permanecer na mesma máquina: " + ", ".join(diferentes))

    def _hashes(self) -> dict[str, Any]:
        brutos = {
            str(caminho.relative_to(self.diretorio)).replace("\\", "/"): sha256_arquivo(caminho)
            for caminho in sorted((self.diretorio / "raw").glob("*.json"))
        }
        return {"resultados.csv": sha256_arquivo(self.csv), "brutos": brutos}

    def _manifesto(self, status: str) -> None:
        contagens: dict[str, int] = {}
        for resultado in self.resultados:
            contagens[resultado.status] = contagens.get(resultado.status, 0) + 1
        dados = {
            "schema": 2,
            "colecao_id": self.diretorio.name,
            "status": status,
            "semente": self.protocolo["semente"],
            "execucoes_por_celula": self.protocolo["execucoes_por_celula"],
            "planejadas": len(self.execucoes),
            "registradas": len(self.resultados),
            "contagens": contagens,
            "taxas_e2": {str(k): v for k, v in sorted(self.taxas_oficiais_e2.items())},
            "blocos": self.sessoes,
            "fixas": plano.FIXAS,
            "hashes": self._hashes(),
            **self.metadados,
        }
        temporario = self.manifesto.with_suffix(".json.tmp")
        temporario.write_text(json.dumps(dados, ensure_ascii=False, indent=2), encoding="utf-8")
        temporario.replace(self.manifesto)

    def _sucessos_por_id(self) -> dict[str, list[Resultado]]:
        saida: dict[str, list[Resultado]] = {}
        for r in self.resultados:
            if r.status == "sucesso":
                saida.setdefault(r.id_execucao, []).append(r)
        duplicados = [ident for ident, sucessos in saida.items() if len(sucessos) > 1]
        if duplicados:
            raise RuntimeError("mais de um sucesso para o mesmo ID: " + ", ".join(sorted(duplicados)))
        return saida

    def _validar_predecessores(self, bloco: str) -> None:
        blocos = self.protocolo["blocos"]
        if bloco not in blocos:
            raise ValueError(f"bloco inválido: {bloco}")
        sucessos = self._sucessos_por_id()
        anteriores = set(blocos[:blocos.index(bloco)])
        faltantes = [
            e.id_execucao for e in self.execucoes.values()
            if e.bloco in anteriores and e.id_execucao not in sucessos
        ]
        if faltantes:
            raise RuntimeError(
                f"{bloco} bloqueado: {len(faltantes)} IDs de blocos anteriores sem sucesso"
            )

    def _garantir_taxas_e2(self) -> None:
        if self.taxas_oficiais_e2:
            if set(self.taxas_oficiais_e2) != set(plano.TAMANHOS_BYTES):
                raise RuntimeError("manifesto contém taxas E2 incompletas")
            return
        sucessos = self._sucessos_por_id()
        ids_e1 = {e.id_execucao for e in self.execucoes.values() if e.experimento == "E1"}
        if not ids_e1.issubset(sucessos):
            raise RuntimeError("E2 bloqueado até todos os 80 IDs do E1 terem sucesso")
        calculadas = taxas_e2([sucessos[ident][0] for ident in ids_e1])
        if set(calculadas) != set(plano.TAMANHOS_BYTES):
            raise RuntimeError("não foi possível calcular as duas taxas oficiais do E2")
        self.taxas_oficiais_e2 = calculadas
        self._manifesto("e1_concluido")

    def _registrar_sessao_no_documento(self, sessao: dict[str, Any]) -> None:
        fuso = ZoneInfo("America/Sao_Paulo")
        inicio = datetime.fromisoformat(sessao["inicio_utc"].replace("Z", "+00:00")).astimezone(fuso)
        fim = datetime.fromisoformat(sessao["fim_utc"].replace("Z", "+00:00")).astimezone(fuso)
        ambiente = self.metadados.get("ambiente", {})
        maquina = ambiente.get("cpu") or ambiente.get("so") or "não identificado"
        energia = sessao["energia"].get("fonte") or "desconhecida"
        plano_energia = sessao["energia"].get("plano_energia") or "não disponível"
        temperatura = sessao.get("temperatura_c")
        energia_temperatura = f"{energia}; {plano_energia}"
        if temperatura is not None:
            energia_temperatura += f"; {temperatura:g} °C"

        def celula(valor: Any) -> str:
            return str(valor).replace("|", "/").replace("\r", " ").replace("\n", " ")

        linha = (
            f"| {celula(self.diretorio.name)} | {celula(sessao['bloco'])} "
            f"| {inicio:%d/%m/%Y %H:%M:%S}–{fim:%H:%M:%S} "
            f"| {celula(maquina)} | {celula(energia_temperatura)} | {celula(sessao['desvio'])} |\n"
        )
        with self.documento_protocolo.open("a", encoding="utf-8") as arquivo:
            arquivo.write(linha)

    def executar_bloco(
        self,
        bloco: str,
        desvio: str,
        temperatura_c: float | None = None,
        repetir_falhas: bool = False,
    ) -> list[Resultado]:
        if not desvio.strip():
            raise ValueError("informe o desvio do protocolo ou declare 'nenhum'")
        self._validar_predecessores(bloco)
        if bloco.startswith("E2-"):
            self._garantir_taxas_e2()

        do_bloco = sorted(
            (e for e in self.execucoes.values() if e.bloco == bloco),
            key=lambda e: e.ordem_no_bloco,
        )
        por_id: dict[str, list[Resultado]] = {}
        for resultado in self.resultados:
            por_id.setdefault(resultado.id_execucao, []).append(resultado)
        if repetir_falhas:
            executar = [
                e for e in do_bloco
                if por_id.get(e.id_execucao)
                and not any(r.status == "sucesso" for r in por_id[e.id_execucao])
            ]
        else:
            executar = [e for e in do_bloco if not por_id.get(e.id_execucao)]

        inicio = agora_utc()
        sessao = {
            "bloco": bloco,
            "tipo": "repeticao" if repetir_falhas else "primaria_ou_retomada",
            "inicio_utc": iso(inicio),
            "fim_utc": None,
            "status": "em_andamento",
            "ids_executados": [],
            "energia": metadados_energia(),
            "temperatura_c": temperatura_c,
            "desvio": desvio.strip(),
        }
        interrompida = False
        novos: list[Resultado] = []
        try:
            for execucao in executar:
                tentativas = por_id.get(execucao.id_execucao, [])
                tentativa = len(tentativas) + 1
                taxa = (
                    plano.TAXA_E1_ABERTA
                    if execucao.experimento == "E1"
                    else self.taxas_oficiais_e2[execucao.tamanho_bytes]
                )
                sessao["ids_executados"].append(execucao.id_execucao)
                resultado = self.executar_uma(
                    execucao, taxa, tentativa=tentativa, nomear_tentativa=True
                )
                novos.append(resultado)
        except KeyboardInterrupt:
            interrompida = True
        finally:
            self.executor.limpar()
            sessao["fim_utc"] = iso(agora_utc())
            sessao["status"] = "interrompida" if interrompida else "concluida"
            self.sessoes.append(sessao)
            sucessos = self._sucessos_por_id()
            status = "concluida" if set(self.execucoes).issubset(sucessos) else "parcial"
            if interrompida:
                status = "interrompida"
            self._manifesto(status)
            self._registrar_sessao_no_documento(sessao)
        return novos


def execucoes_a_repetir(caminho_csv: Path) -> list[plano.Execucao]:
    """Execuções cujas tentativas falharam todas (regra: repetir a execução inteira)."""
    por_id: dict[str, list[dict]] = {}
    with caminho_csv.open(encoding="utf-8") as f:
        for r in csv.DictReader(f):
            por_id.setdefault(r["id_execucao"], []).append(r)
    repetir = []
    for ident, tentativas in por_id.items():
        if any(t["status"] == "sucesso" for t in tentativas):
            continue
        r = tentativas[0]
        repetir.append(
            plano.Execucao(
                bloco=r.get("bloco", ""), ordem=int(r["ordem"]),
                ordem_no_bloco=int(r.get("ordem_no_bloco", r["ordem"])),
                id_execucao=ident, experimento=r["experimento"],
                broker=r["broker"], versao=r["versao"], tamanho_bytes=int(r["tamanho_bytes"]),
                repeticao=int(r["repeticao"]), aquecimento_s=int(r["aquecimento_s"]),
                medicao_s=int(r["medicao_s"]),
            )
        )
    return sorted(repetir, key=lambda e: e.ordem)
