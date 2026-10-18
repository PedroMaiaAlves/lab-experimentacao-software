"""Contrato de entrada, estatísticas descritivas e multiplicidade."""
import csv
import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd
from statsmodels.stats.multitest import multipletests

METRICAS = {
    "deployment_frequency": ("Frequência", "releases/semana"),
    "lead_time_a_horas": ("Lead time (a)", "horas"),
    "lead_time_b_horas": ("Lead time (b)", "horas"),
    "cfr_a": ("CFR (a)", "proporção"),
    "cfr_b": ("CFR (b)", "proporção"),
    "tempo_recuperacao_horas": ("Recuperação", "horas"),
}
TIPOS = ("biblioteca/framework", "aplicação/serviço", "ferramenta CLI", "outro")
CONTAGENS = ("releases_avaliadas", "releases_sem_evidencia_textual", "episodios_total",
             "episodios_concluidos", "episodios_censurados")


def sha256(caminho):
    with Path(caminho).open("rb") as arquivo:
        return hashlib.file_digest(arquivo, "sha256").hexdigest()


def ler_json(caminho):
    return json.loads(Path(caminho).read_text(encoding="utf-8"))


def carregar_dataset(caminho="data/dataset.csv", amostra=None):
    """Confere hashes, população e domínio; não altera nem recalcula fontes."""
    caminho = Path(caminho)
    amostra = Path(amostra) if amostra else caminho.parent / "amostra_final.csv"
    manifesto = ler_json(caminho.with_suffix(".manifest.json"))
    congelada = ler_json(amostra.with_suffix(".manifest.json"))
    if sha256(caminho) != manifesto["dataset_sha256"]:
        raise ValueError("hash do dataset divergente")
    if not (sha256(amostra) == manifesto["amostra_sha256"] == congelada["amostra_sha256"]):
        raise ValueError("hash da amostra divergente")
    with caminho.open(encoding="utf-8-sig", newline="") as arquivo:
        leitor = csv.reader(arquivo)
        campos = next(leitor)
        if len(set(campos)) != len(campos) or any(len(r) != len(campos) for r in leitor):
            raise ValueError("estrutura CSV inválida")
    df = pd.read_csv(caminho, keep_default_na=False, dtype=str).replace("", np.nan)
    exigidos = set(METRICAS) | set(CONTAGENS) | {
        "full_name", "language", "tipo_projeto", "contribuidores", "heuristica_versao",
        "cfr_b_disponivel", "proporcao_censurados",
    }
    if not exigidos <= set(df.columns):
        raise ValueError(f"colunas ausentes: {sorted(exigidos - set(df.columns))}")
    nomes = pd.read_csv(amostra, dtype=str, keep_default_na=False)["full_name"]
    if (df.full_name.isna().any() or df.full_name.duplicated().any()
            or nomes.duplicated().any() or set(df.full_name) != set(nomes)
            or len(df) != manifesto["repositorios"] or len(df) != congelada["repositorios"]
            or len(df) < 300):
        raise ValueError("dataset não cobre exatamente a população congelada de pelo menos 300 projetos")
    if set(df.heuristica_versao) != {manifesto["heuristica"]["versao"]}:
        raise ValueError("versão da heurística divergente")
    for coluna in list(METRICAS) + ["contribuidores", "proporcao_censurados"] + list(CONTAGENS):
        df[coluna] = pd.to_numeric(df[coluna], errors="raise")
        validos = df[coluna].dropna()
        if not np.isfinite(validos).all() or (validos < 0).any():
            raise ValueError(f"valor inválido em {coluna}")
        if coluna in (*CONTAGENS, "contribuidores") and (validos % 1 != 0).any():
            raise ValueError(f"contagem não inteira em {coluna}")
    for coluna in ("cfr_a", "cfr_b", "proporcao_censurados"):
        if (df[coluna].dropna() > 1).any():
            raise ValueError(f"proporção fora de [0,1]: {coluna}")
    if df[list(CONTAGENS)].isna().any().any():
        raise ValueError("contagens de auditoria ausentes")
    if not set(df.tipo_projeto.dropna()) <= set(TIPOS):
        raise ValueError("tipo de projeto desconhecido")
    if int(df.tipo_projeto.isna().sum()) != manifesto["repositorios_sem_tipo"]:
        raise ValueError("contagem de tipos ausentes divergente")
    if int(df.cfr_b.isna().sum()) != manifesto["cfr_b_indisponiveis"]:
        raise ValueError("contagem de CFR(b) ausentes divergente")
    if not set(df.cfr_b_disponivel) <= {"True", "False"}:
        raise ValueError("indicador de disponibilidade inválido")
    indisponivel = (df.cfr_b_disponivel == "False") | (df.releases_avaliadas == 0)
    if not df.cfr_b.isna().equals(indisponivel):
        raise ValueError("CFR(b) incompatível com sua disponibilidade")
    if not (df.episodios_total == df.episodios_concluidos + df.episodios_censurados).all():
        raise ValueError("contagens de episódios inconsistentes")
    if not df.tempo_recuperacao_horas.isna().equals(df.episodios_concluidos == 0):
        raise ValueError("recuperação incompatível com episódios concluídos")
    origens = {"dataset_sha256": sha256(caminho), "amostra_sha256": sha256(amostra),
               "dataset_manifest_sha256": sha256(caminho.with_suffix(".manifest.json")),
               "amostra_manifest_sha256": sha256(amostra.with_suffix(".manifest.json")),
               "janela_inicio": congelada["janela_inicio"], "janela_fim": congelada["janela_fim"],
               "heuristica": manifesto["heuristica"], "repositorios": len(df)}
    return df.sort_values("full_name").reset_index(drop=True), origens


def descrever(valores):
    valores = pd.Series(valores, dtype=float).dropna()
    if valores.empty:
        return dict(n=0, mediana=np.nan, q1=np.nan, q3=np.nan, iqr=np.nan)
    q1, mediana, q3 = valores.quantile([.25, .5, .75], interpolation="linear")
    return dict(n=len(valores), mediana=mediana, q1=q1, q3=q3, iqr=q3-q1)


def ajustar_holm(tabela, coluna="p", destino="p_holm"):
    """Não transforma testes não estimáveis em p=1; informa a família efetiva."""
    tabela = tabela.copy()
    validos = tabela[coluna].notna()
    tabela[destino] = np.nan
    if validos.any():
        tabela.loc[validos, destino] = multipletests(tabela.loc[validos, coluna], method="holm")[1]
    tabela[destino + "_familia_n"] = int(validos.sum())
    return tabela


def motivo_ausencia(linha, coluna):
    if coluna == "cfr_b":
        return ("evidencia_textual_insuficiente" if linha.get("releases_sem_evidencia_textual", 0) > 0
                else "sem_releases_avaliaveis")
    if coluna == "tempo_recuperacao_horas":
        return "sem_episodios" if linha.get("episodios_total", 0) == 0 else "somente_episodios_censurados"
    return "valor_ausente"
