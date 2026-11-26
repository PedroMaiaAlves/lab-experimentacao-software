"""Visualizações Plotly da Lab05S02 (Issue #212 — Papel C: Lorran)."""

from __future__ import annotations

import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots

CORES_BROKER = {"kafka": "#1d4ed8", "rabbitmq": "#ea580c"}
NOMES_BROKER = {"kafka": "Apache Kafka 4.4.0", "rabbitmq": "RabbitMQ 4.4.1"}
ROTULOS_TAMANHO = {1024: "1 KiB", 16384: "16 KiB"}
ORDEM_FOREST = (
    ("E2_latencia_p99_ms_16k", "E2 · Latência p99 · 16 KiB"),
    ("E2_latencia_p99_ms_1k", "E2 · Latência p99 · 1 KiB"),
    ("E1_throughput_msg_s_16k", "E1 · Throughput · 16 KiB"),
    ("E1_throughput_msg_s_1k", "E1 · Throughput · 1 KiB"),
)


def figura_boxplots(registros: list[dict]) -> go.Figure:
    """Boxplots com pontos individuais por célula para E1 (throughput) e E2 (latência p99)."""
    fig = make_subplots(
        rows=1,
        cols=2,
        subplot_titles=("E1 — Throughput máximo (msg/s)", "E2 — Latência p99 (ms)"),
        horizontal_spacing=0.1,
    )
    paineis = (("E1", "throughput_msg_s", 1), ("E2", "latencia_p99_ms", 2))
    for exp, metrica, col in paineis:
        for broker in ("kafka", "rabbitmq"):
            sub = [
                r for r in registros
                if r["experimento"] == exp
                and r["broker"] == broker
                and r.get(metrica) is not None
                and r[metrica] > 0
            ]
            if not sub:
                continue
            xs = [ROTULOS_TAMANHO.get(r["tamanho_bytes"], str(r["tamanho_bytes"])) for r in sub]
            ys = [float(r[metrica]) for r in sub]
            custom = [
                [r["id_execucao"], r.get("bloco") or "—", r.get("ordem"), r.get("tentativa") or 1]
                for r in sub
            ]
            fig.add_trace(
                go.Box(
                    x=xs,
                    y=ys,
                    name=NOMES_BROKER[broker],
                    legendgroup=broker,
                    showlegend=col == 1,
                    marker_color=CORES_BROKER[broker],
                    boxpoints="all",
                    jitter=0.32,
                    pointpos=0,
                    customdata=custom,
                    hovertemplate=(
                        f"{NOMES_BROKER[broker]} (%{{x}})<br>"
                        "ID: %{customdata[0]} · Bloco: %{customdata[1]}<br>"
                        "Ordem: %{customdata[2]} · Tentativa: %{customdata[3]}<br>"
                        "Valor: %{y:.2f}<extra></extra>"
                    ),
                ),
                row=1,
                col=col,
            )

    fig.update_yaxes(title_text="Throughput (msg/s, escala log)", type="log", row=1, col=1)
    fig.update_yaxes(title_text="Latência p99 (ms, escala log)", type="log", row=1, col=2)
    fig.update_xaxes(categoryorder="array", categoryarray=["1 KiB", "16 KiB"])
    fig.update_layout(
        title="Distribuição por célula — pontos individuais preservados (sem exclusão de outliers)",
        boxmode="group",
        template="plotly_white",
        height=500,
        legend=dict(orientation="h", yanchor="bottom", y=1.08, xanchor="left", x=0),
        margin=dict(t=115, b=65),
    )
    return fig


