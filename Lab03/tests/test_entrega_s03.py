import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd
from pandas.testing import assert_frame_equal, assert_index_equal
from pypdf import PdfWriter
import pytest

from analises.sprint3_c import executar
from validacao.dicionario import verificar
from validacao.entrega_s03 import conferir_manifesto, conferir_pdf

BASE = Path(__file__).resolve().parents[1]


def conferir_reproducao(gerada, publicada):
    assert_index_equal(gerada.columns, publicada.columns)
    exatas = [c for c in gerada if not pd.api.types.is_float_dtype(gerada[c])
              or c.startswith("releases_") or c in {"release_id", "mediana_notas"}]
    assert_frame_equal(gerada[exatas], publicada[exatas], check_exact=True)
    reais = gerada.columns.difference(exatas, sort=False)
    assert_frame_equal(gerada[reais], publicada[reais], check_exact=False, rtol=1e-12, atol=0)


@pytest.fixture
def tabela_reproducao():
    return pd.DataFrame({"full_name": ["org/repo"], "release_id": [10**12],
                         "releases_falharam_cfr_b": [2.0], "p_spearman": [.2105778740472281]})


def test_arredondamento_entre_plataformas_nao_muda_o_resultado(tabela_reproducao):
    gerada = tabela_reproducao.copy()
    gerada.loc[0, "p_spearman"] = .2105778740472282
    conferir_reproducao(gerada, tabela_reproducao)


@pytest.mark.parametrize("coluna,valor", [("full_name", "org/outro"), ("release_id", 10**12 + 1),
    ("releases_falharam_cfr_b", np.nextafter(2., 3.)), ("p_spearman", .21057787)])
def test_tolerancia_nao_esconde_mudancas_reais(tabela_reproducao, coluna, valor):
    gerada = tabela_reproducao.copy()
    gerada.loc[0, coluna] = valor
    with pytest.raises(AssertionError):
        conferir_reproducao(gerada, tabela_reproducao)


def test_p_valor_muito_pequeno_nao_pode_ser_trocado_por_zero(tabela_reproducao):
    tabela_reproducao.loc[0, "p_spearman"] = 1e-37
    gerada = tabela_reproducao.copy()
    gerada.loc[0, "p_spearman"] = 0.
    with pytest.raises(AssertionError):
        conferir_reproducao(gerada, tabela_reproducao)


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
        conferir_reproducao(pd.read_csv(tmp_path / f"{nome}.csv"),
                           pd.read_csv(BASE / "results/s03_c" / f"{nome}.csv"))
