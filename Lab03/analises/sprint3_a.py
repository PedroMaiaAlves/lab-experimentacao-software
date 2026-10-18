"""Comando único e offline da parte A: python -m analises.sprint3_a."""
import argparse
import importlib.metadata
import io
import json
import platform
from pathlib import Path

import pandas as pd

from analises import classificacao_c1, rq01_04
from analises.entrada import carregar_commits, carregar_dataset, carregar_episodios, sha256
from analises.graficos_a import (distribuicao_c1, distribuicoes, inteiro, numero, p_formatado, por_unidade,
                                 salvar_figura, tabela_c1, tabela_descritivas, tabela_numeros, tabela_pareadas)

MODULOS = ("__init__.py", "entrada.py", "rq01_04.py", "classificacao_c1.py", "graficos_a.py", "sprint3_a.py")
PACOTES = ("numpy", "pandas", "scipy", "statsmodels", "matplotlib")
DIMENSOES_TEX = {"deployment_frequency": "Freq", "lead_time": "Lead", "cfr": "Cfr", "tempo_recuperacao": "Rec",
                 "geral": "Geral", "geral_minimo_3": "GeralTres"}
CATEGORIAS_TEX = {"Elite": "Elite", "High": "High", "Medium": "Medium", "Low": "Low", "sem_categoria": "Sem"}


def numeros_c1(c1):
    """Macros da classificação C1: contagem e porcentagem por dimensão e categoria."""
    pct = lambda v: numero(100 * v, 1)
    numeros = {}
    for _, r in c1["c1_distribuicao"].iterrows():
        nome = f"labACOne{DIMENSOES_TEX[r.dimensao]}{CATEGORIAS_TEX[r.categoria]}"
        numeros[nome], numeros[nome + "Pct"] = inteiro(r.n), pct(r.proporcao_total)
    tabela = c1["classificacao_C1"]
    completos = tabela.mediana_notas.dropna()
    sem_geral = tabela[tabela.categoria_geral.isna()].categoria_geral_minimo_3
    numeros.update({
        "labACOneClassificados": inteiro(len(completos)),
        "labACOneFracionarias": inteiro((completos % 1 != 0).sum()),
        "labACOneFracionariasPct": pct((completos % 1 != 0).mean()),
        **{f"labACOneSemGeral{c}": inteiro((sem_geral == c).sum()) for c in classificacao_c1.CATEGORIAS},
    })
    return numeros


