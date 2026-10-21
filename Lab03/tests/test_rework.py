import pytest

from metricas.rework import calcular_rework_rate


@pytest.mark.parametrize("flags,esperado", [([True, False, False, False], .25),
                                            ([False, False], 0), ([True, True], 1)])
def test_proporcao_de_releases_corretivas(flags, esperado):
    r = calcular_rework_rate({"corretiva": flag} for flag in flags)
    assert r["rework_rate"] == r["rework_limite_inferior"] == r["rework_limite_superior"] == esperado
    assert r["releases_total"] == len(flags)


def test_ausencia_nao_vira_zero_e_gera_limites_nao_intervalo_de_confianca():
    r = calcular_rework_rate([{"corretiva": True}, {"corretiva": None}, {"corretiva": False}])
    assert r["rework_rate"] is None
    assert r["releases_sem_evidencia"] == 1
    assert r["rework_limite_inferior"] == 1 / 3 and r["rework_limite_superior"] == 2 / 3


def test_sem_releases_nao_inventa_zero():
    r = calcular_rework_rate([])
    assert r["releases_total"] == 0
    assert r["rework_rate"] is None and r["rework_limite_inferior"] is None and r["rework_limite_superior"] is None


def test_drafts_e_prereleases_nao_entram_no_denominador_principal():
    r = calcular_rework_rate([{"corretiva": False}, {"corretiva": True, "draft": True},
                             {"corretiva": True, "prerelease": True}])
    assert r["releases_total"] == 1 and r["rework_rate"] == 0


@pytest.mark.parametrize("valor", [0, 1, "sim", "False", float("nan")])
def test_rotulo_invalido_nao_e_convertido_em_booleano(valor):
    with pytest.raises(ValueError, match="corretiva"):
        calcular_rework_rate([{"corretiva": valor}])
