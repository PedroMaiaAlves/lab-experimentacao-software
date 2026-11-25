import csv
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import portao_g1  # noqa: E402
from experimento import plano  # noqa: E402
from experimento.coleta import estabilidade_intervalos, interpretar_resultado_omb, renderizar_workload  # noqa: E402


def test_colapso_do_piloto_e_detectado():
    # assinatura real de E1-kafka-1k-r01 no piloto de 19/11
    r = estabilidade_intervalos([106476, 24763, 3041, 1.3, 1.3, 1.4])
    assert r["colapso"] is True
    estavel = estabilidade_intervalos([11557, 12676, 12547, 13218, 13863, 12568])
    assert estavel["colapso"] is False and estavel["cv_intervalos"] < 0.1


def test_parser_inclui_consumo_e_estabilidade(tmp_path):
    bruto = tmp_path / "r.json"
    bruto.write_text(json.dumps({"publishRate": [100, 100], "consumeRate": [90, 110]}), encoding="utf-8")
    m = interpretar_resultado_omb(bruto, 1024)
    assert m["throughput_consumo_msg_s"] == 100 and m["colapso"] is False


def test_e1_usa_taxa_fixa_e_nao_o_controlador_adaptativo(tmp_path):
    execucao = plano.gerar_plano("E1", 2)[0]
    texto = renderizar_workload(execucao, plano.TAXA_E1_ABERTA, tmp_path / "w.yaml").read_text(encoding="utf-8")
    assert f"producerRate: {plano.TAXA_E1_ABERTA}" in texto
    assert "producerRate: 0\n" not in texto


def _coleta(tmp_path, series):
    (tmp_path / "raw").mkdir()
    campos = ["id_execucao", "experimento", "broker", "tamanho_bytes", "status", "resultado_bruto"]
    with (tmp_path / "resultados.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=campos)
        w.writeheader()
        for (broker, tam), lista in series.items():
            for i, taxas in enumerate(lista, 1):
                ident = f"E1-{broker}-{tam // 1024}k-r{i:02d}"
                (tmp_path / "raw" / f"{ident}.json").write_text(json.dumps({"publishRate": taxas}))
                w.writerow({"id_execucao": ident, "experimento": "E1", "broker": broker, "tamanho_bytes": tam,
                            "status": "sucesso", "resultado_bruto": f"raw/{ident}.json"})
    return tmp_path / "resultados.csv"


def test_portao_aprova_coleta_estavel_e_reprova_colapso(tmp_path):
    estavel = {(b, t): [[1000 + 10 * i] * 6 for i in range(5)] for b in plano.BROKERS for t in plano.TAMANHOS_BYTES}
    (tmp_path / "a").mkdir()
    rel_ok = portao_g1.avaliar(portao_g1.carregar_e1(_coleta(tmp_path / "a", estavel)))
    assert rel_ok["aprovado"], rel_ok["celulas"]

    ruim = dict(estavel)
    ruim[("kafka", 1024)] = [[1000] * 6] * 4 + [[1000, 1000, 1, 1, 1, 1]]
    (tmp_path / "b").mkdir()
    rel = portao_g1.avaliar(portao_g1.carregar_e1(_coleta(tmp_path / "b", ruim)))
    assert not rel["aprovado"]
    kafka1k = next(c for c in rel["celulas"] if c["broker"] == "kafka" and c["tamanho_bytes"] == 1024)
    assert kafka1k["execucoes_colapsadas"] == ["E1-kafka-1k-r05"]


def test_repetir_so_execucoes_sem_nenhum_sucesso(tmp_path):
    from experimento.coleta import execucoes_a_repetir

    campos = ["ordem", "id_execucao", "experimento", "broker", "versao", "tamanho_bytes",
              "repeticao", "status", "aquecimento_s", "medicao_s"]
    linhas = [
        (1, "E1-kafka-1k-r01", "sucesso"),
        (2, "E1-kafka-16k-r01", "falha"),
        (3, "E1-rabbitmq-1k-r02", "falha"),
        (3, "E1-rabbitmq-1k-r02", "sucesso"),  # já repetida com sucesso
    ]
    with (tmp_path / "resultados.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=campos)
        w.writeheader()
        for ordem, ident, status in linhas:
            _, broker, tam, rep = ident.split("-")
            w.writerow({"ordem": ordem, "id_execucao": ident, "experimento": "E1", "broker": broker,
                        "versao": plano.VERSOES[broker], "tamanho_bytes": int(tam[:-1]) * 1024,
                        "repeticao": int(rep[1:]), "status": status, "aquecimento_s": 30, "medicao_s": 120})
    repetir = execucoes_a_repetir(tmp_path / "resultados.csv")
    assert [e.id_execucao for e in repetir] == ["E1-kafka-16k-r01"]
    assert repetir[0].medicao_s == 120 and repetir[0].tamanho_bytes == 16384
