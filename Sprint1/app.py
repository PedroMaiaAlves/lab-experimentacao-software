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
    st.caption(f"JSON por RQ salvo em `data/rq/`. Dataset completo salvo em `data/raw/`.")

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
    st.success(f"{len(df)} repositório(s) coletado(s). JSONs de cada RQ salvos em `data/rq/`.")
    col1, col2, col3 = st.columns(3)
    col1.metric("Total de repositórios", len(df))
    col2.metric("Total de estrelas", f"{int(df['Estrelas'].sum()):,}".replace(",", "."))
    col3.metric("Linguagens distintas", df["Linguagem"].nunique())

    csv = df.to_csv(index=False).encode("utf-8")
    st.download_button("Baixar dataset completo em CSV", csv, "repositorios_populares.csv", "text/csv")

    (rq01, rq02, rq03, rq04, rq05, rq06, rq07, tabela) = st.tabs(
        ["RQ01 Idade", "RQ02 PRs", "RQ03 Releases", "RQ04 Atualização",
         "RQ05 Linguagem", "RQ06 Issues", "RQ07 Cruzamento", "📋 Dados"]
    )

    with rq01:
        r = resultados_rq["rq01_idade"]
        st.subheader("RQ01 — Sistemas populares são maduros/antigos?")
        st.write("**Métrica:** idade do repositório, em anos, a partir da data de criação.")
        st.metric("Idade mediana", f"{r['idade_mediana_anos']:.1f} anos")
        st.bar_chart(df["Idade (anos)"].value_counts(bins=10).sort_index())


    with rq03:
        r = resultados_rq["rq03_releases"]
        st.subheader("RQ03 — Sistemas populares lançam releases com frequência?")
        st.write("**Métrica:** total de releases do repositório.")
        st.metric("Releases (mediana)", int(r["releases_mediana"]))
        st.bar_chart(df["Total de releases"].value_counts(bins=10).sort_index())

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

    with rq07:
        r = resultados_rq["rq07_cruzamento"]
        st.subheader("RQ07 — Linguagens populares recebem mais contribuição, mais releases e mais atualizações?")
        st.write("Cruzamento das RQ02, RQ03 e RQ04, agrupado por linguagem (linguagens com pelo menos 3 repositórios na amostra).")
        resumo = pd.DataFrame(r["resumo_por_linguagem"]).set_index("Linguagem")
        st.dataframe(resumo, use_container_width=True)
        if not resumo.empty:
            st.bar_chart(resumo["PRs_aceitas_mediana"])
            st.bar_chart(resumo["Releases_mediana"])
            st.bar_chart(resumo["Dias_desde_atualizacao_mediana"])

    with tabela:
        st.dataframe(
            df,
            use_container_width=True,
            hide_index=True,
            column_config={"URL": st.column_config.LinkColumn("URL")},
        )
