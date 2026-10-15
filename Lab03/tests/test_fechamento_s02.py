import json
import hashlib
from pathlib import Path

import pandas as pd
import pytest

import validacao.concordancia as concordancia
import validacao.fechamento_s02 as fechamento
from pipeline.config import carregar_config
from pipeline.sprint2 import ler_csv, salvar_csv, sha256
from validacao.fechamento_s02 import preparar_amostra


@pytest.fixture
def execucao(tmp_path):
    dados = tmp_path / "dados"
    cfg = carregar_config("config_s02.yaml")
    cfg["saida"]["dir_dados"] = str(dados)
    repos = [{"full_name": f"org/r{i:03d}", "stars": 1500} for i in range(300)]
    amostra = tmp_path / "amostra.csv"
    salvar_csv(amostra, ["full_name", "stars"], repos)
    releases = [{"full_name": r["full_name"], "id": i * 5 + k, "tag_name": f"v1.0.{k}",
                 "draft": False, "prerelease": False, "published_at": f"2026-01-{k+1:02d}T00:00:00Z",
                 "html_url": "https://github.com/" + r["full_name"], "name": "Versão", "body": "Notas"}
                for i, r in enumerate(repos) for k in range(5)]
    salvar_csv(dados / "releases.csv", list(releases[0]), releases)
    comparacoes = [{"full_name": r["full_name"], "release_id": r["id"], "previous_tag_name": "v0"}
                  for r in releases]
    salvar_csv(dados / "comparacoes_releases.csv", list(comparacoes[0]), comparacoes)
    salvar_csv(dados / "commits_entre_releases.csv", ["full_name", "release_id", "message"], [
        {"full_name": r["full_name"], "release_id": r["id"], "message": "fix: repair regression"} for r in releases])
    manifesto = {"amostra_sha256": sha256(amostra), "repositorios": 300,
                 "janela_inicio": str(cfg["janela_inicio"]), "janela_fim": str(cfg["janela_fim"]),
                 "fontes_sha256": {n: sha256(dados / n) for n in (
                     "releases.csv", "comparacoes_releases.csv", "commits_entre_releases.csv")}}
    amostra.with_suffix(".manifest.json").write_text(json.dumps(manifesto), encoding="utf-8")
    return cfg, amostra, tmp_path / "ouro"


def test_ouro_60_por_5_deriva_da_populacao_congelada_e_preserva_fontes(execucao):
    cfg, amostra, ouro = execucao
    manifesto = preparar_amostra(cfg, amostra, ouro)
    assert len(ler_csv(ouro / "repos_sorteados.csv")) == 60
    assert len(ler_csv(ouro / "releases_sorteadas.csv")) == 300
    assert manifesto["amostra_sha256"] == sha256(amostra)
    assert manifesto["semente_releases"] == manifesto["semente_repos"] == 42
    casos = json.loads((ouro / "fontes_releases.json").read_text(encoding="utf-8"))["casos"]
    assert len(casos) == 300 and all(c["body"] == "Notas" for c in casos)
    assert all("corretiva" not in c and "predicao" not in c for c in casos)
    assert preparar_amostra(cfg, amostra, ouro) == manifesto


def test_ouro_recusa_semente_alterada_e_sorteio_editado(execucao):
    cfg, amostra, ouro = execucao
    preparar_amostra(cfg, amostra, ouro)
    with pytest.raises(ValueError, match="semente diferente"):
        preparar_amostra({**cfg, "semente": 43}, amostra, ouro)
    (ouro / "releases_sorteadas.csv").write_text("alterado", encoding="utf-8")
    with pytest.raises(ValueError, match="artefato.*alterado"):
        preparar_amostra(cfg, amostra, ouro)


def test_ouro_recusa_fonte_trocada_ou_destino_nao_rastreavel(execucao):
    cfg, amostra, ouro = execucao
    ouro.mkdir()
    (ouro / "rotulos_C.xlsx").write_bytes(b"preservar")
    with pytest.raises(ValueError, match="destino.*contém arquivos"):
        preparar_amostra(cfg, amostra, ouro)
    assert (ouro / "rotulos_C.xlsx").read_bytes() == b"preservar"
    fonte = amostra.parent / "dados/releases.csv"
    fonte.write_text("alterado", encoding="utf-8")
    with pytest.raises(ValueError, match="fonte alterada"):
        preparar_amostra(cfg, amostra, ouro)


