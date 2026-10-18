import hashlib
import json
from pathlib import Path
from zipfile import ZipFile

import numpy as np
import pandas as pd
import pytest

from analises.entrada import NUMERICAS, carregar_dataset, carregar_episodios
from analises.graficos_a import numero, p_formatado, sinal_tex
from analises.rq01_04 import (censura, comparar_pares, descrever, descritivas, mediana_pior_caso,
                              rank_biserial_pareado)
from analises.sprint3_a import conferir_publicado, executar

BASE = Path(__file__).resolve().parents[1]


def projetos(n=12):
    df = pd.DataFrame({"full_name": [f"org/r{i:02d}" for i in range(n)]})
    for coluna in NUMERICAS:
        df[coluna] = np.arange(1, n + 1, dtype=float)
    df["cfr_a"], df["cfr_b"] = np.linspace(.1, .2, n), np.linspace(.3, .5, n)
    df["episodios_total"], df["episodios_concluidos"], df["episodios_censurados"] = 2, 2, 0
    df["proporcao_censurados"] = 0.0
    return df


def episodios_de(df):
    return pd.DataFrame([dict(full_name=r.full_name, ordem=i, horas=float(i))
                         for _, r in df.iterrows() for i in range(1, int(r.episodios_concluidos) + 1)])


def test_quartis_lineares_ignoram_ausentes():
    assert descrever([1, 2, 3, 4, np.nan]) == dict(n=4, mediana=2.5, q1=1.75, q3=3.25, iqr=1.5,
                                                    minimo=1, maximo=4)
    assert descrever([])["n"] == 0 and np.isnan(descrever([])["mediana"])


def test_ausencias_nao_viram_zero_e_censurados_contam_a_parte():
    df = projetos()
    df.loc[0, "cfr_b"] = np.nan
    df.loc[1, ["episodios_total", "episodios_censurados", "proporcao_censurados"]] = [3, 1, 1 / 3]
    tabela = descritivas(df, episodios_de(df)).set_index("metrica")
    assert tabela.loc["cfr_b", "n"] == 11 and tabela.loc["cfr_b", "n_ausentes"] == 1
    assert tabela.loc["cfr_b", "minimo"] > 0
    episodio = tabela.loc["tempo_recuperacao_episodio_horas"]
    assert (episodio.n, episodio.n_ausentes, episodio.n_total) == (24, 1, 25)
    assert episodio.unidade_analise == "episodio"


@pytest.mark.parametrize("diferencas,esperado", [
    ([1, 2, -3], 0.0),             # W+ = 1 + 2 = W- = 3
    ([1, 2, 3, -.5], .8),          # postos 2, 3, 4 contra 1
    ([0, 1, 2], 1.0),              # diferenças nulas saem antes dos postos
    ([0, 0], np.nan)])
def test_rank_biserial_pareado_no_papel(diferencas, esperado):
    assert rank_biserial_pareado(diferencas) == pytest.approx(esperado, nan_ok=True)


def test_pares_testam_so_hipoteses_e_ajustam_por_holm():
    df = projetos()
    df["lead_time_b_horas"] = df.lead_time_a_horas / 2
    df.loc[0, "cfr_b"] = np.nan
    df.loc[1, "cfr_b"] = 0.0
    tabela = comparar_pares(df).set_index("x")
    frequencia = tabela.loc["deployment_frequency_prereleases"]
    assert frequencia.teste == "" and np.isnan(frequencia.p_holm)
    lead = tabela.loc["lead_time_a_horas"]
    assert (lead.n_x_maior, lead.n_iguais, lead.n_x_menor) == (12, 0, 0)
    assert lead.mediana_razao == pytest.approx(2) and lead.efeito_rank_biserial == pytest.approx(1)
    cfr = tabela.loc["cfr_a"]
    assert cfr.n == 11 and cfr.n_ausentes == 1
    assert np.isnan(cfr.mediana_razao)        # razão indefinida quando há CFR (b) zero
    assert cfr.efeito_rank_biserial < 0
    assert (tabela.p_holm_familia_n == 2).all()
    assert lead.p_holm >= lead.p and cfr.p_holm >= cfr.p


def test_mediana_pior_caso_coloca_censurados_no_topo():
    assert mediana_pior_caso([1, 2, 3], 0) == 2
    assert mediana_pior_caso([1, 2, 3], 1) == 2.5
    assert mediana_pior_caso([1, 2, 3], 3) == np.inf
    assert np.isnan(mediana_pior_caso([], 0))


def test_censura_por_episodio_e_por_projeto():
    df = projetos(4)
    df.loc[0, ["episodios_total", "episodios_censurados", "proporcao_censurados"]] = [4, 2, .5]
    df.loc[0, "episodios_concluidos"] = 2
    df.loc[3, ["episodios_total", "episodios_concluidos", "proporcao_censurados"]] = [0, 0, np.nan]
    df.loc[3, "tempo_recuperacao_horas"] = np.nan
    c = censura(df, episodios_de(df)).set_index("indicador").valor
    assert c.episodios_total == 8 and c.episodios_censurados == 2
    assert c.proporcao_episodios_censurados == pytest.approx(.25)
    assert c.repositorios_sem_episodios == 1 and c.repositorios_com_censura == 1
    assert c.proporcao_repositorios_com_censura == pytest.approx(1 / 3)
    assert c.mediana_episodios_horas == 1.5
    assert c.mediana_episodios_pior_caso_horas == 2.0   # 1,1,1,2,2,2 + 2 censurados no topo


