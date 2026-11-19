"""Análise estatística, poder sobre o piloto e estimativa de impacto do Lab05."""

from __future__ import annotations

import argparse
import csv
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np
from scipy import stats

RAIZ = Path(__file__).resolve().parent
if str(RAIZ) not in sys.path:
    sys.path.insert(0, str(RAIZ))

from experimento import poder as mod_poder  # noqa: E402

ALFA = 0.05
SEMENTE = 42
METRICAS_DESCRITIVAS = (
    "throughput_msg_s",
    "throughput_mib_s",
    "latencia_p50_ms",
    "latencia_p99_ms",
    "cpu_percent_medio",
    "memoria_mib_media",
)
COMPARACOES_PRINCIPAIS = (
    ("E1", "throughput_msg_s", 1024),
    ("E1", "throughput_msg_s", 16384),
    ("E2", "latencia_p99_ms", 1024),
    ("E2", "latencia_p99_ms", 16384),
)
COLUNAS_NUMERICAS = (
    "ordem",
    "tamanho_bytes",
    "repeticao",
    "duracao_s",
    "taxa_alvo_msg_s",
    *METRICAS_DESCRITIVAS,
)


def piloto_mais_recente(raiz_piloto: Path = RAIZ / "data" / "piloto") -> Path:
    for pasta in sorted(raiz_piloto.iterdir(), reverse=True):
        manifesto = pasta / "manifesto.json"
        resultados = pasta / "resultados.csv"
        if manifesto.is_file() and resultados.is_file():
            if json.loads(manifesto.read_text(encoding="utf-8")).get("status") == "concluida":
                return resultados
    raise FileNotFoundError(f"Nenhuma coleta concluída encontrada em {raiz_piloto}")


def carregar_resultados(caminho: Path) -> tuple[list[dict], dict[str, int]]:
    sucessos: list[dict] = []
    contagens: Counter[str] = Counter()
    with caminho.open(encoding="utf-8", newline="") as arquivo:
        for linha in csv.DictReader(arquivo):
            status = linha["status"]
            contagens[status] += 1
            if status != "sucesso":
                continue
            item = dict(linha)
            for coluna in COLUNAS_NUMERICAS:
                bruto = item.get(coluna, "")
                item[coluna] = float(bruto) if bruto not in ("", None) else None
            item["tamanho_bytes"] = int(item["tamanho_bytes"])
            sucessos.append(item)
    return sucessos, dict(contagens)


def descrever_celulas(
    registros: list[dict],
    metricas: tuple[str, ...] = METRICAS_DESCRITIVAS,
) -> list[dict]:
    grupos: dict[tuple[str, str, int], list[dict]] = defaultdict(list)
    for r in registros:
        grupos[(r["experimento"], r["broker"], r["tamanho_bytes"])].append(r)

    saida: list[dict] = []
    for (exp, broker, tam), itens in sorted(grupos.items()):
        for metrica in metricas:
            vals = np.array([r[metrica] for r in itens if r[metrica] is not None], dtype=float)
            if vals.size == 0:
                continue
            q1, med, q3 = np.percentile(vals, [25, 50, 75])
            media = float(np.mean(vals))
            dp = float(np.std(vals, ddof=1)) if vals.size > 1 else None
            cv = float(dp / media) if dp is not None and media > 0 else None
            positivos = bool(np.all(vals > 0))
            logs = np.log(vals) if positivos else None
            saida.append({
                "experimento": exp,
                "broker": broker,
                "tamanho_bytes": tam,
                "metrica": metrica,
                "n": int(vals.size),
                "mediana": float(med),
                "q1": float(q1),
                "q3": float(q3),
                "iqr": float(q3 - q1),
                "media_geometrica": float(np.exp(np.mean(logs))) if positivos else None,
                "desvio_padrao": dp,
                "cv": cv,
                "variancia_log": float(np.var(logs, ddof=1)) if positivos and vals.size > 1 else None,
                "desvio_log": float(np.std(logs, ddof=1)) if positivos and vals.size > 1 else None,
            })
    return saida


def cliff_delta(a: np.ndarray, b: np.ndarray) -> float:
    diff = np.asarray(a, dtype=float)[:, None] - np.asarray(b, dtype=float)[None, :]
    return float((np.sum(diff > 0) - np.sum(diff < 0)) / diff.size)


def magnitude_cliff(delta: float) -> str:
    d = abs(delta)
    if d < 0.147:
        return "desprezível"
    if d < 0.33:
        return "pequeno"
    if d < 0.474:
        return "médio"
    return "grande"


