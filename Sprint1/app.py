import json
import os
from pathlib import Path

import pandas as pd
import numpy as np
import requests
import streamlit as st
from dotenv import load_dotenv

from analysis import MODULOS_RQ
from github_collector import coletar_repositorios
from utils import montar_dataframe

load_dotenv()  # lê o arquivo .env na raiz do projeto, se existir
TOKEN_ENV = os.environ.get("GITHUB_TOKEN", "")

st.set_page_config(
    page_title="Laboratório - Repositórios Populares GitHub",
    page_icon="🐙",
    layout="wide",
    initial_sidebar_state="expanded",
)

BASE_DIR = Path(__file__).resolve().parent
DATA_RAW_DIR = BASE_DIR / "data" / "raw"
DATA_RQ_DIR = BASE_DIR / "data" / "rq"

# ---------- Estilo ----------
st.markdown("""
<style>
    .stApp { background: radial-gradient(circle at top left, #1b1f2a 0%, #0e1117 60%); }
    .hero {
        padding: 2rem 2.5rem; border-radius: 18px;
        background: linear-gradient(135deg, #6366f1 0%, #22d3ee 100%);
        margin-bottom: 1.8rem; box-shadow: 0 10px 30px rgba(99, 102, 241, 0.25);
    }
    .hero h1 { color: white; font-size: 2rem; margin: 0; }
    .hero p { color: rgba(255,255,255,0.9); margin: 0.3rem 0 0 0; font-size: 0.95rem; }
    div[data-testid="stMetric"] { background: #161b22; border: 1px solid #30363d; border-radius: 14px; padding: 1rem 1.2rem; }
    div.stButton > button { border-radius: 10px; font-weight: 600; }
</style>
""", unsafe_allow_html=True)

st.markdown("""
<div class="hero">
    <h1>🐙 Repositórios Populares do GitHub — Laboratório de Experimentação</h1>
    <p>Coleta via GraphQL dos repositórios com mais estrelas e análise das RQ01–RQ08 e RQ10.</p>
</div>
""", unsafe_allow_html=True)


def salvar_dataset_bruto(df: pd.DataFrame) -> None:
    """Salva o dataset completo coletado em CSV e JSON na pasta data/raw."""
    DATA_RAW_DIR.mkdir(parents=True, exist_ok=True)
    df.to_csv(DATA_RAW_DIR / "repositorios_populares.csv", index=False)
    registros_json = (
        df.astype(object)
        .where(pd.notna(df), None)
        .to_dict(orient="records")
    )
    with open(DATA_RAW_DIR / "repositorios_populares.json", "w", encoding="utf-8") as f:
        json.dump(
            registros_json,
            f,
            ensure_ascii=False,
            indent=2,
            allow_nan=False,
            default=str,
        )
        f.write("\n")


def executar_analises(df: pd.DataFrame) -> dict:
    DATA_RQ_DIR.mkdir(parents=True, exist_ok=True)
    resultados = {}
    for nome_modulo, modulo in MODULOS_RQ.items():
        resultado = modulo.analisar(df)
        caminho = DATA_RQ_DIR / f"{nome_modulo}.json"
        modulo.salvar_json(resultado, str(caminho))
        resultados[nome_modulo] = resultado
    return resultados

def executar_analises_memoria(df: pd.DataFrame) -> dict:
    """
    Executa as análises apenas em memória, sem sobrescrever
    os JSONs das análises originais.
    """
    resultados = {}

    for nome_modulo, modulo in MODULOS_RQ.items():
        resultados[nome_modulo] = modulo.analisar(df)

    return resultados



