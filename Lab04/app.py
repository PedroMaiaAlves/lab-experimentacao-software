"""Dashboard local do Lab04: t pareado versus Wilcoxon pareado."""

from __future__ import annotations

import numpy as np
import streamlit as st

from experimento.analise import analisar_pares
from experimento.dados import ROOT, ler_json, ler_pares
from experimento.g1 import figura_g1, texto_g1
from experimento.g2 import figura_g2, texto_g2
from experimento.g3 import figura_g3, texto_g3
from experimento.monte_carlo import ler_resultados

REPOSITORIO = "https://github.com/PedroMaiaAlves/lab-experimentacao-software"
MILESTONE = f"{REPOSITORIO}/milestone/5"


@st.cache_data(show_spinner=False)
def carregar_dados() -> tuple[np.ndarray, np.ndarray, dict, list[dict]]:
    reais = ler_pares(ROOT / "data/real/pares_reais.csv")
    simulados = ler_pares(ROOT / "data/simulado/pares_simulados.csv")
    parametros = ler_json(ROOT / "data/simulado/parametros.json")
    q1_path = ROOT / "data/s02/q1_resultados.csv"
    q1 = ler_resultados(q1_path) if q1_path.exists() else []
    return reais, simulados, parametros, q1


def _tabela_resultados(resultados: dict) -> list[dict]:
    linhas = []
    for chave, nome in (("t_pareado", "t pareado"), ("wilcoxon", "Wilcoxon pareado")):
        resultado = resultados[chave]
        linhas.append({
            "Teste": nome,
            "Estatística": resultado["estatistica"],
            "p-valor": resultado["p_valor"],
            "Decisão (α = 0,05)": resultado["decisao"],
            "Método": resultado["metodo"],
        })
    return linhas


def _tabela_pares(reais: np.ndarray) -> list[dict]:
    return [
        {"Par": i, "Sem cache (s)": float(sem), "Com cache (s)": float(com), "Razão": float(sem / com)}
        for i, (sem, com) in enumerate(reais, 1)
    ]


st.set_page_config(
    page_title="Lab04 · Testes pareados",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="collapsed",
)

st.markdown(
    """
    <style>
      .block-container {max-width: 1180px; padding-top: 2.2rem; padding-bottom: 4rem;}
      h1, h2, h3 {letter-spacing: -0.025em;}
      h2 {border-top: 1px solid #e2e8f0; padding-top: 1.7rem; margin-top: 2.4rem;}
      [data-testid="stMetric"] {background: #f8fafc; border: 1px solid #e2e8f0; padding: 1rem; border-radius: .75rem;}
      .hero {padding: 1.5rem 1.7rem; border-radius: 1rem; background: linear-gradient(135deg,#0f172a,#1e3a8a); color: white; margin-bottom: 1.4rem;}
      .hero p {color: #dbeafe; margin: .45rem 0 0; max-width: 850px;}
      .eyebrow {font-size: .78rem; letter-spacing: .12em; text-transform: uppercase; color: #93c5fd; font-weight: 700;}
      .pending {border-left: 4px solid #f59e0b; background: #fffbeb; padding: .85rem 1rem; border-radius: .4rem;}
    </style>
    """,
    unsafe_allow_html=True,
)

reais, simulados, parametros, q1 = carregar_dados()
resultados_simulados = analisar_pares(simulados)

st.markdown(
    """
    <div class="hero">
      <div class="eyebrow">Laboratório de Experimentação de Software · Lab04</div>
      <h1 style="margin:.35rem 0 0;color:white">Cache de bytecode: t pareado × Wilcoxon</h1>
      <p>Um experimento reproduzível sobre tempos de compilação do Django 5.2.8, com dados pareados,
      simulação calibrada e avaliação Monte Carlo dos testes.</p>
    </div>
    """,
    unsafe_allow_html=True,
)
st.markdown(f"[Repositório]({REPOSITORIO}) · [Milestone Lab04S02]({MILESTONE}) · Dashboard local: `localhost:8501`")

