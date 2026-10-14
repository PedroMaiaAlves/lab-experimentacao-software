import json

import requests

from pipeline.http_client import GitHubClient
from pipeline.observabilidade_s02 import observar_http


def test_registra_somente_contagens_e_retoma_sem_vazar_token(tmp_path, monkeypatch):
    client = GitHubClient("segredo-nao-exportar", tmp_path / "cache")
    caminho = tmp_path / "http.json"
    monkeypatch.setattr("pipeline.observabilidade_s02.time.sleep", lambda s: None)
    observar_http(client, caminho)
    resposta = requests.Response()
    resposta.status_code = 429
    for hook in client.sessao.hooks["response"]:
        hook(resposta)
    client._sleep(3)
    observar_http(GitHubClient("outro-segredo", tmp_path / "cache"), caminho)
    bruto = caminho.read_text(encoding="utf-8")
    dados = json.loads(bruto)
    assert dados["respostas_http"] == dados["esperas"] == 1
    assert dados["status"] == {"429": 1} and dados["segundos_espera_solicitados"] == 3
    assert dados["espera_ate"] is None and "segredo" not in bruto
