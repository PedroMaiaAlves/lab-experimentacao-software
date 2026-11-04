import numpy as np
import pytest

from experimento.dados import ler_pares, salvar_pares, validar_pares
from experimento.simulacao import calibrar, gerar_pares


@pytest.fixture
def parametros():
    # Parâmetros analíticos de teste; nunca apresentados como dados reais.
    return {"medias_log": [1.0, 0.0], "covariancia_log": [[0.16, 0.12], [0.12, 0.25]]}


def test_calibracao_conhecida():
    logs = np.array([[1.0, 0.0], [2.0, 2.0], [3.0, 1.0]])
    result = calibrar(np.exp(logs))
    np.testing.assert_allclose(result["medias_log"], [2, 1])
    np.testing.assert_allclose(result["covariancia_log"], [[1, 0.5], [0.5, 1]])
    assert result["razao_geometrica_observada"] == pytest.approx(np.e)


def test_reproducao_semente_e_csv_sem_perda(parametros, tmp_path):
    first = gerar_pares(parametros, 30, 42)
    assert np.array_equal(first, gerar_pares(parametros, 30, 42))
    assert not np.array_equal(first, gerar_pares(parametros, 30, 43))
    path = tmp_path / "amostra.csv"
    salvar_pares(path, first)
    assert np.array_equal(first, ler_pares(path))


def test_distribuicao_pareada_preserva_momentos_populacionais(parametros):
    logs = np.log(gerar_pares(parametros, 100_000, 42))
    np.testing.assert_allclose(logs.mean(axis=0), [1, 0], atol=0.006)
    np.testing.assert_allclose(np.cov(logs, rowvar=False), parametros["covariancia_log"], atol=0.004)
    # A covariância positiva distingue geração pareada de dois sorteios independentes.
    assert np.corrcoef(logs, rowvar=False)[0, 1] > 0.55


def test_delta_zero_e_alternativa_mantem_ponto_medio_e_ruido(parametros):
    null = np.log(gerar_pares(parametros, 100_000, 42, delta_log=0))
    effect = np.log(gerar_pares(parametros, 100_000, 42, delta_log=0.4))
    assert abs((null[:, 0] - null[:, 1]).mean()) < 0.006
    np.testing.assert_allclose(effect[:, 0] - null[:, 0], 0.2, atol=1e-14)
    np.testing.assert_allclose(effect[:, 1] - null[:, 1], -0.2, atol=1e-14)
    np.testing.assert_allclose(null.mean(axis=1), effect.mean(axis=1), atol=1e-14)
    assert parametros["medias_log"] == [1, 0]  # Não modifica parâmetros do chamador.


@pytest.mark.parametrize("pares", [[], [[1, 2]], [[1, 2, 3], [2, 3, 4]],
                                  [[0, 1], [1, 2]], [[-1, 1], [1, 2]],
                                  [[float("nan"), 1], [1, 2]], [[float("inf"), 1], [1, 2]]])
def test_recusa_dados_invalidos(pares):
    with pytest.raises(ValueError):
        validar_pares(pares)


def test_nao_inventa_variabilidade():
    with pytest.raises(ValueError, match="degenerada"):
        calibrar([[1, 1], [2, 2], [3, 3]])


def test_recusa_ids_duplicados(tmp_path):
    path = tmp_path / "invalido.csv"
    path.write_text("par_id,sem_cache_s,com_cache_s\n1,2,1\n1,3,2\n", encoding="utf-8")
    with pytest.raises(ValueError, match="único"):
        ler_pares(path)


def test_recusa_covariancia_invalida():
    with pytest.raises(ValueError, match="covariância|Covariância"):
        gerar_pares({"medias_log": [0, 0], "covariancia_log": [[1, 2], [2, 1]]})


def test_recusa_overflow_sem_truncar():
    with pytest.raises(ValueError, match="faixa numérica"):
        gerar_pares({"medias_log": [1000, 1000], "covariancia_log": [[1, 0], [0, 1]]})


@pytest.mark.parametrize("args", [{"n": 1}, {"n": 2.5}, {"semente": -1}, {"delta_log": float("nan")}])
def test_parametros_invalidos(parametros, args):
    with pytest.raises(ValueError):
        gerar_pares(parametros, **args)
