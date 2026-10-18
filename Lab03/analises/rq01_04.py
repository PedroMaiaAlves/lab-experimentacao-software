"""RQ01 a RQ04: mediana e IQR de cada métrica e variante, comparações pareadas e censura."""
import numpy as np
import pandas as pd
from scipy import stats
from statsmodels.stats.multitest import multipletests

# coluna do dataset: (RQ, rótulo, unidade). Uma observação por repositório.
METRICAS = {
    "deployment_frequency": ("RQ01", "Frequência: releases", "releases/semana"),
    "deployment_frequency_prereleases": ("RQ01", "Frequência: com pré-releases", "releases/semana"),
    "deployment_frequency_tags": ("RQ01", "Frequência: tags", "tags/semana"),
    "lead_time_a_horas": ("RQ02", "Lead time (a): por release", "horas"),
    "lead_time_b_horas": ("RQ02", "Lead time (b): por commit", "horas"),
    "cfr_a": ("RQ03", "CFR (a): runs de CI", "proporção"),
    "cfr_b": ("RQ03", "CFR (b): releases", "proporção"),
    "tempo_recuperacao_horas": ("RQ04", "Recuperação: mediana por projeto", "horas"),
}
EPISODIOS = ("RQ04", "Recuperação: episódios concluídos", "horas")

# (x, y, hipótese). Só as hipóteses H2 e H3 comparam variantes; as de frequência são
# descritivas, pois incluir pré-releases produz um superconjunto das releases.
PARES = (
    ("deployment_frequency_prereleases", "deployment_frequency", ""),
    ("deployment_frequency_tags", "deployment_frequency", ""),
    ("lead_time_a_horas", "lead_time_b_horas", "H2"),
    ("cfr_a", "cfr_b", "H3"),
)


def descrever(valores):
    """Mediana e quartis com interpolação linear; IQR = Q3 - Q1. Ausentes são ignorados."""
    serie = pd.Series(valores, dtype=float).dropna()
    if serie.empty:
        return dict(n=0, mediana=np.nan, q1=np.nan, q3=np.nan, iqr=np.nan, minimo=np.nan, maximo=np.nan)
    q1, mediana, q3 = serie.quantile([.25, .5, .75], interpolation="linear")
    return dict(n=len(serie), mediana=mediana, q1=q1, q3=q3, iqr=q3 - q1,
                minimo=serie.min(), maximo=serie.max())


def descritivas(df, episodios):
    linhas = [dict(rq=rq, metrica=coluna, rotulo=rotulo, unidade=unidade, unidade_analise="repositorio",
                   n_total=len(df), n_ausentes=int(df[coluna].isna().sum()), **descrever(df[coluna]))
              for coluna, (rq, rotulo, unidade) in METRICAS.items()]
    rq, rotulo, unidade = EPISODIOS
    censurados = int(df.episodios_censurados.sum())
    # Um episódio censurado não tem duração observada: conta como ausente, não como zero.
    linhas.append(dict(rq=rq, metrica="tempo_recuperacao_episodio_horas", rotulo=rotulo, unidade=unidade,
                       unidade_analise="episodio", n_total=len(episodios) + censurados,
                       n_ausentes=censurados, **descrever(episodios.horas)))
    return pd.DataFrame(linhas)


def rank_biserial_pareado(diferencas):
    """Correlação rank-biserial pareada: (W+ - W-) / (W+ + W-), sem as diferenças nulas."""
    d = np.asarray(diferencas, dtype=float)
    d = d[d != 0]
    if d.size == 0:
        return np.nan
    postos = stats.rankdata(np.abs(d))
    positivos, negativos = postos[d > 0].sum(), postos[d < 0].sum()
    return (positivos - negativos) / (positivos + negativos)


