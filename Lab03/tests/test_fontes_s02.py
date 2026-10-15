import pytest
from zipfile import ZipFile

from pipeline.sprint2 import sha256
from scripts.fontes_s02 import empacotar, fontes_esperadas, restaurar, verificar


def test_fontes_empacotadas_restauram_bytes_sem_cache_e_nao_sobrescrevem(tmp_path):
    dados = tmp_path / "dados"
    dados.mkdir()
    (dados / "releases.csv").write_bytes(b"id,body\r\n1,nota\r\n")
    (dados / "token.env").write_text("nao incluir")
    manifesto = {"fontes_sha256": {"releases.csv": sha256(dados / "releases.csv")}, "fontes_repos_sha256": {}}
    pacote = tmp_path / "fontes.zip"
    empacotar(manifesto, dados, pacote)
    assert verificar(manifesto, pacote) == 1
    destino = tmp_path / "restaurado"
    restaurar(manifesto, pacote, destino)
    restaurar(manifesto, pacote, destino)
    assert (destino / "releases.csv").read_bytes() == (dados / "releases.csv").read_bytes()
    assert not (destino / "token.env").exists()
    (destino / "releases.csv").write_text("preservar")
    with pytest.raises(ValueError, match="não sobrescreva"):
        restaurar(manifesto, pacote, destino)


def test_pacote_adulterado_ou_com_extra_e_recusado(tmp_path):
    pacote = tmp_path / "malformado.zip"
    with ZipFile(pacote, "w") as arquivo:
        arquivo.writestr("releases.csv", "nota")
    manifesto = {"fontes_sha256": {"releases.csv": "outro"}, "fontes_repos_sha256": {}}
    with pytest.raises(ValueError, match="hash inválido"):
        verificar(manifesto, pacote)
    with ZipFile(pacote, "a") as arquivo:
        arquivo.writestr("extra.env", "nao extrair")
    with pytest.raises(ValueError, match="exatamente"):
        verificar(manifesto, pacote)


@pytest.mark.parametrize("nome", ["../fora.csv", "/fora.csv", "C:/fora.csv", "a\\fora.csv"])
def test_manifesto_nao_permite_escape_do_destino(nome):
    with pytest.raises(ValueError, match="inseguro"):
        fontes_esperadas({"fontes_sha256": {nome: "hash"}, "fontes_repos_sha256": {}})
