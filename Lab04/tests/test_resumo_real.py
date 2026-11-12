import numpy as np
import pytest
from scipy import stats

from experimento.dados import ROOT, ler_pares
from experimento.resumo_real import resumir_reais


def test_efeito_e_intervalo_conferem_com_calculo_direto():
    pares = ler_pares(ROOT / "data/real/pares_reais.csv")
    resumo = resumir_reais(pares)
    d = np.log(pares[:, 0]) - np.log(pares[:, 1])
    assert resumo["n_pares"] == 30
    assert resumo["razao_geometrica"] == pytest.approx(np.exp(d.mean()))
    limites = stats.t.interval(0.95, 29, loc=d.mean(), scale=stats.sem(d))
    np.testing.assert_allclose(resumo["ic95_razao_t"], np.exp(limites))
    assert all(r["p_valor"] < 0.05 for r in resumo["resultados"].values())


def test_diferencas_constantes_nao_fabricam_intervalo_t():
    resumo = resumir_reais(np.array([[2, 1], [4, 2], [6, 3]]))
    assert resumo["ic95_razao_t"] is None
    assert resumo["resultados"]["t_pareado"]["p_valor"] is None


def test_pares_invalidos_sao_rejeitados():
    with pytest.raises(ValueError):
        resumir_reais(np.array([[0, 1], [2, 3]]))
