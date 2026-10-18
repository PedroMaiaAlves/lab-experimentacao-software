"""Classificação DORA de referência (C1), por métrica e geral, com as funções da S01-A4.

C1 = frequência de releases principais, lead time (a), CFR (a) e tempo de recuperação.
A classificação geral exige as quatro métricas (definição principal de
`metricas.classificacao`); projetos sem alguma métrica ficam sem categoria geral e são
contados. A coluna `categoria_geral_minimo_3` é só uma sensibilidade a essa regra.
"""
import numpy as np
import pandas as pd

from metricas.classificacao import (Categoria, classificar_cfr, classificar_deployment_frequency,
                                    classificar_geral, classificar_lead_time,
                                    classificar_tempo_recuperacao)

# métrica -> coluna do dataset. Outras combinações (C2, C3) trocam só as colunas.
COMBINACAO_C1 = {
    "deployment_frequency": "deployment_frequency",
    "lead_time": "lead_time_a_horas",
    "cfr": "cfr_a",
    "tempo_recuperacao": "tempo_recuperacao_horas",
}
FUNCOES = {
    "deployment_frequency": classificar_deployment_frequency,
    "lead_time": classificar_lead_time,
    "cfr": classificar_cfr,
    "tempo_recuperacao": classificar_tempo_recuperacao,
}
ROTULOS = {Categoria.ELITE: "Elite", Categoria.HIGH: "High", Categoria.MEDIUM: "Medium", Categoria.LOW: "Low"}
CATEGORIAS = ("Elite", "High", "Medium", "Low")
SEM_CATEGORIA = "sem_categoria"
DIMENSOES = (*COMBINACAO_C1, "geral", "geral_minimo_3")


def _rotulo(categoria):
    return ROTULOS[categoria] if categoria is not None else np.nan


def _valor(valor):
    return None if pd.isna(valor) else float(valor)


def classificar(df, combinacao=COMBINACAO_C1):
    """Uma linha por projeto: valores usados, categoria por métrica e geral."""
    linhas = []
    for _, repo in df.sort_values("full_name").iterrows():
        categorias = {m: FUNCOES[m](_valor(repo[coluna])) for m, coluna in combinacao.items()}
        notas = [int(c) for c in categorias.values() if c is not None]
        ausentes = [m for m, c in categorias.items() if c is None]
        linhas.append({
            "full_name": repo.full_name,
            **{coluna: repo[coluna] for coluna in combinacao.values()},
            **{f"categoria_{m}": _rotulo(c) for m, c in categorias.items()},
            "metricas_disponiveis": len(notas),
            "metricas_ausentes": ";".join(ausentes),
            "mediana_notas": float(np.median(notas)) if len(notas) == len(categorias) else np.nan,
            "categoria_geral": _rotulo(classificar_geral(categorias.values())),
            "categoria_geral_minimo_3": _rotulo(classificar_geral(categorias.values(), minimo_metricas=3)),
        })
    return pd.DataFrame(linhas)


def distribuicao(classificacao):
    """Contagem por categoria em cada métrica e na geral; ausências ficam em sem_categoria."""
    linhas = []
    total = len(classificacao)
    for dimensao in DIMENSOES:
        coluna = classificacao[f"categoria_{dimensao}"]
        classificados = int(coluna.notna().sum())
        for categoria in (*CATEGORIAS, SEM_CATEGORIA):
            n = int(coluna.isna().sum()) if categoria == SEM_CATEGORIA else int((coluna == categoria).sum())
            linhas.append(dict(
                dimensao=dimensao, categoria=categoria, n=n, n_total=total, n_classificados=classificados,
                proporcao_total=n / total if total else np.nan,
                proporcao_classificados=(n / classificados if classificados else np.nan)
                if categoria != SEM_CATEGORIA else np.nan))
    return pd.DataFrame(linhas)


def ausencias(classificacao, df):
    """Projetos sem alguma métrica de C1 e o motivo registrado no dataset."""
    linhas = []
    dados = df.set_index("full_name")
    for _, r in classificacao[classificacao.metricas_ausentes != ""].iterrows():
        for metrica in r.metricas_ausentes.split(";"):
            linha = dados.loc[r.full_name]
            if metrica == "tempo_recuperacao":
                motivo = ("sem_episodios" if linha.episodios_total == 0
                          else "somente_episodios_censurados")
            else:
                motivo = "valor_ausente"
            linhas.append(dict(full_name=r.full_name, metrica=metrica, motivo=motivo))
    return pd.DataFrame(linhas, columns=["full_name", "metrica", "motivo"])


def analisar(df):
    classificacao = classificar(df)
    return {"classificacao_C1": classificacao, "c1_distribuicao": distribuicao(classificacao),
            "c1_ausencias": ausencias(classificacao, df)}
