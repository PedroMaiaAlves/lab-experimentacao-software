"""Dashboard local do Lab05 — esqueleto da S02 (Issue #212 — Papel C: Lorran)."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import streamlit as st

ROOT = Path(__file__).resolve().parents[0]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import analisar  # noqa: E402
from experimento import plano  # noqa: E402
from experimento.graficos import (  # noqa: E402
    figura_boxplots,
    figura_forest_plot,
    figura_interacao,
    figura_ordem_execucao,
    texto_boxplots,
    texto_forest,
    texto_interacao,
    texto_ordem,
)

REPOSITORIO = "https://github.com/PedroMaiaAlves/lab-experimentacao-software"
MILESTONE = f"{REPOSITORIO}/milestone/7"


@st.cache_data(show_spinner=False)
def carregar_dados_dashboard() -> tuple[str, list[dict], dict]:
    try:
        csv_oficial = analisar.coleta_oficial_mais_recente(ROOT / "data" / "oficial")
    except FileNotFoundError:
        csv_oficial = None

    if csv_oficial is not None:
        registros, _, _ = analisar.carregar_tentativas(csv_oficial)
        json_oficial = ROOT / "data" / "analise" / "oficial_resumo.json"
        if json_oficial.is_file():
            resumo = json.loads(json_oficial.read_text(encoding="utf-8"))
            if resumo.get("metadados_coleta", {}).get("colecao_id") == csv_oficial.parent.name:
                analisar.ler_metadados_coleta(csv_oficial.parent, validar_oficial=True)
                return "oficial", registros, resumo
        return "oficial", registros, analisar.analisar(csv_oficial, validar_oficial=True)

    csv_piloto = analisar.piloto_mais_recente(ROOT / "data" / "piloto")
    registros, _, _ = analisar.carregar_tentativas(csv_piloto)
    json_piloto = ROOT / "data" / "analise" / "piloto_resumo.json"
    if json_piloto.is_file():
        resumo = json.loads(json_piloto.read_text(encoding="utf-8"))
        if resumo.get("metadados_coleta", {}).get("colecao_id") == csv_piloto.parent.name and "checagens" in resumo:
            return "piloto_previa", registros, resumo
    return "piloto_previa", registros, analisar.analisar(csv_piloto)


def _fmt(valor: float | None, casas: int = 2) -> str:
    if valor is None:
        return "—"
    return f"{valor:.{casas}f}".replace(".", ",")


def _fmt_p(valor: float | None) -> str:
    if valor is None:
        return "—"
    return f"{valor:.2e}".replace(".", ",") if valor < 1e-4 else f"{valor:.4f}".replace(".", ",")


def _tabela_descritiva(resumo: dict) -> list[dict]:
    cv_ref_mapa = {
        (c["experimento"], c["metrica"], c["broker"], c["tamanho_bytes"]): c["cv_protocolo_g1"]
        for c in resumo["checagens"]["comparacao_cv_protocolo"]
    }
    desc_idx = {
        (d["experimento"], d["metrica"], d["broker"], d["tamanho_bytes"]): d
        for d in resumo["descritiva"]
    }
    linhas = []
    for exp, metrica, tam in analisar.COMPARACOES_PRINCIPAIS:
        for broker in ("kafka", "rabbitmq"):
            d = desc_idx.get((exp, metrica, broker, tam))
            if not d:
                continue
            cv_ref = cv_ref_mapa.get((exp, metrica, broker, tam))
            linhas.append({
                "Exp": exp,
                "Métrica": metrica,
                "Broker": broker,
                "Tamanho": f"{tam // 1024} KiB",
                "n": d["n"],
                "Mediana": _fmt(d["mediana"], 2),
                "IQR": _fmt(d["iqr"], 2),
                "Média geom.": _fmt(d["media_geometrica"], 2),
                "CV obs.": f"{d['cv'] * 100:.1f}%".replace(".", ",") if d["cv"] is not None else "—",
                "CV ref. (#207)": f"{cv_ref * 100:.1f}%".replace(".", ",") if cv_ref is not None else "indisponível",
            })
    return linhas


def _tabela_testes(comparacoes: dict) -> list[dict]:
    linhas = []
    for chave, c in comparacoes.items():
        rotulo = analisar.ROTULOS_COMPARACAO.get(chave, chave)
        if not c.get("disponivel"):
            linhas.append({"Comparação": rotulo, "Teste recomendado": "indisponível"})
            continue
        linhas.append({
            "Comparação": rotulo,
            "Shapiro log (K / R)": f"{_fmt_p(c['shapiro_log_kafka_p'])} / {_fmt_p(c['shapiro_log_rabbitmq_p'])}",
            "Teste recomendado": c["teste_recomendado"],
            "Welch p": _fmt_p(c["welch_p"]),
            "Mann-Whitney p": _fmt_p(c["mann_whitney_p"]),
            "p Holm (rec.)": _fmt_p(c["p_recomendado_holm"]),
        })
    return linhas


def _tabela_interacoes(interacoes: dict) -> list[dict]:
    linhas = []
    for chave, inter in interacoes.items():
        if not inter.get("disponivel"):
            linhas.append({"Experimento": chave, "Status": "indisponível"})
            continue
        linhas.append({
            "Experimento": chave,
            "n total": inter["n_total"],
            "Contraste log": _fmt(inter["contraste_log"], 4),
            "Razão das razões": _fmt(inter["razao_das_razoes"], 3),
            "ANOVA F": _fmt(inter["anova_f"], 3),
            "ANOVA p": _fmt_p(inter["anova_p"]),
            "Permutação p": _fmt_p(inter["permutacao_p"]),
        })
    return linhas


def _tabela_ordem(efeito_ordem: list[dict]) -> list[dict]:
    linhas = []
    for o in efeito_ordem:
        ic = o.get("ic95_inclinacao")
        linhas.append({
            "Exp": o["experimento"],
            "Métrica": o["metrica"],
            "Broker": o["broker"],
            "Tamanho": f"{o['tamanho_bytes'] // 1024} KiB",
            "n": o["n"],
            "Inclinação log": _fmt(o.get("inclinacao_log"), 5) if o.get("disponivel") else "—",
            "IC 95% inclinação": f"[{_fmt(ic[0], 5)}; {_fmt(ic[1], 5)}]" if ic else "—",
            "Contém 0?": ("sim" if o["ic95_contem_zero"] else "não") if o.get("disponivel") else "—",
            "p-valor": _fmt_p(o.get("p_valor")) if o.get("disponivel") else "—",
        })
    return linhas


def _tabela_carga_relativa(cargas: list[dict]) -> list[dict]:
    return [
        {
            "Broker": c["broker"],
            "Tamanho": f"{c['tamanho_bytes'] // 1024} KiB",
            "Taxa alvo E2": _fmt(c["taxa_alvo_e2_msg_s"], 0),
            "Mediana E1": _fmt(c["throughput_e1_mediano_msg_s"], 1),
            "Carga alvo (% E1)": f"{c['carga_relativa_alvo'] * 100:.1f}%".replace(".", ",") if c["carga_relativa_alvo"] is not None else "—",
            "Carga efetiva (% E1)": f"{c['carga_relativa_efetiva'] * 100:.1f}%".replace(".", ",") if c["carga_relativa_efetiva"] is not None else "—",
        }
        for c in cargas
    ]


def _tabela_efeitos(comparacoes: dict) -> list[dict]:
    linhas = []
    for chave, c in comparacoes.items():
        if not c.get("disponivel"):
            continue
        inf, sup = c["ic95_bootstrap"]
        linhas.append({
            "Comparação": analisar.ROTULOS_COMPARACAO.get(chave, chave),
            "Razão geométrica (K/R)": _fmt(c["razao_geometrica"], 3),
            "IC 95% (bootstrap)": f"[{_fmt(inf, 3)}; {_fmt(sup, 3)}]",
            "δ de Cliff": f"{c['cliff_delta']:+.3f}".replace(".", ","),
            "Magnitude (Romano)": c["cliff_magnitude"],
            "p Holm": _fmt_p(c["p_recomendado_holm"]),
        })
    return linhas


st.set_page_config(
    page_title="Lab05 · Kafka × RabbitMQ",
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

modo, registros, resumo = carregar_dados_dashboard()
meta = resumo["metadados_coleta"]
contagens = resumo["contagens_status"]
sucessos_n = int(contagens.get("sucesso", 0))

st.markdown(
    """
    <div class="hero">
      <div class="eyebrow">Laboratório de Experimentação de Software · Lab05</div>
      <h1 style="margin:.35rem 0 0;color:white">Kafka 4.4.0 × RabbitMQ 4.4.1: throughput e latência p99</h1>
      <p>Experimento fatorial 2×2 randomizado em ambiente Docker isolado com durabilidade equivalente
      (acks=all vs. publisher confirms + quorum queue) e análise pré-registrada.</p>
    </div>
    """,
    unsafe_allow_html=True,
)
st.markdown(f"[Repositório]({REPOSITORIO}) · [Milestone Lab05S02]({MILESTONE}) · Dashboard local: `localhost:8501`")

if modo == "piloto_previa":
    st.warning(
        "**Prévia estrutural sobre dados do piloto (19/11/2026)** — a coleta oficial validada pelo "
        "portão G3 (#210) ainda não foi entregue no repositório. Esses valores **não são evidência "
        "confirmatória** (o E1 do piloto sofreu do controlador adaptativo do OMB e a latência do RabbitMQ "
        "no E2 tinha erro de arredondamento para 1 s, ambos corrigidos na S02)."
    )
elif not meta.get("omb_timestamp_ms_valido"):
    st.error("A imagem OMB registrada no manifesto não corresponde ao patch de timestamp em ms (`5b1fa709-ts-ms`).")

cards = st.columns(4)
cards[0].metric("Execuções válidas", sucessos_n, help=f"Contagens registradas: {contagens}")
cards[1].metric("Semente", plano.SEMENTE, help="Ordem randomizada por bloco e bootstrap/permutação.")
cards[2].metric("Nível de significância", "5%", help="Comparações principais bicaudais com correção de Holm (m = 4).")
cards[3].metric("Fonte exibida", "Oficial (G3)" if modo == "oficial" else "Piloto (prévia)", help=f"Coleta {meta['colecao_id']}")

st.header("1. Cenário")
st.write(
    "**Pergunta de pesquisa:** com a mesma garantia de durabilidade e o mesmo hardware (4 vCPU e 4 GiB em nó único), "
    "Apache Kafka 4.4.0 (KRaft) e RabbitMQ 4.4.1 (*quorum queue*) diferem em throughput máximo (M1) e em latência de cauda p99 (M2)? "
    "Essa diferença depende do tamanho da mensagem (1 KiB vs. 16 KiB)?"
)
col_e1, col_e2 = st.columns(2)
with col_e1:
    st.subheader("Experimento E1 — Saturação (H1)")
    st.write(
        "Mede throughput máximo (`throughput_msg_s` e `throughput_consumo_msg_s`) com taxa aberta e 120 s de medição "
        "(após 30 s de aquecimento descartado). H0: a mediana em Kafka e RabbitMQ é igual em cada tamanho."
    )
with col_e2:
    st.subheader("Experimento E2 — Taxa fixa (H2 e H3)")
    st.write(
        "Mede latência ponta a ponta p50/p99 (`latencia_p99_ms`) durante 60 s a 50% do menor throughput mediano "
        "observado no E1 para evitar confundir latência com tamanho de fila. H3 testa a interação broker × tamanho."
    )
st.caption(
    f"Protocolo oficial (#207): n = {plano.EXECUCOES_POR_CELULA} execuções por célula em 4 blocos balanceados "
    "(E1-B1, E1-B2, E2-B1, E2-B2); repetição apenas em falha técnica registrada, sem exclusão de outliers."
)

st.header("2. Dados")
st.write(
    f"**Coleta carregada:** `{resumo['arquivo']}` · **Status:** `{contagens}` · "
    f"**Portão G3:** {'aprovado' if meta['valido_g3'] else 'prévia sem coleta oficial'} · "
    f"**Imagem OMB (`ts-ms`):** {'válida' if meta['omb_timestamp_ms_valido'] else 'antiga (piloto)'}"
)
st.dataframe(_tabela_descritiva(resumo), width="stretch", hide_index=True)
st.plotly_chart(figura_boxplots(registros), width="stretch", key="boxplots")
st.write(texto_boxplots(registros, contagens))

st.plotly_chart(
    figura_ordem_execucao(registros, resumo["checagens"]["efeito_ordem"]),
    width="stretch",
    key="ordem",
)
st.write(texto_ordem(resumo["checagens"]["efeito_ordem"]))

with st.expander("Checagens de validade interna — ordem, blocos e carga relativa no E2"):
    st.dataframe(_tabela_ordem(resumo["checagens"]["efeito_ordem"]), width="stretch", hide_index=True)
    blocos_disp = [b for b in resumo["checagens"]["efeito_bloco"] if b.get("disponivel")]
    if blocos_disp:
        linhas_blocos = [
            {
                "Exp": b["experimento"],
                "Métrica": b["metrica"],
                "Tamanho": f"{b['tamanho_bytes'] // 1024} KiB",
                "Razão broker ajustada": _fmt(b["modelo_ajustado_bloco"].get("razao_broker_ajustada"), 3),
                "p bloco": _fmt_p(b["modelo_ajustado_bloco"].get("p_bloco")),
                "Significativo?": "sim" if b["modelo_ajustado_bloco"].get("efeito_bloco_significativo") else "não",
            }
            for b in blocos_disp
            if b["modelo_ajustado_bloco"].get("disponivel")
        ]
        st.dataframe(linhas_blocos, width="stretch", hide_index=True)
    else:
        st.info("Efeito de bloco indisponível na coleta atual (exige pelo menos 2 blocos registrados).")
    st.dataframe(_tabela_carga_relativa(resumo["checagens"]["carga_relativa_e2"]), width="stretch", hide_index=True)

st.header("3. Testes")
st.dataframe(_tabela_testes(resumo["comparacoes"]), width="stretch", hide_index=True)
st.subheader("Interação broker × tamanho da mensagem (H3)")
st.dataframe(_tabela_interacoes(resumo["interacoes"]), width="stretch", hide_index=True)
st.plotly_chart(
    figura_interacao(resumo["descritiva"], resumo["interacoes"]),
    width="stretch",
    key="interacao",
)
st.write(texto_interacao(resumo["interacoes"]))

with st.expander("Sensibilidade às repetições técnicas e outliers preservados"):
    sens = resumo["checagens"]["sensibilidade_repeticoes"]
    st.write(
        f"**IDs com repetição técnica:** {sens['n_ids_repetidos']} "
        + (f"(`{', '.join(sens['ids_repetidos'])}`)" if sens["ids_repetidos"] else "(nenhum)")
        + f" · **Altera conclusão sem repetições?** {'sim' if sens['altera_conclusao'] else 'não'}."
    )
    if sens["diferencas"]:
        st.json(sens["diferencas"])
    outliers = resumo["checagens"]["outliers"]
    st.write(f"**Outliers extremos (regra 1,5 × IQR, nunca removidos):** {len(outliers)}")
    if outliers:
        st.dataframe(outliers, width="stretch", hide_index=True)

st.header("4. Efeito")
st.dataframe(_tabela_efeitos(resumo["comparacoes"]), width="stretch", hide_index=True)
st.plotly_chart(figura_forest_plot(resumo["comparacoes"]), width="stretch", key="forest")
st.write(texto_forest(resumo["comparacoes"]))
st.info(
    "A interpretação compara magnitude do efeito (razão geométrica e δ de Cliff) e largura do IC de 95%, "
    "em vez de depender apenas do p-valor. Não rejeitar H0 não comprova igualdade entre os brokers."
)
st.caption(
    "Esqueleto da Lab05S02 (#212). A seção de Impacto (vCPU-hora, GiB-hora, atualização das evidências de adoção e "
    "recomendação arquitetural final) será integrada na S03."
)
