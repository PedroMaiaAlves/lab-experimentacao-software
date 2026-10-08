from collections import deque

import pytest
import requests

from pipeline.http_client import GitHubClient


class RespostaFalsa:
    def __init__(self, status, dados=None, headers=None):
        self.status_code = status
        self._dados = dados
        self.headers = headers or {}
        self.content = b"json" if dados is not None else b""

    def json(self):
        return self._dados

    def raise_for_status(self):
        if self.status_code >= 400:
            raise requests.HTTPError(f"HTTP {self.status_code}", response=self)


class SessaoFalsa:
    def __init__(self, respostas):
        self.headers = {}
        self.respostas = deque(respostas)
        self.chamadas = []

    def get(self, url, params=None, timeout=None):
        self.chamadas.append((url, params, timeout))
        resposta = self.respostas.popleft()
        if isinstance(resposta, Exception):
            raise resposta
        return resposta

    def post(self, url, json=None, timeout=None):
        self.chamadas.append((url, json, timeout))
        resposta = self.respostas.popleft()
        if isinstance(resposta, Exception):
            raise resposta
        return resposta


@pytest.fixture
def fabrica_cliente(tmp_path):
    def criar(respostas, **kwargs):
        sessao = SessaoFalsa(respostas)
        esperas = []
        cliente = GitHubClient(
            "token-teste", tmp_path, session=sessao, sleep=esperas.append,
            now=lambda: 100, **kwargs
        )
        return cliente, sessao, esperas
    return criar


def test_cache_evitar_segunda_requisicao_e_distingue_parametros(fabrica_cliente):
    cliente, sessao, _ = fabrica_cliente([
        RespostaFalsa(200, {"valor": 1}),
        RespostaFalsa(200, {"valor": 2}),
    ])
    assert cliente.get_json("/x", {"page": 1})[0] == {"valor": 1}
    assert cliente.get_json("/x", {"page": 1})[0] == {"valor": 1}
    assert cliente.get_json("/x", {"page": 2})[0] == {"valor": 2}
    assert len(sessao.chamadas) == 2


def test_paginacao_segue_link_next(fabrica_cliente):
    cliente, sessao, _ = fabrica_cliente([
        RespostaFalsa(200, {"items": [1]}, {"Link": '<https://api.github.com/x?page=2>; rel="next"'}),
        RespostaFalsa(200, {"items": [2]}),
    ])
    assert list(cliente.paginate("/x", chave="items")) == [1, 2]
    assert sessao.chamadas[1][0].endswith("page=2")
    assert sessao.chamadas[1][1] is None


def test_rate_limit_primario_espera_reset(fabrica_cliente):
    cliente, _, esperas = fabrica_cliente([
        RespostaFalsa(403, {"message": "rate"}, {
            "X-RateLimit-Remaining": "0", "X-RateLimit-Reset": "110"
        }),
        RespostaFalsa(200, {"ok": True}),
    ])
    assert cliente.get_json("/x")[0] == {"ok": True}
    assert esperas == [11]


def test_retry_after_tem_prioridade(fabrica_cliente):
    cliente, _, esperas = fabrica_cliente([
        RespostaFalsa(429, {"message": "secondary"}, {"Retry-After": "7"}),
        RespostaFalsa(200, {"ok": True}),
    ])
    cliente.get_json("/x")
    assert esperas == [7]


def test_erro_5xx_e_conexao_usam_backoff(fabrica_cliente):
    cliente, _, esperas = fabrica_cliente([
        requests.ConnectionError("queda"),
        RespostaFalsa(503, {"message": "temporário"}),
        RespostaFalsa(200, {"ok": True}),
    ])
    assert cliente.get_json("/x")[0] == {"ok": True}
    assert esperas == [1, 2]


def test_erro_final_nao_e_gravado_no_cache(fabrica_cliente):
    cliente, _, _ = fabrica_cliente([RespostaFalsa(500, {})], max_attempts=1)
    with pytest.raises(requests.HTTPError):
        cliente.get_json("/x")
    assert list(cliente.cache.glob("*.json")) == []


def test_post_json_usa_cache_separado_do_get(fabrica_cliente):
    cliente, sessao, _ = fabrica_cliente([
        RespostaFalsa(200, {"metodo": "get"}),
        RespostaFalsa(200, {"metodo": "post"}),
    ])
    assert cliente.get_json("/graphql", {"q": 1})[0]["metodo"] == "get"
    payload = {"query": "query { viewer { login } }", "variables": {}}
    assert cliente.post_json("/graphql", payload)[0]["metodo"] == "post"
    assert cliente.post_json("/graphql", payload)[0]["metodo"] == "post"
    assert len(sessao.chamadas) == 2
