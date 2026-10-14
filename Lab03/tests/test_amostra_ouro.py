from datetime import date

import pandas as pd
import pytest

from pipeline.amostra_ouro import (
    CAMPOS_ROTULO,
    SEMENTE_RELEASES,
    SEMENTE_REPOSITORIOS,
    gerar_amostra_ouro,
    montar_linha_rotulo,
    salvar_planilhas,
    sortear_releases_do_repositorio,
    sortear_repositorios,
)


CFG = {"janela_inicio": date(2025, 10, 1), "janela_fim": date(2026, 9, 30)}


def _populacao(n=80):
    return pd.DataFrame({"full_name": [f"org/repo{i:03d}" for i in range(n)]})


def _releases_repo(nome, n=8, prerelease=False, draft=False):
    linhas = []
    for i in range(n):
        linhas.append({
            "full_name": nome,
            "id": hash((nome, i)) % 10_000_000,
            "tag_name": f"v1.{i}.0",
            "html_url": f"https://github.com/{nome}/releases/tag/v1.{i}.0",
            "published_at": f"2026-01-{i + 1:02d}T12:00:00Z",
            "draft": draft,
            "prerelease": prerelease,
        })
    return pd.DataFrame(linhas)


def test_sorteio_de_repositorios_e_reprodutivel():
    pop = _populacao()
    a = sortear_repositorios(pop, n=60, semente=SEMENTE_REPOSITORIOS)
    b = sortear_repositorios(pop, n=60, semente=SEMENTE_REPOSITORIOS)
    assert len(a) == 60
    assert list(a["full_name"]) == list(b["full_name"])
    outra = sortear_repositorios(pop, n=60, semente=0)
    assert list(a["full_name"]) != list(outra["full_name"])


def test_populacao_menor_que_60_falha():
    with pytest.raises(ValueError, match="insuficiente"):
        sortear_repositorios(_populacao(10), n=60)


def test_sorteio_de_releases_reprodutivel_e_ordenado_por_data():
    elegiveis = _releases_repo("org/repo000", n=10)
    a = sortear_releases_do_repositorio(elegiveis, "org/repo000", n=5, semente=SEMENTE_RELEASES)
    b = sortear_releases_do_repositorio(elegiveis, "org/repo000", n=5, semente=SEMENTE_RELEASES)
    assert len(a) == 5
    assert list(a["tag_name"]) == list(b["tag_name"])
    assert list(a["published_at"]) == sorted(a["published_at"])


def test_repo_sem_cinco_releases_elegiveis_falha():
    elegiveis = _releases_repo("org/repo000", n=3)
    with pytest.raises(ValueError, match="elegíveis"):
        sortear_releases_do_repositorio(elegiveis, "org/repo000", n=5)


def test_planilha_tem_links_e_nao_tem_heuristica():
    releases = _releases_repo("org/x", n=5)
    linha = montar_linha_rotulo("org/x", releases)
    assert set(linha) == set(CAMPOS_ROTULO)
    assert linha["repo_html_url"] == "https://github.com/org/x"
    assert linha["tipo_projeto"] == ""
    assert linha["entregas_reais"] == ""
    assert linha["r1_html_url"].startswith("https://github.com/org/x/releases/")
    assert linha["r1_corretiva"] == ""
    assert "heuristica" not in "".join(linha).lower()


def test_gerar_e_salvar_tres_planilhas_identicas(tmp_path):
    dados = tmp_path / "data"
    dados.mkdir()
    pop = _populacao(70)
    pop.to_csv(dados / "amostra_final.csv", index=False)
    blocos = [_releases_repo(nome, n=6) for nome in pop["full_name"]]
    pd.concat(blocos, ignore_index=True).to_csv(dados / "releases.csv", index=False)

    repos, rotulos, sorteadas = gerar_amostra_ouro(dados, CFG)
    assert len(repos) == 60
    assert len(rotulos) == 60
    assert len(sorteadas) == 300
    assert list(rotulos.columns) == CAMPOS_ROTULO
    assert rotulos["tipo_projeto"].eq("").all()
    assert "heuristica" not in " ".join(rotulos.columns).lower()

    salvar_planilhas(dados, rotulos, sorteadas)
    a = (dados / "rotulos" / "rotulos_A.csv").read_text(encoding="utf-8")
    b = (dados / "rotulos" / "rotulos_B.csv").read_text(encoding="utf-8")
    c = (dados / "rotulos" / "rotulos_C.csv").read_text(encoding="utf-8")
    assert a == b == c
    assert (dados / "rotulos" / "releases_sorteadas.csv").exists()


def test_usa_metadados_quando_amostra_final_nao_existe(tmp_path):
    dados = tmp_path / "data"
    dados.mkdir()
    pop = _populacao(70)
    pop.to_csv(dados / "metadados.csv", index=False)
    blocos = [_releases_repo(nome, n=6) for nome in pop["full_name"]]
    pd.concat(blocos, ignore_index=True).to_csv(dados / "releases.csv", index=False)
    repos, rotulos, _sorteadas = gerar_amostra_ouro(dados, CFG)
    assert len(repos) == 60
    assert len(rotulos) == 60
