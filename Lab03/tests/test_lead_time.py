from copy import deepcopy

import pytest

from metricas.lead_time import calcular_lead_time, lead_time_por_commit, lead_time_por_release


@pytest.fixture
def release_exemplo():
    return {"published_at": "2026-03-15T00:00:00Z", "status": "ok",
            "commits": [{"author_date": f"2026-03-{dia:02d}T00:00:00Z"} for dia in (2, 10, 14)]}


def test_exemplo_do_enunciado(release_exemplo):
    assert lead_time_por_release([release_exemplo]) == 13 * 24
    assert lead_time_por_commit([release_exemplo]) == 5 * 24


def test_variantes_ponderam_releases_e_commits_de_forma_diferente(release_exemplo):
    outra = {"published_at": "2026-03-16T00:00:00Z",
             "commits": [{"author_date": "2026-03-15T00:00:00Z"}]}
    assert calcular_lead_time([release_exemplo, outra]) == {
        "lead_time_a_horas": 7 * 24, "lead_time_b_horas": 3 * 24}


@pytest.mark.parametrize("status", ["sem_anterior", "erro_404"])
def test_release_ignorada_nao_altera_mediana(release_exemplo, status):
    ignorada = {"status": status, "published_at": None, "commits": [{"author_date": None}]}
    assert calcular_lead_time([ignorada, release_exemplo]) == calcular_lead_time([release_exemplo])


@pytest.mark.parametrize("releases", [[], [{"status": "ok", "commits": []}],
                                     [{"status": "sem_anterior", "commits": []}]])
def test_sem_observacoes_validas_devolve_ausente(releases):
    assert calcular_lead_time(releases) == {"lead_time_a_horas": None, "lead_time_b_horas": None}


def test_respeita_fusos_e_preserva_zero_real():
    release = {"published_at": "2026-03-15T01:00:00+01:00",
               "commits": [{"author_date": "2026-03-15T00:00:00Z"}]}
    assert calcular_lead_time([release]) == {"lead_time_a_horas": 0, "lead_time_b_horas": 0}


def test_nao_altera_os_dados_de_entrada(release_exemplo):
    original = deepcopy(release_exemplo)
    calcular_lead_time([release_exemplo])
    assert release_exemplo == original


@pytest.mark.parametrize("data", ["2026-03-16T00:00:00Z", "2026-03-14T00:00:00"])
def test_rejeita_data_posterior_ou_sem_fuso(data):
    release = {"published_at": "2026-03-15T00:00:00Z", "commits": [{"author_date": data}]}
    with pytest.raises(ValueError):
        calcular_lead_time([release])
