"""Operações estatísticas pequenas compartilháveis pelas análises."""

import math

import pandas as pd


def arredondar(valor, casas: int = 4):
    if pd.isna(valor) or not math.isfinite(float(valor)):
        return None
    return round(float(valor), casas)


def resumir(serie: pd.Series) -> dict:
    valores = serie.dropna()
    if valores.empty:
        return dict.fromkeys(["mediana", "media", "q1", "q3", "minimo", "maximo"])
    return {
        "mediana": arredondar(valores.median()),
        "media": arredondar(valores.mean()),
        "q1": arredondar(valores.quantile(.25)),
        "q3": arredondar(valores.quantile(.75)),
        "minimo": arredondar(valores.min()),
        "maximo": arredondar(valores.max()),
    }


def spearman(x: pd.Series, y: pd.Series) -> dict:
    pares = pd.concat([x, y], axis=1).dropna()
    rho = None
    if len(pares) > 1 and pares.iloc[:, 0].nunique() > 1 and pares.iloc[:, 1].nunique() > 1:
        rho = arredondar(pares.rank(method="average").corr().iloc[0, 1])
    return {"rho": rho, "n": int(len(pares))}


def outliers_iqr(serie: pd.Series) -> tuple[dict, pd.Series]:
    valores = serie.dropna()
    mascara = pd.Series(False, index=serie.index)
    if valores.empty:
        limites = dict.fromkeys(["q1", "q3", "iqr", "limite_inferior", "limite_superior"])
        return {**limites, "quantidade": 0, "inferiores": 0, "superiores": 0}, mascara

    q1, q3 = valores.quantile([.25, .75])
    iqr = q3 - q1
    inferior, superior = q1 - 1.5 * iqr, q3 + 1.5 * iqr
    baixos, altos = serie < inferior, serie > superior
    mascara = (baixos | altos).fillna(False)
    return {
        "q1": arredondar(q1), "q3": arredondar(q3), "iqr": arredondar(iqr),
        "limite_inferior": arredondar(inferior),
        "limite_superior": arredondar(superior),
        "quantidade": int(mascara.sum()),
        "inferiores": int(baixos.sum()), "superiores": int(altos.sum()),
    }, mascara
