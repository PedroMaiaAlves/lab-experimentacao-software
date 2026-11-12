"""Q3: poder sob diferenças simétricas de caudas pesadas, com variância calibrada."""

from __future__ import annotations

import platform
from pathlib import Path

import numpy as np
import scipy
from scipy import stats

from .dados import ROOT, ler_json, salvar_json, sha256
from .monte_carlo import (
    ALPHA_PADRAO, REPETICOES_OFICIAIS, SEMENTE_BASE, avaliar_rejeicoes,
    desvio_diferencas, gerar_diferencas, ler_resultados, resultados_csv_texto, simular_grade,
)
from .q2 import N_Q2, RAZOES_Q2, deltas_q2

SEMENTE_Q3 = int(np.random.SeedSequence([SEMENTE_BASE, 3]).generate_state(1, dtype=np.uint32)[0])
ARQUIVOS_CODIGO = ("experimento/q3.py", "experimento/q2.py", "experimento/monte_carlo.py", "experimento/dados.py")


def executar_q3(parametros: dict, *, repeticoes: int = REPETICOES_OFICIAIS,
                razoes=RAZOES_Q2, alpha: float = ALPHA_PADRAO, semente: int = SEMENTE_Q3) -> list[dict]:
    return simular_grade(
        distribuicao="t3", tamanhos=(N_Q2,), deltas=deltas_q2(razoes),
        repeticoes=repeticoes, alpha=alpha, semente=semente,
        sigma_d=desvio_diferencas(parametros), pergunta="Q3", cenario="t3_poder",
    )


def regenerar_diferencas(parametros: dict, repeticoes: int = REPETICOES_OFICIAIS):
    """Reconstitui os mesmos fluxos de simular_grade, sem persistir amostras brutas."""
    filhos = np.random.SeedSequence(SEMENTE_Q3).spawn(len(RAZOES_Q2))
    sigma = desvio_diferencas(parametros)
    for razao, delta, filho in zip(RAZOES_Q2, deltas_q2(), filhos, strict=True):
        yield razao, gerar_diferencas(np.random.default_rng(filho), repeticoes, N_Q2, delta, sigma, "t3")


def conferir_scipy(parametros: dict, repeticoes: int = REPETICOES_OFICIAIS) -> list[dict]:
    """Confronta decisões em lote com duas chamadas individuais por amostra."""
    conferencia = []
    for razao, diferencas in regenerar_diferencas(parametros, repeticoes):
        lote = avaliar_rejeicoes(diferencas)
        t = np.array([stats.ttest_1samp(d, 0.0, alternative="two-sided").pvalue < ALPHA_PADRAO
                      for d in diferencas])
        w = np.array([stats.wilcoxon(d, alternative="two-sided", method="exact").pvalue < ALPHA_PADRAO
                      for d in diferencas])
        conferencia.append({
            "razao": razao, "repeticoes": repeticoes,
            "divergencias_t": int((t != lote["t_pareado"]).sum()),
            "divergencias_wilcoxon": int((w != lote["wilcoxon"]).sum()),
            "rejeicoes_t": int(t.sum()), "rejeicoes_wilcoxon": int(w.sum()),
        })
    return conferencia


def _configuracao(parametros: dict) -> dict:
    return {
        "alpha": ALPHA_PADRAO, "alternativa": "two-sided", "repeticoes": REPETICOES_OFICIAIS,
        "n": N_Q2, "razoes": list(RAZOES_Q2), "deltas_log": list(deltas_q2()),
        "distribuicao": "t3", "graus_liberdade": 3, "divisor_padronizacao": float(np.sqrt(3)),
        "sigma_d": desvio_diferencas(parametros), "semente_base": SEMENTE_BASE,
        "politica_semente": "SeedSequence([42, 3]).generate_state(1)[0]", "semente_q3": SEMENTE_Q3,
    }


