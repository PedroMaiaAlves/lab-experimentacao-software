import csv
import json

import pytest
import requests

from pipeline.__main__ import GitHubClient, executar_etapas_de_coleta
from pipeline.coleta_commits import coletar_commits
from tests.fakes import ClienteFalso
from tests.test_coleta_releases import CFG, erro_http, release


def commit(sha="abc", data="2026-03-02T00:00:00Z"):
    return {"sha": sha, "commit": {"author": {"date": data},
                                   "committer": {"date": "2026-03-14T00:00:00Z"}}}


def test_compara_com_anterior_fora_da_janela_e_usa_author_date():
    historico = [release(2), release(1, "2025-09-01T00:00:00Z"), release(3, draft=True),
                 release(4, prerelease=True)]
    cli = ClienteFalso({"/repos/o/r/compare/v1...v2": {"commits": [commit()]}})
    resultado = coletar_commits(cli, "o/r", historico, CFG)
    assert len(resultado) == 1 and resultado[0]["previous_tag_name"] == "v1"
    assert resultado[0]["commits"] == [{"sha": "abc", "author_date": "2026-03-02T00:00:00Z"}]


def test_primeira_release_sem_anterior_e_comparacao_vazia():
    cli = ClienteFalso({"/repos/o/r/compare/v1...v2": {"commits": []}})
    resultado = coletar_commits(cli, "o/r", [release(1), release(2)], CFG)
    assert [r["status"] for r in resultado] == ["sem_anterior", "ok"]
    assert all(r["commits"] == [] for r in resultado)
    assert len(cli.chamadas) == 1


def test_repositorio_com_uma_release_nao_chama_compare():
    cli = ClienteFalso({})
    assert coletar_commits(cli, "o/r", [release(1)], CFG)[0]["status"] == "sem_anterior"
    assert cli.chamadas == []


def test_compare_pagina_mais_de_250_commits_sem_duplicatas(tmp_path, monkeypatch):
    client = GitHubClient("token-falso", tmp_path / "cache")
    caminho = "/repos/o/r/compare/v1...v2"
    urls = [caminho, "https://api.github.com/pagina2", "https://api.github.com/pagina3"]
    respostas = {
        urls[0]: ({"commits": [commit(str(i)) for i in range(100)]}, {"link": f'<{urls[1]}>; rel="next"'}),
        urls[1]: ({"commits": [commit(str(i)) for i in range(99, 200)]}, {"link": f'<{urls[2]}>; rel="next"'}),
        urls[2]: ({"commits": [commit(str(i)) for i in range(200, 301)]}, {}),
    }
    chamadas = []
    def get_json(url, params=None):
        chamadas.append((url, params))
        return respostas[url]
    monkeypatch.setattr(client, "get_json", get_json)
    resultado = coletar_commits(client, "o/r", [release(1), release(2)], CFG)
    assert len(resultado[1]["commits"]) == 301
    assert chamadas == [(caminho, {"per_page": 100}), (urls[1], None), (urls[2], None)]


def test_tags_com_barras_e_mais_sao_codificadas():
    anterior, atual = release(1), release(2)
    anterior["tag_name"], atual["tag_name"] = "serie/v1", "serie/v2+patch"
    cli = ClienteFalso({"/repos/o/r/compare/serie%2Fv1...serie%2Fv2%2Bpatch": {"commits": []}})
    assert coletar_commits(cli, "o/r", [anterior, atual], CFG)[1]["status"] == "ok"


def test_404_no_meio_da_paginacao_descarta_commits_parciais():
    class ClienteInterrompido:
        def paginate(self, caminho, params=None, chave=None):
            yield commit()
            raise erro_http(404)
    resultado = coletar_commits(ClienteInterrompido(), "o/r", [release(1), release(2)], CFG)
    assert resultado[1]["status"] == "erro_404" and resultado[1]["commits"] == []


def test_outros_erros_http_propagam():
    def falha(params):
        raise erro_http(403)
    cli = ClienteFalso({"/repos/o/r/compare/v1...v2": falha})
    with pytest.raises(requests.HTTPError):
        coletar_commits(cli, "o/r", [release(1), release(2)], CFG)