metricas = st.columns(3)
metricas[0].metric("Pares reais", len(reais), help="Cada par possui uma execução sem cache e outra com cache.")
metricas[1].metric("Medições reais", len(reais) * 2)
metricas[2].metric("Nível de significância", "5%", help="Testes bicaudais.")

st.header("1. Cenário")
st.write(
    "A pergunta é: **como a reutilização do cache de bytecode altera o tempo de compilação dos arquivos Python "
    "do Django?** Cada unidade experimental é um par dos mesmos arquivos, compilados uma vez sem cache e outra "
    "com cache. A diferença analisada é `log(sem cache) − log(com cache)`; valores positivos favorecem o cache."
)
col_t, col_w = st.columns(2)
with col_t:
    st.subheader("t pareado")
    st.write("H0: a média populacional das diferenças logarítmicas é zero. Exige atenção à normalidade das diferenças.")
with col_w:
    st.subheader("Wilcoxon pareado")
    st.write("H0: as diferenças são simétricas em torno de zero. Usa postos e não pressupõe normalidade.")
st.caption("Ambos são bicaudais, com α = 0,05. Não rejeitar H0 não comprova igualdade.")

st.header("2. Os dados — G1")
st.plotly_chart(figura_g1(reais, simulados), use_container_width=True, key="g1")
st.write(texto_g1(reais, simulados))
with st.expander("Como a amostra simulada foi calibrada"):
    st.write(
        "As médias e a covariância dos dois log-tempos foram estimadas exclusivamente nos 30 pares reais. "
        "A amostra preservada foi gerada com normal bivariada e semente 42."
    )
    st.json({
        "medias_log": parametros["medias_log"],
        "covariancia_log": parametros["covariancia_log"],
        "delta_observado_log": parametros["delta_observado_log"],
        "razao_geometrica_observada": parametros["razao_geometrica_observada"],
    })

st.header("3. Como os testes funcionam — G2")
st.dataframe(_tabela_resultados(resultados_simulados), use_container_width=True, hide_index=True)
st.plotly_chart(figura_g2(simulados, resultados_simulados), use_container_width=True, key="g2")
st.write(texto_g2(simulados, resultados_simulados))
st.caption("Estes resultados usam a amostra simulada preservada; não são ainda a conclusão sobre os dados reais.")

st.header("4. Erro tipo I — Q1 e G3")
if q1:
    st.plotly_chart(figura_g3(q1), use_container_width=True, key="g3")
    st.write(texto_g3(q1))
    with st.expander("Resultados agregados de Q1"):
        st.dataframe(q1, use_container_width=True, hide_index=True)
else:
    st.warning("Os resultados agregados de Q1 ainda não foram gerados. Execute `python Lab04/simular_s02.py`.")

st.header("5. Poder — Q2, Q3 e G4")
st.markdown(
    """
    <div class="pending"><strong>Entrega em andamento.</strong> Q2 medirá o poder sob diferenças normais;
    Q3 repetirá a comparação com caudas pesadas simétricas. O G4 será produzido somente depois de ambas as
    simulações, usando a mesma grade de efeitos e a mesma política de sementes.</div>
    """,
    unsafe_allow_html=True,
)
st.write("Issues relacionadas: [#186](%s/issues/186), [#187](%s/issues/187), [#188](%s/issues/188) e [#189](%s/issues/189)." % ((REPOSITORIO,) * 4))

st.header("6. Dados reais")
st.dataframe(_tabela_pares(reais), use_container_width=True, hide_index=True)
st.info(
    "A tabela preserva os 30 pares reais. A análise inferencial final será exibida aqui somente após Q1–Q3, "
    "para separar resultado observado de avaliação de erro e poder."
)

st.header("7. Conclusão")
st.write(
    "A expectativa registrada antes das simulações é que o t pareado seja competitivo quando as diferenças são "
    "normais e que o Wilcoxon possa ganhar poder em distribuições simétricas de caudas pesadas. A recomendação "
    "final permanece pendente até Q2, Q3 e G4; nenhum teste será declarado universalmente superior."
)
st.caption("Dados reais, dados simulados e resultados Monte Carlo são identificados separadamente em todo o dashboard.")
