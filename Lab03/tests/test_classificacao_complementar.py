import csv
import json
from pathlib import Path
import shutil
import subprocess

import pytest

from scripts.gerar_classificacao_complementar import main as gerar_sugestoes


@pytest.fixture
def snapshot(tmp_path):
    caminho = tmp_path / "snapshot.json"
    registros = [{"full_name": f"org/repo{i}", "description": "A library for tests", "topics": [],
                  "homepage": ""} for i in range(240)]
    caminho.write_text(json.dumps(registros), encoding="utf-8")
    return caminho


def test_gerador_separa_sugestoes_de_avaliacoes_humanas(snapshot, tmp_path):
    saida = tmp_path / "sugestoes"
    assert gerar_sugestoes(["--entrada", str(snapshot), "--saida", str(saida)]) == 0
    for lote in "ABC":
        with (saida / f"tipos_{lote}.csv").open(encoding="utf-8", newline="") as arquivo:
            linhas = list(csv.DictReader(arquivo))
        assert len(linhas) == 80
        assert all(r["tipo_sugerido"] == "biblioteca/framework" and r["justificativa_sugerida"] for r in linhas)
        assert all(not r[c] for r in linhas for c in ("tipo_projeto", "justificativa", "avaliador", "origem", "data_avaliacao"))


def test_gerador_nao_sobrescreve_pasta_existente(snapshot, tmp_path):
    saida = tmp_path / "sugestoes"
    saida.mkdir()
    arquivo = saida / "tipos_A.csv"
    arquivo.write_bytes(b"revisao preservada")
    with pytest.raises(FileExistsError, match="pasta nova"):
        gerar_sugestoes(["--entrada", str(snapshot), "--saida", str(saida)])
    assert arquivo.read_bytes() == b"revisao preservada"


def test_gerador_recusa_destino_final(snapshot):
    finais = Path(__file__).parents[1] / "data/classificacao_complementar"
    with pytest.raises(ValueError, match="classificações finais"):
        gerar_sugestoes(["--entrada", str(snapshot), "--saida", str(finais / "sugestoes")])


@pytest.mark.parametrize("nome", ["tipos_A.csv", "tipos_B.csv", "tipos_C.csv"])
def test_git_preserva_bytes_dos_csvs_complementares(tmp_path, nome):
    if not shutil.which("git"):
        pytest.skip("Git indisponível")
    subprocess.run(["git", "init", "-q", str(tmp_path)], check=True)
    shutil.copyfile(Path(__file__).parents[2] / ".gitattributes", tmp_path / ".gitattributes")
    relativo = f"Lab03/data/classificacao_complementar/{nome}"
    caminho = tmp_path / relativo
    caminho.parent.mkdir(parents=True)
    caminho.write_bytes(b"nome,tipo\r\norg/repo,biblioteca\r\n")
    def hash_git(*args):
        return subprocess.check_output(["git", "-c", "core.autocrlf=true", "hash-object", *args], cwd=tmp_path)
    assert hash_git("--no-filters", relativo) == hash_git(f"--path={relativo}", relativo)
