"""Leitura e validação do config.yaml."""
from datetime import date

import yaml


def carregar_config(caminho="config.yaml"):
    with open(caminho, encoding="utf-8") as f:
        cfg = yaml.safe_load(f)
    # o YAML já converte 2025-10-01 em date; str() cobre os dois casos
    for chave in ("janela_inicio", "janela_fim"):
        cfg[chave] = date.fromisoformat(str(cfg[chave]))
    if cfg["janela_fim"] <= cfg["janela_inicio"]:
        raise ValueError("janela_fim deve ser posterior a janela_inicio")
    return cfg


def semanas_da_janela(cfg):
    """Nº de semanas da janela (≈ 52,1 para 12 meses). Usado em deployment frequency."""
    dias = (cfg["janela_fim"] - cfg["janela_inicio"]).days + 1
    return dias / 7
