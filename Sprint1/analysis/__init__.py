"""Pacote com um módulo por questão de pesquisa (RQ01 a RQ07).

Cada módulo expõe:
    - analisar(df) -> dict:      calcula as métricas daquela RQ
    - salvar_json(dict, path):   grava o resultado em um arquivo JSON

Manter um arquivo por RQ facilita separar commits/PRs por issue,
já que cada questão de pesquisa evolui de forma independente.
"""
from . import (
    rq01_idade,
    rq03_releases,
    rq05_linguagem,
)

MODULOS_RQ = {
    "rq01_idade": rq01_idade,
    "rq03_releases": rq03_releases,
    "rq05_linguagem": rq05_linguagem,
}

__all__ = ["MODULOS_RQ"] + list(MODULOS_RQ.keys())
