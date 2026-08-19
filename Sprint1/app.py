import json
import os
from pathlib import Path

import pandas as pd
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
    <p>Coleta via GraphQL dos repositórios com mais estrelas e análise das RQ01–RQ07.</p>
</div>
""", unsafe_allow_html=True)


def salvar_dataset_bruto(df: pd.DataFrame) -> None:
    """Salva o dataset completo coletado em CSV e JSON na pasta data/raw."""
    DATA_RAW_DIR.mkdir(parents=True, exist_ok=True)
    df.to_csv(DATA_RAW_DIR / "repositorios_populares.csv", index=False)
    with open(DATA_RAW_DIR / "repositorios_populares.json", "w", encoding="utf-8") as f:
        json.dump(df.to_dict(orient="records"), f, ensure_ascii=False, indent=2, default=str)


def executar_analises(df: pd.DataFrame) -> dict:
    DATA_RQ_DIR.mkdir(parents=True, exist_ok=True)
    resultados = {}
    for nome_modulo, modulo in MODULOS_RQ.items():
        resultado = modulo.analisar(df)
        caminho = DATA_RQ_DIR / f"{nome_modulo}.json"
        modulo.salvar_json(resultado, str(caminho))
        resultados[nome_modulo] = resultado
    return resultados



def _distribuicao_binned(serie: pd.Series, bins: int = 10, casas: int = 1) -> pd.DataFrame:
    """Distribuição em faixas categóricas para evitar eixos numéricos pouco intuitivos."""
    dados = pd.to_numeric(serie, errors="coerce").dropna()

    if dados.empty:
        return pd.DataFrame(columns=["Faixa", "Quantidade"])

    if dados.nunique() <= 1:
        valor = float(dados.iloc[0])
        return pd.DataFrame({
            "Faixa": [f"{valor:.{casas}f}"],
            "Quantidade": [len(dados)]
        })

    # Para contagens, faixas fixas são mais fáceis de interpretar.
    if casas == 0:
        maximo = int(dados.max())
        if maximo <= 20:
            edges = sorted(set([0, 1, 2, 5, 10, 20, maximo + 1]))
            edges = [x for x in edges if x <= maximo + 1]
            if edges[-1] != maximo + 1:
                edges.append(maximo + 1)
        else:
            edges = list(pd.cut(dados, bins=bins, retbins=True, include_lowest=True)[1])
        faixas = pd.cut(dados, bins=edges, include_lowest=True, duplicates="drop")
    else:
        faixas = pd.cut(dados, bins=bins, include_lowest=True)

    contagem = faixas.value_counts().sort_index()
    contagem.index = [
        f"{intervalo.left:.{casas}f}–{intervalo.right:.{casas}f}"
        for intervalo in contagem.index
    ]

    return contagem.rename_axis("Faixa").reset_index(name="Quantidade")


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
    st.altair_chart(chart, use_container_width=True)


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

    st.altair_chart(chart, use_container_width=True)
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
    buscar = st.button("Buscar 🚀", type="primary", use_container_width=True)
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
        except RuntimeError as e:
            st.error(f"Erro da API GraphQL: {e}")
        except requests.exceptions.RequestException as e:
            st.error(f"Erro de conexão: {e}")

df = st.session_state.get("df")
resultados_rq = st.session_state.get("resultados_rq", {})

if df is None or df.empty:
    st.info("Defina os parâmetros na barra lateral e clique em **Buscar 🚀** para começar.")
else:
    st.success(f"{len(df)} repositório(s) carregado(s). JSONs de cada RQ salvos em `data/rq/`.")
    col1, col2, col3 = st.columns(3)
    col1.metric("Total de repositórios", len(df))
    col2.metric("Total de estrelas", f"{int(df['Estrelas'].sum()):,}".replace(",", "."))
    col3.metric("Linguagens distintas", df["Linguagem"].nunique())

    df_export = construir_csv_completo(df, resultados_rq)
    csv = df_export.to_csv(index=False).encode("utf-8")
    st.download_button(
        "Baixar CSV com todas as métricas",
        csv,
        "repositorios_populares_completo.csv",
        "text/csv",
    )

    (rq01, rq02, rq03, rq04, rq05, rq06, rq07, tabela) = st.tabs(
        ["RQ01 Idade", "RQ02 PRs", "RQ03 Releases", "RQ04 Atualização",
         "RQ05 Linguagem", "RQ06 Issues", "RQ07 Cruzamento", "📋 Dados"]
    )

    with rq01:
        r = resultados_rq["rq01_idade"]
        st.subheader("RQ01 — Sistemas populares são maduros/antigos?")
        st.write("**Métrica:** idade do repositório, em anos, a partir da data de criação.")
        st.metric("Idade mediana", f"{r['idade_mediana_anos']:.1f} anos")
        st.bar_chart(_distribuicao_binned(df["Idade (anos)"], bins=10, casas=1))

    with rq02:
        r = resultados_rq["rq02_pr_aceitos"]
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
        top_prs = _top_repos(df, "PRs aceitas", 15)
        if not top_prs.empty:
            _grafico_barras(
                top_prs.rename(columns={"PRs aceitas": "PRs"}),
                "Repositório",
                "PRs",
                "Top 15 por PRs aceitas",
            )

        st.markdown("#### 📊 Distribuição por faixas")
        dist_prs = _distribuicao_binned(df["PRs aceitas"], bins=8, casas=0)
        _grafico_barras(
            dist_prs,
            "Faixa",
            "Quantidade",
            "Quantidade de repositórios por faixa de PRs",
        )

    with rq03:
        r = resultados_rq["rq03_releases"]
        st.subheader("RQ03 — Sistemas populares lançam releases com frequência?")
        st.write(
            "**Métrica:** total de releases do repositório. "
            "O ranking mostra os projetos mais ativos e as faixas mostram a distribuição."
        )

        col_a, col_b, col_c = st.columns(3)
        col_a.metric("Releases — mediana", f"{int(r['releases_mediana']):,}".replace(",", "."))
        col_b.metric(
            "Releases — média",
            f"{df['Total de releases'].mean():,.0f}".replace(",", "."),
        )
        col_c.metric(
            "Releases — máximo",
            f"{int(df['Total de releases'].max()):,}".replace(",", "."),
        )

        st.markdown("#### 🚀 Repositórios com mais releases")
        top_releases = _top_repos(df, "Total de releases", 15)
        if not top_releases.empty:
            _grafico_barras(
                top_releases.rename(columns={"Total de releases": "Releases"}),
                "Repositório",
                "Releases",
                "Top 15 por quantidade de releases",
            )

        st.markdown("#### 📊 Distribuição por faixas")
        dist_releases = _distribuicao_binned(
            df["Total de releases"], bins=8, casas=0
        )
        _grafico_barras(
            dist_releases,
            "Faixa",
            "Quantidade",
            "Quantidade de repositórios por faixa de releases",
        )

    with rq04:
        r = resultados_rq["rq04_ultima_atualizacao"]
        st.subheader("RQ04 — Sistemas populares são atualizados com frequência?")
        st.write("**Métrica:** dias decorridos desde o último push no repositório (pushedAt).")
        col_a, col_b = st.columns(2)
        col_a.metric("Dias desde atualização (mediana)", f"{r['dias_desde_atualizacao_mediana']:.1f}")
        col_b.metric("Dias desde atualização (média)", f"{r['dias_desde_atualizacao_media']:.1f}")
        st.bar_chart(_distribuicao_binned(df["Dias desde última atualização"], bins=10, casas=1))

    with rq05:
        r = resultados_rq["rq05_linguagem"]
        st.subheader("RQ05 — Sistemas populares são escritos nas linguagens mais populares?")
        st.write(
            "**Métrica:** linguagem primária de cada repositório, comparada ao ranking de "
            "linguagens mais populares do **GitHub Octoverse** (https://octoverse.github.com/), "
            "usado como referência única em todo o laboratório."
        )
        st.bar_chart(df["Linguagem"].value_counts())
        st.metric("% de repositórios em linguagens do Top 10 Octoverse", f"{r['percentual_no_top10_octoverse']:.1f}%")
        st.caption("Top 10 Octoverse considerado: " + ", ".join(r["ranking_referencia_octoverse"]))

    with rq06:
        r = resultados_rq["rq06_issues_fechadas"]
        st.subheader("RQ06 — Sistemas populares possuem alto percentual de issues fechadas?")
        st.write("**Métrica:** percentual de issues fechadas sobre o total de issues, entre repositórios que têm issues.")
        if r["percentual_issues_fechadas_mediana"] is None:
            st.info("Nenhum repositório da amostra possui issues para calcular este percentual.")
        else:
            col_a, col_b = st.columns(2)
            col_a.metric("% issues fechadas (mediana)", f"{r['percentual_issues_fechadas_mediana']:.1f}%")
            col_b.metric("% issues fechadas (média)", f"{r['percentual_issues_fechadas_media']:.1f}%")
            st.bar_chart(_distribuicao_binned(df["% issues fechadas"], bins=10, casas=1))
        st.caption(
            f"Repositórios com issues: {r['repositorios_com_issues']} | "
            f"sem issues: {r['repositorios_sem_issues']}"
        )

    with rq07:
        r = resultados_rq["rq07_cruzamento"]
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
                use_container_width=True,
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

    with tabela:
        st.dataframe(
            df,
            use_container_width=True,
            hide_index=True,
            column_config={"URL": st.column_config.LinkColumn("URL")},
        )