def razao_bootstrap(
    a: np.ndarray,
    b: np.ndarray,
    repeticoes: int = 5000,
    semente: int = SEMENTE,
) -> tuple[float, float, float]:
    la = np.log(np.asarray(a, dtype=float))
    lb = np.log(np.asarray(b, dtype=float))
    razao = float(np.exp(np.mean(la) - np.mean(lb)))
    rng = np.random.default_rng(semente)
    ia = rng.integers(0, la.size, size=(repeticoes, la.size))
    ib = rng.integers(0, lb.size, size=(repeticoes, lb.size))
    razoes = np.exp(la[ia].mean(axis=1) - lb[ib].mean(axis=1))
    inf, sup = np.percentile(razoes, [2.5, 97.5])
    return razao, float(inf), float(sup)


def corrigir_holm(p_valores: dict[str, float | None]) -> dict[str, float | None]:
    validos = sorted((p, chave) for chave, p in p_valores.items() if p is not None)
    m = len(validos)
    ajustados: dict[str, float | None] = {chave: None for chave in p_valores}
    acumulado = 0.0
    for i, (p, chave) in enumerate(validos):
        acumulado = max(acumulado, min(1.0, (m - i) * p))
        ajustados[chave] = float(acumulado)
    return ajustados


def comparar_brokers(
    kafka: np.ndarray,
    rabbitmq: np.ndarray,
    repeticoes_boot: int = 5000,
    semente: int = SEMENTE,
) -> dict:
    a = np.asarray(kafka, dtype=float)
    b = np.asarray(rabbitmq, dtype=float)
    if a.size < 2 or b.size < 2 or np.any(a <= 0) or np.any(b <= 0):
        return {"disponivel": False, "n_kafka": int(a.size), "n_rabbitmq": int(b.size)}

    la, lb = np.log(a), np.log(b)
    shapiro_k = float(stats.shapiro(la).pvalue) if la.size >= 3 and np.ptp(la) > 0 else None
    shapiro_r = float(stats.shapiro(lb).pvalue) if lb.size >= 3 and np.ptp(lb) > 0 else None
    normal = shapiro_k is not None and shapiro_r is not None and shapiro_k >= ALFA and shapiro_r >= ALFA

    if np.var(la, ddof=1) == 0 and np.var(lb, ddof=1) == 0:
        t_stat, p_welch = None, None
    else:
        welch = stats.ttest_ind(la, lb, equal_var=False, alternative="two-sided")
        t_stat, p_welch = float(welch.statistic), float(welch.pvalue)

    sem_empates = np.unique(np.concatenate([a, b])).size == a.size + b.size
    mw = stats.mannwhitneyu(a, b, alternative="two-sided", method="exact" if sem_empates else "auto")
    razao, ic_inf, ic_sup = razao_bootstrap(a, b, repeticoes=repeticoes_boot, semente=semente)
    delta = cliff_delta(a, b)

    return {
        "disponivel": True,
        "n_kafka": int(a.size),
        "n_rabbitmq": int(b.size),
        "shapiro_log_kafka_p": shapiro_k,
        "shapiro_log_rabbitmq_p": shapiro_r,
        "teste_recomendado": "welch_log" if normal else "mann_whitney",
        "welch_t": t_stat,
        "welch_p": p_welch,
        "mann_whitney_u": float(mw.statistic),
        "mann_whitney_p": float(mw.pvalue),
        "razao_geometrica": razao,
        "ic95_bootstrap": [ic_inf, ic_sup],
        "cliff_delta": delta,
        "cliff_magnitude": magnitude_cliff(delta),
    }


def testar_interacao(
    k1: np.ndarray,
    r1: np.ndarray,
    k16: np.ndarray,
    r16: np.ndarray,
    permutacoes: int = 5000,
    semente: int = SEMENTE,
) -> dict:
    grupos = [np.asarray(g, dtype=float) for g in (k1, r1, k16, r16)]
    if any(g.size < 2 or np.any(g <= 0) for g in grupos):
        return {"disponivel": False}

    lk1, lr1, lk16, lr16 = [np.log(g) for g in grupos]
    contraste = float((lk16.mean() - lr16.mean()) - (lk1.mean() - lr1.mean()))

    y = np.concatenate([lk1, lr1, lk16, lr16])
    n = y.size
    ik = np.concatenate([np.ones(lk1.size), np.zeros(lr1.size), np.ones(lk16.size), np.zeros(lr16.size)])
    it = np.concatenate([np.zeros(lk1.size + lr1.size), np.ones(lk16.size + lr16.size)])
    x_full = np.column_stack([np.ones(n), ik, it, ik * it])

    q, _ = np.linalg.qr(x_full)
    q_add = q[:, :3]
    q_int = q[:, 3]

    ss_int = float((q_int @ y) ** 2)
    ss_res = float(np.sum((y - q @ (q.T @ y)) ** 2))
    gl_res = n - 4
    if ss_res == 0:
        f_obs, p_anova, p_perm = None, None, None
    else:
        f_obs = float(gl_res * ss_int / ss_res)
        p_anova = float(stats.f.sf(f_obs, 1, gl_res))

        res_add = y - q_add @ (q_add.T @ y)
        rng = np.random.default_rng(semente)
        ordens = np.argsort(rng.random((permutacoes, n)), axis=1)
        perm = res_add[ordens]
        num = (perm @ q_int) ** 2
        proj_add = np.sum((perm @ q_add) ** 2, axis=1)
        den = np.sum(perm**2, axis=1) - proj_add - num
        f_perm = gl_res * num / np.where(den > 0, den, np.nan)
        p_perm = float((1 + np.sum(f_perm >= f_obs - 1e-12)) / (permutacoes + 1))

    return {
        "disponivel": True,
        "n_total": int(n),
        "contraste_log": contraste,
        "razao_das_razoes": float(np.exp(contraste)),
        "anova_f": f_obs,
        "anova_gl": [1, int(gl_res)],
        "anova_p": p_anova,
        "permutacao_p": p_perm,
        "permutacoes": int(permutacoes),
    }


