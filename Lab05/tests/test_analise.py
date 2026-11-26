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
    assert resultado["metadados_coleta"]["omb_timestamp_ms_valido"] is False
    texto = json.dumps(resultado, allow_nan=False)
    assert "NaN" not in texto


def test_checar_efeito_ordem_detecta_tendencia_e_serie_constante():
    registros = []
    for i in range(1, 21):
        bloco = "E1-B1" if i <= 10 else "E1-B2"
        ordem_no_bloco = i if i <= 10 else i - 10
        registros.append({
            "ordem": float(i),
            "ordem_no_bloco": float(ordem_no_bloco),
            "bloco": bloco,
            "id_execucao": f"E1-kafka-1k-r{i:02d}",
            "experimento": "E1",
            "broker": "kafka",
            "tamanho_bytes": 1024,
            "throughput_msg_s": float(1000.0 * np.exp(0.08 * i)),
            "latencia_p99_ms": 5.0,
        })
        registros.append({
            "ordem": float(i + 20),
            "ordem_no_bloco": float(ordem_no_bloco),
            "bloco": bloco,
            "id_execucao": f"E1-rabbitmq-1k-r{i:02d}",
            "experimento": "E1",
            "broker": "rabbitmq",
            "tamanho_bytes": 1024,
            "throughput_msg_s": 500.0,
            "latencia_p99_ms": 20.0,
        })

    res = analisar.checar_efeito_ordem(registros)
    kafka_1k = next(r for r in res if r["experimento"] == "E1" and r["broker"] == "kafka" and r["tamanho_bytes"] == 1024)
    rabbit_1k = next(r for r in res if r["experimento"] == "E1" and r["broker"] == "rabbitmq" and r["tamanho_bytes"] == 1024)
    assert kafka_1k["disponivel"] is True
    assert kafka_1k["inclinacao_log"] == pytest.approx(0.08, abs=1e-6)
    assert kafka_1k["ic95_contem_zero"] is False
    assert set(kafka_1k["por_bloco"]) == {"E1-B1", "E1-B2"}
    assert rabbit_1k["disponivel"] is True
    assert rabbit_1k["inclinacao_log"] == 0.0
    assert rabbit_1k["ic95_contem_zero"] is True
    json.dumps(res, allow_nan=False)


def test_checar_efeito_bloco_ajusta_diferenca_entre_blocos():
    sem_bloco = [
        {"experimento": "E1", "broker": "kafka", "tamanho_bytes": 1024, "bloco": "", "throughput_msg_s": 100.0},
        {"experimento": "E1", "broker": "rabbitmq", "tamanho_bytes": 1024, "bloco": "", "throughput_msg_s": 50.0},
    ]
    res_sem = analisar.checar_efeito_bloco(sem_bloco)
    assert res_sem[0]["disponivel"] is False

    rng = np.random.default_rng(42)
    com_bloco = []
    for bloco, fator_bloco in (("E1-B1", 1.0), ("E1-B2", 1.5)):
        for broker, base in (("rabbitmq", 1000.0), ("kafka", 2000.0)):
            for i in range(10):
                ruido = float(np.exp(rng.normal(0.0, 0.02)))
                com_bloco.append({
                    "experimento": "E1",
                    "broker": broker,
                    "tamanho_bytes": 1024,
                    "bloco": bloco,
                    "throughput_msg_s": base * fator_bloco * ruido,
                })

    res_com = analisar.checar_efeito_bloco(com_bloco)
    e1_1k = next(r for r in res_com if r["experimento"] == "E1" and r["tamanho_bytes"] == 1024)
    assert e1_1k["disponivel"] is True
    mod = e1_1k["modelo_ajustado_bloco"]
    assert mod["disponivel"] is True
    assert mod["efeito_bloco_significativo"] is True
    assert mod["razao_bloco"] == pytest.approx(1.5, rel=0.05)
    assert mod["razao_broker_ajustada"] == pytest.approx(2.0, rel=0.05)


