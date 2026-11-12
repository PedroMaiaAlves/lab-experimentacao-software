from pathlib import Path

from streamlit.testing.v1 import AppTest


APP = Path(__file__).parents[1] / "app.py"


def test_app_abre_sem_excecoes_e_tem_sete_secoes():
    app = AppTest.from_file(str(APP)).run(timeout=45)
    assert not app.exception
    titulos = [element.value for element in app.header]
    assert titulos == [
        "1. Cenário",
        "2. Os dados — G1",
        "3. Como os testes funcionam — G2",
        "4. Erro tipo I — Q1 e G3",
        "5. Poder — Q2, Q3 e G4",
        "6. Dados reais",
        "7. Conclusão",
    ]


def test_app_nao_importa_nem_executa_coleta():
    fonte = APP.read_text(encoding="utf-8")
    assert "experimento.coleta" not in fonte
    assert "coletar(" not in fonte


def test_quatro_graficos_dados_reais_e_conclusao_sem_pendencias(monkeypatch):
    def proibido(*args, **kwargs):
        raise AssertionError("O dashboard deve ler dados offline, sem coleta ou Monte Carlo.")

    monkeypatch.setattr("urllib.request.urlopen", proibido)
    monkeypatch.setattr("experimento.monte_carlo.simular_grade", proibido)
    monkeypatch.setattr("experimento.coleta.coletar", proibido)
    app = AppTest.from_file(str(APP)).run(timeout=45)
    assert not app.exception
    assert len(app.get("plotly_chart")) == 4
    assert len(app.dataframe) >= 4
    textos = " ".join(element.value for element in app.markdown)
    assert "IC de 95%" in textos and "razão geométrica" in textos
    assert "permanece pendente" not in textos and "Entrega em andamento" not in textos
    assert "universalmente melhor" in textos