def figura_forest_plot(comparacoes: dict) -> go.Figure:
    """Forest plot das razões geométricas (Kafka / RabbitMQ) com IC 95% por bootstrap."""
    fig = go.Figure()
    xs, ys, err_plus, err_minus, cores, customs, textos = [], [], [], [], [], [], []
    for chave, rotulo in ORDEM_FOREST:
        c = comparacoes.get(chave, {})
        if not c.get("disponivel"):
            continue
        razao = float(c["razao_geometrica"])
        inf, sup = float(c["ic95_bootstrap"][0]), float(c["ic95_bootstrap"][1])
        xs.append(razao)
        ys.append(rotulo)
        err_plus.append(max(0.0, sup - razao))
        err_minus.append(max(0.0, razao - inf))
        cores.append("#1d4ed8" if chave.startswith("E1") else "#ea580c")
        textos.append(f"{razao:.3f}× [{inf:.3f}; {sup:.3f}]")
        customs.append([
            inf,
            sup,
            float(c["cliff_delta"]),
            c["cliff_magnitude"],
            c["teste_recomendado"],
            float(c["p_recomendado_holm"]),
        ])

    if xs:
        fig.add_trace(
            go.Scatter(
                x=xs,
                y=ys,
                mode="markers+text",
                text=textos,
                textposition="top center",
                marker=dict(size=11, color=cores),
                error_x=dict(
                    type="data",
                    symmetric=False,
                    array=err_plus,
                    arrayminus=err_minus,
                    thickness=2,
                    width=6,
                    color="#334155",
                ),
                customdata=customs,
                hovertemplate=(
                    "<b>%{y}</b><br>"
                    "Razão geométrica (K/R): %{x:.3f} [%{customdata[0]:.3f}; %{customdata[1]:.3f}]<br>"
                    "δ de Cliff: %{customdata[2]:+.3f} (%{customdata[3]})<br>"
                    "Teste rec.: %{customdata[4]} · p_Holm = %{customdata[5]:.4g}<extra></extra>"
                ),
                showlegend=False,
            )
        )

    fig.add_vline(
        x=1.0,
        line=dict(color="#64748b", width=2, dash="dash"),
        annotation_text="Sem diferença (razão = 1,0)",
        annotation_position="bottom right",
    )
    fig.update_xaxes(title_text="Razão geométrica Kafka / RabbitMQ (escala log)", type="log")
    fig.update_layout(
        title="Forest plot — Razão geométrica e IC 95% (bootstrap, semente 42)",
        template="plotly_white",
        height=430,
        margin=dict(t=85, b=65, l=190),
    )
    return fig


def figura_interacao(descritiva: list[dict], interacoes: dict) -> go.Figure:
    """Gráfico de interação tamanho × broker (H3) sobre médias geométricas."""
    fig = make_subplots(
        rows=1,
        cols=2,
        subplot_titles=("E1 — Interação no throughput (H3)", "E2 — Interação na latência p99 (H3)"),
        horizontal_spacing=0.1,
    )
    indice = {
        (d["experimento"], d["metrica"], d["broker"], d["tamanho_bytes"]): d
        for d in descritiva
    }
    paineis = (
        ("E1", "throughput_msg_s", "E1_throughput_msg_s", 1),
        ("E2", "latencia_p99_ms", "E2_latencia_p99_ms", 2),
    )
    for exp, metrica, chave_inter, col in paineis:
        for broker in ("kafka", "rabbitmq"):
            xs, ys = [], []
            for tam in (1024, 16384):
                d = indice.get((exp, metrica, broker, tam))
                if d and d.get("media_geometrica") is not None:
                    xs.append(ROTULOS_TAMANHO[tam])
                    ys.append(float(d["media_geometrica"]))
            if xs:
                fig.add_trace(
                    go.Scatter(
                        x=xs,
                        y=ys,
                        mode="lines+markers",
                        name=NOMES_BROKER[broker],
                        legendgroup=broker,
                        showlegend=col == 1,
                        line=dict(color=CORES_BROKER[broker], width=3),
                        marker=dict(size=9),
                        hovertemplate=f"{NOMES_BROKER[broker]} · %{{x}}<br>Média geom.: %{{y:.2f}}<extra></extra>",
                    ),
                    row=1,
                    col=col,
                )
        inter = interacoes.get(chave_inter, {})
        if inter.get("disponivel"):
            fig.add_annotation(
                x=0.5,
                y=1.02,
                xref=f"x{'' if col == 1 else col} domain",
                yref=f"y{'' if col == 1 else col} domain",
                text=(
                    f"razão das razões = {inter['razao_das_razoes']:.2f} · "
                    f"p_ANOVA = {inter['anova_p']:.3g} · p_perm = {inter['permutacao_p']:.3g}"
                ),
                showarrow=False,
                font=dict(size=11, color="#334155"),
            )

    fig.update_yaxes(title_text="Média geométrica (msg/s, log)", type="log", row=1, col=1)
    fig.update_yaxes(title_text="Média geométrica p99 (ms, log)", type="log", row=1, col=2)
    fig.update_xaxes(categoryorder="array", categoryarray=["1 KiB", "16 KiB"])
    fig.update_layout(
        title="Interação tamanho da mensagem × broker (linhas paralelas indicam ausência de interação)",
        template="plotly_white",
        height=470,
        legend=dict(orientation="h", yanchor="bottom", y=1.10, xanchor="left", x=0),
        margin=dict(t=120, b=65),
    )
    return fig


