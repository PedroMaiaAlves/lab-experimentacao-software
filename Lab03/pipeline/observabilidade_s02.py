"""Contadores de transporte, sem armazenar token, cabeçalhos ou payloads."""
from collections import Counter
from datetime import datetime, timedelta, timezone
import json
import logging
from pathlib import Path
import time

from pipeline.coleta_runs import _salvar_json_atomico

log = logging.getLogger(__name__)


def observar_http(client, caminho):
    caminho = Path(caminho)
    estado = (json.loads(caminho.read_text(encoding="utf-8")) if caminho.exists()
              else {"inicio": datetime.now(timezone.utc).isoformat(), "respostas_http": 0,
                    "status": {}, "esperas": 0, "segundos_espera_solicitados": 0})

    def resposta(response, *args, **kwargs):
        estado["respostas_http"] += 1
        contagens = Counter(estado["status"])
        contagens[str(response.status_code)] += 1
        estado["status"] = dict(contagens)
        estado["ultima_resposta"] = datetime.now(timezone.utc).isoformat()
        _salvar_json_atomico(caminho, estado)

    def esperar(segundos):
        estado["esperas"] += 1
        estado["segundos_espera_solicitados"] += segundos
        estado["espera_ate"] = (datetime.now(timezone.utc) + timedelta(seconds=segundos)).isoformat()
        _salvar_json_atomico(caminho, estado)
        log.info("rate limit/backoff: aguardando %.1f segundos", segundos)
        time.sleep(segundos)
        estado["espera_ate"] = None
        _salvar_json_atomico(caminho, estado)

    client.sessao.hooks["response"].append(resposta)
    client._sleep = esperar
    return estado
