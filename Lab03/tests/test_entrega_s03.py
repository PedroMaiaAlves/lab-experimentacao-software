import hashlib
import json
from pathlib import Path

import pandas as pd
from pandas.testing import assert_frame_equal
from pypdf import PdfWriter
import pytest

from analises.sprint3_c import executar
from validacao.dicionario import verificar
from validacao.entrega_s03 import conferir_manifesto, conferir_pdf

BASE = Path(__file__).resolve().parents[1]


@pytest.mark.parametrize("alvo", [None, "artefato", "codigo", "fonte"])
def test_manifesto_detecta_alteracoes_depois_da_geracao(tmp_path, alvo):
    arquivos = {"artefato": tmp_path / "results/s03_c/exemplo.csv",
                "codigo": tmp_path / "analises/exemplo.py", "fonte": tmp_path / "data/dataset.csv"}
    for p in [*arquivos.values(), tmp_path / "data/amostra_final.csv"]:
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(b"x\n")
    sha = hashlib.sha256(b"x\n").hexdigest()
    m = {"artefatos_sha256": {"exemplo.csv": sha}, "codigo_sha256": {"analises/exemplo.py": sha},
         "origens": {"dataset_sha256": sha, "amostra_sha256": sha}}
    (tmp_path / "results/s03_c/manifesto.json").write_text(json.dumps(m), encoding="utf-8")
    if alvo:
        arquivos[alvo].write_bytes(b"alterado\n")
        with pytest.raises(ValueError):
            conferir_manifesto("c", tmp_path)
    else:
        assert conferir_manifesto("c", tmp_path) == m


def test_artigo_final_cobre_as_rqs_e_respeita_o_limite():
    assert 1 <= conferir_pdf(BASE / "docs/artigo/artigo_final.pdf") <= 10


def test_artigo_com_onze_paginas_e_rejeitado(tmp_path):
    escritor = PdfWriter()
    for _ in range(11):
        escritor.add_blank_page(width=595, height=842)
    destino = tmp_path / "excesso.pdf"
    escritor.write(destino)
    with pytest.raises(ValueError, match="10 páginas"):
        conferir_pdf(destino)


def test_dicionario_c_cobre_todas_as_colunas():
    assert verificar(BASE / "docs/dicionario_s03_c.md", BASE / "results/s03_c") == ([], {}, {})


def test_analises_c_reproduzem_as_treze_tabelas_publicadas(tmp_path):
    tabelas = executar(saida=tmp_path)
    assert len(tabelas) == 13
    for nome in tabelas:
        assert_frame_equal(pd.read_csv(tmp_path / f"{nome}.csv"),
                           pd.read_csv(BASE / "results/s03_c" / f"{nome}.csv"), check_exact=True)
