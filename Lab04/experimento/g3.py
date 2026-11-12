"""G3: erro tipo I empírico do t pareado e do Wilcoxon."""

from __future__ import annotations

import plotly.graph_objects as go

from .g2 import COR_T, COR_WILCOXON

NOMES = {"t_pareado": "t pareado", "wilcoxon": "Wilcoxon pareado"}
CORES = {"t_pareado": COR_T, "wilcoxon": COR_WILCOXON}


def _validar(resultados: list[dict]) -> list[dict]:
    if not resultados:
        raise ValueError("G3 exige resultados agregados de Q1.")
    obrigatorios = {
        "pergunta", "teste", "n", "taxa_rejeicao", "ic95_inferior", "ic95_superior", "alpha",
    }
    for resultado in resultados:
        if not obrigatorios.issubset(resultado):
            raise ValueError("Resultado de Q1 não atende ao contrato do G3.")
        if resultado["pergunta"] != "Q1" or resultado["teste"] not in NOMES:
            raise ValueError("G3 aceita somente Q1 e os dois testes definidos.")
        taxa = float(resultado["taxa_rejeicao"])
        inferior = float(resultado["ic95_inferior"])
        superior = float(resultado["ic95_superior"])
        if not 0 <= inferior <= taxa <= superior <= 1:
            raise ValueError("Taxa ou intervalo de Monte Carlo inválido.")
    return resultados


def figura_g3(resultados: list[dict]) -> go.Figure:
    """Mostra erro tipo I por tamanho com incerteza de Monte Carlo."""
    resultados = _validar(resultados)
    fig = go.Figure()
    for teste in ("t_pareado", "wilcoxon"):
        linhas = sorted((r for r in resultados if r["teste"] == teste), key=lambda r: int(r["n"]))
        if not linhas:
            raise ValueError(f"Resultados ausentes para {teste}.")
        taxas = [float(r["taxa_rejeicao"]) for r in linhas]
        fig.add_trace(go.Scatter(
            x=[int(r["n"]) for r in linhas],
            y=taxas,
            name=NOMES[teste],
            mode="lines+markers",
            line=dict(color=CORES[teste], width=3),
            marker=dict(size=9),
            error_y=dict(
                type="data",
                symmetric=False,
                array=[float(r["ic95_superior"]) - taxa for r, taxa in zip(linhas, taxas, strict=True)],
                arrayminus=[taxa - float(r["ic95_inferior"]) for r, taxa in zip(linhas, taxas, strict=True)],
                thickness=1.5,
                width=5,
                color=CORES[teste],
            ),
            customdata=[[int(r["rejeicoes"]), int(r["repeticoes"])] for r in linhas],
            hovertemplate=(
                f"{NOMES[teste]}<br>n = %{{x}}<br>Erro tipo I = %{{y:.2%}}"
                "<br>Rejeições = %{customdata[0]}/%{customdata[1]}<extra></extra>"
            ),
        ))
    alpha = float(resultados[0]["alpha"])
    fig.add_hline(
        y=alpha,
        line=dict(color="#64748b", width=2, dash="dash"),
        annotation_text=f"α = {alpha:.0%}",
        annotation_position="top left",
    )
    fig.update_layout(
        title="G3 — Erro tipo I sob H0 por tamanho amostral",
        xaxis_title="Número de pares por repetição (n)",
        yaxis_title="Taxa empírica de rejeição",
        yaxis=dict(tickformat=".1%", range=[0, max(0.08, max(float(r["ic95_superior"]) for r in resultados) + 0.01)]),
        template="plotly_white",
        height=500,
        hovermode="x unified",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0),
        margin=dict(t=100, b=70),
    )
    return fig


def texto_g3(resultados: list[dict]) -> str:
    """Interpretação descritiva, sem declarar conformidade antecipadamente."""
    resultados = _validar(resultados)
    alpha = float(resultados[0]["alpha"])
    compativeis = sum(
        float(r["ic95_inferior"]) <= alpha <= float(r["ic95_superior"])
        for r in resultados
    )
    total = len(resultados)
    menor = min(float(r["taxa_rejeicao"]) for r in resultados)
    maior = max(float(r["taxa_rejeicao"]) for r in resultados)
    repeticoes = int(resultados[0]["repeticoes"])
    return (
        f"Q1 repetiu cada configuração {repeticoes} vezes sob H0 verdadeira; a taxa de rejeição é, portanto, "
        "uma estimativa do erro tipo I. "
        f"As estimativas variaram de {menor:.2%} a {maior:.2%}, e {compativeis} de {total} intervalos de Wilson "
        f"de 95% contêm o nível nominal de {alpha:.0%}. "
        "As barras representam incerteza de Monte Carlo, não um intervalo para o efeito do cache."
    )