def numeros_texto(df, tabelas):
    """Valores citados no artigo, formatados a partir das mesmas tabelas publicadas."""
    d = tabelas["rq01_04_descritivas"].set_index("metrica")
    p = tabelas["rq01_04_pareadas"].set_index("x")
    c = tabelas["rq04_censura"].set_index("indicador").valor
    pct = lambda v: numero(100 * v, 1)

    def resumo(prefixo, metrica):
        u = d.loc[metrica, "unidade"]
        return {f"{prefixo}Mediana": por_unidade(d.loc[metrica, "mediana"], u),
                f"{prefixo}QUm": por_unidade(d.loc[metrica, "q1"], u),
                f"{prefixo}QTres": por_unidade(d.loc[metrica, "q3"], u),
                f"{prefixo}Maximo": por_unidade(d.loc[metrica, "maximo"], u),
                f"{prefixo}N": inteiro(d.loc[metrica, "n"])}

    def par(prefixo, x):
        r = p.loc[x]
        return {f"{prefixo}XMaior": inteiro(r.n_x_maior), f"{prefixo}Iguais": inteiro(r.n_iguais),
                f"{prefixo}XMenor": inteiro(r.n_x_menor),
                f"{prefixo}DifMediana": por_unidade(r.mediana_diferenca, rq01_04.METRICAS[x][2]),
                f"{prefixo}Razao": numero(r.mediana_razao, 2), f"{prefixo}R": numero(r.efeito_rank_biserial),
                f"{prefixo}PHolm": p_formatado(r.p_holm)}

    frequencia = df.deployment_frequency
    numeros = {
        **resumo("labAFreq", "deployment_frequency"),
        **resumo("labAFreqPre", "deployment_frequency_prereleases"),
        **resumo("labAFreqTags", "deployment_frequency_tags"),
        "labAFreqDiarios": inteiro((frequencia >= 7).sum()),
        "labAFreqSemanais": inteiro((frequencia >= 1).sum()),
        "labAFreqSemanaisPct": pct((frequencia >= 1).mean()),
        **par("labAFreqPre", "deployment_frequency_prereleases"),
        **par("labAFreqTags", "deployment_frequency_tags"),
        **resumo("labALeadA", "lead_time_a_horas"),
        **resumo("labALeadB", "lead_time_b_horas"),
        **par("labALead", "lead_time_a_horas"),
        **resumo("labACfrA", "cfr_a"),
        **resumo("labACfrB", "cfr_b"),
        "labACfrBAusentes": inteiro(df.cfr_b.isna().sum()),
        "labACfrBZeros": inteiro((df.cfr_b == 0).sum()),
        "labACfrBZerosPct": pct((df.cfr_b.dropna() == 0).mean()),
        "labACfrAZeros": inteiro((df.cfr_a == 0).sum()),
        **par("labACfr", "cfr_a"),
        **resumo("labARec", "tempo_recuperacao_horas"),
        "labARecAusentes": inteiro(df.tempo_recuperacao_horas.isna().sum()),
        **resumo("labAEp", "tempo_recuperacao_episodio_horas"),
        "labAEpTotal": inteiro(c.episodios_total),
        "labAEpCensurados": inteiro(c.episodios_censurados),
        "labAEpCensuradosPct": pct(c.proporcao_episodios_censurados),
        "labAEpPNoventa": por_unidade(c.p90_episodios_horas, "horas"),
        "labAEpDiaPct": pct(c.proporcao_episodios_24h_ou_mais),
        "labAEpSemanaPct": pct(c.proporcao_episodios_168h_ou_mais),
        "labAEpPiorCaso": por_unidade(c.mediana_episodios_pior_caso_horas, "horas"),
        "labARecPiorCaso": por_unidade(c.mediana_repositorios_pior_caso_horas, "horas"),
        "labARepoCensura": inteiro(c.repositorios_com_censura),
        "labARepoCensuraPct": pct(c.proporcao_repositorios_com_censura),
        "labARepoSemEpisodios": inteiro(c.repositorios_sem_episodios),
    }
    if "rq02_ponderacao" in tabelas:
        w = tabelas["rq02_ponderacao"].set_index("indicador").valor
        numeros.update({
            "labALeadReleases": inteiro(w.releases_com_commits),
            "labALeadCommitsMediana": inteiro(w.mediana_commits_por_release),
            "labALeadCommitsQUm": inteiro(w.q1_commits_por_release),
            "labALeadCommitsQTres": inteiro(w.q3_commits_por_release),
            "labALeadUmCommitPct": pct(w.proporcao_releases_um_commit),
            "labALeadRhoAgregado": numero(w.rho_agregado, 2),
            "labALeadProjetosRho": inteiro(w.projetos_avaliados),
            "labALeadRhoMediano": numero(w.rho_mediano_projetos, 2),
            "labALeadRhoPositivosPct": pct(w.proporcao_projetos_rho_positivo),
            "labALeadRhoContribuidores": numero(w.rho_contribuidores_commits_por_release, 2),
        })
    return numeros


def conferir_publicado(tabela, caminho, rtol=1e-9):
    """Compara uma tabela recalculada com o CSV publicado, lidos do mesmo jeito."""
    recalculada = pd.read_csv(io.StringIO(tabela.to_csv(index=False, float_format="%.17g")))
    pd.testing.assert_frame_equal(recalculada, pd.read_csv(caminho), check_dtype=False, rtol=rtol)


def validar_saida(saida, dataset):
    saida, fontes = Path(saida).resolve(), Path(dataset).resolve().parent
    # Artefatos de análise nunca são escritos na árvore dos dados congelados.
    if saida == fontes or saida.is_relative_to(fontes) or fontes.is_relative_to(saida):
        raise ValueError("a saída deve ficar fora da pasta dos dados congelados")
    return saida


def _csv(tabela, destino):
    tabela.to_csv(destino, index=False, float_format="%.17g", lineterminator="\n")