def _distribuicao_binned(
    serie: pd.Series,
    tipo: str = "contagem",
) -> pd.DataFrame:
    """
    Cria faixas interpretáveis para distribuição.

    Retorna:
        Faixa
        Quantidade
    """

    dados = pd.to_numeric(serie, errors="coerce").dropna()

    if dados.empty:
        return pd.DataFrame(columns=["Faixa", "Quantidade"])

    maximo = float(dados.max())

    if tipo == "contagem":
        # Faixas adequadas para PRs, releases e outras contagens.
        if maximo <= 10:
            edges = [0, 1, 2, 3, 5, 10]
            labels = [
                "0",
                "1",
                "2",
                "3–5",
                "6–10",
            ]

        elif maximo <= 50:
            edges = [0, 1, 2, 5, 10, 20, 50]
            labels = [
                "0",
                "1–2",
                "3–5",
                "6–10",
                "11–20",
                "21–50",
            ]

        elif maximo <= 100:
            edges = [0, 1, 5, 10, 20, 50, 100]
            labels = [
                "0",
                "1–5",
                "6–10",
                "11–20",
                "21–50",
                "51–100",
            ]

        else:
            edges = [0, 1, 5, 10, 20, 50, 100, 250, 500, float("inf")]
            labels = [
                "0",
                "1–5",
                "6–10",
                "11–20",
                "21–50",
                "51–100",
                "101–250",
                "251–500",
                ">500",
            ]

    elif tipo == "percentual":
        edges = [0, 10, 25, 50, 75, 90, 100]
        labels = [
            "0–10%",
            "11–25%",
            "26–50%",
            "51–75%",
            "76–90%",
            "91–100%",
        ]

    elif tipo == "idade":
        edges = [0, 2, 5, 10, 15, float("inf")]
        labels = [
            "0–2 anos",
            "3–5 anos",
            "6–10 anos",
            "11–15 anos",
            ">15 anos",
        ]

    elif tipo == "dias":
        edges = [0, 30, 90, 180, 365, 730, float("inf")]
        labels = [
            "0–30 dias",
            "31–90 dias",
            "91–180 dias",
            "181–365 dias",
            "1–2 anos",
            ">2 anos",
        ]

    else:
        raise ValueError(f"Tipo de distribuição inválido: {tipo}")

    categorias = pd.cut(
        dados,
        bins=edges,
        labels=labels,
        include_lowest=True,
        right=True,
    )

    contagem = (
        categorias
        .value_counts(sort=False)
        .reset_index()
    )

    contagem.columns = ["Faixa", "Quantidade"]

    contagem["Faixa"] = contagem["Faixa"].astype(str)

    return contagem


def _grafico_barras(df_grafico: pd.DataFrame, categoria: str, valor: str, titulo: str):
    """Gráfico horizontal com categoria no eixo Y e valores sem rótulos numéricos estranhos no X."""
    import altair as alt

    chart = (
        alt.Chart(df_grafico)
        .mark_bar(cornerRadiusEnd=5)
        .encode(
            y=alt.Y(f"{categoria}:N", sort="-x", title=None),
            x=alt.X(f"{valor}:Q", title=None),
            tooltip=[
                alt.Tooltip(f"{categoria}:N", title=categoria),
                alt.Tooltip(f"{valor}:Q", title=valor, format=",.0f"),
            ],
        )
        .properties(title=titulo, height=max(250, min(600, len(df_grafico) * 30)))
    )
    st.altair_chart(chart, width="stretch")

def _grafico_distribuicao(
    df_grafico: pd.DataFrame,
    titulo: str,
):
    """Gráfico de distribuição: faixa de valores × quantidade de repositórios."""
    import altair as alt

    if df_grafico.empty:
        st.info("Não há dados suficientes para montar a distribuição.")
        return

    chart = (
        alt.Chart(df_grafico)
        .mark_bar(cornerRadiusEnd=5)
        .encode(
            x=alt.X(
                "Faixa:N",
                title="Faixa",
                sort=None,
            ),
            y=alt.Y(
                "Quantidade:Q",
                title="Quantidade de repositórios",
                scale=alt.Scale(zero=True),
            ),
            tooltip=[
                alt.Tooltip(
                    "Faixa:N",
                    title="Faixa",
                ),
                alt.Tooltip(
                    "Quantidade:Q",
                    title="Repositórios",
                    format=",d",
                ),
            ],
        )
        .properties(
            title=titulo,
            height=400,
        )
    )

    st.altair_chart(
        chart,
        width="stretch",
    )

def _top_repos(df: pd.DataFrame, coluna: str, n: int = 15) -> pd.DataFrame:
    if coluna not in df.columns:
        return pd.DataFrame()

    top = df[["Nome", "Linguagem", coluna]].copy()
    top[coluna] = pd.to_numeric(top[coluna], errors="coerce").fillna(0)
    top = top.nlargest(n, coluna)
    top["Repositório"] = top["Nome"].astype(str)
    return top


def _grafico_rq07(resumo: pd.DataFrame):
    """RQ07: relação entre PRs aceitas e releases por linguagem."""
    import altair as alt

    if resumo.empty:
        return

    base = resumo.copy()

    tooltip = [
        alt.Tooltip("Linguagem:N", title="Linguagem"),
        alt.Tooltip("PRs_aceitas_mediana:Q", title="PRs aceitas", format=".1f"),
        alt.Tooltip("Releases_mediana:Q", title="Releases", format=".1f"),
        alt.Tooltip("Dias_desde_atualizacao_mediana:Q", title="Dias desde atualização", format=".1f"),
    ]

    if "Repositorios" in base.columns:
        tooltip.append(
            alt.Tooltip("Repositorios:Q", title="Repositórios", format=".0f")
        )
        size = alt.Size(
            "Repositorios:Q",
            title="Nº de repositórios",
            scale=alt.Scale(range=[80, 700]),
        )
    else:
        size = alt.value(180)

    chart = (
        alt.Chart(base)
        .mark_circle(opacity=0.8)
        .encode(
            x=alt.X(
                "PRs_aceitas_mediana:Q",
                title="Mediana de PRs aceitas",
                scale=alt.Scale(zero=True),
            ),
            y=alt.Y(
                "Releases_mediana:Q",
                title="Mediana de releases",
                scale=alt.Scale(zero=True),
            ),
            size=size,
            tooltip=tooltip,
        )
        .properties(
            title="PRs aceitas × Releases por linguagem",
            height=430,
        )
        .interactive()
    )

    st.altair_chart(chart, width="stretch")


