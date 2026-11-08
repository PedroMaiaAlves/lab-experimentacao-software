"""Infraestrutura Monte Carlo compartilhada pelas perguntas Q1, Q2 e Q3."""

from __future__ import annotations

import csv
import io
from pathlib import Path
from typing import Iterable

import numpy as np
import scipy
from scipy import stats

from .dados import ROOT, ler_json, salvar_json, sha256

ALPHA_PADRAO = 0.05
REPETICOES_OFICIAIS = 10_000
SEMENTE_BASE = 42
TAMANHOS_Q1 = (10, 20, 30, 50, 100)
CAMPOS_RESULTADO = (
    "pergunta",
    "cenario",
    "distribuicao",
    "teste",
    "n",
    "delta_log",
    "razao_geometrica",
    "repeticoes",
    "rejeicoes",
    "taxa_rejeicao",
    "ic95_inferior",
    "ic95_superior",
    "alpha",
    "semente_base",
    "semente_derivada",
)


def desvio_diferencas(parametros: dict) -> float:
    """Obtém o desvio populacional de log(sem cache) - log(com cache)."""
    cov = np.asarray(parametros["covariancia_log"], dtype=float)
    if cov.shape != (2, 2) or not np.isfinite(cov).all():
        raise ValueError("covariancia_log deve ser uma matriz 2 x 2 finita.")
    variancia = float(cov[0, 0] + cov[1, 1] - 2 * cov[0, 1])
    if variancia <= 0:
        raise ValueError("A variância calibrada das diferenças deve ser positiva.")
    return float(np.sqrt(variancia))


def intervalo_wilson(rejeicoes: int, repeticoes: int, nivel: float = 0.95) -> tuple[float, float]:
    """Intervalo de Wilson para uma proporção binomial."""
    if not isinstance(rejeicoes, (int, np.integer)) or isinstance(rejeicoes, bool):
        raise ValueError("rejeicoes deve ser inteiro.")
    if not isinstance(repeticoes, (int, np.integer)) or isinstance(repeticoes, bool):
        raise ValueError("repeticoes deve ser inteiro.")
    if repeticoes <= 0 or not 0 <= rejeicoes <= repeticoes:
        raise ValueError("Contagens binomiais inválidas.")
    if not 0 < nivel < 1:
        raise ValueError("nivel deve estar entre zero e um.")
    z = float(stats.norm.ppf(0.5 + nivel / 2))
    p = rejeicoes / repeticoes
    denominador = 1 + z**2 / repeticoes
    centro = (p + z**2 / (2 * repeticoes)) / denominador
    margem = z * np.sqrt(p * (1 - p) / repeticoes + z**2 / (4 * repeticoes**2)) / denominador
    return float(max(0.0, centro - margem)), float(min(1.0, centro + margem))


def gerar_diferencas(
    rng: np.random.Generator,
    repeticoes: int,
    n: int,
    delta_log: float,
    sigma_d: float,
    distribuicao: str,
) -> np.ndarray:
    """Gera uma matriz (repetições x n) de diferenças logarítmicas."""
    if distribuicao not in {"normal", "t3"}:
        raise ValueError("distribuicao deve ser 'normal' ou 't3'.")
    if not isinstance(repeticoes, int) or isinstance(repeticoes, bool) or repeticoes < 1:
        raise ValueError("repeticoes deve ser inteiro positivo.")
    if not isinstance(n, int) or isinstance(n, bool) or n < 2:
        raise ValueError("n deve ser inteiro >= 2.")
    if not np.isfinite(delta_log) or not np.isfinite(sigma_d) or sigma_d <= 0:
        raise ValueError("delta_log deve ser finito e sigma_d deve ser positivo e finito.")
    if distribuicao == "normal":
        padrao = rng.normal(size=(repeticoes, n))
    else:
        # Var(T_3) = 3; a divisão mantém a mesma variância do cenário normal.
        padrao = rng.standard_t(df=3, size=(repeticoes, n)) / np.sqrt(3.0)
    return delta_log + sigma_d * padrao