def executar(dataset="data/dataset.csv", amostra=None, pacote=None, saida="results/s03_a",
             classificacao="data/classificacao_C1.csv"):
    saida = validar_saida(saida, dataset)
    df, origens = carregar_dataset(dataset, amostra)
    episodios, pacote_sha = carregar_episodios(df, dataset, amostra, pacote)
    commits, _ = carregar_commits(df, dataset, amostra, pacote)
    tabelas = rq01_04.analisar(df, episodios, commits)
    c1 = classificacao_c1.analisar(df)
    saida.mkdir(parents=True, exist_ok=True)
    for nome, tabela in tabelas.items():
        _csv(tabela, saida / f"{nome}.csv")
    for nome in ("c1_distribuicao", "c1_ausencias"):
        _csv(c1[nome], saida / f"{nome}.csv")
    # A tabela por projeto é a entrada de C1 para a RQ07 e fica com os dados (critério da S03-A2).
    classificacao = Path(classificacao)
    classificacao.parent.mkdir(parents=True, exist_ok=True)
    _csv(c1["classificacao_C1"], classificacao)
    salvar_figura(distribuicoes(df, episodios), saida / "rq01_04_distribuicoes")
    salvar_figura(distribuicao_c1(c1["c1_distribuicao"]), saida / "c1_distribuicao")
    tabela_descritivas(tabelas["rq01_04_descritivas"], saida / "rq01_04_tabela.tex")
    tabela_pareadas(tabelas["rq01_04_pareadas"], saida / "rq01_04_pareadas.tex")
    tabela_c1(c1["c1_distribuicao"], saida / "c1_tabela.tex")
    tabela_numeros({**numeros_texto(df, tabelas), **numeros_c1(c1)}, saida / "numeros_a.tex")
    escrever_manifesto(saida, {**origens, "fontes_s02_zip_sha256": pacote_sha},
                       {"quartis": "interpolação linear; IQR = Q3 - Q1",
                        "unidade_analise": "repositório; episódios apenas no indicador agregado da RQ04",
                        "comparacoes_pareadas": "Wilcoxon bilateral, zero_method=wilcox, só H2 e H3",
                        "familia_holm": "2 p-valores (H2, H3)", "efeito": "rank-biserial pareado",
                        "ponderacao_lead_time": "Spearman commits x lead time máximo; projetos com >= 5 releases",
                        "semente_jitter_figura": 42,
                        "combinacao_C1": classificacao_c1.COMBINACAO_C1,
                        "classificacao_geral": "mediana das 4 notas arredondada para baixo; exige as 4 métricas"},
                       {classificacao.name: sha256(classificacao)})
    return {**tabelas, **c1}


def escrever_manifesto(saida, origens, parametros, externos=None):
    base = Path(__file__).parent
    manifesto = {
        "origens": origens, "parametros": parametros,
        "ambiente": {"python": platform.python_version(), "sistema": platform.system(),
                     "pacotes": {p: importlib.metadata.version(p) for p in PACOTES}},
        "codigo_sha256": {nome: sha256(base / nome) for nome in MODULOS if (base / nome).exists()},
        "artefatos_sha256": {p.name: sha256(p) for p in sorted(saida.iterdir())
                             if p.is_file() and p.suffix in {".csv", ".tex", ".png", ".pdf"}},
        "artefatos_fora_da_saida_sha256": externos or {},
    }
    (saida / "manifesto.json").write_text(json.dumps(manifesto, ensure_ascii=False, indent=2) + "\n",
                                          encoding="utf-8", newline="\n")


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset", default="data/dataset.csv")
    parser.add_argument("--amostra", help="padrão: amostra_final.csv ao lado do dataset")
    parser.add_argument("--pacote", help="padrão: fontes_s02.zip ao lado do dataset")
    parser.add_argument("--saida", default="results/s03_a")
    parser.add_argument("--classificacao", default="data/classificacao_C1.csv",
                        help="tabela C1 por projeto, usada também pela RQ07")
    args = parser.parse_args(argv)
    tabelas = executar(**vars(args))
    colunas = ["rq", "metrica", "n", "mediana", "q1", "q3", "iqr"]
    print(tabelas["rq01_04_descritivas"][colunas].to_string(index=False))
    geral = tabelas["c1_distribuicao"].query("dimensao == 'geral'")
    print("C1 geral:", ", ".join(f"{r.categoria}={r.n}" for _, r in geral.iterrows()))
    print(f"artefatos em {args.saida} e {args.classificacao}")


if __name__ == "__main__":
    main()
