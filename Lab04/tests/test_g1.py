import plotly.graph_objects as go
import pytest

from experimento.dados import ROOT, ler_pares
from experimento.g1 import COR_REAL, COR_SIMULADO, figura_g1, texto_g1


@pytest.fixture
def amostras():
    return (
        ler_pares(ROOT / "data/real/pares_reais.csv"),
        ler_pares(ROOT / "data/simulado/pares_simulados.csv"),
    )


def test_g1_tem_dois_paineis_e_bins_comuns(amostras):
    fig = figura_g1(*amostras)
    assert isinstance(fig, go.Figure)
    assert len(fig.data) == 4
    assert all(isinstance(trace, go.Histogram) for trace in fig.data)
    assert fig.data[0].xbins == fig.data[1].xbins
    assert fig.data[2].xbins == fig.data[3].xbins
    assert {trace.marker.color for trace in fig.data} == {COR_REAL, COR_SIMULADO}
    assert "G1" in fig.layout.title.text
    assert "(s)" in fig.layout.xaxis.title.text


def test_texto_g1_identifica_amostras_e_limitacao(amostras):
    texto = texto_g1(*amostras)
    assert "30 pares reais" in texto
    assert "30 pares simulados" in texto
    assert "aproximação" in texto
    assert "erro tipo I" in texto


def test_g1_rejeita_pares_invalidos(amostras):
    reais, simulados = amostras
    reais[0, 0] = -1
    with pytest.raises(ValueError, match="positivos"):
        figura_g1(reais, simulados)
