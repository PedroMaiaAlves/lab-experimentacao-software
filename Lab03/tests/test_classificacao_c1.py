from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from analises.classificacao_c1 import (CATEGORIAS, COMBINACAO_C1, SEM_CATEGORIA, analisar, classificar,
                                       distribuicao)
from metricas.classificacao import UM_POR_MES_EM_SEMANAS

BASE = Path(__file__).resolve().parents[1]


def projeto(nome, frequencia, lead, cfr, recuperacao, episodios=1):
    return dict(full_name=nome, deployment_frequency=frequencia, lead_time_a_horas=lead, cfr_a=cfr,
                tempo_recuperacao_horas=recuperacao, episodios_total=episodios,
                # Variantes que C1 não usa: valores extremos não podem afetar o resultado.
                lead_time_b_horas=0.0, cfr_b=1.0, deployment_frequency_tags=100.0)


@pytest.fixture
def df():
    return pd.DataFrame([
        projeto("org/elite", 7, 23.9, .15, .5),                        # 4,4,4,4 -> Elite
        projeto("org/enunciado", 7, 100, .30, 200),                    # 4,3,3,1 -> High
        projeto("org/meio", 1, 168, .3001, 1),                         # 3,2,2,3 -> 2,5 -> Medium
        projeto("org/low", UM_POR_MES_EM_SEMANAS - .001, 720, .46, 168),  # 1,1,1,1 -> Low
        projeto("org/sem", 2, 10, 0, np.nan, episodios=0),             # 3,4,4,- -> sem geral
    ])


def test_c1_usa_as_funcoes_de_referencia_e_os_cortes(df):
    c = classificar(df).set_index("full_name")
    assert c.loc["org/elite", ["categoria_deployment_frequency", "categoria_lead_time", "categoria_cfr",
                               "categoria_tempo_recuperacao"]].tolist() == ["Elite"] * 4
    assert c.loc["org/enunciado", "categoria_geral"] == "High"
    assert c.loc["org/meio", "mediana_notas"] == 2.5 and c.loc["org/meio", "categoria_geral"] == "Medium"
    assert c.loc["org/low", "categoria_geral"] == "Low"


def test_metrica_ausente_deixa_geral_sem_categoria_e_e_registrada(df):
    c = classificar(df).set_index("full_name").loc["org/sem"]
    assert pd.isna(c.categoria_tempo_recuperacao) and pd.isna(c.categoria_geral)
    assert c.metricas_disponiveis == 3 and c.metricas_ausentes == "tempo_recuperacao"
    assert np.isnan(c.mediana_notas)
    assert c.categoria_geral_minimo_3 == "Elite"         # (3, 4, 4) -> 4, só como sensibilidade
    r = analisar(df)["c1_ausencias"]
    assert r.to_dict("records") == [dict(full_name="org/sem", metrica="tempo_recuperacao",
                                         motivo="sem_episodios")]


def test_variantes_fora_de_c1_nao_mudam_a_classificacao(df):
    outra = df.assign(lead_time_b_horas=1e6, cfr_b=0.0, deployment_frequency_tags=0.0)
    pd.testing.assert_frame_equal(classificar(df), classificar(outra))


def test_combinacao_alternativa_troca_apenas_colunas(df):
    c2 = classificar(df, {**COMBINACAO_C1, "lead_time": "lead_time_b_horas"}).set_index("full_name")
    assert "lead_time_b_horas" in c2.columns and "lead_time_a_horas" not in c2.columns
    assert (c2.categoria_lead_time == "Elite").all()     # lead time (b) = 0 em todos


def test_distribuicao_conta_todas_as_categorias_e_ausencias(df):
    d = distribuicao(classificar(df)).set_index(["dimensao", "categoria"])
    for dimensao in ("deployment_frequency", "lead_time", "cfr", "tempo_recuperacao", "geral"):
        assert d.loc[dimensao].n.sum() == len(df)
    assert d.loc[("geral", SEM_CATEGORIA), "n"] == 1
    assert d.loc[("geral", "Elite"), "proporcao_classificados"] == pytest.approx(1 / 4)
    assert d.loc[("geral", "Elite"), "proporcao_total"] == pytest.approx(1 / 5)
    assert np.isnan(d.loc[("geral", SEM_CATEGORIA), "proporcao_classificados"])
    assert list(d.loc["cfr"].index) == [*CATEGORIAS, SEM_CATEGORIA]


def test_classificacao_publicada_cobre_a_amostra():
    publicada = pd.read_csv(BASE / "data/classificacao_C1.csv")
    amostra = pd.read_csv(BASE / "data/amostra_final.csv")
    assert sorted(publicada.full_name) == sorted(amostra.full_name)
    assert set(publicada.categoria_geral.dropna()) <= set(CATEGORIAS)
    assert publicada.categoria_geral.isna().sum() == (publicada.metricas_disponiveis < 4).sum()