def poder_piloto(
    descritiva: list[dict],
    ns: tuple[int, ...] = (10, 15, 20),
    razoes: tuple[float, ...] = (1.20, 1.50, 2.00),
    repeticoes: int = 2000,
    semente: int = SEMENTE,
) -> list[dict]:
    cvs_por_par: dict[tuple[str, str, int], list[float]] = defaultdict(list)
    for item in descritiva:
        chave = (item["experimento"], item["metrica"], item["tamanho_bytes"])
        if chave in COMPARACOES_PRINCIPAIS and item["cv"] is not None:
            cvs_por_par[chave].append(item["cv"])

    linhas: list[dict] = []
    for idx, (exp, metrica, tam) in enumerate(COMPARACOES_PRINCIPAIS):
        cvs = cvs_por_par.get((exp, metrica, tam), [])
        if not cvs:
            continue
        cv_max = max(cvs)
        for razao in razoes:
            for n in ns:
                p = mod_poder.poder(
                    n=n,
                    razao=razao,
                    cv=cv_max,
                    alfa=mod_poder.ALFA_HOLM_PIOR_CASO,
                    repeticoes=repeticoes,
                    semente=semente + idx,
                )
                linhas.append({
                    "experimento": exp,
                    "metrica": metrica,
                    "tamanho_bytes": tam,
                    "cv_observado_max": float(cv_max),
                    "razao": razao,
                    "n": n,
                    "alfa_efetivo": mod_poder.ALFA_HOLM_PIOR_CASO,
                    **p,
                })
    return linhas


def estimar_cpu_hora(registros: list[dict]) -> list[dict]:
    grupos: dict[tuple[str, str, int], list[tuple[float, float]]] = defaultdict(list)
    for r in registros:
        tput = r["throughput_msg_s"]
        cpu = r["cpu_percent_medio"]
        mem = r["memoria_mib_media"]
        if tput is None or tput <= 0 or cpu is None or mem is None:
            continue
        fator = 1_000_000.0 / (tput * 3600.0)
        cpu_h = (cpu / 100.0) * fator
        gib_h = (mem / 1024.0) * fator
        grupos[(r["experimento"], r["broker"], r["tamanho_bytes"])].append((cpu_h, gib_h))

    saida: list[dict] = []
    for (exp, broker, tam), pares in sorted(grupos.items()):
        cpus = np.array([p[0] for p in pares], dtype=float)
        gibs = np.array([p[1] for p in pares], dtype=float)
        saida.append({
            "experimento": exp,
            "broker": broker,
            "tamanho_bytes": tam,
            "n": int(len(pares)),
            "cpu_hora_por_milhao_mediana": float(np.median(cpus)),
            "cpu_hora_por_milhao_gmean": float(np.exp(np.mean(np.log(cpus)))),
            "gib_hora_por_milhao_mediana": float(np.median(gibs)),
            "gib_hora_por_milhao_gmean": float(np.exp(np.mean(np.log(gibs)))),
        })
    return saida