def test_ouro_nao_aceita_populacao_sem_300_qualificados(execucao):
    cfg, amostra, ouro = execucao
    arquivo = amostra.with_suffix(".manifest.json")
    manifesto = json.loads(arquivo.read_text(encoding="utf-8"))
    manifesto["repositorios"] = 100
    arquivo.write_text(json.dumps(manifesto), encoding="utf-8")
    with pytest.raises(ValueError, match="pelo menos 300"):
        preparar_amostra(cfg, amostra, ouro)


@pytest.fixture
def avaliadas(execucao, monkeypatch):
    cfg, amostra, ouro = execucao
    preparar_amostra(cfg, amostra, ouro)
    repos = pd.read_csv(ouro / "repos_sorteados.csv", dtype=str)
    repos["tipo_projeto"], repos["releases_sao_entregas"] = "outro", "sim"
    releases = pd.read_csv(ouro / "releases_sorteadas.csv", dtype=str)
    releases["corretiva"] = "sim"
    dados = {av: {"repositorios": repos.copy(), "releases": releases.copy()} for av in "ABC"}
    monkeypatch.setattr(fechamento, "validar_arquivo", lambda p: None)
    monkeypatch.setattr(fechamento, "ler_rotulos", lambda p: dados)
    monkeypatch.setattr(concordancia, "ler_rotulos", lambda p: dados)
    (ouro / "rotulos").mkdir()
    for av in "ABC":
        arquivo = ouro / "rotulos" / f"rotulos_{av}.xlsx"
        arquivo.write_bytes(f"fixture {av}".encode())
        doc = {"avaliador": av, "origem": "assistida_por_IA", "id_avaliacao": f"execucao-{av}",
               "arquivo_sha256": sha256(arquivo), "itens_sha256": sha256(ouro / "releases_sorteadas.csv"),
               "repos_sha256": sha256(ouro / "repos_sorteados.csv"), "avaliacao_concluida": True,
               "rotulos_outros_lidos": False, "saida_heuristica_lida": False}
        arquivo.with_suffix(".manifest.json").write_text(json.dumps(doc), encoding="utf-8")
    return cfg, amostra, ouro


def test_consolidacao_com_proveniencia_genera_consenso_e_f1_sem_inventar_kappa(avaliadas, tmp_path):
    cfg, amostra, ouro = avaliadas
    artigo = tmp_path / "tabelas"
    artigo.mkdir()
    resultado = fechamento.consolidar_validacao(cfg, amostra, ouro, artigo, "adjudicacao_IA")
    assert resultado["qualificada"] and resultado["metricas"]["f1"] == 1
    assert resultado["origem_rotulagem"] == "assistida_por_IA"
    manifesto = json.loads((ouro / "consenso_repos.manifest.json").read_text(encoding="utf-8"))
    assert manifesto["amostra_sha256"] == sha256(amostra)
    assert manifesto["consenso_sha256"] == sha256(ouro / "consenso_repos.csv")
    kappas = pd.read_csv(ouro / "kappa_fleiss.csv")
    assert kappas["kappa"].isna().all()
    fechamento.relatar_validacao(ouro, artigo, resultado)
    assert "indefinido" in (artigo / "validacao_s02.tex").read_text(encoding="utf-8")
    cfg["heuristica_release"]["usar_patch_semver"] = False
    with pytest.raises(ValueError, match="não sobrescreva uma avaliação"):
        fechamento.consolidar_validacao(cfg, amostra, ouro, artigo, "adjudicacao_IA")


def test_tres_copias_da_mesma_avaliacao_nao_passam_por_independentes(avaliadas):
    cfg, amostra, ouro = avaliadas
    caminho = ouro / "rotulos/rotulos_B.manifest.json"
    doc = json.loads(caminho.read_text(encoding="utf-8"))
    doc["id_avaliacao"] = "execucao-A"
    caminho.write_text(json.dumps(doc), encoding="utf-8")
    with pytest.raises(ValueError, match="independentes distintos"):
        fechamento.validar_avaliacoes(ouro)


