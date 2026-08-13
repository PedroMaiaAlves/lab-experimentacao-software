"""Pacote com um módulo por questão de pesquisa (RQ01 a RQ07).

Cada módulo expõe:
    - analisar(df) -> dict:      calcula as métricas daquela RQ
    - salvar_json(dict, path):   grava o resultado em um arquivo JSON

Manter um arquivo por RQ facilita separar commits/PRs por issue,
já que cada questão de pesquisa evolui de forma independente.
"""
from . import (
    rq01_idade,
    rq02_prAceitos,
    rq03_releases,
    rq04_ultimaAtt,
    rq05_linguagem,
    rq06_issuesFechadas,
    rq07_relacaoLinguagemContribuicao,
)

MODULOS_RQ = {
    "rq01_idade": rq01_idade,
    "rq02_pr_aceitos": rq02_prAceitos,
    "rq03_releases": rq03_releases,
    "rq04_ultima_atualizacao": rq04_ultimaAtt,
    "rq05_linguagem": rq05_linguagem,
    "rq06_issues_fechadas": rq06_issuesFechadas,
    "rq07_cruzamento": rq07_relacaoLinguagemContribuicao,
}

__all__ = ["MODULOS_RQ"]
