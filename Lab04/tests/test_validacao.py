import pytest

from experimento.dados import salvar_json, sha256
from experimento.validacao import validar_coleta, validar_hashes


def test_recusa_coleta_incompleta(tmp_path):
    salvar_json(tmp_path / "manifesto.json", {"status": "incompleto"})
    with pytest.raises(ValueError, match="incompleta"):
        validar_coleta(tmp_path)


def test_detecta_alteracao_de_artefato(tmp_path):
    path = tmp_path / "dados.csv"
    path.write_text("original", encoding="utf-8")
    hashes = {"dados.csv": sha256(path)}
    validar_hashes(tmp_path, hashes)
    path.write_text("modificado", encoding="utf-8")
    with pytest.raises(ValueError, match="modificado"):
        validar_hashes(tmp_path, hashes)