def test_sensibilidade_repeticoes_e_outliers_preservados(tmp_path):
    linhas = [
        {
            "ordem": 1, "ordem_no_bloco": 1, "bloco": "E1-B1",
            "id_execucao": "E1-kafka-1k-r01", "experimento": "E1", "broker": "kafka",
            "tamanho_bytes": 1024, "repeticao": 1, "tentativa": 1,
            "status": "falha", "erro": "timeout simulado",
        },
        {
            "ordem": 1, "ordem_no_bloco": 1, "bloco": "E1-B1",
            "id_execucao": "E1-kafka-1k-r01", "experimento": "E1", "broker": "kafka",
            "tamanho_bytes": 1024, "repeticao": 1, "tentativa": 2,
            "status": "sucesso", "throughput_msg_s": 50000.0, "latencia_p99_ms": 5.0,
        },
    ]
    for i in range(2, 6):
        linhas.append({
            "ordem": i, "ordem_no_bloco": i, "bloco": "E1-B1",
            "id_execucao": f"E1-kafka-1k-r{i:02d}", "experimento": "E1", "broker": "kafka",
            "tamanho_bytes": 1024, "repeticao": i, "tentativa": 1,
            "status": "sucesso", "throughput_msg_s": 10000.0 + i * 10.0, "latencia_p99_ms": 5.0,
        })
        linhas.append({
            "ordem": i + 10, "ordem_no_bloco": i + 10, "bloco": "E1-B1",
            "id_execucao": f"E1-rabbitmq-1k-r{i:02d}", "experimento": "E1", "broker": "rabbitmq",
            "tamanho_bytes": 1024, "repeticao": i, "tentativa": 1,
            "status": "sucesso", "throughput_msg_s": 5000.0 + i * 10.0, "latencia_p99_ms": 20.0,
        })

    csv_path = _escrever_csv_sintetico(tmp_path / "resultados.csv", linhas)
    sucessos, contagens, repetidos = analisar.carregar_tentativas(csv_path)
    assert contagens == {"falha": 1, "sucesso": 9}
    assert repetidos == ["E1-kafka-1k-r01"]

    descritiva = analisar.descrever_celulas(sucessos)
    k_desc = next(d for d in descritiva if d["broker"] == "kafka" and d["metrica"] == "throughput_msg_s")
    assert k_desc["n"] == 5

    outliers = analisar.detectar_outliers(sucessos)
    assert any(o["id_execucao"] == "E1-kafka-1k-r01" and o["removido"] is False and o["direcao"] == "alto" for o in outliers)

    comp, inter = analisar._executar_comparacoes_e_interacoes(sucessos, repeticoes_boot=200, permutacoes=200)
    sens = analisar.checar_sensibilidade_repeticoes(
        sucessos, repetidos, comp, inter, repeticoes_boot=200, permutacoes=200
    )
    assert sens["ha_repeticoes"] is True
    assert sens["n_ids_repetidos"] == 1
    assert sens["comparacoes_sem_repeticoes"]["E1_throughput_msg_s_1k"]["n_kafka"] == 4

    sem_rep = analisar.checar_sensibilidade_repeticoes(sucessos, [], comp, inter)
    assert sem_rep["ha_repeticoes"] is False
    assert sem_rep["altera_conclusao"] is False


