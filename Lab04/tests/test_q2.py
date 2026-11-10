import numpy as np
import pytest

from experimento.dados import ROOT, ler_json
from experimento.monte_carlo import SEMENTE_BASE, executar_q1
from experimento.q2 import (
    RAZOES_Q2,
    SEMENTE_Q2,
    deltas_q2,
    executar_q2,
    salvar_q2,
    validar_q2,
)


@pytest.fixture
def parametros():
    return ler_json(ROOT / "data/simulado/parametros.json")


def test_grade_da_issue_186():
    assert RAZOES_Q2 == (1.00, 1.02, 1.05, 1.10, 1.15, 1.20, 1.25)
    deltas = deltas_q2()
    assert deltas[0] == 0.0
    np.testing.assert_allclose(np.exp(deltas), RAZOES_Q2)
    with pytest.raises(ValueError):
        deltas_q2((1.0, 0.0))


def test_semente_derivada_de_42_e_distinta_da_q1():
    esperado = int(np.random.SeedSequence([42, 2]).generate_state(1, dtype=np.uint32)[0])
    assert SEMENTE_BASE == 42 and SEMENTE_Q2 == esperado and SEMENTE_Q2 != 42


def test_q2_tem_configuracoes_e_campos(parametros):
    resultados = executar_q2(parametros, repeticoes=300)
    assert len(resultados) == 2 * len(RAZOES_Q2)
    assert {r["teste"] for r in resultados} == {"t_pareado", "wilcoxon"}
    assert all(r["n"] == 30 and r["pergunta"] == "Q2" and r["distribuicao"] == "normal" for r in resultados)
    # Tolerância: com taxa 0 ou 1, o limite de Wilson pode diferir no último dígito de ponto flutuante.
    assert all(r["ic95_inferior"] - 1e-12 <= r["taxa_rejeicao"] <= r["ic95_superior"] + 1e-12 for r in resultados)
    np.testing.assert_allclose(sorted({r["razao_geometrica"] for r in resultados}), RAZOES_Q2)


def test_q2_reproduzivel_e_fluxos_diferentes_da_q1(parametros):
    a = executar_q2(parametros, repeticoes=300)
    assert a == executar_q2(parametros, repeticoes=300)
    q1 = executar_q1(parametros, repeticoes=300, tamanhos=(30,))
    assert {r["semente_derivada"] for r in a}.isdisjoint({r["semente_derivada"] for r in q1})


def test_poder_cresce_com_o_efeito(parametros):
    resultados = executar_q2(parametros, repeticoes=2000)
    for teste in ("t_pareado", "wilcoxon"):
        taxas = [r["taxa_rejeicao"] for r in resultados if r["teste"] == teste]
        # Em 1,00 a taxa é erro tipo I (~5%); com o maior efeito o poder chega perto de 1.
        assert 0.03 < taxas[0] < 0.07
        assert taxas[-1] > 0.95
        assert taxas[-1] > taxas[2] > taxas[0]


def test_artefatos_q2_sao_reproduziveis(tmp_path):
    manifesto = salvar_q2(tmp_path)
    assert manifesto["configuracao"]["repeticoes"] == 10_000
    assert manifesto["configuracao"]["n"] == 30
    assert manifesto["configuracao"]["semente_q2"] == SEMENTE_Q2
    assert validar_q2(tmp_path) == {"status": "ok", "pergunta": "Q2", "configuracoes": 14}
    csv = tmp_path / "q2_resultados.csv"
    csv.write_text(csv.read_text(encoding="utf-8") + "\n", encoding="utf-8")
    with pytest.raises(ValueError, match="modificado"):
        validar_q2(tmp_path)
