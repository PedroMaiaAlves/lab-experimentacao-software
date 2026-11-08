import numpy as np
import pytest

from experimento.analise import analisar_pares
from experimento.dados import ROOT, ler_json, ler_pares
from experimento.monte_carlo import (
    avaliar_rejeicoes,
    desvio_diferencas,
    executar_q1,
    gerar_diferencas,
    intervalo_wilson,
    salvar_q1,
    simular_grade,
    validar_q1,
)


@pytest.fixture
def parametros():
    return ler_json(ROOT / "data/simulado/parametros.json")


def test_desvio_das_diferencas_vem_da_calibracao(parametros):
    reais = ler_pares(ROOT / "data/real/pares_reais.csv")
    d = np.log(reais[:, 0]) - np.log(reais[:, 1])
    assert desvio_diferencas(parametros) == pytest.approx(d.std(ddof=1))


def test_intervalo_wilson_contem_estimativa_e_valida_contagens():
    inferior, superior = intervalo_wilson(500, 10_000)
    assert inferior < 0.05 < superior
    with pytest.raises(ValueError):
        intervalo_wilson(11, 10)


def test_geracao_t3_e_normal_tem_formato_e_reprodutibilidade():
    a = gerar_diferencas(np.random.default_rng(7), 100, 12, 0.1, 0.2, "normal")
    b = gerar_diferencas(np.random.default_rng(7), 100, 12, 0.1, 0.2, "normal")
    assert np.array_equal(a, b)
    assert a.shape == (100, 12)
    t3 = gerar_diferencas(np.random.default_rng(8), 100, 12, 0.0, 0.2, "t3")
    assert t3.shape == a.shape and np.isfinite(t3).all()


def test_decisoes_em_lote_coincidem_com_analise_da_sprint_1():
    d = np.array([
        [0.3, -0.1, 0.25, 0.4, -0.05, 0.12, 0.33, -0.2, 0.07, 0.18],
        [0.8, 0.4, 0.5, 0.7, 0.2, 0.6, 0.9, 0.3, 0.1, 1.0],
        [-0.2, 0.1, -0.15, 0.05, -0.3, 0.25, -0.1, 0.2, -0.05, 0.15],
    ])
    lote = avaliar_rejeicoes(d)
    for i, linha in enumerate(d):
        pares = np.column_stack([np.exp(linha), np.ones_like(linha)])
        individual = analisar_pares(pares)
        assert lote["t_pareado"][i] == (individual["t_pareado"]["p_valor"] < 0.05)
        assert lote["wilcoxon"][i] == (individual["wilcoxon"]["p_valor"] < 0.05)


def test_grade_e_reproduzivel_e_agregada(parametros):
    kwargs = dict(
        distribuicao="normal", tamanhos=(10, 20), deltas=(0.0,), repeticoes=200,
        alpha=0.05, semente=42, sigma_d=desvio_diferencas(parametros),
        pergunta="Q1", cenario="teste",
    )
    primeira = simular_grade(**kwargs)
    segunda = simular_grade(**kwargs)
    assert primeira == segunda
    assert len(primeira) == 4
    assert {r["teste"] for r in primeira} == {"t_pareado", "wilcoxon"}
    assert all(r["ic95_inferior"] <= r["taxa_rejeicao"] <= r["ic95_superior"] for r in primeira)


def test_q1_oficial_tem_todas_as_configuracoes(parametros):
    resultados = executar_q1(parametros, repeticoes=250)
    assert len(resultados) == 10
    assert {r["n"] for r in resultados} == {10, 20, 30, 50, 100}
    assert all(r["delta_log"] == 0 and r["pergunta"] == "Q1" for r in resultados)


def test_artefatos_q1_sao_reproduziveis(tmp_path):
    manifesto = salvar_q1(tmp_path)
    assert manifesto["configuracao"]["repeticoes"] == 10_000
    assert validar_q1(tmp_path) == {"status": "ok", "pergunta": "Q1", "configuracoes": 10}