def salvar_q3(saida: Path = ROOT / "data/s02",
              parametros_path: Path = ROOT / "data/simulado/parametros.json") -> dict:
    parametros = ler_json(parametros_path)
    saida.mkdir(parents=True, exist_ok=True)
    csv_path = saida / "q3_resultados.csv"
    csv_path.write_text(resultados_csv_texto(executar_q3(parametros)), encoding="utf-8", newline="\n")
    manifesto = {
        "versao": 1, "pergunta": "Q3",
        "descricao": "Poder sob delta + sigma_d * T3/sqrt(3), com a grade e variância de Q2.",
        "configuracao": _configuracao(parametros),
        "hipoteses_h0": {
            "t_pareado": "Média das diferenças zero; a referência t não é exata sob T3, sendo avaliada empiricamente.",
            "wilcoxon": "Diferenças contínuas, independentes e simétricas em torno de zero.",
        },
        "origem": {"parametros": parametros_path.relative_to(ROOT).as_posix(),
                   "parametros_sha256": sha256(parametros_path)},
        "ambiente": {"python": platform.python_version(), "numpy": np.__version__, "scipy": scipy.__version__},
        "artefatos_sha256": {"q3_resultados.csv": sha256(csv_path)},
        "codigo_sha256": {nome: sha256(ROOT / nome) for nome in ARQUIVOS_CODIGO},
    }
    salvar_json(saida / "q3_manifesto.json", manifesto)
    return manifesto


def validar_q3(saida: Path = ROOT / "data/s02",
               parametros_path: Path = ROOT / "data/simulado/parametros.json") -> dict:
    manifesto = ler_json(saida / "q3_manifesto.json")
    if manifesto["origem"]["parametros_sha256"] != sha256(parametros_path):
        raise ValueError("Os parâmetros de Q3 foram modificados.")
    parametros = ler_json(parametros_path)
    if manifesto["configuracao"] != _configuracao(parametros):
        raise ValueError("A configuração de Q3 foi modificada.")
    if any(manifesto["ambiente"][nome] != versao for nome, versao in
           (("numpy", np.__version__), ("scipy", scipy.__version__))):
        raise ValueError("A reprodução exata exige as versões de NumPy e SciPy registradas.")
    for nome in ARQUIVOS_CODIGO:
        if sha256(ROOT / nome) != manifesto["codigo_sha256"][nome]:
            raise ValueError(f"Código de Q3 modificado: {nome}.")
    csv_path = saida / "q3_resultados.csv"
    if sha256(csv_path) != manifesto["artefatos_sha256"][csv_path.name]:
        raise ValueError("q3_resultados.csv foi modificado.")
    if csv_path.read_bytes() != resultados_csv_texto(executar_q3(parametros)).encode("utf-8"):
        raise ValueError("Q3 não foi reproduzida exatamente.")
    return {"status": "ok", "pergunta": "Q3", "configuracoes": len(ler_resultados(csv_path))}


def salvar_conferencia(saida: Path = ROOT / "data/s02") -> dict:
    validar_q3(saida)
    conferencia = conferir_scipy(ler_json(ROOT / "data/simulado/parametros.json"))
    if any(c["divergencias_t"] or c["divergencias_wilcoxon"] for c in conferencia):
        raise ValueError("As chamadas individuais divergem do cálculo em lote.")
    oficiais = ler_resultados(saida / "q3_resultados.csv")
    for linha in oficiais:
        c = next(c for c in conferencia if np.isclose(c["razao"], linha["razao_geometrica"]))
        chave = "rejeicoes_t" if linha["teste"] == "t_pareado" else "rejeicoes_wilcoxon"
        if c[chave] != linha["rejeicoes"]:
            raise ValueError("A conferência diverge do CSV de Q3.")
    resultado = {
        "status": "ok", "decisoes_conferidas": 2 * len(RAZOES_Q2) * REPETICOES_OFICIAIS,
        "comparacao": conferencia,
        "origem_sha256": {nome: sha256(saida / nome) for nome in ("q3_resultados.csv", "q3_manifesto.json")},
    }
    salvar_json(saida / "q3_conferencia_scipy.json", resultado)
    return resultado
