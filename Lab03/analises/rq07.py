"""Sensibilidade das definições: classificações, concordância e robustez das RQ01–06."""
from itertools import combinations

import numpy as np
import pandas as pd
from pandas.testing import assert_frame_equal
from sklearn.metrics import cohen_kappa_score, confusion_matrix

from analises import rq05, rq06
from analises.classificacao_c1 import COMBINACAO_C1, classificar, distribuicao
from analises.comum import CONTAGENS, ajustar_holm, descrever

COMBINACOES = {
    "C1": dict(COMBINACAO_C1),
    "C2": {**COMBINACAO_C1, "deployment_frequency": "deployment_frequency_prereleases",
           "lead_time": "lead_time_b_horas", "cfr": "cfr_b"},
    "C3": {**COMBINACAO_C1, "deployment_frequency": "deployment_frequency_tags",
           "lead_time": "lead_time_b_horas", "cfr": "cfr_b"},
}
NOTAS = {"Low": 1, "Medium": 2, "High": 3, "Elite": 4}


def concordancia(classificacoes):
    """Ausência não é uma quinta categoria; explicita exclusões e a interseção tripla."""
    if classificacoes.duplicated(["combinacao", "full_name"]).any():
        raise ValueError("classificações duplicadas")
    tabela = classificacoes.pivot(index="full_name", columns="combinacao", values="categoria_geral")
    if set(tabela.columns) != set(COMBINACOES):
        raise ValueError("faltam combinações")
    if len(classificacoes) != len(tabela) * len(COMBINACOES):
        raise ValueError("combinações não cobrem os mesmos projetos")
    if not set(classificacoes.categoria_geral.dropna().unique()) <= set(NOTAS):
        raise ValueError("categoria desconhecida")
    comuns = tabela.notna().all(axis=1)
    resultados, matrizes = [], []
    for a, b in combinations(COMBINACOES, 2):
        ambos = tabela[[a, b]].notna().all(axis=1)
        for populacao, mascara in (("pares_disponiveis", ambos), ("comuns_tres", comuns)):
            x = tabela.loc[mascara, a].map(NOTAS).to_numpy(int)
            y = tabela.loc[mascara, b].map(NOTAS).to_numpy(int)
            status = "sem_pares" if not len(x) else (
                "denominador_zero" if np.unique(np.concatenate([x, y])).size == 1 else "ok")
            kappa = cohen_kappa_score(x, y, labels=[1, 2, 3, 4], weights="linear") if status == "ok" else np.nan
            resultados.append(dict(
                combinacao_a=a, combinacao_b=b, populacao=populacao, n_total=len(tabela), n=len(x),
                n_excluidos=len(tabela)-len(x), mudou=int((x != y).sum()),
                proporcao_mudou=float((x != y).mean()) if len(x) else np.nan,
                subiu=int((y > x).sum()), desceu=int((y < x).sum()),
                kappa_linear=kappa, status_kappa=status,
                ganhou_classificacao=int((tabela[a].isna() & tabela[b].notna()).sum()),
                perdeu_classificacao=int((tabela[a].notna() & tabela[b].isna()).sum()),
                ambos_ausentes=int(tabela[[a, b]].isna().all(axis=1).sum())))
            if populacao == "pares_disponiveis":
                matriz = confusion_matrix(x, y, labels=[1, 2, 3, 4]) if len(x) else np.zeros((4, 4), dtype=int)
                matrizes += [dict(combinacao_a=a, combinacao_b=b, categoria_a=ca, categoria_b=cb,
                                  n=int(matriz[i, j]))
                             for i, ca in enumerate(NOTAS) for j, cb in enumerate(NOTAS)]
    return pd.DataFrame(resultados), pd.DataFrame(matrizes)


def analisar(df, referencia=None, semente=42, reamostragens=9999):
    df = df.copy().sort_values("full_name").reset_index(drop=True)
    if df.full_name.isna().any() or df.full_name.duplicated().any():
        raise ValueError("identificadores ausentes ou duplicados")
    for coluna in CONTAGENS:
        if coluna in df:
            df[coluna] = pd.to_numeric(df[coluna], errors="raise")
    for coluna in {c for combinacao in COMBINACOES.values() for c in combinacao.values()} | {"contribuidores"}:
        df[coluna] = pd.to_numeric(df[coluna], errors="raise")
        if not np.isfinite(df[coluna].dropna()).all() or (df[coluna].dropna() < 0).any():
            raise ValueError(f"métrica inválida: {coluna}")
    metricas, classes, distribuicoes, resumos, correlacoes, fatores = [], [], [], [], [], []
    for nome, combinacao in COMBINACOES.items():
        c = classificar(df, combinacao)
        if nome == "C1" and referencia is not None:
            colunas = ["full_name", "metricas_disponiveis", "mediana_notas"] + [
                col for col in c if col.startswith("categoria_")]
            publicada = pd.read_csv(referencia).sort_values("full_name").reset_index(drop=True)
            assert_frame_equal(c[colunas], publicada[colunas], check_dtype=False, rtol=1e-12)
        metricas.append(pd.DataFrame({"full_name": df.full_name, "combinacao": nome,
                                     **{m: df[col] for m, col in combinacao.items()}}))
        classes.append(c[["full_name", "metricas_disponiveis", "metricas_ausentes", "mediana_notas"] + [
            col for col in c if col.startswith("categoria_")]].assign(combinacao=nome))
        distribuicoes.append(distribuicao(c).assign(combinacao=nome))
        for metrica, coluna in combinacao.items():
            resumos.append(dict(combinacao=nome, metrica=metrica, coluna_origem=coluna,
                                n_total=len(df), n_ausentes=int(df[coluna].isna().sum()), **descrever(df[coluna])))
        variante = df.assign(deployment_frequency=df[combinacao["deployment_frequency"]])
        r5 = rq05.analisar(variante, semente, reamostragens)["rq05_correlacoes"].copy()
        r5["fonte_frequencia"] = combinacao["deployment_frequency"]
        r5["combinacao_frequencia"] = nome
        correlacoes.append(r5)
        r6 = rq06.analisar(variante)["rq06_testes"].copy()
        r6["metrica"] = r6.metrica.replace({"deployment_frequency": combinacao["deployment_frequency"]})
        fatores.append(r6)
    classificacoes = pd.concat(classes, ignore_index=True)
    pares, matrizes = concordancia(classificacoes)
    r5 = ajustar_holm(pd.concat(correlacoes, ignore_index=True), "p_permutacao", "p_holm_sensibilidade")
    r6 = pd.concat(fatores, ignore_index=True).drop_duplicates(["fator", "metrica"]).reset_index(drop=True)
    r6 = ajustar_holm(r6, "p", "p_holm_sensibilidade").drop(
        columns=["p_holm", "p_holm_familia_n", "significativo_holm"])
    return {"metricas_combinacoes": pd.concat(metricas, ignore_index=True),
            "rq07_classificacoes": classificacoes, "rq07_distribuicao": pd.concat(distribuicoes, ignore_index=True),
            "rq07_concordancia": pares, "rq07_matrizes": matrizes,
            "rq07_resumo_metricas": pd.DataFrame(resumos),
            "rq07_robustez_rq05": r5, "rq07_robustez_rq06": r6}