def avaliar_rejeicoes(diferencas: np.ndarray, alpha: float = ALPHA_PADRAO) -> dict[str, np.ndarray]:
    """Aplica em lote os mesmos testes bicaudais usados na Sprint 1."""
    d = np.asarray(diferencas, dtype=float)
    if d.ndim != 2 or d.shape[1] < 2 or not np.isfinite(d).all():
        raise ValueError("diferencas deve ser uma matriz finita de repetições x n.")
    if not 0 < alpha < 1:
        raise ValueError("alpha deve estar entre zero e um.")
    t = stats.ttest_1samp(d, popmean=0.0, axis=1, alternative="two-sided")
    # As distribuições simuladas são contínuas: não há zeros nem empates por construção.
    w = stats.wilcoxon(d, axis=1, alternative="two-sided", method="exact")
    return {
        "t_pareado": np.asarray(t.pvalue < alpha, dtype=bool),
        "wilcoxon": np.asarray(w.pvalue < alpha, dtype=bool),
    }


def simular_grade(
    *,
    distribuicao: str,
    tamanhos: Iterable[int],
    deltas: Iterable[float],
    repeticoes: int,
    alpha: float,
    semente: int,
    sigma_d: float,
    pergunta: str,
    cenario: str,
) -> list[dict]:
    """Executa uma grade reproduzível e retorna somente resultados agregados."""
    tamanhos = tuple(tamanhos)
    deltas = tuple(deltas)
    if not tamanhos or not deltas:
        raise ValueError("A grade precisa de ao menos um tamanho e um delta.")
    if any(not isinstance(n, int) or isinstance(n, bool) or n < 2 for n in tamanhos):
        raise ValueError("Todos os tamanhos devem ser inteiros >= 2.")
    if any(not np.isfinite(delta) for delta in deltas):
        raise ValueError("Todos os deltas devem ser finitos.")
    if not isinstance(semente, int) or isinstance(semente, bool) or semente < 0:
        raise ValueError("semente deve ser inteiro não negativo.")
    configuracoes = [(n, float(delta)) for n in tamanhos for delta in deltas]
    filhos = np.random.SeedSequence(semente).spawn(len(configuracoes))
    resultados: list[dict] = []
    for (n, delta), filho in zip(configuracoes, filhos, strict=True):
        rng = np.random.default_rng(filho)
        d = gerar_diferencas(rng, repeticoes, n, delta, sigma_d, distribuicao)
        decisoes = avaliar_rejeicoes(d, alpha)
        semente_derivada = int(filho.generate_state(1, dtype=np.uint32)[0])
        for teste in ("t_pareado", "wilcoxon"):
            rejeicoes = int(decisoes[teste].sum())
            inferior, superior = intervalo_wilson(rejeicoes, repeticoes)
            resultados.append({
                "pergunta": pergunta,
                "cenario": cenario,
                "distribuicao": distribuicao,
                "teste": teste,
                "n": n,
                "delta_log": delta,
                "razao_geometrica": float(np.exp(delta)),
                "repeticoes": repeticoes,
                "rejeicoes": rejeicoes,
                "taxa_rejeicao": rejeicoes / repeticoes,
                "ic95_inferior": inferior,
                "ic95_superior": superior,
                "alpha": alpha,
                "semente_base": semente,
                "semente_derivada": semente_derivada,
            })
    return resultados


def executar_q1(
    parametros: dict,
    *,
    repeticoes: int = REPETICOES_OFICIAIS,
    tamanhos: Iterable[int] = TAMANHOS_Q1,
    alpha: float = ALPHA_PADRAO,
    semente: int = SEMENTE_BASE,
) -> list[dict]:
    """Q1: estima erro tipo I sob diferenças normais e H0 verdadeira."""
    return simular_grade(
        distribuicao="normal",
        tamanhos=tamanhos,
        deltas=(0.0,),
        repeticoes=repeticoes,
        alpha=alpha,
        semente=semente,
        sigma_d=desvio_diferencas(parametros),
        pergunta="Q1",
        cenario="normal_h0",
    )


