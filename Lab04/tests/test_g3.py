import plotly.graph_objects as go
import pytest

from experimento.dados import ROOT, ler_json
from experimento.g2 import COR_T, COR_WILCOXON
from experimento.g3 import figura_g3, texto_g3
from experimento.monte_carlo import executar_q1


@pytest.fixture(scope="module")
def resultados():
    parametros = ler_json(ROOT / "data/simulado/parametros.json")
    return executar_q1(parametros, repeticoes=300, tamanhos=(10, 30))


def test_g3_mostra_testes_intervalos_e_alpha(resultados):
    fig = figura_g3(resultados)
    assert isinstance(fig, go.Figure)
    assert len(fig.data) == 2
    assert {trace.line.color for trace in fig.data} == {COR_T, COR_WILCOXON}
    assert all(trace.error_y.array is not None for trace in fig.data)
    assert any(shape.type == "line" and shape.y0 == pytest.approx(0.05) for shape in fig.layout.shapes)
    assert "G3" in fig.layout.title.text


def test_texto_g3_explica_monte_carlo(resultados):
    texto = texto_g3(resultados)
    assert "H0 verdadeira" in texto
    assert "Wilson" in texto
    assert "incerteza de Monte Carlo" in texto


def test_g3_rejeita_contrato_invalido(resultados):
    quebrado = [dict(resultados[0], pergunta="Q2")]
    with pytest.raises(ValueError, match="somente Q1"):
        figura_g3(quebrado)
