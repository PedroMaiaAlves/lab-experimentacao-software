"""Cliente HTTP PROVISÓRIO (para A trabalhar enquanto S01-C1 não chega).

Contrato (o mesmo que o cliente de C deve respeitar):
  get_json(caminho, params=None) -> (dados, headers)   # headers com chaves em minúsculas
  paginate(caminho, params=None, chave=None)            # gerador preguiçoso de itens
Apague este arquivo quando o pipeline/http_client.py de C for integrado.
"""
import hashlib
import json
import re
import time
from pathlib import Path

import requests

API = "https://api.github.com"
_PROXIMA = re.compile(r'<([^>]+)>;\s*rel="next"')


class GitHubClient:
    def __init__(self, token, cache_dir="cache"):
        self.sessao = requests.Session()
        self.sessao.headers.update({
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        })
        self.cache = Path(cache_dir)
        self.cache.mkdir(parents=True, exist_ok=True)

    def _arquivo(self, url, params):
        bruto = url + json.dumps(params or {}, sort_keys=True)
        return self.cache / (hashlib.sha1(bruto.encode()).hexdigest() + ".json")

    def get_json(self, caminho, params=None):
        url = caminho if caminho.startswith("http") else API + caminho
        arquivo = self._arquivo(url, params)
        if arquivo.exists():
            c = json.loads(arquivo.read_text(encoding="utf-8"))
            return c["data"], c["headers"]
        for tentativa in range(6):
            r = self.sessao.get(url, params=params, timeout=30)
            if r.status_code in (403, 429) and r.headers.get("X-RateLimit-Remaining") == "0":
                self._esperar_reset(r)
                continue
            if r.status_code >= 500:
                time.sleep(2 ** tentativa)
                continue
            r.raise_for_status()
            break
        else:
            r.raise_for_status()
        dados = r.json() if r.content else None
        headers = {k.lower(): v for k, v in r.headers.items()}
        arquivo.write_text(json.dumps({"data": dados, "headers": headers}), encoding="utf-8")
        if headers.get("x-ratelimit-remaining") == "0":
            self._esperar_reset(r)
        return dados, headers

    @staticmethod
    def _esperar_reset(r):
        reset = int(r.headers.get("X-RateLimit-Reset", time.time() + 60))
        time.sleep(max(reset - time.time(), 0) + 2)

    def paginate(self, caminho, params=None, chave=None):
        params = dict(params or {})
        params.setdefault("per_page", 100)
        url, p = caminho, params
        while url:
            dados, headers = self.get_json(url, p)
            yield from (dados[chave] if chave else dados)
            m = _PROXIMA.search(headers.get("link", ""))
            url, p = (m.group(1) if m else None), None
