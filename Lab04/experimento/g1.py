"""G1: comparação visual entre os tempos reais e os tempos simulados."""

from __future__ import annotations

import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from .dados import validar_pares

COR_REAL = "#334155"
COR_SIMULADO = "#0f766e"


def _bins_comuns(real: np.ndarray, simulado: np.ndarray) -> dict[str, float]:
    """Retorna bins compartilhados para uma condição, em segundos."""
    combinado = np.concatenate([real, simulado])
    arestas = np.histogram_bin_edges(combinado, bins="fd")
    if arestas.size < 6:
        arestas = np.linspace(float(combinado.min()), float(combinado.max()), 7)
    inicio, fim = float(arestas[0]), float(arestas[-1])
    if not fim > inicio:
        margem = max(abs(inicio) * 0.01, 1e-9)
        inicio, fim = inicio - margem, fim + margem
        arestas = np.linspace(inicio, fim, 7)
    return {"start": inicio, "end": fim, "size": float(arestas[1] - arestas[0])}


def figura_g1(reais: np.ndarray, simulados: np.ndarray) -> go.Figure:
    """Cria histogramas comparáveis sem misturar pares ou condições."""
    reais = validar_pares(reais)
    simulados = validar_pares(simulados)
    fig = make_subplots(
        rows=1,
        cols=2,
        subplot_titles=("Compilação sem cache", "Compilação com cache"),
        horizontal_spacing=0.1,
    )
    for coluna in range(2):
        bins = _bins_comuns(reais[:, coluna], simulados[:, coluna])
        for valores, nome, cor, grupo in (
            (reais[:, coluna], "Dados reais", COR_REAL, "real"),
            (simulados[:, coluna], "Dados simulados", COR_SIMULADO, "simulado"),
        ):
            fig.add_trace(
                go.Histogram(
                    x=valores,
                    name=nome,
                    legendgroup=grupo,
                    showlegend=coluna == 0,
                    marker_color=cor,
                    opacity=0.68,
                    histnorm="probability",
                    xbins=bins,
                    hovertemplate=f"{nome}<br>Tempo: %{{x:.4f}} s<br>Proporção: %{{y:.1%}}<extra></extra>",
                ),
                row=1,
                col=coluna + 1,
            )
    fig.update_xaxes(title_text="Tempo de compilação (s)")
    fig.update_yaxes(title_text="Proporção de observações", tickformat=".0%")
    fig.update_layout(
        title="G1 — Tempos reais e simulados por condição",
        barmode="overlay",
        bargap=0.04,
        template="plotly_white",
        height=470,
        legend=dict(orientation="h", yanchor="bottom", y=1.08, xanchor="left", x=0),
        margin=dict(t=110, b=70),
    )
    return fig


def texto_g1(reais: np.ndarray, simulados: np.ndarray) -> str:
    """Explicação curta para acompanhar o G1 no dashboard."""
    reais = validar_pares(reais)
    simulados = validar_pares(simulados)
    razao_real = float(np.exp(np.mean(np.log(reais[:, 0]) - np.log(reais[:, 1]))))
    return (
        f"O G1 compara {len(reais)} pares reais com {len(simulados)} pares simulados; dentro de cada painel, "
        "as duas amostras usam exatamente os mesmos intervalos do histograma. "
        f"Nos dados reais, a razão geométrica sem cache/com cache é {razao_real:.2f}, mas esse tamanho de efeito "
        "não demonstra sozinho controle de erro tipo I ou poder. "
        "A simulação reproduz médias e covariância na escala logarítmica e é uma aproximação, não uma nova medição."
    )