def figura_ordem_execucao(registros: list[dict], efeito_ordem: list[dict] | None = None) -> go.Figure:
    """Throughput do E1 pela ordem global de execução para checar deriva temporal (#208 / #212)."""
    celulas = (
        ("kafka", 1024, 1, 1, "Kafka · 1 KiB"),
        ("kafka", 16384, 1, 2, "Kafka · 16 KiB"),
        ("rabbitmq", 1024, 2, 1, "RabbitMQ · 1 KiB"),
        ("rabbitmq", 16384, 2, 2, "RabbitMQ · 16 KiB"),
    )
    fig = make_subplots(
        rows=2,
        cols=2,
        subplot_titles=[c[4] for c in celulas],
        vertical_spacing=0.16,
        horizontal_spacing=0.09,
    )
    reg_mapa = {
        (e["broker"], e["tamanho_bytes"]): e
        for e in (efeito_ordem or [])
        if e["experimento"] == "E1" and e["metrica"] == "throughput_msg_s"
    }

    e1_sucessos = [
        r for r in registros
        if r["experimento"] == "E1"
        and r.get("throughput_msg_s") is not None
        and r["throughput_msg_s"] > 0
        and r.get("ordem") is not None
    ]
    blocos_e1 = sorted({r.get("bloco", "") for r in e1_sucessos if r.get("bloco")})
    divisor_bloco = None
    if len(blocos_e1) >= 2:
        ordens_b1 = [float(r["ordem"]) for r in e1_sucessos if r.get("bloco") == blocos_e1[0]]
        if ordens_b1:
            divisor_bloco = max(ordens_b1) + 0.5

    mostrou_primaria = False
    mostrou_repetida = False
    for idx, (broker, tam, row, col, _) in enumerate(celulas, start=1):
        itens = sorted(
            (r for r in e1_sucessos if r["broker"] == broker and r["tamanho_bytes"] == tam),
            key=lambda r: float(r["ordem"]),
        )
        if not itens:
            continue
        primarias = [r for r in itens if int(r.get("tentativa") or 1) <= 1]
        repetidas = [r for r in itens if int(r.get("tentativa") or 1) > 1]

        if primarias:
            fig.add_trace(
                go.Scatter(
                    x=[float(r["ordem"]) for r in primarias],
                    y=[float(r["throughput_msg_s"]) for r in primarias],
                    mode="markers",
                    name="Tentativa primária",
                    legendgroup="primaria",
                    showlegend=not mostrou_primaria,
                    marker=dict(size=8, color=CORES_BROKER[broker], opacity=0.85),
                    customdata=[[r["id_execucao"], r.get("bloco") or "—"] for r in primarias],
                    hovertemplate=(
                        "Ordem %{x} · %{customdata[0]} (%{customdata[1]})<br>"
                        "Throughput: %{y:.1f} msg/s<extra></extra>"
                    ),
                ),
                row=row,
                col=col,
            )
            mostrou_primaria = True

        if repetidas:
            fig.add_trace(
                go.Scatter(
                    x=[float(r["ordem"]) for r in repetidas],
                    y=[float(r["throughput_msg_s"]) for r in repetidas],
                    mode="markers",
                    name="Repetição após falha técnica",
                    legendgroup="repetida",
                    showlegend=not mostrou_repetida,
                    marker=dict(
                        size=10,
                        symbol="diamond",
                        color=CORES_BROKER[broker],
                        line=dict(color="#0f172a", width=1.5),
                    ),
                    customdata=[[r["id_execucao"], r.get("tentativa"), r.get("bloco") or "—"] for r in repetidas],
                    hovertemplate=(
                        "Ordem %{x} · %{customdata[0]} (t%{customdata[1]}, %{customdata[2]})<br>"
                        "Throughput: %{y:.1f} msg/s<extra></extra>"
                    ),
                ),
                row=row,
                col=col,
            )
            mostrou_repetida = True

        reg = reg_mapa.get((broker, tam))
        if reg and reg.get("disponivel"):
            xs_ord = np.array([float(r["ordem"]) for r in itens], dtype=float)
            x_grid = np.linspace(float(xs_ord.min()), float(xs_ord.max()), 30)
            y_trend = np.exp(reg["intercepto_log"] + reg["inclinacao_log"] * x_grid)
            fig.add_trace(
                go.Scatter(
                    x=x_grid,
                    y=y_trend,
                    mode="lines",
                    name="Tendência log-linear",
                    legendgroup="tendencia",
                    showlegend=False,
                    line=dict(color="#334155", width=2, dash="dot"),
                    hoverinfo="skip",
                ),
                row=row,
                col=col,
            )
            suf = "" if idx == 1 else str(idx)
            fig.add_annotation(
                x=0.02,
                y=0.98,
                xref=f"x{suf} domain",
                yref=f"y{suf} domain",
                xanchor="left",
                yanchor="top",
                text=f"inclinação = {reg['inclinacao_log']:+.4f} · p = {reg['p_valor']:.3f}",
                showarrow=False,
                bgcolor="rgba(255,255,255,0.82)",
                font=dict(size=10, color="#0f172a"),
            )

        if divisor_bloco is not None:
            fig.add_vline(
                x=divisor_bloco,
                line=dict(color="#94a3b8", width=1.5, dash="dash"),
                row=row,
                col=col,
            )

    fig.update_xaxes(title_text="Ordem de execução no E1", row=2)
    fig.update_yaxes(title_text="Throughput (msg/s, log)", type="log", col=1)
    fig.update_yaxes(type="log", col=2)
    fig.update_layout(
        title="Efeito de ordem — Throughput do E1 ao longo da sequência randomizada",
        template="plotly_white",
        height=620,
        legend=dict(orientation="h", yanchor="bottom", y=1.06, xanchor="left", x=0),
        margin=dict(t=105, b=65),
    )
    return fig


