import json

import pytest

from pipeline.revisao_c import exportar_avaliacao, preparar, preparar_casos
from pipeline.sprint2 import ler_csv, salvar_csv, sha256


def test_fontes_cegas_preservam_notas_e_nao_atestam_avaliacao_humana(tmp_path):
    amostra, releases, commits = [tmp_path / nome for nome in ("sorteadas.csv", "releases.csv", "commits.csv")]
    salvar_csv(amostra, ["full_name", "release_id", "release_url", "compare_url"], [
        {"full_name": "o/r", "release_id": "1", "release_url": "https://github.com/o/r/releases/1", "compare_url": ""}])
    salvar_csv(releases, ["full_name", "id", "name", "body"], [
        {"full_name": "o/r", "id": "1", "name": "v1", "body": "Corrige falha.\nDetalhes completos."}])
    salvar_csv(commits, ["full_name", "release_id", "message"], [
        {"full_name": "o/r", "release_id": "1", "message": "Corrige regressão"}])
    saida = tmp_path / "revisao"
    casos = preparar(amostra, releases, commits, saida)
    assert casos[0]["body"] == "Corrige falha.\nDetalhes completos."
    assert casos[0]["mensagens_commits"] == ["Corrige regressão"]
    manifesto = json.loads((saida / "manifesto.json").read_text(encoding="utf-8"))
    assert manifesto["avaliador"] == "C" and not manifesto["avaliacao_humana_declarada"]
    assert not manifesto["saida_heuristica_lida"] and not manifesto["rotulos_de_outros_avaliadores_lidos"]
    assert "corretiva" not in casos[0]


def test_release_sem_fonte_nao_e_inventada(tmp_path):
    amostra, releases = tmp_path / "amostra.csv", tmp_path / "releases.csv"
    salvar_csv(amostra, ["full_name", "release_id"], [{"full_name": "o/r", "release_id": "1"}])
    salvar_csv(releases, ["full_name", "id", "body"], [])
    with pytest.raises(ValueError, match="sem notas"):
        preparar_casos(amostra, releases, None)


@pytest.fixture
def revisao(tmp_path):
    caso = {"full_name": "o/r", "release_id": "1", "tag_name": "v1", "published_at": "2026-01-01",
            "release_url": "https://github.com/o/r/releases/tag/v1", "compare_url": "", "origem_notas": "api"}
    fontes = tmp_path / "fontes_releases.json"
    fontes.write_text(json.dumps({"casos": [caso]}), encoding="utf-8")
    cabecalho = {"origem": "assistida_por_IA", "avaliacao_humana_declarada": False}
    for nome, dados in {
        "avaliacao_c.json": {**cabecalho, "fontes_sha256": sha256(fontes),
                             "releases": [[0, None, "Sem notas suficientes", "insuficiente"]]},
        "avaliacao_repos_c.json": {**cabecalho, "repositorios": [
            ["o/r", "ferramenta CLI", "sim", "Distribui binário CLI", "completa"]]},
        "manifesto.json": {"revisao_independente_definitiva": False},
    }.items():
        (tmp_path / nome).write_text(json.dumps(dados), encoding="utf-8")
    (tmp_path / "documentacao").mkdir()
    (tmp_path / "documentacao/o__r.json").write_text("{}", encoding="utf-8")
    return tmp_path


def test_exportacao_nao_preenche_ausentes_nem_declara_revisao_humana(revisao):
    resumo = exportar_avaliacao(revisao)
    linha = ler_csv(revisao / "rotulos_releases_C.csv")[0]
    assert linha["corretiva"] == "" and linha["revisao_confirmada"] == "não"
    assert linha["avaliacao_humana_declarada"] == "False"
    assert resumo["releases_examinadas"] == resumo["releases_sem_rotulo"] == 1
    assert not resumo["revisao_independente_definitiva"]


@pytest.mark.parametrize("alteracao", ["fontes", "duplicada", "origem", "ausente_vira_nao"])
def test_exportacao_recusa_fontes_trocadas_duplicadas_e_atestados_falsos(revisao, alteracao):
    arquivo = revisao / "avaliacao_c.json"
    dados = json.loads(arquivo.read_text(encoding="utf-8"))
    if alteracao == "fontes":
        dados["fontes_sha256"] = "outro"
    elif alteracao == "duplicada":
        dados["releases"] *= 2
    elif alteracao == "origem":
        dados["avaliacao_humana_declarada"] = True
    else:
        dados["releases"][0][1] = "não"
    arquivo.write_text(json.dumps(dados), encoding="utf-8")
    with pytest.raises(ValueError):
        exportar_avaliacao(revisao)
