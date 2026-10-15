from copy import deepcopy
import json

import pytest
import requests

import pipeline.sprint2 as sprint
from pipeline.config import carregar_config


@pytest.fixture
def cfg_s02(tmp_path):
    cfg = carregar_config("config_s02.yaml")
    cfg["saida"] = {"dir_dados": str(tmp_path / "s02"), "dir_cache": str(tmp_path / "cache")}
    cfg["selecao"]["meta_repositorios"] = 2
    return cfg


def estado():
    return {"proximo": 0, "repos": [], "descartes": [], "coletados": []}


def candidato(nome):
    return {"full_name": nome, "stars": "1500", "language": "Python", "default_branch": "main",
            "created_at": "2020-01-01T00:00:00Z", "html_url": f"https://github.com/{nome}", "consulta": "snapshot"}


def mock_selecao(monkeypatch):
    monkeypatch.setattr(sprint, "usa_actions", lambda client, nome: nome != "o/sem-actions")
    monkeypatch.setattr(sprint, "contar_releases_janela", lambda *args: 10)
    monkeypatch.setattr(sprint, "contar_runs_validos", lambda *args: 60)
    monkeypatch.setattr(sprint, "coletar_metadados", lambda client, r, cfg: {
        **{c: r[c] for c in sprint.CAMPOS_META if c in r}, "idade_dias": 1000, "contribuidores": 3})


def test_selecao_retoma_e_funil_reconcilia(cfg_s02, monkeypatch, tmp_path):
    mock_selecao(monkeypatch)
    candidatos = [candidato(n) for n in ("o/sem-actions", "o/a", "o/b")]
    checkpoint, salvos = estado(), []
    repos = sprint.selecionar(object(), cfg_s02, candidatos, checkpoint, lambda e: salvos.append(deepcopy(e)))
    assert len(repos) == 2 and checkpoint["proximo"] == 3 and len(salvos) == 3
    assert checkpoint["descartes"][0]["motivo"] == "sem_actions"
    assert sprint.selecionar(object(), cfg_s02, candidatos, checkpoint, lambda e: pytest.fail()) == repos
    sprint.salvar_funil(tmp_path, candidatos, checkpoint)
    funil = sprint.ler_csv(tmp_path / "funil.csv")
    assert [r["restaram"] for r in funil] == ["3", "3", "2", "2", "2", "2"]


@pytest.mark.parametrize("status", [403, 429, 500])
def test_erro_transitorio_nao_descarta_candidato(cfg_s02, monkeypatch, status):
    resposta = requests.Response()
    resposta.status_code = status
    def falha(*args):
        raise requests.HTTPError(response=resposta)
    monkeypatch.setattr(sprint, "usa_actions", falha)
    checkpoint = estado()
    with pytest.raises(requests.HTTPError):
        sprint.selecionar(object(), cfg_s02, [candidato("o/a")], checkpoint, lambda e: None)
    assert checkpoint == estado()


def test_404_e_contado_sem_preencher_amostra(cfg_s02, monkeypatch):
    resposta = requests.Response()
    resposta.status_code = 404
    def falha(*args):
        raise requests.HTTPError(response=resposta)
    monkeypatch.setattr(sprint, "usa_actions", falha)
    checkpoint = estado()
    with pytest.raises(RuntimeError, match="esgotados"):
        sprint.selecionar(object(), cfg_s02, [candidato("o/apagado")], checkpoint, lambda e: None)
    assert checkpoint["descartes"][0]["motivo"] == "erro_http_404"


def test_lock_impede_segunda_coleta(tmp_path):
    caminho = tmp_path / "coleta.lock"
    with sprint.exclusividade(caminho):
        with pytest.raises(RuntimeError, match="já existe"):
            with sprint.exclusividade(caminho):
                pass
    with sprint.exclusividade(caminho):
        pass


def test_checkpoint_incompativel_e_s01_nao_sao_sobrescritos(cfg_s02, tmp_path):
    dados = tmp_path / "s02"
    dados.mkdir()
    sprint.salvar_candidatos([candidato("o/a")], dados / "candidatos.csv")
    (dados / "checkpoint.json").write_text(json.dumps({"contrato": {"outro": True}}), encoding="utf-8")
    with pytest.raises(ValueError, match="checkpoint"):
        sprint.executar(object(), cfg_s02, None, tmp_path / "amostra.csv")
    cfg_s02["saida"]["dir_dados"] = "data"
    with pytest.raises(ValueError, match="separada"):
        sprint.executar(object(), cfg_s02, None, tmp_path / "amostra.csv")