def test_formatacao_brasileira_e_sinal_em_modo_matematico():
    assert numero(12345.678, 2) == "12.345,68" and numero(np.nan) == "--"
    assert p_formatado(1.118e-6) == r"$1,12\times 10^{-6}$"
    assert sinal_tex("CFR & -0,109 & 0,1--0,2 & -- & pré-releases") == \
        "CFR & $-$0,109 & 0,1--0,2 & -- & pré-releases"


def _sha(caminho):
    return hashlib.sha256(Path(caminho).read_bytes()).hexdigest()


@pytest.fixture
def fontes(tmp_path):
    """Uma amostra mínima com manifestos e runs: um episódio de 2 h e um censurado."""
    runs = [dict(workflow_id=1, conclusion=c, run_started_at=f"2025-10-01T{h:02d}:00:00Z",
                 updated_at=f"2025-10-01T{h + 1:02d}:00:00Z")
            for c, h in (("success", 0), ("failure", 1), ("success", 2), ("failure", 4))]
    bruto = json.dumps({"workflow_runs": runs}).encode()
    with ZipFile(tmp_path / "fontes_s02.zip", "w") as pacote:
        pacote.writestr("workflow_runs/org__a.json", bruto)
    pd.DataFrame({"full_name": ["org/a"]}).to_csv(tmp_path / "amostra_final.csv", index=False)
    linha = {c: 1 for c in NUMERICAS}
    linha.update(full_name="org/a", episodios_total=2, episodios_concluidos=1, episodios_censurados=1,
                 proporcao_censurados=.5, tempo_recuperacao_horas=2.0)
    pd.DataFrame([linha]).to_csv(tmp_path / "dataset.csv", index=False)
    amostra_sha = _sha(tmp_path / "amostra_final.csv")
    (tmp_path / "amostra_final.manifest.json").write_text(json.dumps({
        "amostra_sha256": amostra_sha, "janela_inicio": "2025-10-01", "janela_fim": "2026-09-30",
        "fontes_repos_sha256": {"org/a": {"workflow_runs/org__a.json": hashlib.sha256(bruto).hexdigest()}}}))
    (tmp_path / "dataset.manifest.json").write_text(json.dumps({
        "dataset_sha256": _sha(tmp_path / "dataset.csv"), "amostra_sha256": amostra_sha, "repositorios": 1}))
    return tmp_path


def test_episodios_recalculados_conferem_com_o_dataset(fontes):
    df, origens = carregar_dataset(fontes / "dataset.csv")
    episodios, _ = carregar_episodios(df, fontes / "dataset.csv")
    assert episodios.horas.tolist() == [2.0] and origens["repositorios"] == 1
    df.loc[0, "tempo_recuperacao_horas"] = 3.0
    with pytest.raises(ValueError, match="divergem"):
        carregar_episodios(df, fontes / "dataset.csv")


def test_fonte_alterada_interrompe_a_analise(fontes):
    with (fontes / "dataset.csv").open("a") as arquivo:
        arquivo.write("\n")
    with pytest.raises(ValueError, match="hash do dataset"):
        carregar_dataset(fontes / "dataset.csv")


def test_runs_alterados_interrompem_a_analise(fontes):
    df, _ = carregar_dataset(fontes / "dataset.csv")
    with ZipFile(fontes / "fontes_s02.zip", "w") as pacote:
        pacote.writestr("workflow_runs/org__a.json", b'{"workflow_runs": []}')
    with pytest.raises(ValueError, match="hash divergente"):
        carregar_episodios(df, fontes / "dataset.csv")


def test_saida_nao_pode_ficar_nos_dados(fontes):
    with pytest.raises(ValueError, match="fora da pasta"):
        executar(dataset=fontes / "dataset.csv", saida=fontes / "resultados")


def test_artefatos_publicados_reproduzem_a_partir_das_fontes(tmp_path):
    tabelas = executar(dataset=BASE / "data/dataset.csv", saida=tmp_path)
    publicados = BASE / "results/s03_a"
    for nome, tabela in tabelas.items():
        conferir_publicado(tabela, publicados / f"{nome}.csv")
    for tex in ("rq01_04_tabela.tex", "rq01_04_pareadas.tex", "numeros_a.tex"):
        assert (tmp_path / tex).read_text(encoding="utf-8") == (publicados / tex).read_text(encoding="utf-8")
    manifesto = json.loads((publicados / "manifesto.json").read_text(encoding="utf-8"))
    for nome, esperado in manifesto["artefatos_sha256"].items():
        if nome.endswith((".csv", ".tex")):
            assert _sha(publicados / nome) == esperado, nome
