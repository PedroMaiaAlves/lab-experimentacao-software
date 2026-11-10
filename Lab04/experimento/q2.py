"""Q2: poder do t pareado e do Wilcoxon sob diferenças logarítmicas normais."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import scipy

from .dados import ROOT, ler_json, salvar_json, sha256
from .monte_carlo import (
    ALPHA_PADRAO,
    REPETICOES_OFICIAIS,
    SEMENTE_BASE,
    desvio_diferencas,
    ler_resultados,
    resultados_csv_texto,
    simular_grade,
)

N_Q2 = 30
RAZOES_Q2 = (1.00, 1.02, 1.05, 1.10, 1.15, 1.20, 1.25)
# Semente derivada de 42 com a chave da pergunta (2): fixada antes de simular e
# independente dos fluxos da Q1, que usa SeedSequence(42) diretamente.
# Q3 deve seguir a mesma política com a chave 3.
CHAVE_PERGUNTA = 2
SEMENTE_Q2 = int(np.random.SeedSequence([SEMENTE_BASE, CHAVE_PERGUNTA]).generate_state(1, dtype=np.uint32)[0])
ARQUIVOS_CODIGO = ("experimento/q2.py", "experimento/monte_carlo.py")


def deltas_q2(razoes=RAZOES_Q2) -> tuple[float, ...]:
    """Converte razões geométricas sem/com cache em médias de log(sem) − log(com)."""
    razoes = tuple(float(r) for r in razoes)
    if not razoes or any(not np.isfinite(r) or r <= 0 for r in razoes):
        raise ValueError("As razões devem ser positivas e finitas.")
    return tuple(float(np.log(r)) for r in razoes)


def executar_q2(
    parametros: dict,
    *,
    repeticoes: int = REPETICOES_OFICIAIS,
    razoes=RAZOES_Q2,
    alpha: float = ALPHA_PADRAO,
    semente: int = SEMENTE_Q2,
) -> list[dict]:
    """Taxa de rejeição por razão: em 1,00 estima o erro tipo I; nas demais, o poder."""
    return simular_grade(
        distribuicao="normal",
        tamanhos=(N_Q2,),
        deltas=deltas_q2(razoes),
        repeticoes=repeticoes,
        alpha=alpha,
        semente=semente,
        sigma_d=desvio_diferencas(parametros),
        pergunta="Q2",
        cenario="normal_poder",
    )


def salvar_q2(
    saida: Path = ROOT / "data/s02",
    parametros_path: Path = ROOT / "data/simulado/parametros.json",
) -> dict:
    """Executa Q2 e preserva CSV agregado e manifesto de proveniência."""
    parametros = ler_json(parametros_path)
    resultados = executar_q2(parametros)
    saida.mkdir(parents=True, exist_ok=True)
    csv_path = saida / "q2_resultados.csv"
    csv_path.write_text(resultados_csv_texto(resultados), encoding="utf-8", newline="\n")
    manifesto = {
        "versao": 1,
        "pergunta": "Q2",
        "descricao": "Poder sob diferenças logarítmicas normais, 30 pares e razões definidas na issue #186.",
        "configuracao": {
            "alpha": ALPHA_PADRAO,
            "alternativa": "two-sided",
            "repeticoes": REPETICOES_OFICIAIS,
            "n": N_Q2,
            "razoes": list(RAZOES_Q2),
            "deltas_log": list(deltas_q2()),
            "distribuicao": "normal",
            "sigma_d": desvio_diferencas(parametros),
            "semente_base": SEMENTE_BASE,
            "politica_semente": f"SeedSequence([{SEMENTE_BASE}, {CHAVE_PERGUNTA}]).generate_state(1)[0]",
            "semente_q2": SEMENTE_Q2,
        },
        "origem": {
            "parametros": str(parametros_path.relative_to(ROOT)).replace("\\", "/"),
            "parametros_sha256": sha256(parametros_path),
        },
        "ambiente": {"numpy": np.__version__, "scipy": scipy.__version__},
        "artefatos_sha256": {"q2_resultados.csv": sha256(csv_path)},
        "codigo_sha256": {nome: sha256(ROOT / nome) for nome in ARQUIVOS_CODIGO},
    }
    salvar_json(saida / "q2_manifesto.json", manifesto)
    return manifesto


def validar_q2(
    saida: Path = ROOT / "data/s02",
    parametros_path: Path = ROOT / "data/simulado/parametros.json",
) -> dict:
    """Regenera Q2 em memória e confere bytes, origem e código preservados."""
    manifesto = ler_json(saida / "q2_manifesto.json")
    csv_path = saida / "q2_resultados.csv"
    if sha256(csv_path) != manifesto["artefatos_sha256"]["q2_resultados.csv"]:
        raise ValueError("q2_resultados.csv foi modificado.")
    if sha256(parametros_path) != manifesto["origem"]["parametros_sha256"]:
        raise ValueError("Os parâmetros de origem de Q2 foram modificados.")
    for nome, esperado in manifesto["codigo_sha256"].items():
        if sha256(ROOT / nome) != esperado:
            raise ValueError(f"{nome} difere do código usado para gerar Q2.")
    esperado = resultados_csv_texto(executar_q2(ler_json(parametros_path)))
    if csv_path.read_text(encoding="utf-8") != esperado:
        raise ValueError("Q2 não foi reproduzida exatamente.")
    return {"status": "ok", "pergunta": "Q2", "configuracoes": len(ler_resultados(csv_path))}
