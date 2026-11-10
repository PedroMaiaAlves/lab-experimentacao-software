"""Validação e interpretação de Q2: conferência com SciPy, comparação pareada e texto do dashboard."""

from __future__ import annotations

from pathlib import Path

import numpy as np
from scipy import stats

from .dados import ROOT, ler_json, salvar_json, sha256
from .monte_carlo import (
    ALPHA_PADRAO,
    REPETICOES_OFICIAIS,
    avaliar_rejeicoes,
    desvio_diferencas,
    gerar_diferencas,
    ler_resultados,
)
from .q2 import N_Q2, RAZOES_Q2, SEMENTE_Q2, deltas_q2, validar_q2

ARQUIVOS_CODIGO = ("experimento/q2_interpretacao.py", "experimento/q2.py", "experimento/monte_carlo.py")


def regenerar_diferencas(parametros: dict, repeticoes: int = REPETICOES_OFICIAIS):
    """Reproduz as mesmas amostras de simular_grade: um fluxo filho de SEMENTE_Q2 por razão."""
    sigma = desvio_diferencas(parametros)
    filhos = np.random.SeedSequence(SEMENTE_Q2).spawn(len(RAZOES_Q2))
    for razao, delta, filho in zip(RAZOES_Q2, deltas_q2(), filhos, strict=True):
        rng = np.random.default_rng(filho)
        yield razao, gerar_diferencas(rng, repeticoes, N_Q2, delta, sigma, "normal")


def conferir_scipy(parametros: dict, repeticoes: int = REPETICOES_OFICIAIS, alpha: float = ALPHA_PADRAO) -> list[dict]:
    """Repete cada amostra com chamadas individuais ao SciPy e compara com a decisão em lote."""
    conferencia = []
    for razao, d in regenerar_diferencas(parametros, repeticoes):
        lote = avaliar_rejeicoes(d, alpha)
        t = np.array([stats.ttest_1samp(linha, 0.0).pvalue < alpha for linha in d])
        w = np.array([stats.wilcoxon(linha, method="exact").pvalue < alpha for linha in d])
        conferencia.append({
            "razao": razao,
            "repeticoes": repeticoes,
            "divergencias_t": int((t != lote["t_pareado"]).sum()),
            "divergencias_wilcoxon": int((w != lote["wilcoxon"]).sum()),
            "rejeicoes_t": int(t.sum()),
            "rejeicoes_wilcoxon": int(w.sum()),
        })
    return conferencia


def comparar_testes(parametros: dict, csv_path: Path = ROOT / "data/s02/q2_resultados.csv",
                    alpha: float = ALPHA_PADRAO) -> list[dict]:
    """Compara os testes nas MESMAS amostras: discordâncias e teste exato de McNemar por razão."""
    oficiais = {(r["teste"], round(r["razao_geometrica"], 6)): r for r in ler_resultados(csv_path)}
    linhas = []
    for razao, d in regenerar_diferencas(parametros):
        lote = avaliar_rejeicoes(d, alpha)
        t, w = lote["t_pareado"], lote["wilcoxon"]
        ot, ow = oficiais[("t_pareado", round(razao, 6))], oficiais[("wilcoxon", round(razao, 6))]
        if int(t.sum()) != ot["rejeicoes"] or int(w.sum()) != ow["rejeicoes"]:
            raise ValueError(f"Regeneração diverge do CSV oficial na razão {razao}.")
        so_t, so_w = int((t & ~w).sum()), int((w & ~t).sum())
        p_mcnemar = float(stats.binomtest(so_t, so_t + so_w).pvalue) if so_t + so_w else 1.0
        if p_mcnemar < alpha:
            maior = "t_pareado" if so_t > so_w else "wilcoxon"
        else:
            maior = "sem diferença detectável"
        linhas.append({
            "razao": razao,
            "poder_t": ot["taxa_rejeicao"], "ic95_t": [ot["ic95_inferior"], ot["ic95_superior"]],
            "poder_wilcoxon": ow["taxa_rejeicao"], "ic95_wilcoxon": [ow["ic95_inferior"], ow["ic95_superior"]],
            "diferenca_pp": round(100 * (ot["taxa_rejeicao"] - ow["taxa_rejeicao"]), 2),
            "so_t_rejeita": so_t, "so_wilcoxon_rejeita": so_w,
            "p_mcnemar": p_mcnemar, "maior_poder": maior,
        })
    return linhas


def _pct(x: float) -> str:
    return f"{100 * x:.1f}%".replace(".", ",")


def _razao(x: float) -> str:
    return f"{x:.2f}".replace(".", ",")


