import numpy as np
import pytest
from scipy import stats

from experimento import analise
from experimento.analise import analisar_pares
from experimento.dados import ROOT, ler_pares

CHAVES = {"estatistica", "p_valor", "metodo", "n_pares", "alpha", "alternativa", "decisao", "interpretacao"}


def pares_de_diferencas(d):
    # Exemplo sintético de teste (não é dado real): com_cache = 1 s, sem_cache = e^d.
    d = np.asarray(d, dtype=float)
    return np.column_stack([np.exp(d), np.ones_like(d)])


@pytest.fixture
def simulados():
    return ler_pares(ROOT / "data/simulado/pares_simulados.csv")


def test_contrato_na_amostra_simulada(simulados):
    r = analisar_pares(simulados)
    assert set(r) == {"t_pareado", "wilcoxon"}
    for teste in r.values():
        assert CHAVES <= set(teste)
        assert teste["n_pares"] == 30 and teste["alpha"] == 0.05
        assert teste["alternativa"] == "two-sided"
        assert teste["decisao"] == ("rejeitar H0" if teste["p_valor"] < 0.05 else "não rejeitar H0")
    assert r["t_pareado"]["hipoteses"]["H0"] != r["wilcoxon"]["hipoteses"]["H0"]


def test_referencia_scipy_direta(simulados):
    logs = np.log(simulados)
    r = analisar_pares(simulados)
    t = stats.ttest_rel(logs[:, 0], logs[:, 1])
    w = stats.wilcoxon(logs[:, 0] - logs[:, 1], method="exact")
    assert r["t_pareado"]["estatistica"] == pytest.approx(t.statistic, rel=1e-12)
    assert r["t_pareado"]["p_valor"] == pytest.approx(t.pvalue, rel=1e-12)
    assert r["wilcoxon"]["estatistica"] == pytest.approx(w.statistic)
    assert r["wilcoxon"]["p_valor"] == pytest.approx(w.pvalue, rel=1e-12)
    assert "exato" in r["wilcoxon"]["metodo"]


def test_exemplo_conhecido_calculado_a_mao():
    # d = [1, 2, 3, 4, 5]: média 3, dp = sqrt(2,5), t = 3 / (sqrt(2,5)/sqrt(5)) = 3*sqrt(2).
    pares = pares_de_diferencas([1, 2, 3, 4, 5])
    t = analise.teste_t_pareado(pares)
    assert t["estatistica"] == pytest.approx(3 * np.sqrt(2))
    assert t["gl"] == 4
    # Wilcoxon: todos positivos, W- = 0; P exata bicaudal = 2 / 2^5 = 0,0625.
    w = analise.teste_wilcoxon(pares)
    assert w["estatistica"] == 0
    assert w["p_valor"] == pytest.approx(2 / 32)
    assert w["decisao"] == "não rejeitar H0"


def test_empates_e_zeros_usam_aproximacao_explicita():
    d = [0.2, 0.2, -0.1, 0.0, 0.3, 0.3, 0.15, -0.25, 0.4, 0.1]
    w = analise.teste_wilcoxon(pares_de_diferencas(d))
    ref = stats.wilcoxon(np.log(np.exp(d)), method="approx", correction=False)
    assert "aproximação normal" in w["metodo"]
    assert w["zeros"] == 1 and w["empates"] and w["n_efetivo"] == 9
    assert w["p_valor"] == pytest.approx(ref.pvalue, rel=1e-9)


def test_diferencas_constantes_e_todas_zero_ficam_indisponiveis():
    t = analise.teste_t_pareado(pares_de_diferencas([0.2] * 6))
    assert t["estatistica"] is None and t["p_valor"] is None
    assert t["decisao"] == "indisponível" and "constantes" in t["motivo"]
    w = analise.teste_wilcoxon(np.ones((6, 2)))
    assert w["estatistica"] is None and "zero" in w["motivo"]


@pytest.mark.parametrize("pares", [
    np.array([[1.0, 0.0], [2.0, 1.0]]),
    np.array([[1.0, np.nan], [2.0, 1.0]]),
    np.array([[1.0, 2.0]]),
    np.array([1.0, 2.0, 3.0]),
])
def test_dados_invalidos_geram_erro(pares):
    with pytest.raises(ValueError):
        analisar_pares(pares)


def test_alpha_invalido():
    with pytest.raises(ValueError, match="alpha"):
        analisar_pares(pares_de_diferencas([1, 2, 3]), alpha=1.5)


def test_interpretacao_nao_confunde_p_valor(simulados):
    rejeita = analisar_pares(simulados)["t_pareado"]["interpretacao"]
    assert "não é a probabilidade de H0 ser verdadeira" in rejeita
    nao_rejeita = analise.teste_wilcoxon(pares_de_diferencas([1, 2, 3, 4, 5]))["interpretacao"]
    assert "não prova que os tempos são iguais" in nao_rejeita


def test_pareamento_preservado(simulados):
    # Embaralhar só uma coluna quebra os pares e precisa mudar o resultado do t.
    quebrados = simulados.copy()
    quebrados[:, 1] = quebrados[::-1, 1]
    assert analisar_pares(quebrados)["t_pareado"]["estatistica"] != analisar_pares(simulados)["t_pareado"]["estatistica"]