def test_piloto_nao_congela_e_retomada_nao_repete_coleta(cfg_s02, monkeypatch, tmp_path):
    mock_selecao(monkeypatch)
    origem = tmp_path / "candidatos.csv"
    sprint.salvar_candidatos([candidato("o/a"), candidato("o/b")], origem)
    chamadas = []
    def coletar(client, cfg, repos):
        chamadas.append(repos[0]["full_name"])
    monkeypatch.setattr(sprint, "coletar_releases", coletar)
    monkeypatch.setattr(sprint, "coletar_commits", lambda *args: None)
    monkeypatch.setattr(sprint, "coletar_runs", lambda *args: None)
    monkeypatch.setattr(sprint, "_validar_releases", lambda *args: None)
    monkeypatch.setattr(sprint, "_validar_runs", lambda *args: None)
    congelada = tmp_path / "amostra.csv"
    primeiro = sprint.executar(object(), cfg_s02, origem, congelada, limite=1)
    segundo = sprint.executar(object(), cfg_s02, origem, congelada, limite=1)
    assert primeiro["coletados"] == ["o/a"] and segundo["coletados"] == ["o/a", "o/b"]
    assert chamadas == ["o/a", "o/b"] and not congelada.exists()


def test_congelamento_recusa_menos_de_300(cfg_s02, tmp_path):
    with pytest.raises(ValueError, match="300"):
        sprint.congelar(cfg_s02, [{}] * 299, tmp_path / "amostra.csv")


def test_congelamento_300_e_idempotente_sem_sobrescrever(cfg_s02, monkeypatch, tmp_path):
    repos = [{c: f"{c}-{i}" for c in sprint.CAMPOS_META} for i in range(300)]
    dados = tmp_path / "s02"
    dados.mkdir()
    for nome in sprint.CSVS_OBRIGATORIOS:
        sprint.salvar_csv(dados / nome, sprint.CAMPOS_META, repos)
    monkeypatch.setattr(sprint, "validar_artefatos_s01", lambda *args: None)
    monkeypatch.setattr(sprint, "fontes_repo", lambda dados, nome: {"teste": nome})
    destino = tmp_path / "amostra.csv"
    original = sprint.congelar(cfg_s02, repos, destino)
    assert original == sprint.congelar(cfg_s02, repos, destino)
    assert len(sprint.ler_csv(destino)) == 300
    destino.write_text("full_name\no/trocado\n", encoding="utf-8")
    with pytest.raises(ValueError, match="sobrescrita"):
        sprint.congelar(cfg_s02, repos, destino)


@pytest.mark.parametrize("consenso", [None, "consenso-validado.csv"])
def test_cli_encaminha_fechamento_sem_reutilizar_consenso_legado(monkeypatch, tmp_path, consenso):
    import pipeline.observabilidade_s02 as observabilidade
    import validacao.fechamento_s02 as fechamento
    monkeypatch.setenv("GITHUB_TOKEN", "token-fixture-offline")
    monkeypatch.setattr(sprint, "GitHubClient", lambda *args, **kwargs: object())
    monkeypatch.setattr(observabilidade, "observar_http", lambda *args: None)
    amostra = tmp_path / "amostra.csv"
    monkeypatch.setattr(sprint, "executar", lambda *args: amostra.write_text("fixture", encoding="utf-8"))
    chamadas = []
    monkeypatch.setattr(fechamento, "main", lambda args: chamadas.append(args))
    args = ["--congelada", str(amostra), "--ouro", "ouro-definitivo"]
    if consenso:
        args.extend(["--consenso", consenso])
    sprint.main(args)
    assert len(chamadas) == 1 and "ouro-definitivo" in chamadas[0]
    assert ("--consenso" in chamadas[0]) == bool(consenso)
    assert "data/amostra_ouro/consenso_repos.csv" not in chamadas[0]
