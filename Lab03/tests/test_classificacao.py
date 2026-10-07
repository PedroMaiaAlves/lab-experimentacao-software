import pytest

from metricas.classificacao import (
    Categoria, classificar_cfr, classificar_deployment_frequency, classificar_geral,
    classificar_lead_time, classificar_repositorio, classificar_tempo_recuperacao,
    UM_POR_MES_EM_SEMANAS)

E, H, M, L = Categoria.ELITE, Categoria.HIGH, Categoria.MEDIUM, Categoria.LOW


@pytest.mark.parametrize("valor,esperado", [
    (7, E), (50, E), (6.99, H), (1, H), (0.99, M),
    (UM_POR_MES_EM_SEMANAS, M), (UM_POR_MES_EM_SEMANAS - 0.001, L), (0, L)])
def test_deployment_frequency(valor, esperado):
    assert classificar_deployment_frequency(valor) == esperado


@pytest.mark.parametrize("horas,esperado", [
    (0, E), (23.99, E), (24, H), (167.99, H), (168, M), (719.99, M), (720, L), (5000, L)])
def test_lead_time(horas, esperado):
    assert classificar_lead_time(horas) == esperado


@pytest.mark.parametrize("taxa,esperado", [
    (0, E), (0.15, E), (0.1501, H), (0.30, H), (0.3001, M), (0.45, M), (0.4501, L), (1, L)])
def test_cfr(taxa, esperado):
    assert classificar_cfr(taxa) == esperado


@pytest.mark.parametrize("horas,esperado", [
    (0.5, E), (0.99, E), (1, H), (23.99, H), (24, M), (167.99, M), (168, L), (1000, L)])
def test_tempo_recuperacao(horas, esperado):
    assert classificar_tempo_recuperacao(horas) == esperado


@pytest.mark.parametrize("funcao", [
    classificar_deployment_frequency, classificar_lead_time, classificar_cfr,
    classificar_tempo_recuperacao])
def test_metrica_ausente_devolve_none(funcao):
    assert funcao(None) is None


@pytest.mark.parametrize("funcao", [
    classificar_deployment_frequency, classificar_lead_time, classificar_cfr,
    classificar_tempo_recuperacao])
def test_valor_negativo_levanta_erro(funcao):
    with pytest.raises(ValueError):
        funcao(-1)


def test_geral_exemplo_do_enunciado_4_3_3_1_e_high():
    assert classificar_geral([E, H, H, L]) == H


def test_geral_mediana_de_dois_centrais_arredonda_para_baixo():
    assert classificar_geral([E, H, M, L]) == M      # (3 + 2) / 2 = 2,5 -> 2
    assert classificar_geral([E, E, H, M]) == H      # (4 + 3) / 2 = 3,5 -> 3
    assert classificar_geral([L, L, L, L]) == L
    assert classificar_geral([E, E, E, E]) == E


def test_geral_com_metrica_ausente_usa_as_disponiveis():
    assert classificar_geral([E, H, None, H]) == H


def test_geral_sem_notas_suficientes_devolve_none():
    assert classificar_geral([E, None, None, None]) is None
    assert classificar_geral([E, H, None, None], minimo_metricas=2) == H


def test_classificar_repositorio_completo():
    r = classificar_repositorio(deployment_frequency=2, lead_time_horas=100, cfr=0.10,
                                tempo_recuperacao_horas=0.5)
    assert r == {"deployment_frequency": H, "lead_time": H, "cfr": E,
                 "tempo_recuperacao": E, "geral": H}
