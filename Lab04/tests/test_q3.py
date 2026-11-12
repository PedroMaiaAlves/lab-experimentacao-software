import numpy as np
import pytest
from scipy import stats

from experimento.dados import ROOT, ler_json, salvar_json
from experimento.monte_carlo import avaliar_rejeicoes, gerar_diferencas
from experimento.q2 import RAZOES_Q2, SEMENTE_Q2
from experimento.q3 import (
    SEMENTE_Q3, conferir_scipy, executar_q3, regenerar_diferencas, salvar_q3, validar_q3,
)


@pytest.fixture(scope="module")
def parametros():
    return ler_json(ROOT / "data/simulado/parametros.json")


def test_semente_fixada_e_fluxos_independentes():
    esperado = int(np.random.SeedSequence([42, 3]).generate_state(1, dtype=np.uint32)[0])
    assert SEMENTE_Q3 == esperado and SEMENTE_Q3 not in (42, SEMENTE_Q2)


def test_t3_padroniza_variancia_sem_recalibrar_a_amostra():
    esperado = 0.1 + 0.2 * (np.random.default_rng(7).standard_t(3, size=(200, 30)) / np.sqrt(3))
    obtido = gerar_diferencas(np.random.default_rng(7), 200, 30, 0.1, 0.2, "t3")
    np.testing.assert_array_equal(obtido, esperado)
    assert stats.t.var(3, scale=0.2 / np.sqrt(3)) == pytest.approx(0.2**2)
    assert stats.t.mean(3) == stats.t.median(3) == 0
    assert np.isinf(stats.t.stats(3, moments="k"))


def test_grade_reproduzivel_e_igual_a_q2_exceto_distribuicao(parametros):
    linhas = executar_q3(parametros, repeticoes=200)
    assert linhas == executar_q3(parametros, repeticoes=200)
    assert len(linhas) == 14
    np.testing.assert_allclose(sorted({r["razao_geometrica"] for r in linhas}), RAZOES_Q2)
    assert all(r["n"] == 30 and r["alpha"] == 0.05 and r["distribuicao"] == "t3"
               and r["pergunta"] == "Q3" for r in linhas)
    assert all(r["ic95_inferior"] - 1e-12 <= r["taxa_rejeicao"] <= r["ic95_superior"] + 1e-12
               for r in linhas)


def test_regeneracao_e_scipy_individual(parametros):
    linhas = executar_q3(parametros, repeticoes=150)
    for razao, diferencas in regenerar_diferencas(parametros, repeticoes=150):
        decisoes = avaliar_rejeicoes(diferencas)
        for linha in linhas:
            if np.isclose(linha["razao_geometrica"], razao):
                assert linha["rejeicoes"] == int(decisoes[linha["teste"]].sum())
    assert all(c["divergencias_t"] == c["divergencias_wilcoxon"] == 0
               for c in conferir_scipy(parametros, repeticoes=25))


def test_h0_e_efeito_grande_sem_escolher_semente(parametros):
    linhas = executar_q3(parametros, repeticoes=2000, razoes=(1.0, 1.25))
    for linha in linhas:
        taxa = linha["taxa_rejeicao"]
        assert 0.025 < taxa < 0.075 if linha["delta_log"] == 0 else taxa > 0.9


def test_artefatos_oficiais_e_rejeicao_de_adulteracoes(tmp_path):
    manifesto = salvar_q3(tmp_path)
    assert manifesto["configuracao"]["repeticoes"] == 10_000
    assert validar_q3(tmp_path) == {"status": "ok", "pergunta": "Q3", "configuracoes": 14}
    manifesto["configuracao"]["graus_liberdade"] = 5
    salvar_json(tmp_path / "q3_manifesto.json", manifesto)
    with pytest.raises(ValueError, match="configuração"):
        validar_q3(tmp_path)
    manifesto["configuracao"]["graus_liberdade"] = 3
    salvar_json(tmp_path / "q3_manifesto.json", manifesto)
    csv = tmp_path / "q3_resultados.csv"
    csv.write_bytes(csv.read_bytes() + b"\n")
    with pytest.raises(ValueError, match="modificado"):
        validar_q3(tmp_path)


def test_entrega_preservada_valida():
    assert validar_q3()["configuracoes"] == 14