def _formatar_rho(valor) -> str:
    """Formata uma correlação, preservando cenários sem valor calculável."""

    if valor is None or pd.isna(valor):
        return "—"
    return f"{float(valor):.3f}"


def _extrair_correlacao(cenario: dict, chave: str) -> tuple[object, object]:
    """Extrai rho e n do contrato da RQ08 sem falhar em dados incompletos."""

    correlacao = cenario.get(chave, {}) if isinstance(cenario, dict) else {}
    if isinstance(correlacao, dict):
        return correlacao.get("rho"), correlacao.get("n")
    return correlacao, cenario.get("n") if isinstance(cenario, dict) else None


def _grafico_rq08(
    df_grafico: pd.DataFrame,
    coluna_taxa: str,
    titulo: str,
):
    """Dispersão da popularidade contra uma taxa anual da RQ08."""

    import altair as alt

    colunas = [
        "Nome",
        "Estrelas",
        "Idade (anos)",
        "PRs aceitas",
        "Total de releases",
        coluna_taxa,
    ]
    if df_grafico.empty or any(coluna not in df_grafico for coluna in colunas):
        st.info("Não há dados suficientes para gerar este gráfico.")
        return

    base = df_grafico[colunas].copy()
    for coluna in colunas[1:]:
        base[coluna] = pd.to_numeric(base[coluna], errors="coerce")
    base = base.dropna(subset=["Estrelas", coluna_taxa])
    base = base[(base["Estrelas"] > 0) & (base[coluna_taxa] >= 0)]
    if base.empty:
        st.info("Não há dados válidos para gerar este gráfico.")
        return

    chart = (
        alt.Chart(base)
        .mark_circle(size=55, opacity=0.28, color="#38bdf8")
        .encode(
            x=alt.X(
                "Estrelas:Q",
                title="Estrelas (escala logarítmica)",
                scale=alt.Scale(type="log", zero=False),
            ),
            y=alt.Y(
                f"{coluna_taxa}:Q",
                title=f"{coluna_taxa} (escala symlog)",
                scale=alt.Scale(type="symlog", constant=1, zero=True),
            ),
            tooltip=[
                alt.Tooltip("Nome:N", title="Repositório"),
                alt.Tooltip("Estrelas:Q", title="Estrelas", format=",.0f"),
                alt.Tooltip("Idade (anos):Q", title="Idade (anos)", format=".2f"),
                alt.Tooltip("PRs aceitas:Q", title="PRs mescladas", format=",.0f"),
                alt.Tooltip(
                    "Total de releases:Q",
                    title="Releases acumuladas",
                    format=",.0f",
                ),
                alt.Tooltip(
                    f"{coluna_taxa}:Q",
                    title=coluna_taxa,
                    format=",.2f",
                ),
            ],
        )
        .properties(title=titulo, height=410)
        .interactive()
    )
    st.altair_chart(chart, width="stretch")


