import json
from pathlib import Path
import shutil

import numpy as np
import pandas as pd
import pytest
from scipy import stats

from analises.comum import METRICAS, ajustar_holm, carregar_dataset, descrever, sha256
from analises.rq05 import analisar as rq05, rho_vetorizado
from analises.rq06 import analisar as rq06, comparar_grupos, interpretar_delta, preparar_grupos


def exemplo(n=40):
    rng = np.random.default_rng(123)
    df = pd.DataFrame({"full_name": [f"org/r{i:03d}" for i in range(n)],
                       "deployment_frequency": np.arange(1, n+1)/7,
                       "cfr_a": rng.uniform(0, 1, n), "cfr_b": rng.uniform(0, 1, n),
                       "contribuidores": np.arange(1, n+1), "language": ["Python"]*(n//2)+["Go"]*(n-n//2),
                       "tipo_projeto": ["biblioteca/framework"]*(n//2)+["ferramenta CLI"]*(n-n//2),
                       "releases_sem_evidencia_textual": 0, "episodios_total": 1})
    for campo in ("lead_time_a_horas", "lead_time_b_horas", "tempo_recuperacao_horas"):
        df[campo] = np.arange(1, n+1)
    return df


def test_spearman_empates_e_vetorizacao():
    x, y = np.array([1, 2, 2, 3]), np.array([4, 1, 1, 2])
    assert rho_vetorizado(x, y) == pytest.approx(-1/3)
    assert rho_vetorizado(np.stack([x, x]), np.stack([y, -y])).tolist() == pytest.approx([-1/3, 1/3])


def test_holm_familia_unica_com_indefinidos():
    r = ajustar_holm(pd.DataFrame({"p": [.04, np.nan, .01, .03]}))
    assert r.p_holm.dropna().tolist() == pytest.approx([.06, .03, .06])
    assert r.p_holm_familia_n.tolist() == [3]*4
    assert np.isnan(r.p_holm[1])


def test_quartis_descritivos_lineares_e_ausencia():
    assert descrever([1, 2, 3, 4, np.nan]) == dict(n=4, mediana=2.5, q1=1.75, q3=3.25, iqr=1.5)
    assert descrever([])["n"] == 0


def test_rq05_preserva_zero_e_exclui_so_pares_necessarios():
    df = exemplo()
    df.loc[0, "cfr_a"] = 0
    df.loc[1, "cfr_b"] = np.nan
    df.loc[1, "releases_sem_evidencia_textual"] = 1
    r = rq05(df, reamostragens=199)
    a, b = r["rq05_correlacoes"].iloc[0], r["rq05_correlacoes"].iloc[1]
    assert a["n"] == 40 and b["n"] == 39
    assert a.rho == pytest.approx(stats.spearmanr(df.deployment_frequency, df.cfr_a).statistic)
    assert r["exclusoes"].motivo.tolist() == ["evidencia_textual_insuficiente"]
    assert a.status_ic == b.status_ic == "ok"
    assert -1 <= a.ic95_inferior <= a.ic95_superior <= 1
    # Saída preserva cada projeto no leave-one-out e calcula a influência certa.
    primeira = r["rq05_influencia"].iloc[0]
    esperado = stats.spearmanr(df.deployment_frequency.iloc[1:], df.cfr_a.iloc[1:]).statistic
    assert primeira.rho_sem_repo == pytest.approx(esperado)


def test_rq05_reproduzivel_independente_da_ordem():
    df = exemplo()
    a = rq05(df, semente=42, reamostragens=199)
    b = rq05(df.sample(frac=1, random_state=8), semente=42, reamostragens=199)
    for nome in a:
        pd.testing.assert_frame_equal(a[nome], b[nome])


def test_rq05_constantes_e_ausencias_nao_viram_resultados():
    df = exemplo()
    df["cfr_a"], df["cfr_b"] = 0, np.nan
    r = rq05(df, reamostragens=99)["rq05_correlacoes"]
    assert r.status.tolist() == ["dados_constantes", "amostra_insuficiente"]
    assert r.rho.isna().all() and r.p_permutacao_holm.isna().all()


def test_bootstrap_perfeitamente_correlacionado_tem_degeneracao_explicita():
    df = exemplo()
    df["cfr_a"] = df.deployment_frequency / df.deployment_frequency.max()
    r = rq05(df, reamostragens=99)["rq05_correlacoes"].iloc[0]
    assert r.rho == pytest.approx(1)
    assert r.status_ic in {"ok", "distribuicao_degenerada"}
    if r.status_ic != "ok":
        assert pd.isna(r.ic95_inferior)


def test_kw_epsilon_calculado_no_papel():
    r = comparar_grupos([np.arange(1, 6), np.arange(6, 11), np.arange(11, 16)])
    assert r["estatistica"] == pytest.approx(12.5)
    assert r["efeito"] == pytest.approx(12.5/14)
    assert r["tipo_efeito"] == "epsilon_quadrado"


def test_mann_whitney_cliff_sinal_e_interpretacao():
    r = comparar_grupos([np.arange(1, 6), np.arange(6, 11)])
    assert r["estatistica"] == 0 and r["efeito"] == -1
    assert r["interpretacao_efeito"] == "grande"
    assert interpretar_delta(.1469) == "desprezível"
    assert interpretar_delta(-.147) == "pequeno"
    assert interpretar_delta(.33) == "médio"
    assert interpretar_delta(.474) == "grande"


@pytest.mark.parametrize("grupos,status", [([np.arange(8)], "grupos_insuficientes"),
    ([np.arange(4), np.arange(6)], "grupo_com_menos_de_5"),
    ([np.ones(5), np.ones(5)], "dados_constantes")])
def test_rq06_diagnostica_casos_nao_estimaveis(grupos, status):
    r = comparar_grupos(grupos)
    assert r["status"] == status and np.isnan(r["p"]) and np.isnan(r["efeito"])


def test_grupos_fixados_antes_de_ausencias_e_empates_preservados():
    df = exemplo()
    df.loc[:4, "language"] = "Rust"
    df.loc[:14, "contribuidores"] = 1
    grupos, definicao = preparar_grupos(df)
    assert set(grupos.loc[:14, "contribuidores_quartil"]) == {"Q1"}
    assert set(grupos.loc[:4, "linguagem_grupo"]) == {"Outras"}
    assert definicao["linguagens_agrupadas"] == ["Rust"]
    df.loc[:9, "tempo_recuperacao_horas"] = np.nan
    depois, _ = preparar_grupos(df)
    pd.testing.assert_frame_equal(grupos, depois)


def test_18_testes_e_denominadores_por_metrica():
    df = exemplo()
    df.loc[0, "cfr_b"] = np.nan
    df.loc[0, "releases_sem_evidencia_textual"] = 1
    df.loc[1, "tempo_recuperacao_horas"] = np.nan
    df.loc[1, "episodios_total"] = 0
    r = rq06(df)
    t = r["rq06_testes"]
    assert len(t) == 18 and set(t.p_holm_familia_n) == {18}
    assert set(t.loc[t.metrica == "cfr_b", "n"]) == {39}
    assert set(t.loc[t.metrica == "deployment_frequency", "n"]) == {40}
    assert len(r["exclusoes"]) == 6
    assert set(r["exclusoes"].motivo) == {"evidencia_textual_insuficiente", "sem_episodios"}


@pytest.fixture
def entrada(tmp_path):
    fonte = Path(__file__).parents[1] / "data"
    for nome in ("dataset.csv", "dataset.manifest.json", "amostra_final.csv", "amostra_final.manifest.json"):
        shutil.copyfile(fonte / nome, tmp_path / nome)
    return tmp_path / "dataset.csv"


def atestar(caminho):
    manifesto = caminho.with_suffix(".manifest.json")
    m = json.loads(manifesto.read_text(encoding="utf-8"))
    m["dataset_sha256"] = sha256(caminho)
    manifesto.write_text(json.dumps(m), encoding="utf-8")


def test_dataset_real_e_cobertura(entrada):
    df, m = carregar_dataset(entrada)
    assert len(df) == 300 and m["heuristica"]["versao"] == "v3"
    assert df.cfr_b.isna().sum() == 11
    assert df.tempo_recuperacao_horas.isna().sum() == 22
    assert df.tipo_projeto.notna().all()


def test_hash_trocado_recusado(entrada):
    with entrada.open("a", encoding="utf-8") as f:
        f.write("\n")
    with pytest.raises(ValueError, match="hash"):
        carregar_dataset(entrada)


@pytest.mark.parametrize("campo,valor,erro", [("cfr_a", 1.5, "proporção"),
    ("lead_time_a_horas", -1, "valor inválido"), ("contribuidores", 1.5, "não inteira"),
    ("tempo_recuperacao_horas", np.inf, "valor inválido"), ("tipo_projeto", "inventado", "desconhecido"),
    ("heuristica_versao", "v0", "versão"), ("episodios_total", 99999, "episódios")])
def test_integridade_nao_substitui_validacao_de_dominio(entrada, campo, valor, erro):
    df = pd.read_csv(entrada)
    df[campo] = df[campo].astype(object)
    df.loc[0, campo] = valor
    df.to_csv(entrada, index=False)
    atestar(entrada)
    with pytest.raises(ValueError, match=erro):
        carregar_dataset(entrada)


def test_identidade_duplicada_recusada_mesmo_com_hash(entrada):
    df = pd.read_csv(entrada)
    df.loc[0, "full_name"] = df.loc[1, "full_name"]
    df.to_csv(entrada, index=False)
    atestar(entrada)
    with pytest.raises(ValueError, match="população"):
        carregar_dataset(entrada)


def test_comando_integrado_reproduz_artefatos_e_preserva_fontes(entrada, tmp_path):
    from analises.sprint3_b import executar
    antes = sha256(entrada)
    destino = tmp_path.parent / (tmp_path.name + "_resultados")
    executar(entrada, destino, reamostragens=99)
    manifesto = json.loads((destino / "manifesto.json").read_text(encoding="utf-8"))
    assert manifesto["origens"]["dataset_sha256"] == antes == sha256(entrada)
    assert pd.read_csv(destino / "rq06_testes.csv").shape[0] == 18
    assert pd.read_csv(destino / "ausencias.csv").shape[0] == 33
    assert (destino / "rq05_dispersao.pdf").stat().st_size > 1000
    for p in destino.iterdir():
        if p.suffix in {".csv", ".json", ".tex"}:
            assert b"\r\n" not in p.read_bytes()
    executar(entrada, destino, reamostragens=99)
    depois = json.loads((destino / "manifesto.json").read_text(encoding="utf-8"))
    assert depois == manifesto
    with pytest.raises(ValueError, match="separada"):
        executar(entrada, entrada.parent / "resultados", reamostragens=99)
