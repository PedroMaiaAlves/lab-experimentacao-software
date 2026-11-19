"""Coleta reproduzível das evidências de impacto e operação (issue #196).

Consulta a API pública do Docker Hub (pulls e última atualização das imagens) e a
página oficial do Kafka (afirmação sobre a Fortune 100), e salva um snapshot
datado em data/evidencias/. Faz poucas requisições, com 1 s entre elas.

Uso: python Lab05/evidencias.py
"""

from __future__ import annotations

import json
import re
import time
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

IMAGENS = {
    "rabbitmq": "library/rabbitmq",
    "kafka_apache": "apache/kafka",
    "kafka_confluent": "confluentinc/cp-kafka",
    "kafka_bitnami": "bitnami/kafka",
}
VERSOES_PROPOSTA = {"library/rabbitmq": "4.4.1", "apache/kafka": "4.4.0"}
URL_KAFKA = "https://kafka.apache.org/"
SAIDA = Path(__file__).resolve().parent / "data" / "evidencias"
AGENTE = {"User-Agent": "lab05-evidencias/1.0"}


def _contexto_ssl():
    """Usa o repositório de certificados do sistema (truststore), se houver."""
    try:
        import ssl

        import truststore

        return truststore.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
    except ImportError:
        return None


def _get(url: str) -> bytes:
    req = urllib.request.Request(url, headers=AGENTE)
    with urllib.request.urlopen(req, timeout=30, context=_contexto_ssl()) as resp:
        return resp.read()


def imagem(repo: str) -> dict:
    url = f"https://hub.docker.com/v2/repositories/{repo}/"
    dados = json.loads(_get(url))
    item = {
        "fonte": url,
        "pull_count": dados["pull_count"],
        "last_updated": dados["last_updated"],
    }
    if repo in VERSOES_PROPOSTA:
        tag = VERSOES_PROPOSTA[repo]
        time.sleep(1)
        tag_url = f"https://hub.docker.com/v2/repositories/{repo}/tags/{tag}"
        info = json.loads(_get(tag_url))
        item["versao_proposta"] = tag
        item["versao_publicada_em"] = info.get("last_updated")
    return item


def afirmacao_kafka() -> dict:
    html = _get(URL_KAFKA).decode("utf-8", errors="replace")
    achado = re.search(r"More than \d+% of all Fortune 100[^.<\"]*\.", html)
    setores = dict(re.findall(r"\n([A-Z][A-Za-z ]+?) (\d+ OUT OF 10)", html))
    return {
        "fonte": URL_KAFKA,
        "texto": achado.group(0) if achado else None,
        "setores_top10": setores,
    }


def main() -> Path:
    agora = datetime.now(timezone.utc)
    snapshot: dict = {"coletado_em_utc": agora.isoformat(timespec="seconds"), "imagens": {}}
    for nome, repo in IMAGENS.items():
        snapshot["imagens"][nome] = imagem(repo)
        time.sleep(1)
    snapshot["kafka_fortune100"] = afirmacao_kafka()
    kafka = [v["pull_count"] for k, v in snapshot["imagens"].items() if k.startswith("kafka")]
    snapshot["kafka_pulls_somados"] = sum(kafka)

    SAIDA.mkdir(parents=True, exist_ok=True)
    destino = SAIDA / f"impacto_{agora:%Y-%m-%d}.json"
    if destino.exists():  # não sobrescreve snapshot anterior
        destino = SAIDA / f"impacto_{agora:%Y-%m-%dT%H%M%S}.json"
    destino.write_text(json.dumps(snapshot, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"snapshot salvo em {destino}")
    for nome, item in snapshot["imagens"].items():
        print(f"  {nome:16} {item['pull_count']:>14,} pulls  (atualizada {item['last_updated'][:10]})")
    print(f"  kafka somado     {snapshot['kafka_pulls_somados']:>14,} pulls")
    print(f"  Fortune 100: {snapshot['kafka_fortune100']['texto']}")
    return destino


if __name__ == "__main__":
    main()