def test_carga_relativa_e2_e_comparar_cv_protocolo():
    registros = [
        {"experimento": "E1", "broker": "kafka", "tamanho_bytes": 1024, "throughput_msg_s": 10000.0, "taxa_alvo_msg_s": None},
        {"experimento": "E1", "broker": "rabbitmq", "tamanho_bytes": 1024, "throughput_msg_s": 2000.0, "taxa_alvo_msg_s": None},
        {"experimento": "E2", "broker": "kafka", "tamanho_bytes": 1024, "throughput_msg_s": 1000.0, "taxa_alvo_msg_s": 1000.0},
        {"experimento": "E2", "broker": "rabbitmq", "tamanho_bytes": 1024, "throughput_msg_s": 990.0, "taxa_alvo_msg_s": 1000.0},
    ]
    cargas = analisar.calcular_carga_relativa_e2(registros, {1024: 1000})
    k1 = next(c for c in cargas if c["broker"] == "kafka" and c["tamanho_bytes"] == 1024)
    r1 = next(c for c in cargas if c["broker"] == "rabbitmq" and c["tamanho_bytes"] == 1024)
    assert k1["carga_relativa_alvo"] == pytest.approx(0.10)
    assert r1["carga_relativa_alvo"] == pytest.approx(0.50)
    assert r1["carga_relativa_efetiva"] == pytest.approx(0.495)

    desc = [
        {"experimento": "E1", "metrica": "throughput_msg_s", "broker": "kafka", "tamanho_bytes": 1024, "n": 20, "cv": 0.18},
        {"experimento": "E2", "metrica": "latencia_p99_ms", "broker": "rabbitmq", "tamanho_bytes": 1024, "n": 20, "cv": 0.25},
    ]
    comp_cv = analisar.comparar_cv_protocolo(desc)
    e1_k1 = next(c for c in comp_cv if c["experimento"] == "E1" and c["broker"] == "kafka" and c["tamanho_bytes"] == 1024)
    e2_r1 = next(c for c in comp_cv if c["experimento"] == "E2" and c["broker"] == "rabbitmq" and c["tamanho_bytes"] == 1024)
    assert e1_k1["cv_protocolo_g1"] == pytest.approx(0.2010)
    assert e1_k1["atende_g1_20pct"] is True
    assert e2_r1["status_protocolo"] == "cv_indisponivel"


def _criar_coleta_oficial_sintetica(raiz_temp: Path) -> Path:
    from dataclasses import asdict
    from experimento import plano
    from experimento.coleta import carregar_plano_oficial, criar_diretorio_coleta, sha256_arquivo

    protocolo = json.loads((RAIZ / "data" / "plano" / "protocolo_oficial.json").read_text(encoding="utf-8"))
    diretorio = criar_diretorio_coleta(raiz_temp / "oficial")
    rng = np.random.default_rng(42)
    taxas_e2 = {1024: 4000, 16384: 1500}
    linhas = []

    for exp in plano.EXPERIMENTOS:
        for e in carregar_plano_oficial(exp):
            if e.id_execucao == "E1-rabbitmq-1k-r01":
                linhas.append(Resultado(
                    colecao_id=diretorio.name, ordem=e.ordem, id_execucao=e.id_execucao,
                    experimento=e.experimento, broker=e.broker, versao=e.versao,
                    tamanho_bytes=e.tamanho_bytes, repeticao=e.repeticao, bloco=e.bloco,
                    ordem_no_bloco=e.ordem_no_bloco, tentativa=1, status="falha",
                    inicio_utc="2026-11-26T00:00:00.000Z", fim_utc="2026-11-26T00:00:10.000Z",
                    duracao_s=10.0, aquecimento_s=e.aquecimento_s, medicao_s=e.medicao_s,
                    codigo_saida=1, erro="erro transiente simulado",
                ))
                tentativa = 2
            else:
                tentativa = 1

            bruto = diretorio / "raw" / f"{e.id_execucao}-t{tentativa:02d}.json"
            bruto.write_text(json.dumps({"ok": True}), encoding="utf-8")
            taxa = plano.TAXA_E1_ABERTA if exp == "E1" else taxas_e2[e.tamanho_bytes]
            if exp == "E1":
                base_tput = (100000.0 if e.broker == "kafka" else 8500.0) if e.tamanho_bytes == 1024 else (7500.0 if e.broker == "kafka" else 3400.0)
                tput = float(base_tput * np.exp(rng.normal(0.0, 0.08)))
                p50, p99 = 5.0, 20.0
            else:
                tput = float(taxa)
                p50 = 2.0 if e.broker == "kafka" else 10.0
                p99 = float((4.0 if e.broker == "kafka" else 45.0) * np.exp(rng.normal(0.0, 0.1)))

            linhas.append(Resultado(
                colecao_id=diretorio.name, ordem=e.ordem, id_execucao=e.id_execucao,
                experimento=e.experimento, broker=e.broker, versao=e.versao,
                tamanho_bytes=e.tamanho_bytes, repeticao=e.repeticao, bloco=e.bloco,
                ordem_no_bloco=e.ordem_no_bloco, tentativa=tentativa, status="sucesso",
                inicio_utc="2026-11-26T00:01:00.000Z", fim_utc="2026-11-26T00:03:00.000Z",
                duracao_s=120.0, aquecimento_s=e.aquecimento_s, medicao_s=e.medicao_s,
                taxa_alvo_msg_s=taxa, throughput_msg_s=tput,
                throughput_mib_s=tput * e.tamanho_bytes / 1024**2,
                latencia_p50_ms=p50, latencia_p99_ms=p99,
                throughput_consumo_msg_s=tput * 0.99, cv_intervalos=0.05,
                intervalo_min_rel=0.90, colapso=False, cpu_percent_medio=120.0,
                memoria_mib_media=512.0 if e.broker == "kafka" else 180.0,
                codigo_saida=0, resultado_bruto=str(bruto.relative_to(diretorio)),
            ))

    csv_path = diretorio / "resultados.csv"
    with csv_path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(Resultado.__dataclass_fields__))
        w.writeheader()
        w.writerows(asdict(r) for r in linhas)

    manifesto = {
        "schema": 2,
        "colecao_id": diretorio.name,
        "status": "concluida",
        "taxas_e2": {str(k): v for k, v in taxas_e2.items()},
        "blocos": [{"bloco": b} for b in protocolo["blocos"]],
        "ambiente": {"so": "Windows", "cpu": "CPU-teste", "processadores_logicos": 12, "memoria_total_bytes": 16 * 1024**3},
        "imagens": {nome: dados["fingerprint"] for nome, dados in protocolo["imagens"].items()},
        "hashes": {
            "resultados.csv": sha256_arquivo(csv_path),
            "brutos": {
                str(p.relative_to(diretorio)).replace("\\", "/"): sha256_arquivo(p)
                for p in sorted((diretorio / "raw").glob("*.json"))
            },
        },
    }
    (diretorio / "manifesto.json").write_text(json.dumps(manifesto), encoding="utf-8")
    return csv_path