def texto_boxplots(registros: list[dict], contagens: dict[str, int] | None = None) -> str:
    n_e1 = sum(1 for r in registros if r["experimento"] == "E1")
    n_e2 = sum(1 for r in registros if r["experimento"] == "E2")
    falhas = sum(v for k, v in (contagens or {}).items() if k != "sucesso")
    return (
        f"Os painéis exibem todas as {n_e1} medições válidas do E1 e {n_e2} do E2 em escala logarítmica, "
        "mostrando mediana, quartis (IQR) e cada ponto individual. "
        f"Foram registradas {falhas} tentativa(s) com falha ou bloqueio técnico, que não são imputadas nem "
        "convertidas em zero; valores extremos tecnicamente válidos permanecem na amostra."
    )


def texto_forest(comparacoes: dict) -> str:
    disponiveis = [c for c in comparacoes.values() if c.get("disponivel")]
    if not disponiveis:
        return "Comparações principais indisponíveis para os dados carregados."
    significativos = sum(
        1 for c in disponiveis
        if c.get("p_recomendado_holm") is not None and c["p_recomendado_holm"] < 0.05
    )
    return (
        f"Cada marcador mostra a razão das médias geométricas (Kafka ÷ RabbitMQ) e seu intervalo de "
        f"confiança de 95% por bootstrap (5.000 reamostragens, semente 42). Valores acima de 1,0 indicam "
        f"maior métrica no Kafka (desejável em throughput) e abaixo de 1,0 indicam menor métrica no Kafka "
        f"(desejável em latência p99); {significativos} de {len(disponiveis)} comparações mantiveram p < 0,05 após Holm."
    )


def texto_interacao(interacoes: dict) -> str:
    e1 = interacoes.get("E1_throughput_msg_s", {})
    e2 = interacoes.get("E2_latencia_p99_ms", {})
    partes = []
    if e1.get("disponivel"):
        partes.append(
            f"em E1 (throughput), razão das razões = {e1['razao_das_razoes']:.2f} "
            f"(p_perm = {e1['permutacao_p']:.4g})"
        )
    if e2.get("disponivel"):
        partes.append(
            f"em E2 (p99), razão das razões = {e2['razao_das_razoes']:.2f} "
            f"(p_perm = {e2['permutacao_p']:.4g})"
        )
    detalhe = "; ".join(partes) if partes else "interação indisponível"
    return (
        "O gráfico verifica H3 comparando como a razão entre brokers muda de 1 KiB para 16 KiB: "
        f"linhas paralelas correspondem à razão das razões próxima de 1,0 ({detalhe})."
    )


def texto_ordem(efeito_ordem: list[dict]) -> str:
    e1 = [e for e in efeito_ordem if e["experimento"] == "E1" and e.get("disponivel")]
    if not e1:
        return "Não há execuções suficientes no E1 para ajustar regressão de tendência por ordem."
    estaveis = sum(1 for e in e1 if e["ic95_contem_zero"])
    return (
        f"Em {estaveis} de {len(e1)} células do E1 o IC 95% da inclinação sobre ln(throughput) contém zero, "
        "indicando ausência de deriva sistemática ao longo da ordem de execução. Quando presentes, repetições "
        "após falha técnica são destacadas em losango e linhas verticais separam os blocos de coleta."
    )
