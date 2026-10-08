from copy import deepcopy

import pytest
import yaml

from pipeline.config import carregar_config, validar_config


@pytest.fixture
def config_valida():
    return {
        "janela_inicio": "2025-10-01",
        "janela_fim": "2026-09-30",
        "semente": 42,
        "criterios": {"min_releases": 5, "min_runs": 50},
        "selecao": {
            "meta_repositorios": 100,
            "faixas_estrelas": ["1000..2000"],
            "linguagens": ["Python"],
        },
        "saida": {"dir_dados": "data", "dir_cache": "cache"},
        "etapas_coleta": [
            "pipeline.coleta_releases",
            "pipeline.coleta_commits",
            "pipeline.coleta_runs",
        ],
    }


def test_carregar_config_converte_datas(config_valida, tmp_path):
    caminho = tmp_path / "config.yaml"
    caminho.write_text(yaml.safe_dump(config_valida), encoding="utf-8")

    cfg = carregar_config(caminho)

    assert cfg["janela_inicio"].isoformat() == "2025-10-01"
    assert cfg["janela_fim"].isoformat() == "2026-09-30"


def test_chave_obrigatoria_ausente_falha(config_valida):
    cfg = deepcopy(config_valida)
    del cfg["criterios"]
    with pytest.raises(ValueError, match="criterios"):
        validar_config(cfg)


@pytest.mark.parametrize(
    ("caminho", "valor"),
    [
        (("semente",), 0),
        (("criterios", "min_releases"), 0),
        (("criterios", "min_runs"), -1),
        (("selecao", "meta_repositorios"), 0),
    ],
)
def test_inteiros_que_devem_ser_positivos(config_valida, caminho, valor):
    cfg = deepcopy(config_valida)
    alvo = cfg
    for chave in caminho[:-1]:
        alvo = alvo[chave]
    alvo[caminho[-1]] = valor
    with pytest.raises(ValueError, match="positivo"):
        validar_config(cfg)


@pytest.mark.parametrize(
    "caminho",
    [
        ("selecao", "faixas_estrelas"),
        ("selecao", "linguagens"),
        ("etapas_coleta",),
    ],
)
def test_listas_obrigatorias_nao_podem_ser_vazias(config_valida, caminho):
    cfg = deepcopy(config_valida)
    alvo = cfg
    for chave in caminho[:-1]:
        alvo = alvo[chave]
    alvo[caminho[-1]] = []
    with pytest.raises(ValueError, match="lista não vazia"):
        validar_config(cfg)


def test_janela_invertida_falha(config_valida, tmp_path):
    config_valida["janela_inicio"] = "2026-10-01"
    caminho = tmp_path / "config.yaml"
    caminho.write_text(yaml.safe_dump(config_valida), encoding="utf-8")
    with pytest.raises(ValueError, match="posterior"):
        carregar_config(caminho)


def test_etapa_obrigatoria_ausente_falha(config_valida):
    config_valida["etapas_coleta"].remove("pipeline.coleta_commits")
    with pytest.raises(ValueError, match="coleta_commits"):
        validar_config(config_valida)


def test_releases_deve_preceder_commits(config_valida):
    config_valida["etapas_coleta"][:2] = reversed(config_valida["etapas_coleta"][:2])
    with pytest.raises(ValueError, match="deve preceder"):
        validar_config(config_valida)