def test_pipeline_oficial_g3_json_markdown_e_rejeicoes(tmp_path):
    csv_oficial = _criar_coleta_oficial_sintetica(tmp_path)
    resultado = analisar.analisar(
        csv_oficial, repeticoes_boot=300, permutacoes=300, repeticoes_poder=100, validar_oficial=True
    )
    assert resultado["metadados_coleta"]["valido_g3"] is True
    assert resultado["metadados_coleta"]["omb_timestamp_ms_valido"] is True
    assert resultado["metadados_coleta"]["maquina_unica"] is True
    assert resultado["contagens_status"] == {"falha": 1, "sucesso": 160}
    assert resultado["checagens"]["sensibilidade_repeticoes"]["ids_repetidos"] == ["E1-rabbitmq-1k-r01"]
    assert all(b["disponivel"] for b in resultado["checagens"]["efeito_bloco"])

    texto_json = json.dumps(resultado, allow_nan=False)
    assert "NaN" not in texto_json

    md = analisar.gerar_resultados_md(resultado)
    for trecho in ("# Resultados Estatísticos", "Holm", "ANOVA", "Cliff", "Efeito de ordem", "Efeito de bloco", "Carga relativa"):
        assert trecho in md

    with pytest.raises(ValueError, match="piloto"):
        analisar.analisar(analisar.piloto_mais_recente(), validar_oficial=True)

    manifesto_path = csv_oficial.parent / "manifesto.json"
    manifesto = json.loads(manifesto_path.read_text(encoding="utf-8"))
    manifesto["imagens"]["omb"] = "sha256:antiga"
    manifesto_path.write_text(json.dumps(manifesto), encoding="utf-8")
    with pytest.raises(ValueError, match="portão G3"):
        analisar.analisar(csv_oficial, validar_oficial=True)
