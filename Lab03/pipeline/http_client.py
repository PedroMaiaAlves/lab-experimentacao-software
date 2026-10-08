"""Cliente HTTP da API REST do GitHub com cache, paginação e retomada.

O módulo usa apenas ``requests``; bibliotecas que encapsulam a API do GitHub não
são necessárias. As dependências de tempo e transporte podem ser injetadas para
que os testes não façam chamadas reais nem esperem pelo rate limit.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import tempfile
import time
from pathlib import Path
from typing import Any, Callable, Iterator

import requests

API = "https://api.github.com"
_PROXIMA = re.compile(r'<([^>]+)>;\s*rel="next"')


class GitHubClient:
    """Cliente mínimo usado por todos os coletores do Lab03."""

    def __init__(
        self,
        token: str,
        cache_dir: str | Path = "cache",
        *,
        session: requests.Session | None = None,
        sleep: Callable[[float], None] = time.sleep,
        now: Callable[[], float] = time.time,
        timeout: float = 30,
        max_attempts: int = 6,
    ) -> None:
        if not token:
            raise ValueError("token do GitHub não pode ser vazio")
        if max_attempts < 1:
            raise ValueError("max_attempts deve ser pelo menos 1")

        self.sessao = session or requests.Session()
        self.sessao.headers.update({
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        })
        self.cache = Path(cache_dir)
        self.cache.mkdir(parents=True, exist_ok=True)
        self._sleep = sleep
        self._now = now
        self.timeout = timeout
        self.max_attempts = max_attempts

    def _arquivo(self, url: str, params: dict[str, Any] | None) -> Path:
        bruto = url + json.dumps(params or {}, sort_keys=True, ensure_ascii=False)
        return self.cache / (hashlib.sha256(bruto.encode("utf-8")).hexdigest() + ".json")

    @staticmethod
    def _headers_minusculos(headers: Any) -> dict[str, str]:
        return {str(chave).lower(): str(valor) for chave, valor in headers.items()}

    @staticmethod
    def _salvar_atomico(arquivo: Path, conteudo: dict[str, Any]) -> None:
        """Evita deixar um JSON parcial se o processo for interrompido."""
        temporario = None
        try:
            with tempfile.NamedTemporaryFile(
                "w", encoding="utf-8", dir=arquivo.parent, delete=False
            ) as f:
                temporario = Path(f.name)
                json.dump(conteudo, f, ensure_ascii=False)
                f.flush()
                os.fsync(f.fileno())
            os.replace(temporario, arquivo)
        finally:
            if temporario is not None and temporario.exists():
                temporario.unlink()

    def _espera_rate_limit(self, headers: dict[str, str], tentativa: int) -> float:
        if headers.get("retry-after"):
            return max(float(headers["retry-after"]), 0)
        if headers.get("x-ratelimit-remaining") == "0":
            reset = float(headers.get("x-ratelimit-reset", self._now() + 60))
            return max(reset - self._now(), 0) + 1
        # Limite secundário: o GitHub recomenda começar com pelo menos um minuto.
        return 60 * (2 ** tentativa)

    def get_json(
        self, caminho: str, params: dict[str, Any] | None = None
    ) -> tuple[Any, dict[str, str]]:
        url = caminho if caminho.startswith("http") else API + caminho
        arquivo = self._arquivo(url, params)
        if arquivo.exists():
            cache = json.loads(arquivo.read_text(encoding="utf-8"))
            return cache["data"], cache["headers"]

        resposta = None
        for tentativa in range(self.max_attempts):
            try:
                resposta = self.sessao.get(url, params=params, timeout=self.timeout)
            except (requests.ConnectionError, requests.Timeout):
                if tentativa == self.max_attempts - 1:
                    raise
                self._sleep(2 ** tentativa)
                continue

            headers = self._headers_minusculos(resposta.headers)
            if resposta.status_code in (403, 429):
                if tentativa == self.max_attempts - 1:
                    resposta.raise_for_status()
                self._sleep(self._espera_rate_limit(headers, tentativa))
                continue
            if resposta.status_code >= 500:
                if tentativa == self.max_attempts - 1:
                    resposta.raise_for_status()
                self._sleep(2 ** tentativa)
                continue

            resposta.raise_for_status()
            dados = resposta.json() if resposta.content else None
            self._salvar_atomico(arquivo, {"data": dados, "headers": headers})

            # A resposta atual já foi obtida, mas a próxima chamada não pode ocorrer
            # antes do reset quando a cota acabou exatamente nesta requisição.
            if headers.get("x-ratelimit-remaining") == "0":
                self._sleep(self._espera_rate_limit(headers, tentativa))
            return dados, headers

        # O laço sempre retorna ou levanta, mas mantém o erro explícito para type checkers.
        raise RuntimeError("requisição terminou sem resposta")

    def paginate(
        self,
        caminho: str,
        params: dict[str, Any] | None = None,
        chave: str | None = None,
    ) -> Iterator[Any]:
        parametros = dict(params or {})
        parametros.setdefault("per_page", 100)
        url: str | None = caminho
        while url:
            dados, headers = self.get_json(url, parametros)
            itens = dados[chave] if chave else dados
            yield from itens
            proxima = _PROXIMA.search(headers.get("link", ""))
            url = proxima.group(1) if proxima else None
            parametros = None
