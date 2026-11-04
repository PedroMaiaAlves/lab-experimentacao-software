"""Normal bivariada nos log-tempos, calibrada exclusivamente pela coleta real."""

from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np

from .dados import ROOT, ler_pares, salvar_json, salvar_pares, sha256, validar_pares


def calibrar(pares: np.ndarray) -> dict:
    tempos = validar_pares(pares)
    logs = np.log(tempos)
    medias = logs.mean(axis=0)
    cov = np.cov(logs, rowvar=False, ddof=1)
    if np.var(logs[:, 0] - logs[:, 1], ddof=1) <= 0:
        raise ValueError("Diferenças constantes: calibração degenerada; não inventar variabilidade.")
    return {
        "versao": 1, "modelo": "lognormal_bivariada", "colunas": ["sem_cache_s", "com_cache_s"],
        "unidade_tempos": "segundos", "transformacao": "log natural",
        "n_pares_reais": len(tempos), "medias_log": medias.tolist(),
        "covariancia_log": cov.tolist(), "covariancia_ddof": 1,
        "delta_observado_log": float(medias[0] - medias[1]),
        "razao_geometrica_observada": float(np.exp(medias[0] - medias[1])),
    }


def gerar_pares(parametros: dict, n: int = 30, semente: int = 42,
                delta_log: float | None = None) -> np.ndarray:
    """Retorna n x 2: segundos sem/com cache. Delta=None preserva médias reais."""
    if not isinstance(n, int) or isinstance(n, bool) or n < 2:
        raise ValueError("n deve ser inteiro >= 2.")
    if not isinstance(semente, int) or isinstance(semente, bool) or semente < 0:
        raise ValueError("Semente deve ser inteiro não negativo.")
    mu = np.asarray(parametros["medias_log"], dtype=float).copy()
    cov = np.asarray(parametros["covariancia_log"], dtype=float)
    if mu.shape != (2,) or cov.shape != (2, 2) or not np.isfinite(mu).all() or not np.isfinite(cov).all():
        raise ValueError("Parâmetros devem ter duas médias e covariância 2 x 2 finitas.")
    if not np.allclose(cov, cov.T, rtol=0, atol=1e-12) or np.linalg.eigvalsh(cov).min() < -1e-12:
        raise ValueError("Covariância deve ser simétrica e positiva semidefinida.")
    if delta_log is not None:
        if not np.isfinite(delta_log):
            raise ValueError("Delta deve ser finito.")
        centro = mu.mean()
        mu[:] = [centro + delta_log / 2, centro - delta_log / 2]
    rng = np.random.default_rng(semente)
    logs = rng.multivariate_normal(mu, cov, size=n, check_valid="raise", method="svd")
    try:
        with np.errstate(over="raise", under="raise", invalid="raise"):
            pares = np.exp(logs)
    except FloatingPointError as exc:
        raise ValueError("Tempos fora da faixa numérica; parâmetros não serão truncados.") from exc
    return validar_pares(pares)


def executar(entrada: Path, saida: Path, delta_log: float | None = None) -> dict:
    # Importação local evita dependência circular com a verificação integrada.
    from .validacao import validar_coleta

    manifesto = validar_coleta(entrada)
    real = entrada / "pares_reais.csv"
    parametros = calibrar(ler_pares(real))
    cfg = manifesto["protocolo"]
    parametros.update({
        "fonte": {"arquivo": "pares_reais.csv", "sha256": sha256(real),
                  "manifesto_sha256": sha256(entrada / "manifesto.json"),
                  "django": cfg["django"], "arquivo_django_sha256": cfg["fonte_sha256"]},
        "cenario_previo_sha256": manifesto["registro_previo"]["docs/cenario.md"],
        "semente": cfg["semente"], "n_simulado": cfg["pares"],
        "delta_log_aplicado": delta_log, "numpy": np.__version__,
        "gerador": "numpy.random.default_rng / PCG64 / multivariate_normal(method=svd)",
    })
    pares = gerar_pares(parametros, cfg["pares"], cfg["semente"], delta_log)
    saida.mkdir(parents=True, exist_ok=True)
    salvar_json(saida / "parametros.json", parametros)
    salvar_pares(saida / "pares_simulados.csv", pares)
    salvar_json(saida / "manifesto.json", {
        "tipo": "dados_simulados_nao_sao_medicoes_reais", "semente": cfg["semente"],
        "artefatos_sha256": {name: sha256(saida / name) for name in ("parametros.json", "pares_simulados.csv")},
        "codigo_sha256": {f"experimento/{name}": sha256(ROOT / "experimento" / name)
                          for name in ("simulacao.py", "dados.py")},
    })
    return parametros


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--entrada", type=Path, default=ROOT / "data/real")
    parser.add_argument("--saida", type=Path, default=ROOT / "data/simulado")
    parser.add_argument("--delta-log", type=float, default=None,
                        help="None preserva efeito observado; zero gera sob H0. Use --saida separada para variantes.")
    args = parser.parse_args()
    if args.delta_log is not None and args.saida.resolve() == (ROOT / "data/simulado").resolve():
        parser.error("Variantes de delta exigem --saida diferente para preservar a amostra oficial.")
    params = executar(args.entrada.resolve(), args.saida.resolve(), args.delta_log)
    print(f"Simulação: {params['n_simulado']} pares, semente {params['semente']}, saída {args.saida}")
