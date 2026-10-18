"""Fatores da H6, grupos fixos e família única de 18 testes."""
import numpy as np
import pandas as pd
from scipy import stats

from analises.comum import METRICAS, TIPOS, ajustar_holm, descrever, motivo_ausencia

FATORES = ("tipo_projeto", "contribuidores_quartil", "linguagem_grupo")


def preparar_grupos(df):
    grupos = df[["full_name", "tipo_projeto", "contribuidores", "language"]].copy()
    frequencias = df.language.value_counts()
    grupos["linguagem_grupo"] = df.language.map(lambda v: np.nan if pd.isna(v) else (
        v if frequencias[v] >= 10 else "Outras"))
    valores = df.contribuidores.dropna()
    limites = valores.quantile([0, .25, .5, .75, 1], interpolation="linear").unique()
    if len(limites) > 1:
        grupos["contribuidores_quartil"] = pd.cut(df.contribuidores, bins=limites, include_lowest=True,
                                                 labels=[f"Q{i+1}" for i in range(len(limites)-1)]).astype(object)
    else:
        grupos["contribuidores_quartil"] = df.contribuidores.map(lambda x: np.nan if pd.isna(x) else "Q1")
    definicao = {"contribuidores_limites": [float(v) for v in limites],
                "quartis_metodo": "quantis lineares; intervalos fechados à direita, primeiro inclui mínimo; limites repetidos removidos",
                "linguagens_minimo": 10, "linguagens_agrupadas": sorted(frequencias[frequencias < 10].index),
                "tipos_ordem": list(TIPOS), "grupos_definidos_sobre": "amostra completa antes de excluir métricas ausentes"}
    return grupos, definicao


def interpretar_delta(delta):
    valor = abs(delta)
    return "desprezível" if valor < .147 else "pequeno" if valor < .33 else "médio" if valor < .474 else "grande"


def comparar_grupos(grupos):
    """Recebe grupos já filtrados, mas preserva grupos vazios para diagnosticar n."""
    resultado = dict(teste="", estatistica=np.nan, p=np.nan, efeito=np.nan, tipo_efeito="",
                     interpretacao_efeito="", status="ok")
    if len(grupos) < 2:
        return {**resultado, "status": "grupos_insuficientes"}
    if any(len(g) < 5 for g in grupos):
        return {**resultado, "status": "grupo_com_menos_de_5"}
    if np.unique(np.concatenate(grupos)).size < 2:
        return {**resultado, "status": "dados_constantes"}
    if len(grupos) == 2:
        teste = stats.mannwhitneyu(*grupos, alternative="two-sided", method="asymptotic", use_continuity=True)
        delta = 2 * teste.statistic / (len(grupos[0]) * len(grupos[1])) - 1
        resultado.update(teste="Mann-Whitney", efeito=delta, tipo_efeito="Cliff_delta",
                         interpretacao_efeito=interpretar_delta(delta))
    else:
        teste = stats.kruskal(*grupos)
        resultado.update(teste="Kruskal-Wallis", efeito=teste.statistic/(sum(map(len, grupos))-1),
                         tipo_efeito="epsilon_quadrado", interpretacao_efeito="sem_cortes_convencionados")
    return {**resultado, "estatistica": teste.statistic, "p": teste.pvalue}


def analisar(df):
    df = df.sort_values("full_name").reset_index(drop=True)
    grupos, definicao = preparar_grupos(df)
    testes, descritivas, exclusoes = [], [], []
    for fator in FATORES:
        categorias = ([t for t in TIPOS if t in set(grupos[fator])] if fator == "tipo_projeto"
                      else sorted(grupos[fator].dropna().unique()))
        for metrica in METRICAS:
            vetores = []
            for categoria in categorias:
                mascara = grupos[fator] == categoria
                valores = df.loc[mascara, metrica].dropna().to_numpy(float)
                vetores.append(valores)
                descritivas.append(dict(fator=fator, grupo=categoria, metrica=metrica, unidade=METRICAS[metrica][1],
                                        n_total=int(mascara.sum()), n_ausentes=int(mascara.sum())-len(valores), **descrever(valores)))
            for i, r in df.iterrows():
                for campo in ([fator] if pd.isna(grupos.loc[i, fator]) else []) + ([metrica] if pd.isna(r[metrica]) else []):
                    exclusoes.append(dict(analise="RQ06", fator=fator, metrica=metrica, full_name=r.full_name,
                                          campo=campo, motivo=motivo_ausencia(r, campo)))
            n = sum(map(len, vetores))
            testes.append(dict(fator=fator, metrica=metrica, n_total=len(df), n=n, n_excluidos=len(df)-n,
                               grupos_n=len(vetores), ordem_grupos=" | ".join(categorias),
                               **comparar_grupos(vetores)))
    tabela = ajustar_holm(pd.DataFrame(testes))
    tabela["significativo_holm"] = tabela.p_holm.map(lambda v: pd.NA if pd.isna(v) else v < .05)
    return {"rq06_testes": tabela, "rq06_descritivas": pd.DataFrame(descritivas),
            "rq06_grupos": grupos, "grupos_definicao": definicao,
            "exclusoes": pd.DataFrame(exclusoes, columns=["analise", "fator", "metrica", "full_name", "campo", "motivo"])}