def resultados_csv_texto(resultados: list[dict]) -> str:
    buffer = io.StringIO(newline="")
    writer = csv.DictWriter(buffer, fieldnames=CAMPOS_RESULTADO, lineterminator="\n")
    writer.writeheader()
    for resultado in resultados:
        writer.writerow({campo: resultado[campo] for campo in CAMPOS_RESULTADO})
    return buffer.getvalue()


def ler_resultados(path: Path) -> list[dict]:
    inteiros = {"n", "repeticoes", "rejeicoes", "semente_base", "semente_derivada"}
    flutuantes = {"delta_log", "razao_geometrica", "taxa_rejeicao", "ic95_inferior", "ic95_superior", "alpha"}
    with path.open(encoding="utf-8", newline="") as arquivo:
        linhas = list(csv.DictReader(arquivo))
    resultados = []
    for linha in linhas:
        resultado = dict(linha)
        for campo in inteiros:
            resultado[campo] = int(resultado[campo])
        for campo in flutuantes:
            resultado[campo] = float(resultado[campo])
        resultados.append(resultado)
    return resultados


def salvar_q1(
    saida: Path = ROOT / "data/s02",
    parametros_path: Path = ROOT / "data/simulado/parametros.json",
) -> dict:
    """Executa Q1 e preserva CSV agregado e manifesto de proveniência."""
    parametros = ler_json(parametros_path)
    resultados = executar_q1(parametros)
    saida.mkdir(parents=True, exist_ok=True)
    csv_path = saida / "q1_resultados.csv"
    csv_path.write_text(resultados_csv_texto(resultados), encoding="utf-8", newline="\n")
    manifesto = {
        "versao": 1,
        "pergunta": "Q1",
        "descricao": "Erro tipo I sob diferenças logarítmicas normais com média zero.",
        "configuracao": {
            "alpha": ALPHA_PADRAO,
            "alternativa": "two-sided",
            "repeticoes": REPETICOES_OFICIAIS,
            "tamanhos": list(TAMANHOS_Q1),
            "semente_base": SEMENTE_BASE,
            "distribuicao": "normal",
            "delta_log": 0.0,
            "sigma_d": desvio_diferencas(parametros),
        },
        "origem": {
            "parametros": str(parametros_path.relative_to(ROOT)).replace("\\", "/"),
            "parametros_sha256": sha256(parametros_path),
        },
        "ambiente": {"numpy": np.__version__, "scipy": scipy.__version__},
        "artefatos_sha256": {"q1_resultados.csv": sha256(csv_path)},
        "codigo_sha256": {"experimento/monte_carlo.py": sha256(Path(__file__))},
    }
    salvar_json(saida / "q1_manifesto.json", manifesto)
    return manifesto


def validar_q1(
    saida: Path = ROOT / "data/s02",
    parametros_path: Path = ROOT / "data/simulado/parametros.json",
) -> dict:
    """Regenera Q1 em memória e confere bytes, origem e código preservados."""
    manifesto = ler_json(saida / "q1_manifesto.json")
    csv_path = saida / "q1_resultados.csv"
    if sha256(csv_path) != manifesto["artefatos_sha256"]["q1_resultados.csv"]:
        raise ValueError("q1_resultados.csv foi modificado.")
    if sha256(parametros_path) != manifesto["origem"]["parametros_sha256"]:
        raise ValueError("Os parâmetros de origem de Q1 foram modificados.")
    if sha256(Path(__file__)) != manifesto["codigo_sha256"]["experimento/monte_carlo.py"]:
        raise ValueError("O código Monte Carlo difere do código usado para gerar Q1.")
    esperado = resultados_csv_texto(executar_q1(ler_json(parametros_path)))
    if csv_path.read_text(encoding="utf-8") != esperado:
        raise ValueError("Q1 não foi reproduzida exatamente.")
    return {"status": "ok", "pergunta": "Q1", "configuracoes": len(ler_resultados(csv_path))}
