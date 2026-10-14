import pytest

from scripts.validar_rotulos_b import validar_rotulos


def linhas_validas(repos=2, releases=2):
    return [
        {
            "full_name": f"org/repo{repo}",
            "release_id": f"{repo}-{release}",
            "tipo_projeto": "biblioteca/framework" if repo == 0 else "ferramenta CLI",
            "releases_sao_entregas": "sim",
            "corretiva": "sim" if release == 0 else "não",
            "revisado_por": "Pedro",
            "revisao_confirmada": "sim",
            "html_url": "https://example.test",
        }
        for repo in range(repos)
        for release in range(releases)
    ]


def test_validador_aceita_colunas_extras_e_resume_rotulos():
    assert validar_rotulos(linhas_validas(), 2, 2) == {
        "repositorios": 2,
        "releases": 4,
        "releases_corretivas": 2,
        "revisoes_confirmadas": 4,
    }


@pytest.mark.parametrize(
    ("alterar", "mensagem"),
    [
        (lambda linhas: linhas.pop(), "esperadas 4 linhas"),
        (lambda linhas: linhas[0].update(release_id=""), "campos vazios"),
        (lambda linhas: linhas[0].update(corretiva="talvez"), "esperado"),
        (lambda linhas: linhas[1].update(release_id="0-0"), "releases duplicadas"),
        (lambda linhas: linhas[1].update(tipo_projeto="outro"), "varia entre releases"),
    ],
)
def test_validador_rejeita_problemas_estruturais(alterar, mensagem):
    linhas = linhas_validas()
    alterar(linhas)
    with pytest.raises(ValueError, match=mensagem):
        validar_rotulos(linhas, 2, 2)


def test_validador_rejeita_coluna_ausente():
    linhas = linhas_validas()
    del linhas[0]["releases_sao_entregas"]
    with pytest.raises(ValueError, match="colunas ausentes"):
        validar_rotulos(linhas, 2, 2)


def test_revisao_humana_pode_ser_exigida():
    linhas = linhas_validas()
    linhas[0]["revisao_confirmada"] = "nao"
    with pytest.raises(ValueError, match="revisao_confirmada deve ser 'sim'"):
        validar_rotulos(linhas, 2, 2, exigir_revisao=True)


def test_revisao_exigida_rejeita_identificacao_ausente():
    linhas = linhas_validas()
    linhas[0]["revisado_por"] = ""
    with pytest.raises(ValueError, match="campos vazios: revisado_por"):
        validar_rotulos(linhas, 2, 2, exigir_revisao=True)