def analisar(
    caminho_csv: Path,
    repeticoes_boot: int = 5000,
    permutacoes: int = 5000,
    repeticoes_poder: int = 2000,
) -> dict:
    registros, contagens = carregar_resultados(caminho_csv)
    descritiva = descrever_celulas(registros)

    por_celula: dict[tuple[str, str, int, str], np.ndarray] = {}
    for exp, metrica, tam in COMPARACOES_PRINCIPAIS:
        for broker in ("kafka", "rabbitmq"):
            vals = [
                r[metrica]
                for r in registros
                if r["experimento"] == exp
                and r["broker"] == broker
                and r["tamanho_bytes"] == tam
                and r[metrica] is not None
            ]
            por_celula[(exp, broker, tam, metrica)] = np.array(vals, dtype=float)

    comparacoes: dict[str, dict] = {}
    for idx, (exp, metrica, tam) in enumerate(COMPARACOES_PRINCIPAIS):
        chave = f"{exp}_{metrica}_{tam // 1024}k"
        comparacoes[chave] = comparar_brokers(
            por_celula[(exp, "kafka", tam, metrica)],
            por_celula[(exp, "rabbitmq", tam, metrica)],
            repeticoes_boot=repeticoes_boot,
            semente=SEMENTE + idx,
        )

    p_welch = corrigir_holm({k: v.get("welch_p") for k, v in comparacoes.items()})
    p_mw = corrigir_holm({k: v.get("mann_whitney_p") for k, v in comparacoes.items()})
    p_rec = corrigir_holm({
        k: (v.get("welch_p") if v.get("teste_recomendado") == "welch_log" else v.get("mann_whitney_p"))
        for k, v in comparacoes.items()
    })
    for chave, resultado in comparacoes.items():
        if resultado.get("disponivel"):
            resultado["welch_p_holm"] = p_welch[chave]
            resultado["mann_whitney_p_holm"] = p_mw[chave]
            resultado["p_recomendado_holm"] = p_rec[chave]

    interacoes = {
        "E1_throughput_msg_s": testar_interacao(
            por_celula[("E1", "kafka", 1024, "throughput_msg_s")],
            por_celula[("E1", "rabbitmq", 1024, "throughput_msg_s")],
            por_celula[("E1", "kafka", 16384, "throughput_msg_s")],
            por_celula[("E1", "rabbitmq", 16384, "throughput_msg_s")],
            permutacoes=permutacoes,
            semente=SEMENTE,
        ),
        "E2_latencia_p99_ms": testar_interacao(
            por_celula[("E2", "kafka", 1024, "latencia_p99_ms")],
            por_celula[("E2", "rabbitmq", 1024, "latencia_p99_ms")],
            por_celula[("E2", "kafka", 16384, "latencia_p99_ms")],
            por_celula[("E2", "rabbitmq", 16384, "latencia_p99_ms")],
            permutacoes=permutacoes,
            semente=SEMENTE + 1,
        ),
    }

    return {
        "arquivo": str(caminho_csv.relative_to(RAIZ)).replace("\\", "/") if caminho_csv.is_relative_to(RAIZ) else str(caminho_csv),
        "contagens_status": contagens,
        "alfa": ALFA,
        "semente": SEMENTE,
        "descritiva": descritiva,
        "comparacoes": comparacoes,
        "interacoes": interacoes,
        "poder_piloto": poder_piloto(descritiva, repeticoes=repeticoes_poder),
        "impacto_recursos": estimar_cpu_hora(registros),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Análise estatística e de impacto do Lab05")
    parser.add_argument("--entrada", type=Path, default=None, help="caminho para resultados.csv")
    parser.add_argument("--saida", type=Path, default=None, help="opcional: salva o JSON completo")
    args = parser.parse_args()

    entrada = args.entrada.resolve() if args.entrada else piloto_mais_recente()
    resultado = analisar(entrada)

    if args.saida:
        args.saida.parent.mkdir(parents=True, exist_ok=True)
        args.saida.write_text(
            json.dumps(resultado, ensure_ascii=False, indent=2, allow_nan=False) + "\n",
            encoding="utf-8",
        )

    print(f"Arquivo: {resultado['arquivo']} | Status: {resultado['contagens_status']}")
    print("\nComparações principais (Kafka / RabbitMQ):")
    for chave, c in resultado["comparacoes"].items():
        if not c["disponivel"]:
            print(f"  {chave}: indisponível")
            continue
        inf, sup = c["ic95_bootstrap"]
        print(
            f"  {chave}: razão={c['razao_geometrica']:.3f} [{inf:.3f}, {sup:.3f}] | "
            f"Cliff={c['cliff_delta']:+.2f} ({c['cliff_magnitude']}) | "
            f"rec={c['teste_recomendado']} | p_holm={c['p_recomendado_holm']:.4g}"
        )
    print("\nInterações (H3):")
    for chave, inter in resultado["interacoes"].items():
        if inter["disponivel"]:
            print(
                f"  {chave}: razão_das_razões={inter['razao_das_razoes']:.3f} | "
                f"p_anova={inter['anova_p']:.4g} | p_perm={inter['permutacao_p']:.4g}"
            )
    print("\nCPU-hora por milhão de mensagens (mediana):")
    for r in resultado["impacto_recursos"]:
        print(
            f"  {r['experimento']} {r['broker']:8s} {r['tamanho_bytes']//1024:2d}KiB: "
            f"{r['cpu_hora_por_milhao_mediana']:.4f} vCPU-h/1M | "
            f"{r['gib_hora_por_milhao_mediana']:.4f} GiB-h/1M"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
