import csv
import json
import sys
from pathlib import Path

import numpy as np
import pytest

RAIZ = Path(__file__).resolve().parents[1]
if str(RAIZ) not in sys.path:
    sys.path.insert(0, str(RAIZ))

import analisar  # noqa: E402
from experimento.coleta import Resultado  # noqa: E402


def _escrever_csv_sintetico(caminho: Path, linhas: list[dict]) -> Path:
    campos = list(Resultado.__dataclass_fields__)
    with caminho.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=campos)
        w.writeheader()
        for linha in linhas:
            base = {c: "" for c in campos}
            base.update(linha)
            w.writerow(base)
    return caminho


def test_carregar_resultados_ignora_falhas_sem_imputar_zero(tmp_path):
    csv_path = _escrever_csv_sintetico(
        tmp_path / "resultados.csv",
        [
            {
                "ordem": 1, "id_execucao": "E1-kafka-1k-r01", "experimento": "E1",
                "broker": "kafka", "tamanho_bytes": 1024, "repeticao": 1,
                "status": "sucesso", "duracao_s": 90.0, "throughput_msg_s": 10000.0,
                "throughput_mib_s": 9.76, "latencia_p50_ms": 2.0, "latencia_p99_ms": 5.0,
                "cpu_percent_medio": 120.0, "memoria_mib_media": 1024.0,
            },
            {
                "ordem": 2, "id_execucao": "E1-rabbitmq-1k-r01", "experimento": "E1",
                "broker": "rabbitmq", "tamanho_bytes": 1024, "repeticao": 1,
                "status": "falha", "duracao_s": 12.0, "erro": "docker up falhou",
            },
            {
                "ordem": 3, "id_execucao": "E2-rabbitmq-1k-r01", "experimento": "E2",
                "broker": "rabbitmq", "tamanho_bytes": 1024, "repeticao": 1,
                "status": "bloqueada", "duracao_s": 0.0, "erro": "E1 sem sucesso",
            },
        ],
    )
    sucessos, contagens = analisar.carregar_resultados(csv_path)
    assert len(sucessos) == 1
    assert contagens == {"sucesso": 1, "falha": 1, "bloqueada": 1}
    assert sucessos[0]["throughput_msg_s"] == 10000.0
    assert sucessos[0]["taxa_alvo_msg_s"] is None


def test_cliff_delta_e_magnitude():
    assert analisar.cliff_delta(np.array([10, 20, 30]), np.array([1, 2, 3])) == 1.0
    assert analisar.cliff_delta(np.array([1, 2, 3]), np.array([10, 20, 30])) == -1.0
    assert analisar.cliff_delta(np.array([1, 2, 3]), np.array([1, 2, 3])) == 0.0
    assert analisar.magnitude_cliff(0.1) == "desprezível"
    assert analisar.magnitude_cliff(-0.2) == "pequeno"
    assert analisar.magnitude_cliff(0.4) == "médio"
    assert analisar.magnitude_cliff(-0.8) == "grande"


def test_corrigir_holm_ordena_e_preserva_none():
    ajustados = analisar.corrigir_holm({"a": 0.01, "b": 0.04, "c": 0.03, "d": None})
    assert ajustados["a"] == pytest.approx(0.03)
    assert ajustados["c"] == pytest.approx(0.06)
    assert ajustados["b"] == pytest.approx(0.06)
    assert ajustados["d"] is None


def test_razao_bootstrap_reprodutivel_e_contem_razao():
    a = np.array([200.0, 210.0, 190.0, 205.0, 195.0])
    b = np.array([100.0, 105.0, 95.0, 102.0, 98.0])
    r1 = analisar.razao_bootstrap(a, b, repeticoes=1000, semente=42)
    r2 = analisar.razao_bootstrap(a, b, repeticoes=1000, semente=42)
    assert r1 == r2
    razao, inf, sup = r1
    assert inf < razao < sup
    assert razao == pytest.approx(2.0, rel=0.05)


def test_comparar_brokers_detecta_diferenca_e_recomenda_teste():
    rng = np.random.default_rng(42)
    kafka = np.exp(rng.normal(np.log(2000), 0.05, size=10))
    rabbit = np.exp(rng.normal(np.log(1000), 0.05, size=10))
    res = analisar.comparar_brokers(kafka, rabbit, repeticoes_boot=1000)
    assert res["disponivel"] is True
    assert res["teste_recomendado"] == "welch_log"
    assert res["welch_p"] < 0.001
    assert res["mann_whitney_p"] < 0.001
    assert res["cliff_delta"] == 1.0
    assert 1.8 < res["razao_geometrica"] < 2.2


def test_comparar_brokers_escolhe_mann_whitney_sem_shapiro():
    res = analisar.comparar_brokers(np.array([10.0, 20.0]), np.array([5.0, 6.0]), repeticoes_boot=200)
    assert res["disponivel"] is True
    assert res["shapiro_log_kafka_p"] is None
    assert res["teste_recomendado"] == "mann_whitney"


def test_interacao_nao_confunde_efeito_principal_e_detecta_interacao_real():
    rng = np.random.default_rng(42)
    sem_int = analisar.testar_interacao(
        np.exp(rng.normal(np.log(200), 0.05, 10)),
        np.exp(rng.normal(np.log(100), 0.05, 10)),
        np.exp(rng.normal(np.log(40), 0.05, 10)),
        np.exp(rng.normal(np.log(20), 0.05, 10)),
        permutacoes=1000,
    )
    assert sem_int["anova_p"] > 0.05
    assert sem_int["permutacao_p"] > 0.05
    assert 0.85 < sem_int["razao_das_razoes"] < 1.15

    com_int = analisar.testar_interacao(
        np.exp(rng.normal(np.log(200), 0.05, 10)),
        np.exp(rng.normal(np.log(100), 0.05, 10)),
        np.exp(rng.normal(np.log(400), 0.05, 10)),
        np.exp(rng.normal(np.log(100), 0.05, 10)),
        permutacoes=1000,
    )
    assert com_int["anova_p"] < 0.001
    assert com_int["permutacao_p"] < 0.01
    assert 1.8 < com_int["razao_das_razoes"] < 2.2


def test_estimar_cpu_hora_formula_exata():
    registros = [
        {
            "experimento": "E2", "broker": "kafka", "tamanho_bytes": 1024,
            "throughput_msg_s": 1000.0, "cpu_percent_medio": 200.0, "memoria_mib_media": 1024.0,
        }
    ]
    res = analisar.estimar_cpu_hora(registros)
    assert len(res) == 1
    assert res[0]["cpu_hora_por_milhao_mediana"] == pytest.approx(2.0 * 1_000_000 / (1000.0 * 3600.0))
    assert res[0]["gib_hora_por_milhao_mediana"] == pytest.approx(1.0 * 1_000_000 / (1000.0 * 3600.0))


def test_analise_completa_no_piloto_real(tmp_path):
    csv_piloto = analisar.piloto_mais_recente()
    resultado = analisar.analisar(csv_piloto, repeticoes_boot=500, permutacoes=500, repeticoes_poder=200)
    assert resultado["contagens_status"]["sucesso"] == 23
    assert resultado["contagens_status"]["falha"] == 1
    assert set(resultado["comparacoes"]) == {
        "E1_throughput_msg_s_1k",
        "E1_throughput_msg_s_16k",
        "E2_latencia_p99_ms_1k",
        "E2_latencia_p99_ms_16k",
    }
    assert len(resultado["poder_piloto"]) == 4 * 3 * 3
    assert len(resultado["impacto_recursos"]) == 8
    texto = json.dumps(resultado, allow_nan=False)
    assert "NaN" not in texto
