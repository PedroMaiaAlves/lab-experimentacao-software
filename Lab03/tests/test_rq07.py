import numpy as np
import pandas as pd
from pandas.testing import assert_frame_equal
import pytest

from analises.classificacao_c1 import classificar
from analises.rq07 import COMBINACOES, analisar, concordancia


def classes(a, b, c):
    return pd.DataFrame([{"full_name": f"org/{i}", "combinacao": nome, "categoria_geral": valor}
                         for nome, valores in zip(COMBINACOES, (a, b, c)) for i, valor in enumerate(valores)])


def test_kappa_linear_confere_calculo_manual_e_mudancas():
    tabela = classes(["Low", "Medium", "High", "Elite"], ["Low", "High", "High", "Elite"],
                     ["Low", "Medium", "High", "Elite"])
    pares, matrizes = concordancia(tabela)
    r = pares.iloc[0]
    # Distância observada=1/4; distância esperada entre as marginais=5/4.
    assert r.kappa_linear == pytest.approx(1 - .25 / 1.25)
    assert r.n == 4 and r.mudou == 1 and r.proporcao_mudou == .25
    assert r.subiu == 1 and r.desceu == 0
    assert len(matrizes) == 48 and matrizes.n.sum() == 12


def test_ausencias_nao_sao_categoria_nem_mudanca():
    tabela = classes(["Low", "High", None, "Elite"], ["Low", None, "High", "Low"],
                     ["Low", "High", "High", None])
    pares, _ = concordancia(tabela)
    par, comuns = pares.iloc[0], pares.iloc[1]
    assert par.n == 2 and par.mudou == 1 and par.proporcao_mudou == .5
    assert par.ganhou_classificacao == 1 and par.perdeu_classificacao == 1
    assert comuns.n == 1 and comuns.n_excluidos == 3
    assert comuns.status_kappa == "denominador_zero" and pd.isna(comuns.kappa_linear)


def test_sem_pares_nao_gera_zero_de_mudanca():
    pares, matrizes = concordancia(classes([None], [None], [None]))
    assert pares.n.eq(0).all() and pares.proporcao_mudou.isna().all()
    assert pares.kappa_linear.isna().all() and pares.status_kappa.eq("sem_pares").all()
    assert matrizes.n.sum() == 0


@pytest.mark.parametrize("erro", ["duplicada", "faltando", "categoria"])
def test_estrutura_invalida_rejeitada(erro):
    tabela = classes(["Low"], ["Low"], ["High"])
    if erro == "duplicada":
        tabela = pd.concat([tabela, tabela.iloc[:1]])
    elif erro == "faltando":
        tabela = tabela.iloc[:2]
    else:
        tabela.loc[0, "categoria_geral"] = "Very high"
    with pytest.raises(ValueError):
        concordancia(tabela)


@pytest.fixture
def dados():
    n = 24
    return pd.DataFrame({"full_name": [f"org/{i:02d}" for i in range(n)],
                         "deployment_frequency": np.arange(1, n + 1) / n,
                         "deployment_frequency_prereleases": np.arange(1, n + 1) / 2,
                         "deployment_frequency_tags": np.arange(1, n + 1, dtype=float),
                         "lead_time_a_horas": np.arange(1, n + 1) * 40.,
                         "lead_time_b_horas": np.arange(1, n + 1) * 20.,
                         "cfr_a": np.arange(n) / 100, "cfr_b": np.arange(n) / n,
                         "tempo_recuperacao_horas": np.arange(1, n + 1) / 2,
                         "contribuidores": np.arange(1, n + 1), "language": ["Python"] * 12 + ["Java"] * 12,
                         "tipo_projeto": ["biblioteca/framework"] * 12 + ["aplicação/serviço"] * 12})


def test_reutiliza_metricas_sem_modificar_entradas_e_ajusta_familias_unicas(dados):
    antes = dados.copy(deep=True)
    tabelas = analisar(dados, reamostragens=99)
    assert_frame_equal(dados, antes)
    assert len(tabelas["metricas_combinacoes"]) == 72
    assert len(tabelas["rq07_robustez_rq06"]) == 24
    assert tabelas["rq07_robustez_rq06"].p_holm_sensibilidade_familia_n.eq(24).all()
    assert tabelas["rq07_robustez_rq05"].p_holm_sensibilidade_familia_n.eq(6).all()
    c3 = tabelas["metricas_combinacoes"].query("combinacao == 'C3'").reset_index(drop=True)
    assert c3.deployment_frequency.tolist() == dados.deployment_frequency_tags.tolist()
    assert c3.lead_time.tolist() == dados.lead_time_b_horas.tolist()
    assert c3.cfr.tolist() == dados.cfr_b.tolist()


def test_c1_publicada_precisa_ser_reproduzida(dados, tmp_path):
    caminho = tmp_path / "C1.csv"
    c1 = classificar(dados)
    c1.loc[0, "categoria_geral"] = "Low"
    c1.to_csv(caminho, index=False)
    with pytest.raises(AssertionError):
        analisar(dados, caminho, reamostragens=99)


@pytest.mark.parametrize("erro", ["duplicado", "negativo", "infinito"])
def test_dataset_invalido_rejeitado(dados, erro):
    if erro == "duplicado":
        dados.loc[0, "full_name"] = dados.loc[1, "full_name"]
    else:
        dados.loc[0, "deployment_frequency_tags"] = -1 if erro == "negativo" else np.inf
    with pytest.raises(ValueError):
        analisar(dados, reamostragens=99)


def test_cobertura_incompleta_de_uma_combinacao_e_erro_estrutural():
    tabela = classes(["Low", "High"], ["Low", "High"], ["Low", "High"]).iloc[:-1]
    with pytest.raises(ValueError, match="mesmos projetos"):
        concordancia(tabela)