def ler_csv(caminho):
    with caminho.open(newline="", encoding="utf-8") as arquivo:
        return list(csv.DictReader(arquivo))


def test_etapas_integradas_com_100_repositorios_simulados(tmp_path):
    repos = [{"full_name": f"grupo/repo{i}"} for i in range(100)]
    rotas = {}
    for repo in repos:
        nome = repo["full_name"]
        rotas[f"/repos/{nome}/releases"] = [release(2), release(1, "2025-09-01T00:00:00Z")]
        rotas[f"/repos/{nome}/tags"] = [{"name": "v2", "commit": {"sha": "abc"}}]
        rotas[f"/repos/{nome}/commits/abc"] = commit()
        rotas[f"/repos/{nome}/compare/v1...v2"] = {
            "commits": [commit(str(dia), f"2026-03-{dia:02d}T00:00:00Z") for dia in (2, 10, 14)]}
    cfg = {**CFG, "saida": {"dir_dados": str(tmp_path)},
           "etapas_coleta": ["pipeline.coleta_releases", "pipeline.coleta_commits"]}
    executar_etapas_de_coleta(ClienteFalso(rotas), cfg, repos)
    assert len(ler_csv(tmp_path / "releases.csv")) == 200
    assert len(ler_csv(tmp_path / "tags.csv")) == 100
    assert len(ler_csv(tmp_path / "commits_entre_releases.csv")) == 300
    comparacoes = ler_csv(tmp_path / "comparacoes_releases.csv")
    assert len(comparacoes) == 100 and all(c["commits_count"] == "3" for c in comparacoes)
    metricas = ler_csv(tmp_path / "lead_time.csv")
    assert len(metricas) == 100
    assert all(float(m["lead_time_a_horas"]) == 312 and float(m["lead_time_b_horas"]) == 120
               for m in metricas)


def test_contagens_de_404_e_primeira_release_nao_viram_zero(tmp_path):
    def ausente(params):
        raise erro_http(404)
    cli = ClienteFalso({"/repos/o/r/releases": [release(1), release(2)], "/repos/o/r/tags": [],
                        "/repos/o/r/compare/v1...v2": ausente})
    cfg = {**CFG, "saida": {"dir_dados": str(tmp_path)},
           "etapas_coleta": ["pipeline.coleta_releases", "pipeline.coleta_commits"]}
    executar_etapas_de_coleta(cli, cfg, [{"full_name": "o/r"}])
    metricas = ler_csv(tmp_path / "lead_time.csv")[0]
    assert metricas["releases_sem_anterior"] == metricas["releases_erro_404"] == "1"
    assert metricas["lead_time_a_horas"] == metricas["lead_time_b_horas"] == ""
    assert ler_csv(tmp_path / "commits_entre_releases.csv") == []


def test_retomada_recria_csvs_sem_repetir_chamadas_http(tmp_path, monkeypatch):
    client = GitHubClient("token-falso", tmp_path / "cache")
    rotas = {"/repos/o/r/releases": [release(2), release(1, "2025-09-01T00:00:00Z")],
             "/repos/o/r/tags": [{"name": "v2", "commit": {"sha": "abc"}}],
             "/repos/o/r/commits/abc": commit(),
             "/repos/o/r/compare/v1...v2": {"commits": [commit()]}}
    chamadas = []
    def get(url, params=None, timeout=None):
        chamadas.append(url)
        resposta = requests.Response()
        resposta.status_code = 200
        resposta._content = json.dumps(rotas[url.removeprefix("https://api.github.com")]).encode()
        return resposta
    monkeypatch.setattr(requests.Session, "get", lambda sessao, url, params=None, timeout=None:
                        get(url, params, timeout))
    cfg = {**CFG, "saida": {"dir_dados": str(tmp_path)},
           "etapas_coleta": ["pipeline.coleta_releases", "pipeline.coleta_commits"]}
    repos = [{"full_name": "o/r"}]
    executar_etapas_de_coleta(client, cfg, repos)
    primeira_saida = (tmp_path / "lead_time.csv").read_bytes()
    executar_etapas_de_coleta(GitHubClient("token-falso", tmp_path / "cache"), cfg, repos)
    assert len(chamadas) == 4
    assert (tmp_path / "lead_time.csv").read_bytes() == primeira_saida