def construir_csv_completo(df: pd.DataFrame, resultados_rq: dict) -> pd.DataFrame:

    df_completo = df.copy()

    # RQ05 — marca se a linguagem do repositório está no Top 10 Octoverse
    rq05 = resultados_rq.get("rq05_linguagem", {})
    top10 = set(rq05.get("ranking_referencia_octoverse", []))
    if top10:
        df_completo["Linguagem no Top 10 Octoverse"] = df_completo["Linguagem"].isin(top10)

    # RQ07 — anexa as métricas agregadas por linguagem em cada linha correspondente
    rq07 = resultados_rq.get("rq07_cruzamento", {})
    resumo_linguagem = pd.DataFrame(rq07.get("resumo_por_linguagem", []))
    if not resumo_linguagem.empty:
        resumo_linguagem = resumo_linguagem.rename(columns={
            "PRs_aceitas_mediana": "PRs aceitas (mediana da linguagem)",
            "Releases_mediana": "Releases (mediana da linguagem)",
            "Dias_desde_atualizacao_mediana": "Dias desde atualização (mediana da linguagem)",
        })
        df_completo = df_completo.merge(resumo_linguagem, on="Linguagem", how="left")

    # Métricas gerais das RQs (mesmo valor em todas as linhas, útil como referência)
    rq01 = resultados_rq.get("rq01_idade", {})
    rq02 = resultados_rq.get("rq02_pr_aceitos", {})
    rq03 = resultados_rq.get("rq03_releases", {})
    rq04 = resultados_rq.get("rq04_ultima_atualizacao", {})
    rq06 = resultados_rq.get("rq06_issues_fechadas", {})
    rq10 = resultados_rq.get("rq10_idade_issues", {})
    if "idade_mediana_anos" in rq01:
        df_completo["Idade mediana geral (anos)"] = rq01["idade_mediana_anos"]
    if "prs_aceitas_mediana" in rq02:
        df_completo["PRs aceitas mediana geral"] = rq02["prs_aceitas_mediana"]
    if "releases_mediana" in rq03:
        df_completo["Releases mediana geral"] = rq03["releases_mediana"]
    if "dias_desde_atualizacao_mediana" in rq04:
        df_completo["Dias desde atualização mediana geral"] = rq04["dias_desde_atualizacao_mediana"]
    if "percentual_issues_fechadas_mediana" in rq06:
        df_completo["% issues fechadas mediana geral"] = rq06["percentual_issues_fechadas_mediana"]
    if "percentual_no_top10_octoverse" in rq05:
        df_completo["% no Top 10 Octoverse (geral)"] = rq05["percentual_no_top10_octoverse"]
    if "correlacao_spearman" in rq10:
        df_completo["rq10 - Correlação Spearman idade x issues fechadas"] = (
        rq10["correlacao_spearman"]
    )
    if "repositorios_com_issues" in rq10:
        df_completo["rq10 - Repositórios com issues"] = (
            rq10["repositorios_com_issues"]
        )
    if "repositorios_sem_issues" in rq10:
        df_completo["rq10 - Repositórios sem issues"] = (
            rq10["repositorios_sem_issues"]
        )

    return df_completo


# ---------- Barra lateral ----------
with st.sidebar:
    st.header("⚙️ Parâmetros")
    if TOKEN_ENV:
        st.success("Token carregado da variável de ambiente `GITHUB_TOKEN`.")
        token = st.text_input(
            "GitHub Personal Access Token (opcional — sobrescreve o da env)",
            type="password",
            help="Deixe em branco para usar o token de GITHUB_TOKEN.",
        ) or TOKEN_ENV
    else:
        token = st.text_input(
            "GitHub Personal Access Token",
            type="password",
            help="Necessário para consultar a API GraphQL do GitHub. "
                 "Defina GITHUB_TOKEN no .env para não precisar digitar aqui.",
        )
    linguagem = st.selectbox(
        "Linguagem (opcional)",
        ["Todas", "Python", "JavaScript", "TypeScript", "Java", "Go", "Rust", "C++", "C#", "PHP", "Ruby"],
        index=0,
    )
    qtd_repos = st.number_input("Número de repositórios (top-N por estrelas)", min_value=1, max_value=1000, value=100, step=1)
    buscar = st.button("Buscar 🚀", type="primary", width="stretch")
    st.caption("Critério fixo: sempre os repositórios com mais estrelas (sort:stars-desc).")
    st.caption("JSON por RQ salvo em `data/rq/`. Dataset completo salvo em `data/raw/`.")

if buscar:
    if not token.strip():
        st.warning("Informe um GitHub Personal Access Token na barra lateral. Veja o README para instruções de como gerar um.")
    else:
        try:
            barra = st.progress(0, text="Iniciando coleta...")
            registros = coletar_repositorios(token.strip(), linguagem, int(qtd_repos), progresso=barra)
            df = montar_dataframe(registros)
            barra.empty()

            salvar_dataset_bruto(df)
            resultados_rq = executar_analises(df)

            st.session_state["df"] = df
            st.session_state["resultados_rq"] = resultados_rq
        except requests.exceptions.HTTPError as e:
            st.error(f"Erro HTTP ao consultar a API do GitHub: {e}")
        except (RuntimeError, ValueError) as e:
            st.error(f"Erro ao processar os dados da API GraphQL: {e}")
        except requests.exceptions.RequestException as e:
            st.error(f"Erro de conexão: {e}")

df = st.session_state.get("df")
resultados_rq = st.session_state.get("resultados_rq", {})

df_exibicao = df
resultados_exibicao = resultados_rq

