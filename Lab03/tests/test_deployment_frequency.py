from datetime import date

import pytest

from metricas.deployment_frequency import deployment_frequency
from pipeline.coleta_releases import filtrar_releases

CFG = {"janela_inicio": date(2026, 1, 1), "janela_fim": date(2026, 1, 7)}


def test_extremos_inclusivos_e_datas_fora_da_janela():
    datas = ["2025-12-31T23:59:59Z", "2026-01-01T00:00:00Z",
             "2026-01-07T23:59:59Z", "2026-01-08T00:00:00Z"]
    assert deployment_frequency(datas, CFG) == 2


def test_lista_generica_de_datas_pode_representar_tags():
    assert deployment_frequency([date(2026, 1, 1), "2026-01-02"], CFG) == 2
    assert deployment_frequency([], CFG) == 0


def test_uma_janela_de_365_dias_tem_fracao_de_semanas():
    cfg = {"janela_inicio": date(2025, 10, 1), "janela_fim": date(2026, 9, 30)}
    assert deployment_frequency(["2026-01-01"], cfg) == pytest.approx(7 / 365)


def test_drafts_e_prereleases_sao_filtrados_antes_do_calculo():
    releases = [{"draft": draft, "prerelease": prerelease, "published_at": "2026-01-02T00:00:00Z"}
                for draft, prerelease in [(False, False), (True, False), (False, True)]]
    principais = filtrar_releases(releases, CFG)
    assert deployment_frequency([r["published_at"] for r in principais], CFG) == 1
    variantes = filtrar_releases(releases, CFG, incluir_prereleases=True)
    assert deployment_frequency([r["published_at"] for r in variantes], CFG) == 2


def test_janela_invertida_nao_gera_frequencia_negativa():
    with pytest.raises(ValueError):
        deployment_frequency([], {"janela_inicio": date(2026, 1, 7), "janela_fim": date(2026, 1, 1)})