def comparar_pares(df):
    """Compara variantes no mesmo repositório; Wilcoxon e Holm apenas para H2 e H3."""
    linhas = []
    for x, y, hipotese in PARES:
        pares = df[[x, y]].dropna()
        d = pares[x] - pares[y]
        q1, mediana, q3 = d.quantile([.25, .5, .75]) if len(d) else (np.nan,) * 3
        linha = dict(rq=METRICAS[x][0], hipotese=hipotese, x=x, y=y, n=len(pares),
                     n_ausentes=len(df) - len(pares), n_x_maior=int((d > 0).sum()),
                     n_iguais=int((d == 0).sum()), n_x_menor=int((d < 0).sum()),
                     mediana_diferenca=mediana, q1_diferenca=q1, q3_diferenca=q3,
                     mediana_razao=(pares[x] / pares[y]).median() if (pares[y] > 0).all() else np.nan,
                     teste="", estatistica=np.nan, p=np.nan, efeito_rank_biserial=np.nan)
        if hipotese and (d != 0).sum() >= 5:
            teste = stats.wilcoxon(pares[x], pares[y], zero_method="wilcox", alternative="two-sided")
            linha.update(teste="wilcoxon_pareado", estatistica=teste.statistic, p=teste.pvalue,
                         efeito_rank_biserial=rank_biserial_pareado(d))
        linhas.append(linha)
    tabela = pd.DataFrame(linhas)
    testados = tabela.p.notna()
    tabela["p_holm"] = np.nan
    if testados.any():
        tabela.loc[testados, "p_holm"] = multipletests(tabela.loc[testados, "p"], method="holm")[1]
    tabela["p_holm_familia_n"] = int(testados.sum())
    return tabela


def ponderacao_lead_time(commits, df=None, minimo_releases=5):
    """Quanto o tamanho de uma release acompanha o seu lead time (a).

    A variante (b) pondera cada release pelo número de commits; se releases com mais
    commits também têm o commit mais antigo mais distante, (b) se aproxima de (a).
    Mede-se o Spearman entre commits por release e lead time máximo da release, no
    conjunto e dentro de cada projeto com variação suficiente.
    """
    releases = commits.groupby(["full_name", "release_id"]).horas.agg(n="size", maximo="max").reset_index()
    rhos = []
    for _, grupo in releases.groupby("full_name"):
        if len(grupo) >= minimo_releases and grupo.n.nunique() > 1 and grupo.maximo.nunique() > 1:
            rhos.append(stats.spearmanr(grupo.n, grupo.maximo).statistic)
    rhos = np.asarray(rhos, dtype=float)
    indicadores = [
        ("releases_com_commits", len(releases), "Releases com ao menos um commit válido"),
        ("commits_validos", len(commits), "Pares release/commit usados no lead time"),
        ("mediana_commits_por_release", releases.n.median(), "Commits válidos por release"),
        ("q1_commits_por_release", releases.n.quantile(.25), "Primeiro quartil de commits por release"),
        ("q3_commits_por_release", releases.n.quantile(.75), "Terceiro quartil de commits por release"),
        ("proporcao_releases_um_commit", (releases.n == 1).mean(), "Releases com um único commit, em que a = b"),
        ("rho_agregado", stats.spearmanr(releases.n, releases.maximo).statistic if len(releases) > 2 else np.nan,
         "Spearman entre commits e lead time máximo, todas as releases juntas"),
        ("projetos_avaliados", len(rhos), f"Projetos com ao menos {minimo_releases} releases e variação"),
        ("rho_mediano_projetos", np.median(rhos) if rhos.size else np.nan, "Mediana do Spearman por projeto"),
        ("q1_rho_projetos", np.quantile(rhos, .25) if rhos.size else np.nan, "Primeiro quartil do Spearman"),
        ("q3_rho_projetos", np.quantile(rhos, .75) if rhos.size else np.nan, "Terceiro quartil do Spearman"),
        ("proporcao_projetos_rho_positivo", (rhos > 0).mean() if rhos.size else np.nan,
         "Projetos em que releases maiores têm lead time máximo maior"),
    ]
    if df is not None:
        # Liga o tamanho das releases à comunidade, para interpretar a RQ06.
        por_projeto = releases.groupby("full_name").n.median().rename("commits")
        pares = df.set_index("full_name").join(por_projeto, how="inner")
        pares = pares.assign(contribuidores=pd.to_numeric(pares.contribuidores)).dropna(
            subset=["contribuidores", "commits"])
        indicadores.append(("rho_contribuidores_commits_por_release",
                            stats.spearmanr(pares.contribuidores, pares.commits).statistic
                            if len(pares) > 2 else np.nan,
                            "Spearman entre contribuidores e mediana de commits por release do projeto"))
    return pd.DataFrame(indicadores, columns=["indicador", "valor", "descricao"])


