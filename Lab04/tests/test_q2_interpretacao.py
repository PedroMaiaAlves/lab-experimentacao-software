import pytest

from experimento.dados import ROOT, ler_json
from experimento.monte_carlo import ler_resultados
from experimento.q2 import RAZOES_Q2, executar_q2
from experimento.q2_interpretacao import (
    comparar_testes,
    conferir_scipy,
    ler_texto_q2,
    regenerar_diferencas,
    salvar_interpretacao,
    texto_q2,
    validar_interpretacao,
)
from experimento.q2 import salvar_q2

S02 = ROOT / "data/s02"


@pytest.fixture
def parametros():
    return ler_json(ROOT / "data/simulado/parametros.json")


@pytest.fixture(scope="module")
def comparacao():
    return comparar_testes(ler_json(ROOT / "data/simulado/parametros.json"))


def test_regeneracao_usa_as_mesmas_amostras_de_simular_grade(parametros):
    from experimento.monte_carlo import avaliar_rejeicoes

    oficial = executar_q2(parametros, repeticoes=200)
    for razao, d in regenerar_diferencas(parametros, repeticoes=200):
        lote = avaliar_rejeicoes(d)
        linhas = {r["teste"]: r for r in oficial if round(r["razao_geometrica"], 6) == round(razao, 6)}
        assert int(lote["t_pareado"].sum()) == linhas["t_pareado"]["rejeicoes"]
        assert int(lote["wilcoxon"].sum()) == linhas["wilcoxon"]["rejeicoes"]


def test_chamadas_diretas_ao_scipy_coincidem(parametros):
    # Amostra reduzida para o teste; a CLI --scipy confere as 10.000 repetições oficiais.
    conferencia = conferir_scipy(parametros, repeticoes=150)
    assert len(conferencia) == len(RAZOES_Q2)
    assert all(c["divergencias_t"] == 0 and c["divergencias_wilcoxon"] == 0 for c in conferencia)


def test_comparacao_bate_com_csv_oficial(comparacao):
    oficiais = ler_resultados(S02 / "q2_resultados.csv")
    assert [c["razao"] for c in comparacao] == list(RAZOES_Q2)
    for c in comparacao:
        t = next(r for r in oficiais if r["teste"] == "t_pareado" and round(r["razao_geometrica"], 6) == round(c["razao"], 6))
        assert c["poder_t"] == t["taxa_rejeicao"]
        # Discordâncias explicam exatamente a diferença de rejeições entre os testes.
        assert c["so_t_rejeita"] - c["so_wilcoxon_rejeita"] == round(10_000 * (c["poder_t"] - c["poder_wilcoxon"]))


def test_h0_sem_diferenca_e_t_com_mais_poder_nos_efeitos_intermediarios(comparacao):
    por_razao = {c["razao"]: c for c in comparacao}
    assert por_razao[1.00]["maior_poder"] == "sem diferença detectável"
    assert all(por_razao[r]["maior_poder"] == "t_pareado" for r in (1.05, 1.10))
    assert por_razao[1.25]["maior_poder"] == "sem diferença detectável"


def test_texto_explica_poder_sem_confundir(comparacao):
    texto = texto_q2(comparacao)
    frases = [f for f in texto.split(". ") if f.strip()]
    assert 3 <= len(frases) <= 4
    assert "não é um p-valor" in texto and "nem o tamanho do efeito" in texto
    assert "Wilson" in texto and "Q3" in texto


def test_interpretacao_preservada_e_reproduzivel(tmp_path):
    salvar_q2(tmp_path)
    salvo = salvar_interpretacao(tmp_path)
    assert validar_interpretacao(tmp_path) == {"status": "ok", "pergunta": "Q2", "razoes": 7}
    lido = ler_texto_q2(tmp_path / "q2_interpretacao.json")
    assert lido["texto"] == salvo["texto_dashboard"] and lido["limitacoes"]


def test_artefato_oficial_valida():
    assert validar_interpretacao() == {"status": "ok", "pergunta": "Q2", "razoes": 7}
