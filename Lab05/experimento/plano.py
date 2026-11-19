"""Design do experimento (issue #197): fatores, células e ordem randomizada.

Design fatorial 2 (broker) x 2 (tamanho da mensagem), com execuções independentes
por célula, em dois experimentos:
  E1 — saturação (throughput máximo, CPU, memória);
  E2 — taxa fixa (latência p50/p99 a 50% do menor throughput do E1).

A ordem das execuções de cada experimento é embaralhada com semente fixa, para
espalhar efeitos de ordem, aquecimento térmico e deriva do sistema por todas as
células. O coletor (P2, #199) lê o CSV gerado e executa as linhas na ordem.
"""

from __future__ import annotations

import csv
import itertools
from dataclasses import asdict, dataclass
from pathlib import Path

import numpy as np

SEMENTE = 42
EXECUCOES_POR_CELULA = 10  # provisório: revisar após o piloto (#199) e o poder (#201)
BROKERS = ("kafka", "rabbitmq")
VERSOES = {"kafka": "4.4.0", "rabbitmq": "4.4.1"}
TAMANHOS_BYTES = (1024, 16384)
EXPERIMENTOS = ("E1", "E2")
AQUECIMENTO_S = 30
MEDICAO_S = 60

FIXAS = {
    "cpus": 4,
    "memoria_gib": 4,
    "produtores": 1,
    "consumidores": 1,
    "particoes_ou_filas": 1,
    "durabilidade_kafka": "acks=all",
    "durabilidade_rabbitmq": "publisher confirms + quorum queue",
    "containers": "recriados (com volumes) a cada execução",
}


@dataclass(frozen=True)
class Execucao:
    ordem: int
    id_execucao: str
    experimento: str
    broker: str
    versao: str
    tamanho_bytes: int
    repeticao: int
    aquecimento_s: int = AQUECIMENTO_S
    medicao_s: int = MEDICAO_S


def celulas() -> list[tuple[str, int]]:
    return list(itertools.product(BROKERS, TAMANHOS_BYTES))


def gerar_plano(
    experimento: str,
    execucoes_por_celula: int = EXECUCOES_POR_CELULA,
    semente: int = SEMENTE,
) -> list[Execucao]:
    if experimento not in EXPERIMENTOS:
        raise ValueError(f"experimento inválido: {experimento}")
    if execucoes_por_celula < 2:
        raise ValueError("são necessárias ao menos 2 execuções por célula")
    base = [
        (broker, tamanho, rep)
        for broker, tamanho in celulas()
        for rep in range(1, execucoes_por_celula + 1)
    ]
    # Semente distinta e determinística por experimento: E1 e E2 não repetem a ordem.
    rng = np.random.default_rng([semente, EXPERIMENTOS.index(experimento)])
    ordem = rng.permutation(len(base))
    plano = []
    for pos, idx in enumerate(ordem, start=1):
        broker, tamanho, rep = base[idx]
        plano.append(
            Execucao(
                ordem=pos,
                id_execucao=f"{experimento}-{broker}-{tamanho // 1024}k-r{rep:02d}",
                experimento=experimento,
                broker=broker,
                versao=VERSOES[broker],
                tamanho_bytes=tamanho,
                repeticao=rep,
            )
        )
    return plano


def salvar_plano(plano: list[Execucao], destino: Path) -> Path:
    destino.parent.mkdir(parents=True, exist_ok=True)
    with destino.open("w", newline="", encoding="utf-8") as f:
        campos = list(asdict(plano[0]).keys())
        escritor = csv.DictWriter(f, fieldnames=campos)
        escritor.writeheader()
        escritor.writerows(asdict(e) for e in plano)
    return destino
