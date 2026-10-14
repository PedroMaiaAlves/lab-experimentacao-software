"""S02-A3: concordância entre avaliadores (kappa de Fleiss) e rótulo de consenso.

Uso (na raiz do projeto):
    python -m validacao.concordancia
"""
import argparse
import math
from collections import Counter
from pathlib import Path

import pandas as pd
from statsmodels.stats.inter_rater import aggregate_raters, fleiss_kappa

from validacao.amostra_ouro import CORRETIVA, ENTREGAS, TIPOS

AVALIADORES = ["A", "B", "C"]
# dimensão -> (aba, colunas-chave, coluna do rótulo, valores permitidos, nome para o artigo)
DIMENSOES = {
    "tipo_projeto": ("repositorios", ["full_name"], "tipo_projeto", TIPOS, "Tipo do projeto"),
    "releases_sao_entregas": ("repositorios", ["full_name"], "releases_sao_entregas", ENTREGAS,
                              "Releases são entregas reais"),
    "corretiva": ("releases", ["full_name", "release_id"], "corretiva", CORRETIVA, "Release corretiva"),
}


class ErroRotulos(Exception):
    """Rótulos ausentes, inválidos ou itens diferentes entre os avaliadores."""


def _normalizar_chave(df, chaves):
    partes = []
    for c in chaves:
        partes.append(df[c].fillna("").astype(str).str.strip().str.replace(r"\.0$", "", regex=True))
    chave = partes[0]
    for p in partes[1:]:
        chave = chave + "|" + p
    return chave


def ler_rotulos(pasta):
    pasta = Path(pasta)
    dados = {}
    for av in AVALIADORES:
        caminho = pasta / f"rotulos_{av}.xlsx"
        if not caminho.exists():
            raise ErroRotulos(f"Arquivo não encontrado: {caminho}")
        dados[av] = {aba: pd.read_excel(caminho, sheet_name=aba, dtype=str)
                     for aba in ("repositorios", "releases")}
    return dados


def tabela_dimensao(dados, dim):
    """DataFrame (itens x A,B,C) com os rótulos canônicos; levanta ErroRotulos se houver problema."""
    aba, chaves, coluna, permitidos, _ = DIMENSOES[dim]
    canon = {p.lower(): p for p in permitidos}
    colunas, problemas, indices = {}, [], {}
    for av in AVALIADORES:
        df = dados[av][aba].copy()
        df["_chave"] = _normalizar_chave(df, chaves)
        df["_linha"] = df.index + 2  # linha no Excel (cabeçalho = 1)
        bruto = df[coluna].fillna("").astype(str).str.strip().str.lower()
        for chave, linha, valor in zip(df["_chave"], df["_linha"], bruto):
            if valor not in canon:
                problemas.append(f"{av} / {dim} / linha {linha} ({chave}): "
                                 f"{'em branco' if not valor else repr(valor)}")
        colunas[av] = pd.Series([canon.get(v) for v in bruto], index=df["_chave"].values)
        indices[av] = set(df["_chave"])
    if len({frozenset(i) for i in indices.values()}) > 1:
        raise ErroRotulos(f"Os avaliadores não têm os mesmos itens na dimensão {dim}.")
    if problemas:
        raise ErroRotulos("Rótulos inválidos ou em branco:\n  " + "\n  ".join(problemas))
    tab = pd.DataFrame(colunas)
    return tab[~tab.index.duplicated()].sort_index()


def calcular_kappa(tab):
    """Kappa de Fleiss de uma tabela itens x avaliadores. NaN se só houve uma categoria."""
    categorias = sorted(set(tab.to_numpy().ravel()))
    if len(categorias) < 2:
        return float("nan")
    mapa = {c: i for i, c in enumerate(categorias)}
    codigos = tab.apply(lambda col: col.map(mapa)).to_numpy()
    contagens, _ = aggregate_raters(codigos)
    return float(fleiss_kappa(contagens, method="fleiss"))


def interpretar_kappa(k):
    """Faixas de Landis & Koch (1977)."""
    if k is None or (isinstance(k, float) and math.isnan(k)):
        return "indefinido (sem variação)"
    if k < 0:
        return "pobre"
    if k <= 0.20:
        return "leve"
    if k <= 0.40:
        return "razoável"
    if k <= 0.60:
        return "moderada"
    if k <= 0.80:
        return "substancial"
    return "quase perfeita"


def consenso(tab, dim, decisoes):
    """Maioria simples; 1-1-1 usa as decisões da reunião (decisoes[(dim, chave)])."""
    linhas = []
    for chave, row in tab.iterrows():
        votos = Counter(row[av] for av in AVALIADORES)
        rotulo, n = votos.most_common(1)[0]
        if n == 3:
            tipo = "unanime"
        elif n == 2:
            tipo = "maioria"
        else:
            tipo, rotulo = "reuniao", decisoes.get((dim, chave), "")
        linhas.append({"chave": chave, "rotulo": rotulo, "decisao": tipo})
    return pd.DataFrame(linhas).set_index("chave")


def ler_decisoes(caminho):
    """CSV opcional com colunas dimensao,chave,rotulo (decisões dos casos 1-1-1)."""
    caminho = Path(caminho)
    if not caminho.exists():
        return {}
    df = pd.read_csv(caminho, dtype=str, keep_default_na=False)
    decisoes = {}
    for r in df.itertuples():
        if r.dimensao not in DIMENSOES:
            raise ErroRotulos(f"Dimensão desconhecida em {caminho}: {r.dimensao}")
        canon = {p.lower(): p for p in DIMENSOES[r.dimensao][3]}
        valor = canon.get(r.rotulo.strip().lower())
        if valor is None:
            raise ErroRotulos(f"Rótulo inválido em {caminho}: {r.dimensao} / {r.chave} / {r.rotulo!r}")
        decisoes[(r.dimensao, r.chave.strip())] = valor
    return decisoes


