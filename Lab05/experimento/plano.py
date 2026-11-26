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
EXECUCOES_POR_CELULA = 20  # decisão final da #207: teto pré-registrado
BLOCOS_POR_EXPERIMENTO = 2
BROKERS = ("kafka", "rabbitmq")
VERSOES = {"kafka": "4.4.0", "rabbitmq": "4.4.1"}
TAMANHOS_BYTES = (1024, 16384)
EXPERIMENTOS = ("E1", "E2")
AQUECIMENTO_S = 30
MEDICAO_S_POR_EXPERIMENTO = {"E1": 120, "E2": 60}

# E1 (saturação) usa uma taxa-alvo FIXA e inalcançável, não `producerRate: 0`.
# No OMB, `producerRate: 0` liga o RateController adaptativo, que roda durante a
# medição inteira e, após um único pico de backlog, derruba a taxa para ~1 msg/s
# sem recuperar (causa do CV de 50–130% no piloto; ver protocolo_coleta.md, #209).
# Com taxa fixa alta, o produtor publica o mais rápido que o broker aceita e o
# limite vem da contrapressão do próprio broker (buffer do produtor Kafka /
# controle de fluxo da conexão RabbitMQ), que é o que E1 pretende medir.
TAXA_E1_ABERTA = 1_000_000

# Critérios do portão G1 (planejamento_s02.md).
G1_CV_MAXIMO = 0.20  # CV entre execuções da mesma célula
G1_FRACAO_COLAPSO = 0.10  # intervalo abaixo de 10% do maior intervalo da execução = colapso

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
    bloco: str
    ordem: int
    ordem_no_bloco: int
    id_execucao: str
    experimento: str
    broker: str
    versao: str
    tamanho_bytes: int
    repeticao: int
    aquecimento_s: int = AQUECIMENTO_S
    medicao_s: int = 60


def celulas() -> list[tuple[str, int]]:
    return list(itertools.product(BROKERS, TAMANHOS_BYTES))


def gerar_plano(
    experimento: str,
    execucoes_por_celula: int = EXECUCOES_POR_CELULA,
    semente: int = SEMENTE,
    blocos_por_experimento: int | None = None,
) -> list[Execucao]:
    if experimento not in EXPERIMENTOS:
        raise ValueError(f"experimento inválido: {experimento}")
    if execucoes_por_celula < 2:
        raise ValueError("são necessárias ao menos 2 execuções por célula")
    if blocos_por_experimento is None:
        # Os planos oficiais têm dois blocos. Pilotos históricos com n=3/5
        # continuam em um bloco e não são confundidos com o plano oficial.
        blocos_por_experimento = (
            BLOCOS_POR_EXPERIMENTO
            if execucoes_por_celula == EXECUCOES_POR_CELULA
            else 1
        )
    if blocos_por_experimento < 1:
        raise ValueError("é necessário ao menos um bloco")
    if execucoes_por_celula % blocos_por_experimento:
        raise ValueError("n por célula deve ser divisível pelo número de blocos")

    repeticoes_por_bloco = execucoes_por_celula // blocos_por_experimento
    plano = []
    ordem_global = 0
    for indice_bloco in range(blocos_por_experimento):
        inicio = indice_bloco * repeticoes_por_bloco + 1
        fim = inicio + repeticoes_por_bloco
        base = [
            (broker, tamanho, rep)
            for broker, tamanho in celulas()
            for rep in range(inicio, fim)
        ]
        # Cada bloco é balanceado e recebe uma sequência determinística própria.
        rng = np.random.default_rng(
            [semente, EXPERIMENTOS.index(experimento), indice_bloco]
        )
        permutacao = rng.permutation(len(base))
        for ordem_no_bloco, idx in enumerate(permutacao, start=1):
            broker, tamanho, rep = base[idx]
            ordem_global += 1
            plano.append(
                Execucao(
                    bloco=f"{experimento}-B{indice_bloco + 1}",
                    ordem=ordem_global,
                    ordem_no_bloco=ordem_no_bloco,
                    id_execucao=f"{experimento}-{broker}-{tamanho // 1024}k-r{rep:02d}",
                    experimento=experimento,
                    broker=broker,
                    versao=VERSOES[broker],
                    tamanho_bytes=tamanho,
                    repeticao=rep,
                    medicao_s=MEDICAO_S_POR_EXPERIMENTO[experimento],
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
