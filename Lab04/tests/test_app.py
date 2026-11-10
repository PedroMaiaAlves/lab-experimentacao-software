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