def _num(x, casas=2):
    return "--" if x is None or (isinstance(x, float) and math.isnan(x)) else f"{x:.{casas}f}".replace(".", ",")


def tabela_tex(linhas_kappa):
    corpo = "".join(
        f"{r['nome']} & {r['n_itens']} & {_num(r['concordancia_unanime_pct'], 1)} & "
        f"{_num(r['kappa'])} & {r['interpretacao']} \\\\\n" for r in linhas_kappa)
    return ("\\begin{table}[ht]\n\\centering\n"
            "\\caption{Concordância entre os três avaliadores (kappa de Fleiss).}\n\\label{tab:kappa}\n"
            "\\begin{tabular}{lrrrl}\n\\hline\n"
            "Dimensão & $n$ & Unânime (\\%) & $\\kappa$ & Interpretação \\\\\n\\hline\n"
            f"{corpo}\\hline\n\\end{{tabular}}\n\\end{{table}}\n")


def executar(pasta="data/amostra_ouro", tex=None):
    pasta = Path(pasta)
    dados = ler_rotulos(pasta / "rotulos")
    decisoes = ler_decisoes(pasta / "decisoes_reuniao.csv")

    tabs, cons, linhas_kappa, divergentes = {}, {}, [], []
    for dim, (_, _, _, _, nome) in DIMENSOES.items():
        tabs[dim] = tabela_dimensao(dados, dim)
        cons[dim] = consenso(tabs[dim], dim, decisoes)
        k = calcular_kappa(tabs[dim])
        c = cons[dim]
        linhas_kappa.append({
            "dimensao": dim, "nome": nome, "n_itens": len(c), "kappa": k,
            "interpretacao": interpretar_kappa(k),
            "concordancia_unanime_pct": round(100 * (c["decisao"] == "unanime").mean(), 1),
            "n_maioria": int((c["decisao"] == "maioria").sum()),
            "n_reuniao": int((c["decisao"] == "reuniao").sum())})
        for chave, row in c[c["decisao"] != "unanime"].iterrows():
            divergentes.append({"dimensao": dim, "chave": chave, **{av: tabs[dim].loc[chave, av] for av in AVALIADORES},
                                "desempate": row["decisao"], "rotulo_final": row["rotulo"]})

    repos = pd.DataFrame(index=tabs["tipo_projeto"].index)
    for dim in ("tipo_projeto", "releases_sao_entregas"):
        for av in AVALIADORES:
            repos[f"{dim}_{av}"] = tabs[dim][av]
        repos[dim] = cons[dim]["rotulo"]
        repos[f"{dim}_decisao"] = cons[dim]["decisao"]
    repos.index.name = "full_name"
    repos.to_csv(pasta / "consenso_repos.csv", encoding="utf-8")

    rel = pd.DataFrame(index=tabs["corretiva"].index)
    partes = rel.index.to_series().str.rsplit("|", n=1, expand=True)
    rel["full_name"], rel["release_id"] = partes[0], partes[1]
    df_a = dados["A"]["releases"].copy()
    df_a["_chave"] = _normalizar_chave(df_a, ["full_name", "release_id"])
    rel["tag_name"] = df_a.drop_duplicates("_chave").set_index("_chave")["tag_name"].reindex(rel.index)
    for av in AVALIADORES:
        rel[f"corretiva_{av}"] = tabs["corretiva"][av]
    rel["corretiva"] = cons["corretiva"]["rotulo"]
    rel["corretiva_decisao"] = cons["corretiva"]["decisao"]
    rel.reset_index(drop=True).to_csv(pasta / "consenso_releases.csv", index=False, encoding="utf-8")

    cols = ["dimensao", "n_itens", "kappa", "interpretacao", "concordancia_unanime_pct", "n_maioria", "n_reuniao"]
    pd.DataFrame(linhas_kappa)[cols].to_csv(pasta / "kappa_fleiss.csv", index=False, encoding="utf-8")
    pd.DataFrame(divergentes, columns=["dimensao", "chave", *AVALIADORES, "desempate", "rotulo_final"]).to_csv(
        pasta / "casos_divergentes.csv", index=False, encoding="utf-8")
    if tex:
        Path(tex).parent.mkdir(parents=True, exist_ok=True)
        Path(tex).write_text(tabela_tex(linhas_kappa), encoding="utf-8")

    for r in linhas_kappa:
        print(f"{r['nome']}: kappa = {_num(r['kappa'])} ({r['interpretacao']}); "
              f"unânime {r['concordancia_unanime_pct']}%; {r['n_reuniao']} caso(s) 1-1-1")
    pendentes = sum(r["n_reuniao"] for r in linhas_kappa) - sum(1 for d in divergentes if d["desempate"] == "reuniao" and d["rotulo_final"])
    if pendentes:
        print(f"\nATENÇÃO: {pendentes} caso(s) 1-1-1 sem decisão. Veja casos_divergentes.csv, decida em reunião e "
              f"registre em {pasta / 'decisoes_reuniao.csv'} (colunas: dimensao,chave,rotulo); depois rode de novo.")
        return 1
    return 0


def main(argv=None):
    ap = argparse.ArgumentParser(description="Kappa de Fleiss e consenso da amostra-ouro.")
    ap.add_argument("--pasta", default="data/amostra_ouro")
    ap.add_argument("--tex", default="docs/artigo/tabelas/kappa.tex", help="tabela LaTeX do artigo")
    a = ap.parse_args(argv)
    try:
        return executar(a.pasta, a.tex)
    except ErroRotulos as e:
        print(f"ERRO: {e}")
        return 2


if __name__ == "__main__":
    raise SystemExit(main())