def test_v3_vincula_implementacao_e_preserva_avaliacao_registrada(avaliadas, tmp_path):
    cfg, amostra, ouro = avaliadas
    cfg["heuristica_release"]["versao"] = "v3"
    artigo = tmp_path / "tabelas"
    artigo.mkdir()
    resultado = fechamento.consolidar_validacao(cfg, amostra, ouro, artigo, "adjudicacao_IA")
    registro = ouro / "avaliacao_v3.manifest.json"
    manifesto = json.loads(registro.read_text(encoding="utf-8"))
    assert resultado["qualificada"]
    fonte = (Path(fechamento.__file__).parents[1] / "metricas/cfr.py").read_text(encoding="utf-8")
    assert manifesto["implementacao_sha256"] == hashlib.sha256(fonte.encode("utf-8")).hexdigest()
    assert manifesto["implementacao_formato"] == "utf-8-lf"
    manifesto["implementacao_sha256"] = "outra-implementacao"
    registro.write_text(json.dumps(manifesto), encoding="utf-8")
    with pytest.raises(ValueError, match="não sobrescreva uma avaliação"):
        fechamento.consolidar_validacao(cfg, amostra, ouro, artigo, "adjudicacao_IA")


def test_planilha_editada_depois_da_declaracao_nao_e_validada(avaliadas):
    cfg, amostra, ouro = avaliadas
    (ouro / "rotulos/rotulos_C.xlsx").write_bytes(b"outra avaliacao")
    with pytest.raises(ValueError, match="proveniência inválida"):
        fechamento.validar_avaliacoes(ouro)


@pytest.mark.parametrize("modo", ["preparar", "aprovada", "f1_baixo"])
def test_cli_distingue_preparacao_de_fechamento_qualificado(execucao, monkeypatch, tmp_path, modo):
    cfg, amostra, ouro = execucao
    monkeypatch.setattr(fechamento, "carregar_config", lambda p: cfg)
    monkeypatch.setattr(fechamento, "gerar_tabelas", lambda args: None)
    monkeypatch.setattr(fechamento, "gerar_dataset", lambda *args: {
        "repositorios": 300, "amostra_sha256": sha256(amostra), "dataset_sha256": "fixture",
        "consenso_utilizado": modo != "preparar"})
    monkeypatch.setattr(fechamento, "consolidar_validacao", lambda *args: {
        "qualificada": modo == "aprovada", "consenso_concluido": True,
        "pendencias": [] if modo == "aprovada" else ["refinar heurística"]})
    args = ["--amostra", str(amostra), "--ouro", str(ouro), "--artigo", str(tmp_path / "tabelas")]
    if modo != "preparar":
        args.append("--validar-avaliacoes")
    assert fechamento.main(args) == (1 if modo == "f1_baixo" else 0)
    estado = json.loads((ouro / "fechamento.json").read_text(encoding="utf-8"))
    assert estado["concluido"] == (modo == "aprovada")
    assert estado["validacao_concluida"] == estado["concluido"]
    assert not estado["entrega_completa"]
    assert any("300 projetos sem tipo" in p for p in estado["pendencias_entrega"])
    if modo == "aprovada":
        assert fechamento.main(args[:-1]) == 0
        assert json.loads((ouro / "fechamento.json").read_text(encoding="utf-8"))["concluido"]


def test_cli_com_classificacao_complementar_fecha_entrega_completa(execucao, monkeypatch, tmp_path):
    cfg, amostra, ouro = execucao
    monkeypatch.setattr(fechamento, "carregar_config", lambda p: cfg)
    monkeypatch.setattr(fechamento, "gerar_tabelas", lambda args: None)
    monkeypatch.setattr(fechamento, "gerar_dataset", lambda *args, **kwargs: {
        "repositorios": 300, "amostra_sha256": sha256(amostra), "dataset_sha256": "fixture",
        "consenso_utilizado": True, "repositorios_sem_tipo": 0, "totais": {"cfr_b_indisponiveis": 11}})
    monkeypatch.setattr(fechamento, "consolidar_validacao", lambda *args, **kwargs: {
        "qualificada": True, "consenso_concluido": True, "pendencias": []})
    args = ["--amostra", str(amostra), "--ouro", str(ouro), "--artigo", str(tmp_path / "tabelas"),
            "--validar-avaliacoes", "--complementar", str(tmp_path / "complementar")]
    assert fechamento.main(args) == 0
    estado = json.loads((ouro / "fechamento.json").read_text(encoding="utf-8"))
    assert estado["concluido"]
    assert estado["validacao_concluida"]
    assert estado["entrega_completa"]
    assert estado["projetos_sem_tipo"] == 0
    assert estado["pendencias_entrega"] == []
