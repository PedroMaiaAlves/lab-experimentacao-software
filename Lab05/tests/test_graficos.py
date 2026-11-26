import sys
from pathlib import Path

import pytest

go = pytest.importorskip("plotly.graph_objects")

RAIZ = Path(__file__).resolve().parents[1]
if str(RAIZ) not in sys.path:
    sys.path.insert(0, str(RAIZ))

import analisar  # noqa: E402
from experimento import graficos  # noqa: E402


def test_figuras_e_textos_no_piloto_real():
    csv_piloto = analisar.piloto_mais_recente()
    registros, contagens, _ = analisar.carregar_tentativas(csv_piloto)
    resumo = analisar.analisar(csv_piloto, repeticoes_boot=200, permutacoes=200, repeticoes_poder=100)

    fig_box = graficos.figura_boxplots(registros)
    fig_for = graficos.figura_forest_plot(resumo["comparacoes"])
    fig_int = graficos.figura_interacao(resumo["descritiva"], resumo["interacoes"])
    fig_ord = graficos.figura_ordem_execucao(registros, resumo["checagens"]["efeito_ordem"])

    for fig in (fig_box, fig_for, fig_int, fig_ord):
        assert isinstance(fig, go.Figure)
        assert len(fig.data) >= 1

    assert fig_for.layout.xaxis.type == "log"
    assert len(fig_for.layout.shapes) >= 1
    assert fig_box.layout.yaxis.type == "log"
    assert fig_box.layout.yaxis2.type == "log"
    txt_box = graficos.texto_boxplots(registros, contagens)
    assert "11" in txt_box and "12" in txt_box
    assert "bootstrap" in graficos.texto_forest(resumo["comparacoes"])
    assert "H3" in graficos.texto_interacao(resumo["interacoes"])
    assert "ordem" in graficos.texto_ordem(resumo["checagens"]["efeito_ordem"])


def test_figura_ordem_destaca_repeticoes_e_divisor_de_blocos():
    registros = []
    for i in range(1, 9):
        bloco = "E1-B1" if i <= 4 else "E1-B2"
        broker = "kafka" if i % 2 else "rabbitmq"
        for tam in (1024, 16384):
            registros.append({
                "ordem": float(i if tam == 1024 else i + 8),
                "ordem_no_bloco": float(i if i <= 4 else i - 4),
                "bloco": bloco,
                "id_execucao": f"E1-{broker}-{tam // 1024}k-r{i:02d}",
                "experimento": "E1",
                "broker": broker,
                "tamanho_bytes": tam,
                "tentativa": 2 if i == 2 and tam == 1024 else 1,
                "throughput_msg_s": 5000.0 + i * 100.0,
            })

    efeito_ordem = analisar.checar_efeito_ordem(registros)
    fig = graficos.figura_ordem_execucao(registros, efeito_ordem)
    assert any(trace.name == "Repetição após falha técnica" for trace in fig.data)
    assert len(fig.layout.shapes) >= 4
