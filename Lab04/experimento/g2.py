"""G2: distribuição sob H0, região de rejeição e p-valor do t pareado e do Wilcoxon."""

from __future__ import annotations

import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from scipy import stats

from experimento.dados import validar_pares

COR_T = "#2563eb"
COR_WILCOXON = "#ea580c"
COR_WILCOXON_CLARO = "#fdba74"
COR_REJEICAO = "#9ca3af"
RTOL_P = 1e-6
ATOL_P = 1e-12


def diferencas_log(pares: np.ndarray) -> np.ndarray:
    a = validar_pares(pares)
    return np.log(a[:, 0]) - np.log(a[:, 1])


def distribuicao_t(pares: np.ndarray, alpha: float = 0.05) -> dict:
    """Student com n−1 gl; o t pareado dos logs equivale ao t de uma amostra das diferenças."""
    d = diferencas_log(pares)
    n = d.size
    dp = d.std(ddof=1)
    # Tolerância relativa: diferenças constantes podem deixar resíduo de ponto flutuante.
    if dp <= 1e-12 * max(1.0, abs(d.mean())):
        raise ValueError("Diferenças constantes: desvio padrão zero, estatística t indefinida.")
    t = d.mean() / (dp / np.sqrt(n))
    gl = n - 1
    return {
        "estatistica": float(t),
        "gl": gl,
        "critico": float(stats.t.ppf(1 - alpha / 2, gl)),
        "p_valor": float(min(1.0, 2 * stats.t.sf(abs(t), gl))),
        "alpha": alpha,
    }


def _contagens_w_mais(n: int) -> np.ndarray:
    """Número de subconjuntos de {1..n} com cada soma: frequências exatas de W+ sob H0."""
    total = n * (n + 1) // 2
    c = np.zeros(total + 1, dtype=np.int64)
    c[0] = 1
    for r in range(1, n + 1):
        c[r:] = c[r:] + c[:-r]
    return c