def mediana_pior_caso(concluidos, censurados):
    """Mediana se cada episódio censurado durasse mais que todos os concluídos.

    É um limite superior simples para o efeito da censura: os censurados ocupam o
    topo da ordenação. Se forem metade ou mais, a mediana não é limitada (infinito).
    """
    ordenados = np.sort(np.asarray(concluidos, dtype=float))
    total = len(ordenados) + int(censurados)
    if total == 0:
        return np.nan
    centrais = [(total - 1) // 2, total // 2]
    if centrais[1] >= len(ordenados):
        return np.inf
    return float(ordenados[centrais].mean())


def censura(df, episodios):
    """Proporção de episódios censurados e o quanto ela poderia mover as medianas."""
    total, censurados = int(df.episodios_total.sum()), int(df.episodios_censurados.sum())
    com_episodios = df.episodios_total > 0
    com_censura = df.episodios_censurados > 0
    proporcoes = df.loc[com_episodios, "proporcao_censurados"]
    horas = episodios.horas.to_numpy(float)
    por_repo = episodios.groupby("full_name").horas.apply(list)
    pior_caso_repos = [mediana_pior_caso(por_repo.get(r.full_name, []), r.episodios_censurados)
                       for _, r in df[com_episodios].iterrows()]
    indicadores = [
        ("episodios_total", total, "Episódios de falha abertos após um sucesso"),
        ("episodios_concluidos", total - censurados, "Episódios encerrados por um sucesso posterior"),
        ("episodios_censurados", censurados, "Episódios sem sucesso posterior até o fim dos runs"),
        ("proporcao_episodios_censurados", censurados / total if total else np.nan,
         "episodios_censurados / episodios_total"),
        ("repositorios", len(df), "Projetos da amostra"),
        ("repositorios_com_episodios", int(com_episodios.sum()), "Projetos com ao menos um episódio"),
        ("repositorios_sem_episodios", int((~com_episodios).sum()),
         "Projetos sem episódio observável; recuperação ausente, não zero"),
        ("repositorios_somente_censurados", int((com_episodios & (df.episodios_concluidos == 0)).sum()),
         "Projetos cujos episódios estão todos censurados"),
        ("repositorios_com_censura", int(com_censura.sum()), "Projetos com ao menos um episódio censurado"),
        ("proporcao_repositorios_com_censura",
         com_censura.sum() / com_episodios.sum() if com_episodios.any() else np.nan,
         "repositorios_com_censura / repositorios_com_episodios"),
        ("mediana_proporcao_censurados", proporcoes.median(), "Mediana por projeto com episódios"),
        ("q3_proporcao_censurados", proporcoes.quantile(.75), "Terceiro quartil por projeto com episódios"),
        ("maximo_proporcao_censurados", proporcoes.max(), "Maior proporção de censura de um projeto"),
        ("mediana_proporcao_censurados_com_censura", df.loc[com_censura, "proporcao_censurados"].median(),
         "Mediana entre os projetos com ao menos um censurado"),
        ("mediana_episodios_horas", np.median(horas) if horas.size else np.nan,
         "Mediana dos episódios concluídos de todos os projetos"),
        ("mediana_episodios_pior_caso_horas", mediana_pior_caso(horas, censurados),
         "Mediana dos episódios supondo cada censurado mais longo que todos os concluídos"),
        ("p90_episodios_horas", np.quantile(horas, .9) if horas.size else np.nan,
         "Percentil 90 dos episódios concluídos"),
        ("proporcao_episodios_24h_ou_mais", (horas >= 24).mean() if horas.size else np.nan,
         "Episódios concluídos com 24 horas ou mais"),
        ("proporcao_episodios_168h_ou_mais", (horas >= 168).mean() if horas.size else np.nan,
         "Episódios concluídos com uma semana ou mais"),
        ("mediana_repositorios_horas", df.tempo_recuperacao_horas.median(),
         "Mediana das medianas por projeto (episódios concluídos)"),
        ("mediana_repositorios_pior_caso_horas", np.median(pior_caso_repos) if pior_caso_repos else np.nan,
         "Mediana das medianas por projeto no pior caso de censura"),
    ]
    return pd.DataFrame(indicadores, columns=["indicador", "valor", "descricao"])


def analisar(df, episodios, commits=None):
    df = df.sort_values("full_name").reset_index(drop=True)
    tabelas = {"rq01_04_descritivas": descritivas(df, episodios),
               "rq01_04_pareadas": comparar_pares(df),
               "rq04_censura": censura(df, episodios),
               "rq04_episodios": episodios.sort_values(["full_name", "ordem"]).reset_index(drop=True)}
    if commits is not None:
        tabelas["rq02_ponderacao"] = ponderacao_lead_time(commits, df)
    return tabelas