if df is not None and not df.empty:
    repositorios_disponiveis = sorted(
        df["Nome"]
        .dropna()
        .astype(str)
        .unique()
        .tolist()
    )

    with st.sidebar:
        st.markdown("---")
        st.header("🔎 Filtrar repositórios")

        repositorios_selecionados = st.multiselect(
            "Repositórios",
            options=repositorios_disponiveis,
            default=[],
            placeholder="Selecione um ou mais repositórios",
            help=(
                "Deixe vazio para visualizar todos os repositórios. "
                "Ao selecionar repositórios, as métricas, gráficos e "
                "tabelas serão recalculados somente para a seleção."
            ),
        )

        if repositorios_selecionados:
            df_exibicao = df[
                df["Nome"].isin(repositorios_selecionados)
            ].copy()

            resultados_exibicao = executar_analises_memoria(
                df_exibicao
            )

            st.success(
                f"{len(repositorios_selecionados)} "
                f"repositório(s) selecionado(s)."
            )
        else:
            st.caption(
                f"Exibindo todos os {len(df)} repositórios."
            )

if df is None or df.empty:
    st.info("Defina os parâmetros na barra lateral e clique em **Buscar 🚀** para começar.")
else:
    st.success(
        f"{len(df_exibicao)} repositório(s) sendo exibido(s). "
        f"Dataset original: {len(df)} repositório(s)."
    )

    col1, col2, col3 = st.columns(3)

    col1.metric(
        "Repositórios exibidos",
        len(df_exibicao),
    )

    col2.metric(
        "Total de estrelas",
        f"{int(df_exibicao['Estrelas'].sum()):,}".replace(",", "."),
    )

    col3.metric(
        "Linguagens distintas",
        df_exibicao["Linguagem"].nunique(),
    )

    df_export = construir_csv_completo(
        df_exibicao,
        resultados_exibicao,
    )
    csv = df_export.to_csv(index=False).encode("utf-8")
    st.download_button(
        "Baixar CSV com todas as métricas",
        csv,
        "repositorios_populares_completo.csv",
        "text/csv",
    )

    (rq01, rq02, rq03, rq04, rq05, rq06, rq07, rq08, rq10, tabela) = st.tabs(
        [
            "RQ01 Idade",
            "RQ02 PRs",
            "RQ03 Releases",
            "RQ04 Atualização",
            "RQ05 Linguagem",
            "RQ06 Issues",
            "RQ07 Cruzamento",
            "RQ08 Intensidade",
            "RQ10 Idade × Issues",
            "📋 Dados",
        ]
    )

    with rq01:
        r = resultados_exibicao["rq01_idade"]
        st.subheader("RQ01 — Sistemas populares são maduros/antigos?")
        st.write("**Métrica:** idade do repositório, em anos, a partir da data de criação.")
        st.metric("Idade mediana", f"{r['idade_mediana_anos']:.1f} anos")
        dist_idade = _distribuicao_binned(
            df_exibicao["Idade (anos)"],
            tipo="idade",
        )

        _grafico_distribuicao(
            dist_idade,
            "Distribuição dos repositórios por idade",
        )

    with rq02:
        r = resultados_exibicao["rq02_pr_aceitos"]
        st.subheader("RQ02 — Sistemas populares recebem muita contribuição externa?")
        st.write(
            "**Métrica:** total de pull requests aceitas (estado MERGED). "
            "A visualização usa ranking e faixas para facilitar a interpretação."
        )

        col_a, col_b, col_c = st.columns(3)
        col_a.metric("PRs aceitas — mediana", f"{r['prs_aceitas_mediana']:.0f}")
        col_b.metric("PRs aceitas — média", f"{r['prs_aceitas_media']:.0f}")
        col_c.metric("PRs aceitas — máxima", f"{int(r['prs_aceitas_maxima']):,}".replace(",", "."))

        st.markdown("#### 🏆 Repositórios com mais PRs aceitas")
        top_prs = _top_repos(df_exibicao, "PRs aceitas", 15)
        if not top_prs.empty:
            _grafico_barras(
                top_prs.rename(columns={"PRs aceitas": "PRs"}),
                "Repositório",
                "PRs",
                "Top 15 por PRs aceitas",
            )

        st.markdown("#### 📊 Distribuição por faixas")
        dist_prs = _distribuicao_binned(
            df_exibicao["PRs aceitas"],
            tipo="contagem",
        )

        _grafico_distribuicao(
            dist_prs,
            "Distribuição dos repositórios por quantidade de PRs aceitas",
        )

    with rq03:
        r = resultados_exibicao["rq03_releases"]
        st.subheader("RQ03 — Sistemas populares lançam releases com frequência?")
        st.write(
            "**Métrica:** total de releases do repositório. "
            "O ranking mostra os projetos mais ativos e as faixas mostram a distribuição."
        )

        col_a, col_b, col_c = st.columns(3)
        col_a.metric("Releases — mediana", f"{int(r['releases_mediana']):,}".replace(",", "."))
        col_b.metric(
            "Releases — média",
            f"{df_exibicao['Total de releases'].mean():,.0f}".replace(",", "."),
        )
        col_c.metric(
            "Releases — máximo",
            f"{int(df_exibicao['Total de releases'].max()):,}".replace(",", "."),
        )

        st.markdown("#### 🚀 Repositórios com mais releases")
        top_releases = _top_repos(df_exibicao, "Total de releases", 15)
        if not top_releases.empty:
            _grafico_barras(
                top_releases.rename(columns={"Total de releases": "Releases"}),
                "Repositório",
                "Releases",
                "Top 15 por quantidade de releases",
            )

        st.markdown("#### 📊 Distribuição por faixas")
        # RQ03
        dist_releases = _distribuicao_binned(
            df_exibicao["Total de releases"],
            tipo="contagem",
        )

        _grafico_distribuicao(
            dist_releases,
            "Distribuição dos repositórios por quantidade de releases",
)

    with rq04:
        r = resultados_exibicao["rq04_ultima_atualizacao"]
        st.subheader("RQ04 — Sistemas populares são atualizados com frequência?")
        st.write("**Métrica:** dias decorridos desde o último push no repositório (pushedAt).")
        col_a, col_b = st.columns(2)
        col_a.metric("Dias desde atualização (mediana)", f"{r['dias_desde_atualizacao_mediana']:.1f}")
        col_b.metric("Dias desde atualização (média)", f"{r['dias_desde_atualizacao_media']:.1f}")
        # RQ04
        dist_dias = _distribuicao_binned(
            df_exibicao["Dias desde última atualização"],
            tipo="dias",
        )

        _grafico_distribuicao(
            dist_dias,
            "Distribuição dos repositórios por tempo desde a última atualização",
        )

    with rq05:
        r = resultados_exibicao["rq05_linguagem"]
        st.subheader("RQ05 — Sistemas populares são escritos nas linguagens mais populares?")
        st.write(
            "**Métrica:** linguagem primária de cada repositório, comparada ao ranking de "
            "linguagens mais populares do **GitHub Octoverse** (https://octoverse.github.com/), "
            "usado como referência única em todo o laboratório."
        )
        st.bar_chart(df_exibicao["Linguagem"].value_counts())
        st.metric("% de repositórios em linguagens do Top 10 Octoverse", f"{r['percentual_no_top10_octoverse']:.1f}%")
        st.caption("Top 10 Octoverse considerado: " + ", ".join(r["ranking_referencia_octoverse"]))

    with rq06:
        r = resultados_exibicao["rq06_issues_fechadas"]
        st.subheader("RQ06 — Sistemas populares possuem alto percentual de issues fechadas?")
        st.write("**Métrica:** percentual de issues fechadas sobre o total de issues, entre repositórios que têm issues.")
        if r["percentual_issues_fechadas_mediana"] is None:
            st.info("Nenhum repositório da amostra possui issues para calcular este percentual.")
        else:
            col_a, col_b = st.columns(2)
            col_a.metric("% issues fechadas (mediana)", f"{r['percentual_issues_fechadas_mediana']:.1f}%")
            col_b.metric("% issues fechadas (média)", f"{r['percentual_issues_fechadas_media']:.1f}%")
            # RQ06
            dist_issues = _distribuicao_binned(
                df_exibicao["% issues fechadas"],
                tipo="percentual",
            )

            _grafico_distribuicao(
                dist_issues,
                "Distribuição dos repositórios pelo percentual de issues fechadas",
            )
        st.caption(
            f"Repositórios com issues: {r['repositorios_com_issues']} | "
            f"sem issues: {r['repositorios_sem_issues']}"
        )

    with rq07:
        r = resultados_exibicao["rq07_cruzamento"]
        st.subheader("RQ07 — Linguagens populares recebem mais contribuição, mais releases e mais atualizações?")
        st.write(
            "Cruzamento das RQ02, RQ03 e RQ04, agrupado por linguagem "
            "(linguagens com pelo menos 3 repositórios na amostra)."
        )

        resumo = pd.DataFrame(r["resumo_por_linguagem"])

        if resumo.empty:
            st.info("Não há dados suficientes para o cruzamento por linguagem.")
        else:
            st.markdown("#### 🔎 Resumo por linguagem")
            st.dataframe(
                resumo.sort_values("PRs_aceitas_mediana", ascending=False),
                width="stretch",
                hide_index=True,
            )

            st.markdown("#### 🔗 Relação entre contribuição e releases")
            st.caption(
                "Cada ponto representa uma linguagem. À direita = mais PRs aceitas; "
                "acima = mais releases; tamanho = quantidade de repositórios."
            )
            _grafico_rq07(resumo)

            st.markdown("#### 📌 Comparar uma métrica por linguagem")
            metrica_rq07 = st.selectbox(
                "Métrica",
                [
                    "PRs_aceitas_mediana",
                    "Releases_mediana",
                    "Dias_desde_atualizacao_mediana",
                ],
                format_func=lambda x: {
                    "PRs_aceitas_mediana": "PRs aceitas (mediana)",
                    "Releases_mediana": "Releases (mediana)",
                    "Dias_desde_atualizacao_mediana": "Dias desde atualização (mediana)",
                }[x],
            )

            comparacao = (
                resumo[["Linguagem", metrica_rq07]]
                .dropna()
                .sort_values(metrica_rq07, ascending=False)
            )
            _grafico_barras(
                comparacao,
                "Linguagem",
                metrica_rq07,
                "Comparação entre linguagens",
            )

    with rq08:
        r = resultados_exibicao.get("rq08_popularidade_intensidade", {})
        st.subheader("RQ08 — Popularidade e intensidade de desenvolvimento")
        st.write(
            "**Métricas:** correlação de Spearman entre estrelas e as taxas "
            "anuais de PRs mescladas e releases, normalizadas pela idade."
        )
        st.warning(
            "A quantidade de PRs mescladas é uma aproximação do volume de "
            "contribuições; os dados não identificam se a autoria é externa."
        )

        if not r:
            st.info("Os resultados da RQ08 ainda não estão disponíveis para esta amostra.")
        else:
            amostra = r.get("amostra", {})
            correlacoes = r.get("correlacoes_spearman", {})
            principal = correlacoes.get("principal_idade_maior_igual_1", {})
            sensibilidade = correlacoes.get(
                "sensibilidade_todas_idades_positivas",
                {},
            )

            rho_prs, n_prs = _extrair_correlacao(
                principal,
                "estrelas_vs_prs_por_ano",
            )
            rho_releases, n_releases = _extrair_correlacao(
                principal,
                "estrelas_vs_releases_por_ano",
            )

            col_prs, col_releases = st.columns(2)
            col_prs.metric(
                "ρ — estrelas × PRs/ano",
                _formatar_rho(rho_prs),
                delta=f"n = {n_prs}" if n_prs is not None else "n indisponível",
                delta_color="off",
            )
            col_releases.metric(
                "ρ — estrelas × releases/ano",
                _formatar_rho(rho_releases),
                delta=(
                    f"n = {n_releases}"
                    if n_releases is not None
                    else "n indisponível"
                ),
                delta_color="off",
            )

            col_amostra, col_jovens = st.columns(2)
            col_amostra.metric(
                "Amostra principal (idade ≥ 1 ano)",
                amostra.get("analise_principal", 0),
            )
            col_jovens.metric(
                "Repositórios com idade < 1 ano",
                amostra.get("idade_menor_1_ano", 0),
            )
            st.caption(
                f"Amostra total: {amostra.get('total_repositorios', 0)} | "
                f"idade não positiva: {amostra.get('idade_nao_positiva', 0)} | "
                f"dados ausentes: {amostra.get('dados_ausentes', 0)}"
            )

            quantidade_principal = amostra.get("analise_principal", 0)
            if quantidade_principal:
                idade = pd.to_numeric(
                    df_exibicao["Idade (anos)"],
                    errors="coerce",
                )
                df_principal = df_exibicao[idade >= 1].copy()
                grafico_prs, grafico_releases = st.columns(2)
                with grafico_prs:
                    _grafico_rq08(
                        df_principal,
                        "PRs por ano",
                        "Estrelas × PRs mescladas por ano",
                    )
                with grafico_releases:
                    _grafico_rq08(
                        df_principal,
                        "Releases por ano",
                        "Estrelas × releases por ano",
                    )
                st.caption(
                    "Os gráficos mostram a análise principal (idade ≥ 1 ano). "
                    "A escala symlog preserva taxas iguais a zero e reduz a "
                    "compressão provocada por valores extremos."
                )
            else:
                st.info("A amostra principal da RQ08 está vazia.")

            st.markdown("#### Resumo por quartil de estrelas")
            resumo_quartis = pd.DataFrame(
                r.get("resumo_por_quartil_estrelas", [])
            )
            if resumo_quartis.empty:
                st.info("Não há resumo por quartis para esta amostra.")
            else:
                st.dataframe(
                    resumo_quartis,
                    width="stretch",
                    hide_index=True,
                )

            st.markdown("#### Análise de sensibilidade — todas as idades positivas")
            sens_prs, sens_n_prs = _extrair_correlacao(
                sensibilidade,
                "estrelas_vs_prs_por_ano",
            )
            sens_releases, sens_n_releases = _extrair_correlacao(
                sensibilidade,
                "estrelas_vs_releases_por_ano",
            )
            st.dataframe(
                pd.DataFrame(
                    [
                        {
                            "Relação": "Estrelas × PRs por ano",
                            "ρ de Spearman": _formatar_rho(sens_prs),
                            "N": sens_n_prs,
                        },
                        {
                            "Relação": "Estrelas × releases por ano",
                            "ρ de Spearman": _formatar_rho(sens_releases),
                            "N": sens_n_releases,
                        },
                    ]
                ),
                width="stretch",
                hide_index=True,
            )

            outliers = r.get("outliers_iqr", {})
            if outliers:
                with st.expander("Diagnóstico de outliers pelo IQR"):
                    st.json(outliers)

    with tabela:
        st.dataframe(
            df_exibicao,
            width="stretch",
            hide_index=True,
            column_config={
                "URL": st.column_config.LinkColumn("URL")
            },
        )

    with rq10:
        r = resultados_exibicao["rq10_idade_issues"]

        st.subheader(
            "RQ10 — Repositórios mais antigos apresentam maior proporção de issues fechadas?"
        )

        st.write(
            "**Métrica:** relação entre idade do repositório e percentual "
            "de issues fechadas."
        )

        st.caption(
            "Hipótese: espera-se que repositórios mais antigos apresentem "
            "maior percentual mediano de issues fechadas, por possuírem "
            "processos de manutenção mais consolidados."
        )

        col_a, col_b, col_c = st.columns(3)

        correlacao = r["correlacao_spearman"]

        col_a.metric(
            "Spearman",
            "N/A" if correlacao is None else f"{correlacao:.3f}",
        )

        col_b.metric(
            "Repositórios com issues",
            r["repositorios_com_issues"],
        )

        col_c.metric(
            "Excluídos por não terem issues",
            r["repositorios_sem_issues"],
        )

        st.info(
            f"Interpretação da correlação: {r['interpretacao_correlacao']}"
        )

        st.markdown("#### 📈 Idade × percentual de issues fechadas")

        import altair as alt

        dados_rq10  = df_exibicao[
            ["Nome", "Idade (anos)", "% issues fechadas"]
        ].copy()

        dados_rq10 ["Idade (anos)"] = pd.to_numeric(
            dados_rq10 ["Idade (anos)"],
            errors="coerce",
        )

        dados_rq10 ["% issues fechadas"] = pd.to_numeric(
            dados_rq10 ["% issues fechadas"],
            errors="coerce",
        )

        dados_rq10  = dados_rq10 .dropna(
            subset=["Idade (anos)", "% issues fechadas"]
        )

        if not dados_rq10 .empty:
            chart = (
                alt.Chart(dados_rq10 )
                .mark_circle(size=80, opacity=0.7)
                .encode(
                    x=alt.X(
                        "Idade (anos):Q",
                        title="Idade do repositório (anos)",
                    ),
                    y=alt.Y(
                        "% issues fechadas:Q",
                        title="% de issues fechadas",
                        scale=alt.Scale(domain=[0, 100]),
                    ),
                    tooltip=[
                        alt.Tooltip(
                            "Nome:N",
                            title="Repositório",
                        ),
                        alt.Tooltip(
                            "Idade (anos):Q",
                            title="Idade",
                            format=".2f",
                        ),
                        alt.Tooltip(
                            "% issues fechadas:Q",
                            title="% issues fechadas",
                            format=".2f",
                        ),
                    ],
                )
                .properties(
                    title="Relação entre idade e percentual de issues fechadas",
                    height=450,
                )
                .interactive()
            )

            st.altair_chart(
                chart,
                width="stretch",
            )

        st.markdown("#### 📊 Mediana e intervalo interquartil por faixa de idade")

        resumo_rq08 = pd.DataFrame(
            r["resumo_por_faixa_etaria"]
        )

        if resumo_rq08.empty:
            st.info(
                "Não existem dados suficientes para calcular "
                "as estatísticas por faixa de idade."
            )
        else:
            tabela_rq08 = resumo_rq08.rename(
                columns={
                    "Faixa de idade": "Faixa de idade",
                    "Quantidade_repositorios": "Repositórios",
                    "Mediana_issues_fechadas": "Mediana (%)",
                    "Q1_issues_fechadas": "Q1 (%)",
                    "Q3_issues_fechadas": "Q3 (%)",
                    "IQR_issues_fechadas": "IQR (%)",
                }
            )

            st.dataframe(
                tabela_rq08[
                    [
                        "Faixa de idade",
                        "Repositórios",
                        "Mediana (%)",
                        "Q1 (%)",
                        "Q3 (%)",
                        "IQR (%)",
                    ]
                ],
                width="stretch",
                hide_index=True,
            )

            st.markdown("#### 📊 Mediana de issues fechadas por idade")

            grafico_mediana = tabela_rq08[
                ["Faixa de idade", "Mediana (%)"]
            ].copy()

            st.bar_chart(
                grafico_mediana.set_index("Faixa de idade")
            )

        st.caption(
            "Critério de exclusão: repositórios que nunca tiveram issues "
            "não participam da correlação nem das estatísticas por faixa de idade."
        )
