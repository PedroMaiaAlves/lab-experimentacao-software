import pytest

from metricas.recuperacao import calcular_tempo_recuperacao


def run(workflow, inicio, conclusao, fim=None):
    return {
        "workflow_id": workflow,
        "run_started_at": inicio,
        "updated_at": fim or inicio,
        "conclusion": conclusao,
    }


@pytest.fixture
def exemplo_enunciado():
    return [
        run(1, "2026-01-01T09:00:00Z", "success", "2026-01-01T09:05:00Z"),
        run(1, "2026-01-01T10:00:00Z", "failure", "2026-01-01T10:05:00Z"),
        run(1, "2026-01-01T10:30:00Z", "failure", "2026-01-01T10:35:00Z"),
        run(1, "2026-01-01T11:15:00Z", "success", "2026-01-01T11:20:00Z"),
    ]


def test_exemplo_resulta_em_uma_hora_e_vinte(exemplo_enunciado):
    resultado = calcular_tempo_recuperacao(exemplo_enunciado)
    assert resultado.mediana_horas == pytest.approx(4 / 3)
    assert resultado.episodios_horas == pytest.approx((4 / 3,))
    assert resultado.episodios_total == 1
    assert resultado.proporcao_censurados == 0


def test_workflows_sao_independentes_e_runs_ignorados_nao_mudam_estado():
    runs = [
        run(1, "2026-01-01T09:00:00Z", "success"),
        run(2, "2026-01-01T09:05:00Z", "failure"),  # sem sucesso anterior: ignora
        run(1, "2026-01-01T10:00:00Z", "failure"),
        run(1, "2026-01-01T10:30:00Z", "cancelled"),
        run(2, "2026-01-01T11:00:00Z", "success"),
        run(1, "2026-01-01T12:00:00Z", "success", "2026-01-01T12:00:00Z"),
    ]
    resultado = calcular_tempo_recuperacao(runs)
    assert resultado.episodios_horas == (2.0,)
    assert resultado.episodios_total == 1


def test_episodio_sem_sucesso_e_censurado():
    resultado = calcular_tempo_recuperacao([
        run(1, "2026-01-01T09:00:00Z", "success"),
        run(1, "2026-01-01T10:00:00Z", "failure"),
        run(1, "2026-01-01T11:00:00Z", "timed_out"),
    ])
    assert resultado.mediana_horas is None
    assert resultado.episodios_total == 1
    assert resultado.episodios_censurados == 1
    assert resultado.proporcao_censurados == 1


def test_sem_episodios_tem_valores_ausentes():
    resultado = calcular_tempo_recuperacao([
        run(1, "2026-01-01T09:00:00Z", "failure"),
        run(1, "2026-01-01T10:00:00Z", "success"),
    ])
    assert resultado.mediana_horas is None
    assert resultado.episodios_total == 0
    assert resultado.proporcao_censurados is None