def distribuicao_wilcoxon(pares: np.ndarray, alpha: float = 0.05) -> dict:
    """Distribuição de W=min(W+, W−); exata sem empates/zeros, normal aproximada caso contrário."""
    d = diferencas_log(pares)
    nz = d[d != 0]
    n = nz.size
    if n == 0:
        raise ValueError("Todas as diferenças são zero: Wilcoxon indefinido.")
    postos = stats.rankdata(np.abs(nz))
    w_mais = float(postos[nz > 0].sum())
    w = min(w_mais, n * (n + 1) / 2 - w_mais)
    zeros = int(d.size - n)
    _, repeticoes = np.unique(np.abs(nz), return_counts=True)
    empates = bool((repeticoes > 1).any())
    base = {"estatistica": w, "n_efetivo": n, "zeros": zeros, "empates": empates, "alpha": alpha}

    if not empates and not zeros:
        total = n * (n + 1) // 2
        prob = _contagens_w_mais(n) / 2.0**n
        suporte = np.arange(total // 2 + 1)
        # min(W+, W−) dobra a distribuição simétrica de W+ no centro.
        pmf = 2 * prob[suporte]
        if total % 2 == 0:
            pmf[-1] = prob[total // 2]
        acumulada = np.cumsum(pmf)
        rejeita = suporte[acumulada <= alpha]
        return base | {
            "metodo": "exato",
            "suporte": suporte,
            "pmf": pmf,
            "critico": int(rejeita[-1]) if rejeita.size else None,
            "p_valor": float(min(1.0, acumulada[int(w)])),
        }

    media = n * (n + 1) / 4
    var = n * (n + 1) * (2 * n + 1) / 24 - (repeticoes**3 - repeticoes).sum() / 48
    dp = float(np.sqrt(var))
    z = (w - media) / dp
    return base | {
        "metodo": "aproximação normal",
        "media": media,
        "dp": dp,
        "critico": float(media - stats.norm.ppf(1 - alpha / 2) * dp),
        "p_valor": float(min(1.0, 2 * stats.norm.sf(abs(z)))),
    }


def conferir_p_valores(pares: np.ndarray, resultados: dict) -> dict:
    """Compara a área/massa desenhada com o p-valor devolvido por D1."""
    conferencia = {}
    for chave, fn in (("t_pareado", distribuicao_t), ("wilcoxon", distribuicao_wilcoxon)):
        p_d1 = resultados.get(chave, {}).get("p_valor")
        alpha = resultados.get(chave, {}).get("alpha", 0.05)
        try:
            p_fig = fn(pares, alpha)["p_valor"]
        except ValueError as erro:
            conferencia[chave] = {"p_figura": None, "p_d1": p_d1, "ok": p_d1 is None, "motivo": str(erro)}
            continue
        ok = p_d1 is not None and bool(np.isclose(p_fig, p_d1, rtol=RTOL_P, atol=ATOL_P))
        conferencia[chave] = {"p_figura": p_fig, "p_d1": p_d1, "ok": ok}
    return conferencia


def _br(valor: float, formato: str = ".3g") -> str:
    return format(valor, formato).replace(".", ",")


def _painel_t(fig: go.Figure, dist: dict) -> None:
    t, gl, crit = dist["estatistica"], dist["gl"], dist["critico"]
    lim_linear = max(5.0, crit + 1.5)
    lim_log = max(lim_linear, abs(t) * 1.1)
    for row, lim in ((1, lim_linear), (2, lim_log)):
        x = np.linspace(-lim, lim, 2001)
        y = stats.t.pdf(x, gl)
        primeira = row == 1
        fig.add_trace(go.Scatter(x=x, y=y, mode="lines", line=dict(color=COR_T, width=2),
                                 name=f"t de Student, {gl} gl (H0)", legendgroup="t", showlegend=primeira),
                      row=row, col=1)
        for lado, mascara in enumerate((x <= -crit, x >= crit)):
            fig.add_trace(go.Scatter(x=x[mascara], y=y[mascara], fill="tozeroy", mode="none",
                                     fillcolor="rgba(156,163,175,0.55)", legendgroup="rej",
                                     name=f"Região de rejeição (α = {dist['alpha']:g})",
                                     showlegend=primeira and lado == 0),
                          row=row, col=1)
        for lado, mascara in enumerate((x <= -abs(t), x >= abs(t))):
            if mascara.any():
                fig.add_trace(go.Scatter(x=x[mascara], y=y[mascara], fill="tozeroy", mode="none",
                                         fillcolor="rgba(37,99,235,0.75)", legendgroup="pt",
                                         name="Área = p-valor do t", showlegend=primeira and lado == 0),
                              row=row, col=1)
        fig.add_vline(x=t, line=dict(color=COR_T, dash="dot"), row=row, col=1)
        fig.update_xaxes(range=[-lim, lim], row=row, col=1)

    if abs(t) > lim_linear:
        fig.add_annotation(x=np.sign(t) * lim_linear * 0.97, y=stats.t.pdf(0, gl) * 0.6, row=1, col=1,
                           text=f"t observado = {_br(t, '.2f')}<br>fora da escala →<br>ver ampliação abaixo",
                           showarrow=False, xanchor="right" if t > 0 else "left", font=dict(color=COR_T))
    fig.add_annotation(x=0, y=stats.t.pdf(0, gl) * 1.08, row=1, col=1, showarrow=False,
                       text=f"t = {_br(t, '.3f')} · ±t crítico = {_br(crit, '.3f')} · p = {_br(dist['p_valor'])}")


def _painel_wilcoxon(fig: go.Figure, dist: dict) -> None:
    w, crit = dist["estatistica"], dist["critico"]
    if dist["metodo"] == "exato":
        k, pmf = dist["suporte"], dist["pmf"]
        p_mask = k <= w
        rej_mask = (k <= crit) & ~p_mask if crit is not None else np.zeros_like(p_mask)
        resto = ~p_mask & ~rej_mask
        for row in (1, 2):
            primeira = row == 1
            for mascara, cor, nome, grupo in (
                (resto, COR_WILCOXON_CLARO, "Massa de min(W+, W−) sob H0 (exata)", "w"),
                (rej_mask, COR_REJEICAO, f"Região de rejeição (α = {dist['alpha']:g})", "rej"),
                (p_mask, COR_WILCOXON, "Massa = p-valor do Wilcoxon", "pw"),
            ):
                if mascara.any():
                    fig.add_trace(go.Bar(x=k[mascara], y=pmf[mascara], marker_color=cor, name=nome,
                                         legendgroup=grupo, showlegend=primeira and grupo != "rej"),
                                  row=row, col=2)
            if crit is not None:
                fig.add_vline(x=crit + 0.5, line=dict(color=COR_REJEICAO, dash="dash"), row=row, col=2)
            fig.add_vline(x=w, line=dict(color=COR_WILCOXON, dash="dot"), row=row, col=2)
        topo = float(pmf.max())
        texto_crit = f"W crítico = {crit}" if crit is not None else "sem região de rejeição possível"
        nota = "distribuição exata, sem empates nem zeros"
    else:
        media, dp = dist["media"], dist["dp"]
        x = np.linspace(0, 2 * media, 2001)
        y = stats.norm.pdf(x, media, dp)
        dist_obs = abs(w - media)
        for row in (1, 2):
            primeira = row == 1
            fig.add_trace(go.Scatter(x=x, y=y, mode="lines", line=dict(color=COR_WILCOXON, width=2, dash="dash"),
                                     name="Aproximação normal de W+ (NÃO é a distribuição exata)",
                                     showlegend=primeira), row=row, col=2)
            for lado, mascara in enumerate((x <= crit, x >= 2 * media - crit)):
                fig.add_trace(go.Scatter(x=x[mascara], y=y[mascara], fill="tozeroy", mode="none",
                                         fillcolor="rgba(156,163,175,0.55)", legendgroup="rej",
                                         showlegend=False), row=row, col=2)
            for lado, mascara in enumerate((x <= media - dist_obs, x >= media + dist_obs)):
                if mascara.any():
                    fig.add_trace(go.Scatter(x=x[mascara], y=y[mascara], fill="tozeroy", mode="none",
                                             fillcolor="rgba(234,88,12,0.75)", legendgroup="pw",
                                             name="Área = p-valor do Wilcoxon (aprox.)",
                                             showlegend=primeira and lado == 0), row=row, col=2)
            fig.add_vline(x=w, line=dict(color=COR_WILCOXON, dash="dot"), row=row, col=2)
        topo = float(y.max())
        texto_crit = f"W crítico ≈ {_br(crit, '.1f')}"
        nota = (f"aproximação normal com correção de empates ({dist['zeros']} zero(s) descartado(s)); "
                "limitada em amostras pequenas")
    fig.add_annotation(x=0.5, xref="x2 domain", y=topo * 1.08, yref="y2", showarrow=False,
                       text=f"W = {w:g} · {texto_crit} · p = {_br(dist['p_valor'])}<br><i>{nota}</i>")


def figura_g2(pares: np.ndarray, resultados: dict) -> go.Figure:
    """Figura Plotly com os dois testes; não inicia Streamlit nem grava arquivos."""
    conferencia = conferir_p_valores(pares, resultados)
    divergentes = [k for k, v in conferencia.items() if not v["ok"]]
    if divergentes:
        raise ValueError(f"p-valor desenhado diverge do resultado de D1: {divergentes} {conferencia}")

    fig = make_subplots(
        rows=2, cols=2, vertical_spacing=0.14, horizontal_spacing=0.08,
        subplot_titles=(
            "t pareado: distribuição t sob H0", "Wilcoxon pareado: min(W+, W−) sob H0",
            "t pareado: ampliação das caudas (escala log)", "Wilcoxon: ampliação das caudas (escala log)",
        ),
    )
    alpha_t = resultados["t_pareado"].get("alpha", 0.05)
    alpha_w = resultados["wilcoxon"].get("alpha", 0.05)
    _painel_t(fig, distribuicao_t(pares, alpha_t))
    _painel_wilcoxon(fig, distribuicao_wilcoxon(pares, alpha_w))

    fig.update_xaxes(title_text="Estatística t (adimensional)", col=1)
    fig.update_xaxes(title_text="W = min(W+, W−) (adimensional)", col=2)
    fig.update_yaxes(title_text="Densidade sob H0", row=1, col=1)
    fig.update_yaxes(title_text="Probabilidade sob H0", row=1, col=2)
    fig.update_yaxes(title_text="Densidade (log)", type="log", row=2, col=1)
    fig.update_yaxes(title_text="Probabilidade (log)", type="log", row=2, col=2)
    fig.update_layout(
        title="G2 — Como cada teste obtém a decisão e o p-valor (amostra simulada, bicaudal)",
        barmode="overlay", bargap=0.05, height=820, template="plotly_white",
        legend=dict(orientation="h", yanchor="top", y=-0.1, x=0),
        margin=dict(t=90, b=140),
    )
    return fig


def texto_g2(pares: np.ndarray, resultados: dict) -> str:
    """Explicação de 2 a 4 frases para acompanhar o G2 no dashboard."""
    t, w = distribuicao_t(pares, resultados["t_pareado"].get("alpha", 0.05)), \
        distribuicao_wilcoxon(pares, resultados["wilcoxon"].get("alpha", 0.05))
    return (
        f"Cada painel mostra como a estatística se distribuiria se H0 fosse verdadeira: t de Student com "
        f"{t['gl']} graus de liberdade e, no Wilcoxon, a distribuição "
        f"{'exata' if w['metodo'] == 'exato' else 'aproximada (normal)'} de min(W+, W−). "
        f"A faixa cinza é a região de rejeição bicaudal com α = {_br(t['alpha'], 'g')}, e a parte colorida é a "
        f"probabilidade, calculada supondo H0, de obter um valor tão ou mais extremo que o observado: "
        f"p = {_br(t['p_valor'])} no t e p = {_br(w['p_valor'])} no Wilcoxon. "
        "O p-valor não é a probabilidade de H0 ser verdadeira, e não rejeitar H0 não provaria que os tempos são iguais. "
        "Como caudas muito pequenas ficam invisíveis na escala linear, a linha inferior repete os painéis em escala log."
    )
