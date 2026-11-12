"""Dashboard local do Lab04: t pareado versus Wilcoxon pareado."""

from __future__ import annotations

import numpy as np
import streamlit as st

from experimento.analise import analisar_pares
from experimento.dados import ROOT, ler_json, ler_pares
from experimento.g1 import figura_g1, texto_g1
from experimento.g2 import figura_g2, texto_g2
from experimento.g3 import figura_g3, texto_g3
from experimento.g4 import figura_g4, texto_g4
from experimento.monte_carlo import ler_resultados
from experimento.q2_interpretacao import ler_texto_q2
from experimento.resumo_real import resumir_reais

REPOSITORIO = "https://github.com/PedroMaiaAlves/lab-experimentacao-software"
MILESTONE = f"{REPOSITORIO}/milestone/5"


@st.cache_data(show_spinner=False)
def carregar_dados() -> tuple:
    reais = ler_pares(ROOT / "data/real/pares_reais.csv")
    simulados = ler_pares(ROOT / "data/simulado/pares_simulados.csv")
    parametros = ler_json(ROOT / "data/simulado/parametros.json")
    q1_path = ROOT / "data/s02/q1_resultados.csv"
    q1 = ler_resultados(q1_path) if q1_path.exists() else []
    q2 = ler_resultados(ROOT / "data/s02/q2_resultados.csv")
    q3 = ler_resultados(ROOT / "data/s02/q3_resultados.csv")
    return reais, simulados, parametros, q1, q2, q3


def _tabela_resultados(resultados: dict) -> list[dict]:
    linhas = []
    for chave, nome in (("t_pareado", "t pareado"), ("wilcoxon", "Wilcoxon pareado")):
        resultado = resultados[chave]
        linhas.append({
            "Teste": nome,
            "Estatística": resultado["estatistica"],
            "p-valor": f"{resultado['p_valor']:.3e}" if resultado["p_valor"] is not None else "indisponível",
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
      [data-testid="stMetric"] {background: rgba(128,128,128,.08); border: 1px solid rgba(128,128,128,.25); padding: 1rem; border-radius: .75rem;}
      .hero {padding: 1.5rem 1.7rem; border-radius: 1rem; background: linear-gradient(135deg,#0f172a,#1e3a8a); color: white; margin-bottom: 1.4rem;}
      .hero p {color: #dbeafe; margin: .45rem 0 0; max-width: 850px;}
      .eyebrow {font-size: .78rem; letter-spacing: .12em; text-transform: uppercase; color: #93c5fd; font-weight: 700;}
    </style>
    """,
    unsafe_allow_html=True,
)

reais, simulados, parametros, q1, q2, q3 = carregar_dados()
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
st.plotly_chart(figura_g4(q2, q3), use_container_width=True, key="g4")
st.write(texto_g4(q2, q3))
st.warning(
    "Sob H0 em Q3, o t rejeitou 4,19% das vezes (IC 95%: 3,81–4,60%), abaixo dos 5% nominais; "
    "o Wilcoxon rejeitou 4,59% (IC 95%: 4,20–5,02%). O t foi conservador neste cenário, "
    "e o intervalo do Wilcoxon inclui 5%; não interprete todas essas taxas como poder."
)
st.caption(
    "Razão 1,00 significa H0: nesse ponto medimos erro tipo I, não poder sob uma diferença real. "
    "A linha tracejada marca α = 5%; nos demais pontos, maior razão representa maior efeito."
)
with st.expander("Q2 — interpretação e comparação pareada de Diogo"):
    interpretacao_q2 = ler_texto_q2()
    st.write(interpretacao_q2["texto"])
    st.dataframe(interpretacao_q2["comparacao"], use_container_width=True, hide_index=True)
with st.expander("Q3 — hipóteses e limites da comparação"):
    st.write(
        "Usamos d = log(razão) + σ × T₃/√3, com σ calibrado nos dados reais. Como Var(T₃) = 3, "
        "a variância populacional de d permanece σ²; não forçamos a variância de cada amostra. "
        "A t₃ tem média e variância finitas, mas caudas mais pesadas que a normal e quarto momento infinito. "
        "Sob H0, a média é zero e a distribuição é simétrica em zero: as duas hipóteses nulas valem. "
        "A distribuição exata da estatística t, porém, exige normalidade das diferenças; Q3 avalia sua robustez."
    )
    st.write(
        "Os testes usam as mesmas amostras dentro de cada cenário; Q2 e Q3 usam fluxos independentes "
        "derivados de 42, com chaves 2 e 3. Barras sobrepostas não são um teste de diferença entre poderes. "
        "A incerteza exibida é só de Monte Carlo, sem incluir a estimação de σ nos 30 pares reais."
    )
with st.expander("Resultados agregados de Q2 e Q3"):
    st.dataframe(q2 + q3, use_container_width=True, hide_index=True)

st.header("6. Dados reais")
resumo_real = resumir_reais(reais)
st.dataframe(_tabela_resultados(resumo_real["resultados"]), use_container_width=True, hide_index=True)
ic = resumo_real["ic95_razao_t"]
st.write(
    f"Nos {resumo_real['n_pares']} pares reais, a razão geométrica sem/com cache foi "
    f"**{resumo_real['razao_geometrica']:.2f}**"
    + (f", com IC de 95% pelo t de **{ic[0]:.2f} a {ic[1]:.2f}**. " if ic else "; IC t indisponível. ")
    + "Razão maior que 1 indica menor tempo com cache; esse efeito observado não é o poder estimado nas simulações."
)
for resultado in resumo_real["resultados"].values():
    st.write(resultado["interpretacao"])
st.caption(
    "O IC t pressupõe adequação das diferenças e independência; a interpretação do Wilcoxon também requer simetria. "
    "Foram repetições do mesmo projeto na mesma máquina: carga, ordem e cache do sistema podem influenciar os tempos. "
    "Não medimos todo o build nem demonstramos desempenho em outras máquinas ou projetos."
)
with st.expander("Os 30 pares reais preservados"):
    st.dataframe(_tabela_pares(reais), use_container_width=True, hide_index=True)

st.header("7. Conclusão")
st.write(
    "Q1 apresentou taxas compatíveis com os 5% nominais sob normalidade. Em Q2, o t pareado mostrou pequena "
    "vantagem nos efeitos intermediários; com caudas pesadas em Q3, o Wilcoxon teve maior poder estimado "
    "em todas as razões acima de 1 (até 10,44 pontos percentuais), enquanto o t foi conservador sob H0. "
    "A escolha depende da distribuição das diferenças e da pergunta: t para a média, com atenção à normalidade "
    "e aos valores extremos; Wilcoxon para deslocamentos simétricos, sem assumir normalidade, mas não livre de hipóteses."
)
st.write(
    f"O efeito real estimado favorece o cache nesta etapa local (razão geométrica "
    f"{resumo_real['razao_geometrica']:.2f}); isso não torna um teste universalmente melhor. "
    "A simulação compara comportamento dos testes, enquanto os dados reais respondem à pergunta sobre o cache."
)
st.caption("Dados reais, dados simulados e resultados Monte Carlo são identificados separadamente em todo o dashboard.")
