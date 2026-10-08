import csv
from datetime import date

import pytest
import requests

from pipeline.coleta_releases import coletar, coletar_releases, coletar_tags, filtrar_releases
from tests.fakes import ClienteFalso

CFG = {"janela_inicio": date(2025, 10, 1), "janela_fim": date(2026, 9, 30)}


def release(numero, data="2026-03-15T00:00:00Z", draft=False, prerelease=False):
    return {"id": numero, "tag_name": f"v{numero}", "published_at": data,
            "draft": draft, "prerelease": prerelease, "target_commitish": "main",
            "name": f"Versão {numero}", "body": "Correção, teste\nsegunda linha",
            "html_url": f"https://github.com/o/r/releases/tag/v{numero}"}


def erro_http(status):
    resposta = requests.Response()
    resposta.status_code = status
    return requests.HTTPError(response=resposta)


def test_filtro_separado_inclui_limites_e_preserva_prereleases():
    releases = [release(1, "2025-10-01T00:00:00Z"), release(2, "2026-09-30T23:59:59Z"),
                release(3, "2025-09-30T23:59:59Z"), release(4, draft=True),
                release(5, prerelease=True), release(6, None)]
    assert [r["id"] for r in filtrar_releases(releases, CFG)] == [1, 2]
    assert [r["id"] for r in filtrar_releases(releases, CFG, True)] == [1, 2, 5]
    assert len(releases) == 6 and releases[4]["prerelease"]


def test_coleta_preserva_historico_draft_e_pre_sem_duplicar_id():
    anterior = release(1, "2025-01-01T00:00:00Z")
    cli = ClienteFalso({"/repos/o/r/releases": [anterior, release(2, draft=True),
                                                release(3, prerelease=True), anterior]})
    assert [r["id"] for r in coletar_releases(cli, "o/r")] == [1, 2, 3]
    assert cli.chamadas == [("/repos/o/r/releases", {"per_page": 100})]


def test_tags_usam_data_do_commit_e_reutilizam_sha():
    cli = ClienteFalso({"/repos/o/r/tags": [{"name": nome, "commit": {"sha": "abc"}}
                                           for nome in ("v1", "v2")],
                        "/repos/o/r/commits/abc": {"commit": {"author": {"date": "2025-12-01T12:00:00Z"},
                                                            "committer": {"date": "2026-01-01T00:00:00Z"}}}})
    tags = list(coletar_tags(cli, "o/r"))
    assert all(t["commit_author_date"] == "2025-12-01T12:00:00Z" for t in tags)
    assert sum(caminho.endswith("/abc") for caminho, _ in cli.chamadas) == 1


def test_tag_apagada_tem_status_e_data_ausente():
    def ausente(params):
        raise erro_http(404)
    cli = ClienteFalso({"/repos/o/r/tags": [{"name": "v1", "commit": {"sha": "abc"}}],
                        "/repos/o/r/commits/abc": ausente})
    tag = list(coletar_tags(cli, "o/r"))[0]
    assert tag["status"] == "erro_404" and tag["commit_author_date"] is None


def test_erro_diferente_de_404_nao_e_ocultado():
    def indisponivel(params):
        raise erro_http(503)
    cli = ClienteFalso({"/repos/o/r/tags": [{"name": "v1", "commit": {"sha": "abc"}}],
                        "/repos/o/r/commits/abc": indisponivel})
    with pytest.raises(requests.HTTPError):
        list(coletar_tags(cli, "o/r"))


def test_saida_preserva_textos_flags_e_calcula_frequencia(tmp_path):
    releases = [release(1), release(2, prerelease=True), release(3, draft=True)]
    cli = ClienteFalso({"/repos/o/r/releases": releases, "/repos/o/r/tags": []})
    coletar(cli, {**CFG, "saida": {"dir_dados": str(tmp_path)}}, [{"full_name": "o/r"}])
    with (tmp_path / "releases.csv").open(newline="", encoding="utf-8") as arquivo:
        linhas = list(csv.DictReader(arquivo))
    assert len(linhas) == 3 and linhas[0]["body"] == releases[0]["body"]
    assert linhas[1]["prerelease"] == "True" and linhas[2]["draft"] == "True"
    with (tmp_path / "deployment_frequency.csv").open(newline="", encoding="utf-8") as arquivo:
        frequencia = next(csv.DictReader(arquivo))
    assert frequencia["releases_principais"] == "1"
    assert float(frequencia["deployment_frequency"]) == pytest.approx(7 / 365)
