from copy import deepcopy

import pytest

from experimento.dados import ROOT
from experimento.g3 import CORES
from experimento.g4 import figura_g4, texto_g4
from experimento.monte_carlo import ler_resultados


@pytest.fixture
def resultados():
    return tuple(ler_resultados(ROOT / f"data/s02/q{numero}_resultados.csv") for numero in (2, 3))


def test_paineis_comparaveis_com_quatro_curvas_e_intervalos(resultados):
    q2, q3 = resultados
    fig = figura_g4(q2, q3)
    assert len(fig.data) == 4
    assert list(fig.layout.yaxis.range) == list(fig.layout.yaxis2.range) == [0, 1]
    assert fig.layout.xaxis.range == fig.layout.xaxis2.range
    for trace, teste in zip(fig.data, ("t_pareado", "wilcoxon") * 2, strict=True):
        assert trace.line.color == CORES[teste]
        assert len(trace.x) == len(trace.error_y.array) == 7
        assert all(e >= 0 for e in trace.error_y.array)
    assert sum(trace.showlegend for trace in fig.data) == 2
    assert len(fig.layout.shapes) == 2


@pytest.mark.parametrize("alteracao", ["ausente", "duplicada", "intervalo", "configuracao", "distribuicao", "razao", "contagem"])
def test_rejeita_dados_que_impedem_comparacao(resultados, alteracao):
    q2, q3 = deepcopy(resultados)
    if alteracao == "ausente":
        q3.pop()
    elif alteracao == "duplicada":
        q3[1] = dict(q3[0])
    elif alteracao == "intervalo":
        q3[0]["ic95_inferior"] = float("nan")
    elif alteracao == "configuracao":
        q3[0]["alpha"] = 0.1
    elif alteracao == "distribuicao":
        q3[0]["distribuicao"] = "normal"
    elif alteracao == "razao":
        q3[0]["razao_geometrica"] = 1.03
    else:
        q3[0]["rejeicoes"] += 10
    with pytest.raises(ValueError):
        figura_g4(q2, q3)


def test_texto_distingue_h0_poder_efeito_e_incerteza(resultados):
    texto = texto_g4(*resultados)
    assert "H0" in texto and "não o p-valor" in texto
    assert "variância" in texto and "Wilson" in texto
    assert "descritiva" in texto and "superioridade universal" in texto