def texto_q2(comparacao: list[dict]) -> str:
    """Texto de 3 a 4 frases para a seção de poder do dashboard."""
    h0 = comparacao[0]
    efeitos = comparacao[1:]
    vantagem_t = [_razao(c["razao"]) for c in efeitos if c["maior_poder"] == "t_pareado"]
    vantagem_w = [_razao(c["razao"]) for c in efeitos if c["maior_poder"] == "wilcoxon"]
    alvo = next((c for c in efeitos if min(c["poder_t"], c["poder_wilcoxon"]) >= 0.8), None)
    if vantagem_t and not vantagem_w:
        comparacao_txt = (f"o t pareado teve poder maior que o Wilcoxon nas razões {'; '.join(vantagem_t)} "
                          f"(McNemar nas mesmas amostras, α = 0,05), com diferença de no máximo "
                          f"{max(abs(c['diferenca_pp']) for c in efeitos):.1f} pontos percentuais".replace(".", ",", 1))
    elif vantagem_w and not vantagem_t:
        comparacao_txt = f"o Wilcoxon teve poder maior nas razões {'; '.join(vantagem_w)}"
    elif not vantagem_t and not vantagem_w:
        comparacao_txt = "nenhum teste teve poder detectavelmente maior em nenhuma razão"
    else:
        comparacao_txt = (f"o t teve vantagem nas razões {'; '.join(vantagem_t)} e o Wilcoxon nas razões "
                          f"{'; '.join(vantagem_w)}")
    return (
        "Poder é a proporção das 10.000 amostras simuladas, com 30 pares de diferenças normais, em que o teste "
        "rejeitou H0 quando a razão sem/com cache era de fato maior que 1; não é um p-valor, que se refere a "
        "uma única amostra, nem o tamanho do efeito, que é a própria razão no eixo horizontal. "
        f"Na razão 1,00, em que H0 é verdadeira, as taxas ficaram em {_pct(h0['poder_t'])} (t) e "
        f"{_pct(h0['poder_wilcoxon'])} (Wilcoxon), próximas do α de 5%, e o poder cresce com o efeito"
        + (f", passando de 80% a partir da razão {_razao(alvo['razao'])}" if alvo else "") + ". "
        f"Sob normalidade, {comparacao_txt}, o que é esperado porque o t é o teste ótimo nesse cenário. "
        "Os intervalos de Wilson de 95% medem só a incerteza da simulação: os resultados valem para diferenças "
        "normais com o desvio calibrado e 30 pares, e não garantem o mesmo comportamento com caudas pesadas (Q3)."
    )


LIMITACOES_Q2 = (
    "Incerteza de Monte Carlo: com 10.000 repetições, o erro padrão de uma taxa p é sqrt(p(1−p)/10.000), "
    "no máximo 0,5 ponto percentual (p = 50%); os intervalos de Wilson de 95% têm meia-largura de até ~1 p.p.",
    "Intervalos de Wilson de cada teste podem se sobrepor mesmo quando a diferença é real, porque os dois testes "
    "são aplicados às mesmas amostras; por isso a comparação usa McNemar sobre as amostras discordantes.",
    "O cenário supõe diferenças logarítmicas normais, independentes, com o desvio calibrado nos dados reais "
    "da S01 e n = 30; outros n, desvios ou distribuições (ex.: caudas pesadas, Q3) podem mudar a ordem dos testes.",
    "Poder próximo de 100% nas razões maiores satura: nelas a comparação entre testes perde informação.",
    "Os resultados descrevem o comportamento dos testes, não o efeito real do cache, que é estimado nos dados reais.",
)


def salvar_interpretacao(
    saida: Path = ROOT / "data/s02",
    parametros_path: Path = ROOT / "data/simulado/parametros.json",
) -> dict:
    """Valida Q2, compara os testes e preserva a interpretação com proveniência."""
    validar_q2(saida, parametros_path)
    comparacao = comparar_testes(ler_json(parametros_path), saida / "q2_resultados.csv")
    resultado = {
        "versao": 1,
        "pergunta": "Q2",
        "comparacao": comparacao,
        "texto_dashboard": texto_q2(comparacao),
        "limitacoes": list(LIMITACOES_Q2),
        "origem": {"q2_resultados.csv": sha256(saida / "q2_resultados.csv")},
        "codigo_sha256": {nome: sha256(ROOT / nome) for nome in ARQUIVOS_CODIGO},
    }
    salvar_json(saida / "q2_interpretacao.json", resultado)
    return resultado


def validar_interpretacao(
    saida: Path = ROOT / "data/s02",
    parametros_path: Path = ROOT / "data/simulado/parametros.json",
) -> dict:
    """Regenera Q2 e a interpretação em memória e confere com o arquivo preservado."""
    validar_q2(saida, parametros_path)
    preservado = ler_json(saida / "q2_interpretacao.json")
    if sha256(saida / "q2_resultados.csv") != preservado["origem"]["q2_resultados.csv"]:
        raise ValueError("A interpretação foi gerada a partir de outro q2_resultados.csv.")
    comparacao = comparar_testes(ler_json(parametros_path), saida / "q2_resultados.csv")
    if comparacao != preservado["comparacao"] or texto_q2(comparacao) != preservado["texto_dashboard"]:
        raise ValueError("A interpretação de Q2 não foi reproduzida exatamente.")
    return {"status": "ok", "pergunta": "Q2", "razoes": len(comparacao)}


def ler_texto_q2(path: Path = ROOT / "data/s02/q2_interpretacao.json") -> dict:
    """Leitura para o dashboard, sem simular: texto, limitações e comparação preservados."""
    dados = ler_json(path)
    return {"texto": dados["texto_dashboard"], "limitacoes": dados["limitacoes"], "comparacao": dados["comparacao"]}
