import numpy as np
import plotly.graph_objects as go
import pytest
from scipy import stats

from experimento.analise import analisar_pares
from experimento.dados import ROOT, ler_pares
from experimento.g2 import (
    COR_T,
    COR_WILCOXON,
    conferir_p_valores,
    distribuicao_t,
    distribuicao_wilcoxon,
    figura_g2,
    texto_g2,
)


def referencia_scipy(pares, alpha=0.05):
    # Referência independente de D1: resultados calculados diretamente no SciPy.
    logs = np.log(pares)
    d = logs[:, 0] - logs[:, 1]
    t = stats.ttest_rel(logs[:, 0], logs[:, 1], alternative="two-sided")
    exato = np.count_nonzero(d) == d.size and np.unique(np.abs(d)).size == d.size
    w = stats.wilcoxon(d, alternative="two-sided", method="exact" if exato else "approx")
    return {
        "t_pareado": {"estatistica": float(t.statistic), "p_valor": float(t.pvalue), "alpha": alpha},
        "wilcoxon": {"estatistica": float(w.statistic), "p_valor": float(w.pvalue), "alpha": alpha},
    }


def pares_de_diferencas(d):
    # Exemplo sintético de teste (não é dado real): com_cache = 1 s, sem_cache = e^d.
    d = np.asarray(d, dtype=float)
    return np.column_stack([np.exp(d), np.ones_like(d)])


@pytest.fixture
def simulados():
    return ler_pares(ROOT / "data/simulado/pares_simulados.csv")


@pytest.mark.parametrize("d", [
    [0.3, -0.1, 0.25, 0.4, -0.05, 0.12, 0.33, -0.2, 0.07, 0.18],
    [-0.5, 0.2, -0.3, 0.1, -0.45, 0.6, -0.15, 0.05],
    np.linspace(0.01, 0.3, 30),
])
def test_p_valores_coincidem_com_scipy(d):
    pares = pares_de_diferencas(d)
    ref = referencia_scipy(pares)
    t = distribuicao_t(pares)
    w = distribuicao_wilcoxon(pares)
    assert t["gl"] == len(d) - 1
    assert t["estatistica"] == pytest.approx(ref["t_pareado"]["estatistica"])
    assert t["p_valor"] == pytest.approx(ref["t_pareado"]["p_valor"], rel=1e-9)
    assert w["metodo"] == "exato"
    assert w["estatistica"] == pytest.approx(ref["wilcoxon"]["estatistica"])
    assert w["p_valor"] == pytest.approx(ref["wilcoxon"]["p_valor"], rel=1e-9)
    d1 = analisar_pares(pares)
    assert d1["t_pareado"]["p_valor"] == pytest.approx(t["p_valor"], rel=1e-9)
    assert d1["wilcoxon"]["p_valor"] == pytest.approx(w["p_valor"], rel=1e-9)


def test_massa_exata_de_min_w_soma_um_e_e_simetrica():
    w = distribuicao_wilcoxon(pares_de_diferencas(np.arange(1, 13) * 0.1))
    assert w["pmf"].sum() == pytest.approx(1.0)
    assert w["suporte"][-1] == 12 * 13 // 2 // 2
    # Região de rejeição: maior W com P(min <= W) <= alpha.
    acum = np.cumsum(w["pmf"])
    assert acum[w["critico"]] <= 0.05 < acum[w["critico"] + 1]


def test_empates_e_zeros_usam_aproximacao_explicita():
    pares = pares_de_diferencas([0.2, 0.2, -0.1, 0.0, 0.3, 0.3, 0.15, -0.25, 0.4, 0.1])
    w = distribuicao_wilcoxon(pares)
    assert w["metodo"] == "aproximação normal"
    assert w["zeros"] == 1 and w["empates"]
    ref = stats.wilcoxon(np.log(pares[:, 0]), method="approx", correction=False)
    assert w["p_valor"] == pytest.approx(ref.pvalue, rel=1e-9)
    fig = figura_g2(pares, analisar_pares(pares))
    assert any("NÃO é a distribuição exata" in (tr.name or "") for tr in fig.data)


def test_diferencas_constantes_e_dados_invalidos():
    with pytest.raises(ValueError, match="constantes"):
        distribuicao_t(pares_de_diferencas([0.2] * 6))
    with pytest.raises(ValueError, match="zero"):
        distribuicao_wilcoxon(pares_de_diferencas([0.0] * 6))
    with pytest.raises(ValueError):
        distribuicao_t(np.array([[1.0, -1.0], [2.0, 1.0]]))


def test_figura_na_amostra_simulada(simulados):
    resultados = analisar_pares(simulados)
    fig = figura_g2(simulados, resultados)
    assert isinstance(fig, go.Figure)
    assert "G2" in fig.layout.title.text
    assert fig.layout.yaxis3.type == "log" and fig.layout.yaxis4.type == "log"
    assert "adimensional" in fig.layout.xaxis.title.text
    cores = {tr.marker.color if isinstance(tr, go.Bar) else tr.line.color for tr in fig.data}
    assert COR_T in cores and COR_WILCOXON in cores
    conf = conferir_p_valores(simulados, resultados)
    assert all(v["ok"] for v in conf.values())


def test_area_desenhada_e_igual_ao_p_valor(simulados):
    pares = pares_de_diferencas([0.3, -0.1, 0.25, 0.4, -0.05, 0.12, 0.33, -0.2, 0.07, 0.18])
    fig = figura_g2(pares, analisar_pares(pares))
    barras_p = [tr for tr in fig.data if tr.name == "Massa = p-valor do Wilcoxon" and tr.xaxis == "x2"]
    massa = sum(float(np.sum(tr.y)) for tr in barras_p)
    assert massa == pytest.approx(analisar_pares(pares)["wilcoxon"]["p_valor"], rel=1e-9)
    # Área integrada das caudas t coincide com o p-valor (tolerância da integração numérica).
    t = distribuicao_t(pares)
    area = 2 * stats.t.sf(abs(t["estatistica"]), t["gl"])
    assert area == pytest.approx(t["p_valor"], rel=1e-9)


def test_divergencia_com_d1_e_rejeitada(simulados):
    resultados = analisar_pares(simulados)
    resultados["wilcoxon"]["p_valor"] = 0.5
    with pytest.raises(ValueError, match="diverge"):
        figura_g2(simulados, resultados)


def test_texto_tem_duas_a_quatro_frases_e_interpretacao_correta(simulados):
    texto = texto_g2(simulados, analisar_pares(simulados))
    frases = [f for f in texto.split(". ") if f.strip()]
    assert 2 <= len(frases) <= 4
    assert "não é a probabilidade de H0" in texto
