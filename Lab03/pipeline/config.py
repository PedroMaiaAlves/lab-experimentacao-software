"""Leitura e validação do config.yaml."""
from datetime import date

import yaml


CHAVES_OBRIGATORIAS = {
    "janela_inicio", "janela_fim", "semente", "criterios", "selecao", "saida",
    "etapas_coleta",
}


def _exigir_mapeamento(valor, caminho):
    if not isinstance(valor, dict):
        raise ValueError(f"{caminho} deve ser um mapeamento")
    return valor


def _exigir_chaves(mapeamento, chaves, caminho="config"):
    ausentes = sorted(set(chaves) - set(mapeamento))
    if ausentes:
        raise ValueError(f"chaves obrigatórias ausentes em {caminho}: {', '.join(ausentes)}")


def _exigir_inteiro_positivo(valor, caminho):
    if isinstance(valor, bool) or not isinstance(valor, int) or valor <= 0:
        raise ValueError(f"{caminho} deve ser um inteiro positivo")


def _exigir_lista_de_textos(valor, caminho):
    if not isinstance(valor, list) or not valor or not all(
        isinstance(item, str) and item.strip() for item in valor
    ):
        raise ValueError(f"{caminho} deve ser uma lista não vazia de textos")


def validar_config(cfg):
    """Valida o contrato mínimo exigido pelo pipeline antes de acessar a API."""
    _exigir_mapeamento(cfg, "config")
    _exigir_chaves(cfg, CHAVES_OBRIGATORIAS)

    _exigir_inteiro_positivo(cfg["semente"], "semente")

    criterios = _exigir_mapeamento(cfg["criterios"], "criterios")
    _exigir_chaves(criterios, {"min_releases", "min_runs"}, "criterios")
    _exigir_inteiro_positivo(criterios["min_releases"], "criterios.min_releases")
    _exigir_inteiro_positivo(criterios["min_runs"], "criterios.min_runs")

    selecao = _exigir_mapeamento(cfg["selecao"], "selecao")
    _exigir_chaves(
        selecao, {"meta_repositorios", "faixas_estrelas", "linguagens"}, "selecao"
    )
    _exigir_inteiro_positivo(selecao["meta_repositorios"], "selecao.meta_repositorios")
    _exigir_lista_de_textos(selecao["faixas_estrelas"], "selecao.faixas_estrelas")
    _exigir_lista_de_textos(selecao["linguagens"], "selecao.linguagens")

    saida = _exigir_mapeamento(cfg["saida"], "saida")
    _exigir_chaves(saida, {"dir_dados", "dir_cache"}, "saida")
    for chave in ("dir_dados", "dir_cache"):
        if not isinstance(saida[chave], str) or not saida[chave].strip():
            raise ValueError(f"saida.{chave} deve ser um texto não vazio")

    _exigir_lista_de_textos(cfg["etapas_coleta"], "etapas_coleta")
    return cfg


def carregar_config(caminho="config.yaml"):
    with open(caminho, encoding="utf-8") as f:
        cfg = yaml.safe_load(f)
    validar_config(cfg)
    # o YAML já converte 2025-10-01 em date; str() cobre os dois casos
    for chave in ("janela_inicio", "janela_fim"):
        try:
            cfg[chave] = date.fromisoformat(str(cfg[chave]))
        except ValueError as exc:
            raise ValueError(f"{chave} deve estar no formato AAAA-MM-DD") from exc
    if cfg["janela_fim"] <= cfg["janela_inicio"]:
        raise ValueError("janela_fim deve ser posterior a janela_inicio")
    return cfg


def semanas_da_janela(cfg):
    """Nº de semanas da janela (≈ 52,1 para 12 meses). Usado em deployment frequency."""
    dias = (cfg["janela_fim"] - cfg["janela_inicio"]).days + 1
    return dias / 7
