import pytest

from metricas.cfr import calcular_cfr_a, classificar_conclusao, contar_conclusoes


@pytest.fixture
def runs_mistos():
    return [
        {"conclusion": "success"},
        {"conclusion": "success"},
        {"conclusion": "failure"},
        {"conclusion": "timed_out"},
        {"conclusion": "startup_failure"},
        {"conclusion": "cancelled"},
        {"conclusion": None},
    ]


def test_classificacao_da_tabela_do_enunciado():
    assert classificar_conclusao("success") == "sucesso"
    for valor in ("failure", "timed_out", "startup_failure"):
        assert classificar_conclusao(valor) == "falha"
    for valor in ("cancelled", "skipped", "neutral", "action_required", "stale", "", None, "nova"):
        assert classificar_conclusao(valor) == "ignorar"


def test_cfr_fixture_calculada_a_mao(runs_mistos):
    assert contar_conclusoes(runs_mistos) == {"sucessos": 2, "falhas": 3, "ignoradas": 2}
    assert calcular_cfr_a(runs_mistos) == pytest.approx(3 / 5)


def test_so_sucessos_da_zero_e_cancelados_nao_alteram():
    assert calcular_cfr_a([{"conclusion": "success"}, {"conclusion": "cancelled"}]) == 0


def test_nenhum_run_valido_devolve_none():
    assert calcular_cfr_a([{"conclusion": "cancelled"}, {"conclusion": None}]) is None
