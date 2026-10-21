"""Spearman e robustez: bootstrap pareado, permutação e influência individual."""
import warnings

import numpy as np
import pandas as pd
from scipy import stats

from analises.comum import ajustar_holm, motivo_ausencia


def rho_vetorizado(x, y, axis=-1):
    """Correlação de postos médios, equivalente ao rho de spearmanr com empates."""
    rx, ry = stats.rankdata(x, axis=axis), stats.rankdata(y, axis=axis)
    rx = rx - np.mean(rx, axis=axis, keepdims=True)
    ry = ry - np.mean(ry, axis=axis, keepdims=True)
    with np.errstate(divide="ignore", invalid="ignore"):
        return np.sum(rx * ry, axis=axis) / np.sqrt(
            np.sum(rx * rx, axis=axis) * np.sum(ry * ry, axis=axis))


def analisar(df, semente=42, reamostragens=9999):
    if reamostragens < 99:
        raise ValueError("use pelo menos 99 reamostragens")
    df = df.sort_values("full_name").reset_index(drop=True)
    sementes = np.random.SeedSequence(semente).spawn(4)
    resultados, influencias, exclusoes = [], [], []
    for indice, variante in enumerate(("cfr_a", "cfr_b")):
        mascara = df[["deployment_frequency", variante]].notna().all(axis=1)
        pares = df.loc[mascara]
        for _, r in df.loc[~mascara].iterrows():
            for campo in ("deployment_frequency", variante):
                if pd.isna(r[campo]):
                    exclusoes.append(dict(analise="RQ05", fator="", metrica=variante,
                                          full_name=r.full_name, campo=campo, motivo=motivo_ausencia(r, campo)))
        x, y = pares.deployment_frequency.to_numpy(float), pares[variante].to_numpy(float)
        resultado = dict(variante=variante, n_total=len(df), n=len(pares), n_excluidos=len(df)-len(pares),
                         rho=np.nan, p_spearman=np.nan, p_permutacao=np.nan,
                         ic95_inferior=np.nan, ic95_superior=np.nan, status="ok", status_ic="nao_estimavel",
                         rho_loo_min=np.nan, rho_loo_max=np.nan, delta_loo_max=np.nan,
                         repo_maior_influencia="", mudancas_sinal=0, loo_indefinidos=0)
        if len(x) < 5 or np.unique(x).size < 2 or np.unique(y).size < 2:
            resultado["status"] = "amostra_insuficiente" if len(x) < 5 else "dados_constantes"
            resultados.append(resultado)
            continue
        rho, p = stats.spearmanr(x, y, alternative="two-sided")
        resultado.update(rho=rho, p_spearman=p)
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", stats.DegenerateDataWarning)
            warnings.simplefilter("ignore", RuntimeWarning)
            boot = stats.bootstrap((x, y), rho_vetorizado, paired=True, vectorized=True,
                                   method="BCa", confidence_level=.95, n_resamples=reamostragens,
                                   batch=256, rng=np.random.default_rng(sementes[2*indice]))
        limites = np.asarray(boot.confidence_interval)
        if np.isfinite(limites).all() and np.isfinite(boot.bootstrap_distribution).all():
            resultado.update(ic95_inferior=limites[0], ic95_superior=limites[1], status_ic="ok")
        else:
            resultado["status_ic"] = "distribuicao_degenerada"

        def estatistica_permutada(x_permutado, axis=-1):
            return rho_vetorizado(x_permutado, y, axis=axis)

        perm = stats.permutation_test((x,), estatistica_permutada, permutation_type="pairings",
                                      alternative="two-sided", vectorized=True, n_resamples=reamostragens,
                                      batch=256, rng=np.random.default_rng(sementes[2*indice+1]))
        resultado["p_permutacao"] = perm.pvalue
        locais = []
        for i, nome in enumerate(pares.full_name):
            xx, yy = np.delete(x, i), np.delete(y, i)
            r = float(rho_vetorizado(xx, yy))
            valido = bool(np.isfinite(r))
            item = dict(variante=variante, full_name=nome, rho_sem_repo=r,
                        delta_rho=r-rho, mudou_sinal=bool(np.sign(r) != np.sign(rho)) if valido else False,
                        status="ok" if valido else "dados_constantes")
            influencias.append(item)
            if valido:
                locais.append(item)
        resultado["loo_indefinidos"] = len(x) - len(locais)
        if locais:
            maior = max(locais, key=lambda r: abs(r["delta_rho"]))
            resultado.update(rho_loo_min=min(r["rho_sem_repo"] for r in locais),
                             rho_loo_max=max(r["rho_sem_repo"] for r in locais),
                             delta_loo_max=abs(maior["delta_rho"]), repo_maior_influencia=maior["full_name"],
                             mudancas_sinal=sum(r["mudou_sinal"] for r in locais))
        resultados.append(resultado)
    resumo = ajustar_holm(pd.DataFrame(resultados), "p_permutacao", "p_permutacao_holm")
    return {"rq05_correlacoes": resumo,
            "rq05_influencia": pd.DataFrame(influencias, columns=["variante", "full_name", "rho_sem_repo",
                                          "delta_rho", "mudou_sinal", "status"]),
            "exclusoes": pd.DataFrame(exclusoes, columns=["analise", "fator", "metrica", "full_name", "campo", "motivo"])}
