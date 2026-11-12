"""G4: comparação descritiva de poder normal × caudas pesadas."""

from __future__ import annotations

import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from .g3 import CORES, NOMES
from .q2 import RAZOES_Q2


def validar_comparacao(q2: list[dict], q3: list[dict]) -> None:
    configuracoes = set()
    for linhas, pergunta, distribuicao in ((q2, "Q2", "normal"), (q3, "Q3", "t3")):
        if len(linhas) != 2 * len(RAZOES_Q2):
            raise ValueError("G4 exige as duas grades completas, sem linhas ausentes ou duplicadas.")
        chaves = set()
        for linha in linhas:
            if linha["pergunta"] != pergunta or linha["distribuicao"] != distribuicao:
                raise ValueError("Pergunta ou distribuição incorreta no G4.")
            razao = float(linha["razao_geometrica"])
            chave = (linha["teste"], round(razao, 6))
            if linha["teste"] not in NOMES or chave in chaves:
                raise ValueError("Teste inválido ou resultado duplicado no G4.")
            chaves.add(chave)
            taxa = float(linha["taxa_rejeicao"])
            inferior, superior = float(linha["ic95_inferior"]), float(linha["ic95_superior"])
            if not (0 <= taxa <= 1 and 0 <= inferior <= superior <= 1
                    and inferior - 1e-12 <= taxa <= superior + 1e-12):
                raise ValueError("Taxa ou intervalo inválido no G4.")
            if not np.isclose(np.exp(linha["delta_log"]), razao):
                raise ValueError("Efeito logarítmico incompatível com a razão geométrica.")
            n, repeticoes, alpha = linha["n"], linha["repeticoes"], linha["alpha"]
            if n != 30 or repeticoes <= 0 or not 0 < alpha < 1:
                raise ValueError("Configuração amostral inválida no G4.")
            if not np.isclose(taxa, linha["rejeicoes"] / repeticoes, rtol=0, atol=1e-12):
                raise ValueError("A taxa diverge da contagem de rejeições.")
            configuracoes.add((n, repeticoes, alpha))
        esperado = {(teste, razao) for teste in NOMES for razao in RAZOES_Q2}
        if chaves != esperado:
            raise ValueError("As razões do G4 diferem da grade definida em Q2/Q3.")
    if len(configuracoes) != 1:
        raise ValueError("Q2 e Q3 precisam do mesmo n, repetições e alpha.")


def figura_g4(q2: list[dict], q3: list[dict]) -> go.Figure:
    validar_comparacao(q2, q3)
    fig = make_subplots(rows=1, cols=2, shared_yaxes=True,
                        subplot_titles=("Q2 · Diferenças normais", "Q3 · Student t₃ / √3"))
    for coluna, linhas in enumerate((q2, q3), 1):
        for teste in NOMES:
            curva = sorted((r for r in linhas if r["teste"] == teste), key=lambda r: r["razao_geometrica"])
            taxas = [r["taxa_rejeicao"] for r in curva]
            fig.add_trace(go.Scatter(
                x=[r["razao_geometrica"] for r in curva], y=taxas,
                name=NOMES[teste], legendgroup=teste, showlegend=coluna == 1, mode="lines+markers",
                line=dict(color=CORES[teste], width=3), marker=dict(size=8),
                error_y=dict(type="data", symmetric=False,
                             array=[max(0, r["ic95_superior"] - r["taxa_rejeicao"]) for r in curva],
                             arrayminus=[max(0, r["taxa_rejeicao"] - r["ic95_inferior"]) for r in curva]),
                hovertemplate="Razão = %{x:.2f}<br>Taxa de rejeição = %{y:.2%}<extra>%{fullData.name}</extra>",
            ), row=1, col=coluna)
        fig.add_hline(y=q2[0]["alpha"], line_dash="dash", line_color="#64748b", row=1, col=coluna)
        fig.update_xaxes(title_text="Razão geométrica sem/com cache", tickvals=list(RAZOES_Q2),
                         tickformat=".2f", range=[0.99, 1.26], row=1, col=coluna)
        fig.update_yaxes(range=[0, 1], tickformat=".0%", row=1, col=coluna)
    fig.update_yaxes(title_text="Poder (razão 1,00: erro tipo I)", row=1, col=1)
    fig.update_layout(
        title="G4 — Poder dos testes: mesma variância, distribuições diferentes",
        template="plotly_white", height=510, hovermode="x unified",
        legend=dict(orientation="h", y=1.18), margin=dict(t=140, b=75),
    )
    return fig


def texto_g4(q2: list[dict], q3: list[dict]) -> str:
    validar_comparacao(q2, q3)
    h0 = {r["teste"]: r for r in q3 if r["delta_log"] == 0}
    efeitos = [r for r in q3 if r["teste"] == "wilcoxon" and r["delta_log"] > 0]
    t = {round(r["razao_geometrica"], 6): r["taxa_rejeicao"] for r in q3 if r["teste"] == "t_pareado"}
    diferencas = [(r["taxa_rejeicao"] - t[round(r["razao_geometrica"], 6)], r["razao_geometrica"]) for r in efeitos]
    diferenca, razao = max(diferencas, key=lambda par: abs(par[0]))
    nome = "Wilcoxon" if diferenca >= 0 else "t pareado"
    return (
        f"Cada ponto resume {q3[0]['repeticoes']:,} repetições com 30 pares; sob efeito não nulo a taxa "
        "estima o poder, não o p-valor nem o tamanho do efeito. "
        "Q3 troca a normal por t de Student com três graus de liberdade, dividida por √3: mantém a variância, "
        "mas aumenta a ocorrência de valores extremos, preservando a simetria. "
        f"Em Q3 sob H0, as rejeições foram {h0['t_pareado']['taxa_rejeicao']:.2%} (t) e "
        f"{h0['wilcoxon']['taxa_rejeicao']:.2%} (Wilcoxon); entre os efeitos, a maior diferença estimada "
        f"favoreceu {nome} em {100 * abs(diferenca):.2f} pontos percentuais na razão {razao:.2f}. "
        "As barras são intervalos de Wilson de 95% para cada taxa, não para a diferença entre testes; "
        "a comparação é descritiva e não estabelece superioridade universal."
    )
