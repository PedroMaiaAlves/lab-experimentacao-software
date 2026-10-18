"""Entradas congeladas da S02 para a parte A, conferidas por hash antes do uso."""
import hashlib
import io
import json
from pathlib import Path
from zipfile import ZipFile

import numpy as np
import pandas as pd

from metricas.lead_time import data_commit_valida
from metricas.recuperacao import calcular_tempo_recuperacao

NUMERICAS = (
    "deployment_frequency", "deployment_frequency_prereleases", "deployment_frequency_tags",
    "lead_time_a_horas", "lead_time_b_horas", "cfr_a", "cfr_b", "tempo_recuperacao_horas",
    "episodios_total", "episodios_concluidos", "episodios_censurados", "proporcao_censurados",
)


def sha256(caminho):
    with Path(caminho).open("rb") as arquivo:
        return hashlib.file_digest(arquivo, "sha256").hexdigest()


def ler_json(caminho):
    return json.loads(Path(caminho).read_text(encoding="utf-8"))


def caminhos(dataset="data/dataset.csv", amostra=None, pacote=None):
    """Resolve as entradas; amostra e pacote ficam por padrão ao lado do dataset."""
    dataset = Path(dataset)
    amostra = Path(amostra) if amostra else dataset.parent / "amostra_final.csv"
    pacote = Path(pacote) if pacote else dataset.parent / "fontes_s02.zip"
    return dataset, amostra, pacote


def carregar_dataset(dataset="data/dataset.csv", amostra=None):
    """Lê o dataset congelado e confere hashes e cobertura; não recalcula métricas."""
    dataset, amostra, _ = caminhos(dataset, amostra)
    manifesto = ler_json(dataset.with_suffix(".manifest.json"))
    congelada = ler_json(amostra.with_suffix(".manifest.json"))
    if sha256(dataset) != manifesto["dataset_sha256"]:
        raise ValueError("hash do dataset diverge do manifesto")
    if not sha256(amostra) == manifesto["amostra_sha256"] == congelada["amostra_sha256"]:
        raise ValueError("hash da amostra diverge dos manifestos")
    # Sem conversão automática de NA: um repositório ou linguagem "NA" continua texto.
    df = pd.read_csv(dataset, dtype=str, keep_default_na=False).replace("", np.nan)
    faltando = sorted(set(NUMERICAS) - set(df.columns))
    if faltando:
        raise ValueError(f"colunas ausentes no dataset: {faltando}")
    nomes = pd.read_csv(amostra, dtype=str, keep_default_na=False)["full_name"]
    if (df.full_name.isna().any() or df.full_name.duplicated().any()
            or set(df.full_name) != set(nomes) or len(df) != manifesto["repositorios"]):
        raise ValueError("dataset não cobre exatamente a amostra congelada")
    for coluna in NUMERICAS:
        df[coluna] = pd.to_numeric(df[coluna], errors="raise")
        if (df[coluna].dropna() < 0).any():
            raise ValueError(f"valor negativo em {coluna}")
    origens = {
        "dataset_sha256": manifesto["dataset_sha256"],
        "dataset_manifest_sha256": sha256(dataset.with_suffix(".manifest.json")),
        "amostra_sha256": congelada["amostra_sha256"],
        "amostra_manifest_sha256": sha256(amostra.with_suffix(".manifest.json")),
        "janela_inicio": congelada["janela_inicio"], "janela_fim": congelada["janela_fim"],
        "repositorios": len(df),
    }
    return df.sort_values("full_name").reset_index(drop=True), origens


def carregar_episodios(df, dataset="data/dataset.csv", amostra=None, pacote=None):
    """Recalcula os episódios de recuperação a partir dos runs congelados.

    Cada arquivo de runs precisa ter o hash registrado no manifesto da amostra, e a
    agregação precisa reproduzir as contagens e a mediana do dataset; caso
    contrário a análise para, em vez de misturar fontes diferentes.
    """
    _, amostra, pacote = caminhos(dataset, amostra, pacote)
    fontes = ler_json(amostra.with_suffix(".manifest.json"))["fontes_repos_sha256"]
    linhas = []
    with ZipFile(pacote) as arquivo:
        for _, repo in df.iterrows():
            arquivos = fontes[repo.full_name]
            nome = next(n for n in arquivos if n.startswith("workflow_runs/"))
            bruto = arquivo.read(nome)
            if hashlib.sha256(bruto).hexdigest() != arquivos[nome]:
                raise ValueError(f"hash divergente nos runs de {repo.full_name}")
            resultado = calcular_tempo_recuperacao(json.loads(bruto)["workflow_runs"])
            mediana = resultado.mediana_horas
            if (len(resultado.episodios_horas) != repo.episodios_concluidos
                    or resultado.episodios_censurados != repo.episodios_censurados
                    or (mediana is None) != pd.isna(repo.tempo_recuperacao_horas)
                    or (mediana is not None and not np.isclose(mediana, repo.tempo_recuperacao_horas,
                                                                rtol=1e-12, atol=1e-9))):
                raise ValueError(f"episódios recalculados divergem do dataset: {repo.full_name}")
            linhas += [dict(full_name=repo.full_name, ordem=i, horas=horas)
                       for i, horas in enumerate(resultado.episodios_horas, start=1)]
    return pd.DataFrame(linhas, columns=["full_name", "ordem", "horas"]), sha256(pacote)


def carregar_commits(df, dataset="data/dataset.csv", amostra=None, pacote=None):
    """Pares release/commit válidos do lead time, conferidos contra o dataset.

    Usa a mesma regra de `metricas.lead_time`: commits com data inválida ou posterior
    à publicação ficam de fora. As medianas (a) e (b) recalculadas precisam coincidir
    com o dataset em todos os projetos.
    """
    _, amostra, pacote = caminhos(dataset, amostra, pacote)
    esperado = ler_json(amostra.with_suffix(".manifest.json"))["fontes_sha256"]["commits_entre_releases.csv"]
    with ZipFile(pacote) as arquivo:
        bruto = arquivo.read("commits_entre_releases.csv")
    if hashlib.sha256(bruto).hexdigest() != esperado:
        raise ValueError("hash divergente em commits_entre_releases.csv")
    commits = pd.read_csv(io.BytesIO(bruto), dtype=str, keep_default_na=False)
    commits = commits[commits.full_name.isin(df.full_name)]
    validos = [data_commit_valida(p, a) for p, a in zip(commits.published_at, commits.author_date)]
    commits = commits.loc[pd.Series(validos, index=commits.index, dtype=bool)].assign(horas=lambda c: (
        pd.to_datetime(c.published_at, utc=True) - pd.to_datetime(c.author_date, utc=True)
    ).dt.total_seconds() / 3600)
    por_release = commits.groupby(["full_name", "release_id"]).horas.max()
    recalculado = pd.DataFrame({"a": por_release.groupby(level=0).median(),
                                "b": commits.groupby("full_name").horas.median()})
    dados = df.set_index("full_name").reindex(recalculado.index)
    if (len(recalculado) != df.lead_time_a_horas.notna().sum()
            or not np.allclose(recalculado.a, dados.lead_time_a_horas, rtol=1e-12, atol=1e-6)
            or not np.allclose(recalculado.b, dados.lead_time_b_horas, rtol=1e-12, atol=1e-6)):
        raise ValueError("lead times recalculados divergem do dataset")
    tabela = commits[["full_name", "release_id", "horas"]].reset_index(drop=True)
    return tabela, len(validos) - int(sum(validos))
