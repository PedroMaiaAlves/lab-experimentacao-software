from pathlib import Path

import pytest

pytest.importorskip("plotly")
from streamlit.testing.v1 import AppTest  # noqa: E402

APP = Path(__file__).parents[1] / "app.py"


def test_app_abre_sem_excecoes_e_tem_quatro_secoes():
    app = AppTest.from_file(str(APP)).run(timeout=45)
    assert not app.exception
    titulos = [element.value for element in app.header]
    assert titulos == [
        "1. Cenário",
        "2. Dados",
        "3. Testes",
        "4. Efeito",
    ]


def test_app_nao_importa_nem_executa_coleta():
    fonte = APP.read_text(encoding="utf-8")
    assert "experimento.coleta" not in fonte
    assert "coletar(" not in fonte


def test_quatro_graficos_e_previa_piloto_offline(monkeypatch):
    def proibido(*args, **kwargs):
        raise AssertionError("O dashboard deve ler dados locais offline.")

    monkeypatch.setattr("urllib.request.urlopen", proibido)
    app = AppTest.from_file(str(APP)).run(timeout=45)
    assert not app.exception
    assert len(app.get("plotly_chart")) == 4
    assert len(app.dataframe) >= 4
    assert len(app.warning) == 1
    assert "Prévia estrutural" in app.warning[0].value
    textos = " ".join(element.value for element in app.markdown)
    captions = " ".join(element.value for element in app.caption)
    assert "bootstrap" in textos
    assert "S03" in captions
