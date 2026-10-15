"""S02-A5: gera as tabelas e macros LaTeX do artigo a partir dos CSVs e do config.yaml.

Os números do artigo vêm dos arquivos gerados pelo pipeline, então não ficam desatualizados.

Uso (na raiz do projeto):
    python -m validacao.artefatos_artigo
"""
import argparse
from datetime import date
from pathlib import Path
import re

import pandas as pd
import yaml

PENDENTE = r"\textbf{[PREENCHER]}"


def fmt_int(n):
    return f"{int(n):,}".replace(",", ".")


def fmt_data(iso):
    return date.fromisoformat(str(iso)).strftime("%d/%m/%Y")


def escapar(texto):
    for velho, novo in (("\\", "\\textbackslash{}"), ("_", "\\_"), ("%", "\\%"), ("&", "\\&"), ("#", "\\#")):
        texto = texto.replace(velho, novo)
    return texto


def limites_estrelas(faixas):
    """(mínimo, máximo ou None) das faixas do config, como '1000..1500' ou '>30000'."""
    los, his = [], []
    for f in faixas:
        f = str(f).strip()
        if ".." in f:
            lo, hi = f.split("..")
            los.append(int(lo))
            his.append(int(hi))
        elif f.startswith(">"):
            los.append(int(f[1:]))
            his.append(None)
        else:
            raise ValueError(f"Faixa de estrelas não reconhecida: {f}")
    return min(los), (None if any(h is None for h in his) else max(his))


def texto_faixa(lo, hi):
    return f"mais de {fmt_int(lo)} estrelas" if hi is None else f"{fmt_int(lo)} a {fmt_int(hi)} estrelas"


def ler_csv(caminho):
    caminho = Path(caminho)
    if not caminho.exists():
        return None
    return pd.read_csv(caminho, dtype=str, keep_default_na=False)


def _soma(df, coluna):
    return fmt_int(pd.to_numeric(df[coluna]).sum())


def calcular_macros(cfg, funil, saturados, lead, candidatos=None):
    faixas = cfg["selecao"]["faixas_estrelas"]
    if candidatos is not None:
        consultas = candidatos["consulta"].drop_duplicates()
        limites = [re.search(r"(?:^|\s)stars:([^\s]+)", q) for q in consultas]
        if not all(limites):
            raise ValueError("snapshot de candidatos sem faixas de estrelas auditáveis")
        faixas = [m.group(1) for m in limites]
    lo, hi = limites_estrelas(faixas)
    m = {
        "JanelaInicio": fmt_data(cfg["janela_inicio"]),
        "JanelaFim": fmt_data(cfg["janela_fim"]),
        "MinReleases": str(cfg["criterios"]["min_releases"]),
        "MinRuns": str(cfg["criterios"]["min_runs"]),
        "Semente": str(cfg["semente"]),
        "FaixaEstrelas": texto_faixa(lo, hi),
        "CandidatosBusca": PENDENTE, "CandidatosAvaliados": PENDENTE, "ReposAmostra": PENDENTE,
        "IntervalosSaturados": PENDENTE, "IntervalosIncompletos": PENDENTE, "ReposSaturados": PENDENTE,
        "ReleasesComparadas": PENDENTE, "ReleasesSemAnterior": PENDENTE, "ReleasesErroHttp": PENDENTE,
        "ReleasesSemCommits": PENDENTE, "CommitsDataInvalida": PENDENTE,
    }
    if funil is not None:
        linha = funil.set_index("etapa")["restaram"]
        for macro, etapa in (("CandidatosBusca", "candidatos_na_busca"),
                             ("CandidatosAvaliados", "candidatos_avaliados"),
                             ("ReposAmostra", "amostra_final")):
            if etapa in linha.index and linha[etapa] != "":
                m[macro] = fmt_int(linha[etapa])
    if saturados is not None:
        m["IntervalosSaturados"] = fmt_int(len(saturados))
        m["IntervalosIncompletos"] = fmt_int((saturados["status"] == "incompleto").sum())
        m["ReposSaturados"] = fmt_int(saturados["full_name"].nunique())
    if lead is not None:
        for macro, coluna in (("ReleasesComparadas", "releases_comparadas"),
                              ("ReleasesSemAnterior", "releases_sem_anterior"),
                              ("ReleasesErroHttp", "releases_erro_404"),
                              ("ReleasesSemCommits", "releases_sem_commits"),
                              ("CommitsDataInvalida", "commits_data_invalida")):
            m[macro] = _soma(lead, coluna)
    return m


def escrever_macros(macros, caminho):
    linhas = ["% Gerado por validacao/artefatos_artigo.py; não edite à mão."]
    linhas += [f"\\newcommand{{\\lab{nome}}}{{{valor}}}" for nome, valor in macros.items()]
    Path(caminho).write_text("\n".join(linhas) + "\n", encoding="utf-8")


def tabela_funil(funil, cfg):
    rotulos = {
        "candidatos_na_busca": "Candidatos retornados pela busca",
        "candidatos_avaliados": "Candidatos avaliados (ordem aleatória)",
        "actions": "Usam GitHub Actions",
        "releases": f"$\\geq$ {cfg['criterios']['min_releases']} releases publicadas na janela",
        "runs": f"$\\geq$ {cfg['criterios']['min_runs']} execuções de CI válidas",
        "amostra_final": "Amostra final",
    }

    def celula(v):
        return "--" if v == "" else fmt_int(v)

    corpo = "".join(
        f"{rotulos.get(r.etapa, escapar(r.etapa))} & {celula(r.entraram)} & {celula(r.descartados)} & "
        f"{celula(r.restaram)} \\\\\n" for r in funil.itertuples())
    return ("\\begin{table}[ht]\n\\centering\n\\caption{Funil de seleção dos repositórios.}\n\\label{tab:funil}\n"
            "\\begin{tabular}{lrrr}\n\\hline\nEtapa & Entraram & Descartados & Restaram \\\\\n\\hline\n"
            f"{corpo}\\hline\n\\end{{tabular}}\n\\end{{table}}\n")


def main(argv=None):
    ap = argparse.ArgumentParser(description="Gera tabelas e macros LaTeX do artigo.")
    ap.add_argument("--config", default="config.yaml")
    ap.add_argument("--dados", default="data")
    ap.add_argument("--saida", default="docs/artigo/tabelas")
    a = ap.parse_args(argv)

    with open(a.config, encoding="utf-8") as f:
        cfg = yaml.safe_load(f)
    dados, saida = Path(a.dados), Path(a.saida)
    saida.mkdir(parents=True, exist_ok=True)

    funil = ler_csv(dados / "funil.csv")
    macros = calcular_macros(cfg, funil, ler_csv(dados / "runs_saturados.csv"), ler_csv(dados / "lead_time.csv"),
                             ler_csv(dados / "candidatos.csv"))
    escrever_macros(macros, saida / "numeros.tex")
    if funil is None:
        print(f"AVISO: {dados / 'funil.csv'} não encontrado; tabela do funil não gerada.")
    else:
        (saida / "funil.tex").write_text(tabela_funil(funil, cfg), encoding="utf-8")
    pendentes = [k for k, v in macros.items() if v == PENDENTE]
    print(f"Arquivos gerados em {saida}/ ({len(macros)} macros).")
    if pendentes:
        print("Macros pendentes (arquivo de origem ausente): " + ", ".join(pendentes))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
