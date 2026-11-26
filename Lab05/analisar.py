"""Análise estatística, checagens de validade e relatório do Lab05."""

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

import validar as validador  # noqa: E402
from experimento import poder as mod_poder  # noqa: E402

ALFA = 0.05
SEMENTE = 42
PROTOCOLO_OFICIAL = RAIZ / "data" / "plano" / "protocolo_oficial.json"
DIRETORIOS_PILOTO = {"piloto", "piloto_g1", "verificacao_e2"}
METRICAS_DESCRITIVAS = (
    "throughput_msg_s",
    "throughput_mib_s",
    "throughput_consumo_msg_s",
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
    "ordem_no_bloco",
    "tamanho_bytes",
    "repeticao",
    "tentativa",
    "duracao_s",
    "taxa_alvo_msg_s",
    "cv_intervalos",
    "intervalo_min_rel",
    *METRICAS_DESCRITIVAS,
)
ROTULOS_COMPARACAO = {
    "E1_throughput_msg_s_1k": "E1 · Throughput (msg/s) · 1 KiB (H1)",
    "E1_throughput_msg_s_16k": "E1 · Throughput (msg/s) · 16 KiB (H1)",
    "E2_latencia_p99_ms_1k": "E2 · Latência p99 (ms) · 1 KiB (H2)",
    "E2_latencia_p99_ms_16k": "E2 · Latência p99 (ms) · 16 KiB (H2)",
}


def piloto_mais_recente(raiz_piloto: Path = RAIZ / "data" / "piloto") -> Path:
    for pasta in sorted(raiz_piloto.iterdir(), reverse=True):
        if not pasta.is_dir():
            continue
        manifesto = pasta / "manifesto.json"
        resultados = pasta / "resultados.csv"
        if manifesto.is_file() and resultados.is_file():
            if json.loads(manifesto.read_text(encoding="utf-8")).get("status") == "concluida":
                return resultados
    raise FileNotFoundError(f"Nenhuma coleta concluída encontrada em {raiz_piloto}")


def coleta_oficial_mais_recente(raiz_oficial: Path = RAIZ / "data" / "oficial") -> Path:
    if not raiz_oficial.is_dir():
        raise FileNotFoundError(f"Nenhuma coleta oficial encontrada em {raiz_oficial} (aguardando #210 / portão G3)")
    for pasta in sorted(raiz_oficial.iterdir(), reverse=True):
        if not pasta.is_dir():
            continue
        if (pasta / "manifesto.json").is_file() and (pasta / "resultados.csv").is_file():
            return pasta / "resultados.csv"
    raise FileNotFoundError(f"Nenhuma coleta oficial encontrada em {raiz_oficial} (aguardando #210 / portão G3)")


def carregar_tentativas(caminho: Path) -> tuple[list[dict], dict[str, int], list[str]]:
    sucessos: list[dict] = []
    contagens: Counter[str] = Counter()
    ids_com_falha: set[str] = set()
    ids_tentativa_gt1: set[str] = set()
    with caminho.open(encoding="utf-8", newline="") as arquivo:
        for linha in csv.DictReader(arquivo):
            status = linha["status"]
            contagens[status] += 1
            ident = linha.get("id_execucao", "")
            tentativa_bruta = linha.get("tentativa", "")
            tentativa_num = int(float(tentativa_bruta)) if tentativa_bruta not in ("", None) else 1
            if status != "sucesso":
                if ident:
                    ids_com_falha.add(ident)
                continue
            if tentativa_num > 1 and ident:
                ids_tentativa_gt1.add(ident)
            item = dict(linha)
            for coluna in COLUNAS_NUMERICAS:
                bruto = item.get(coluna, "")
                item[coluna] = float(bruto) if bruto not in ("", None) else None
            item["tamanho_bytes"] = int(item["tamanho_bytes"])
            item["bloco"] = (linha.get("bloco") or "").strip()
            item["tentativa"] = tentativa_num
            sucessos.append(item)
    ids_repetidos = sorted(
        {
            r["id_execucao"]
            for r in sucessos
            if r["tentativa"] > 1 or r["id_execucao"] in ids_com_falha or r["id_execucao"] in ids_tentativa_gt1
        }
    )
    return sucessos, dict(contagens), ids_repetidos


def carregar_resultados(caminho: Path) -> tuple[list[dict], dict[str, int]]:
    sucessos, contagens, _ = carregar_tentativas(caminho)
    return sucessos, contagens


def ler_metadados_coleta(
    diretorio: Path,
    validar_oficial: bool = False,
    caminho_protocolo: Path = PROTOCOLO_OFICIAL,
) -> dict:
    partes = {p.lower() for p in diretorio.resolve().parts}
    eh_piloto = bool(partes & DIRETORIOS_PILOTO)
    if validar_oficial and eh_piloto:
        raise ValueError("Análise oficial proíbe diretórios de piloto/verificação (revisao_analise.md)")

    protocolo = json.loads(caminho_protocolo.read_text(encoding="utf-8"))
    omb_proto = protocolo["imagens"]["omb"]
    caminho_manifesto = diretorio / "manifesto.json"
    manifesto = json.loads(caminho_manifesto.read_text(encoding="utf-8")) if caminho_manifesto.is_file() else {}

    valido_g3 = None
    avisos_g3: list[str] = []
    if validar_oficial:
        relatorio_g3 = validador.validar(diretorio, fase="completa", caminho_protocolo=caminho_protocolo)
        if not relatorio_g3["valido"]:
            raise ValueError("Coleta oficial reprovada no portão G3: " + "; ".join(relatorio_g3["erros"]))
        valido_g3 = True
        avisos_g3 = list(relatorio_g3.get("avisos", []))

    imagens = manifesto.get("imagens", {})
    omb_imagem = imagens.get("omb")
    omb_timestamp_ms_valido = bool(
        omb_imagem and (omb_imagem == omb_proto["fingerprint"] or "ts-ms" in str(omb_imagem))
    )
    ambiente = manifesto.get("ambiente") or {}
    taxas_e2 = {int(k): int(v) for k, v in manifesto.get("taxas_e2", {}).items()}
    blocos_manifesto = sorted({b["bloco"] for b in manifesto.get("blocos", []) if b.get("bloco")})

    origem = "oficial" if validar_oficial else ("piloto" if eh_piloto else "personalizada")
    return {
        "colecao_id": manifesto.get("colecao_id") or diretorio.name,
        "origem": origem,
        "schema": manifesto.get("schema"),
        "valido_g3": valido_g3,
        "avisos_g3": avisos_g3,
        "omb_referencia_esperada": omb_proto["referencia"],
        "omb_fingerprint_esperado": omb_proto["fingerprint"],
        "omb_imagem": omb_imagem,
        "omb_timestamp_ms_valido": omb_timestamp_ms_valido,
        "maquina_unica": bool(ambiente),
        "ambiente": {
            "so": ambiente.get("so"),
            "cpu": ambiente.get("cpu"),
            "processadores_logicos": ambiente.get("processadores_logicos"),
            "memoria_total_bytes": ambiente.get("memoria_total_bytes"),
            "git_commit": ambiente.get("git_commit"),
        },
        "taxas_e2": taxas_e2,
        "blocos_registrados": blocos_manifesto,
    }


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
            vals = np.array([r[metrica] for r in itens if r.get(metrica) is not None], dtype=float)
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


def _executar_comparacoes_e_interacoes(
    registros: list[dict],
    repeticoes_boot: int,
    permutacoes: int,
) -> tuple[dict[str, dict], dict[str, dict]]:
    por_celula: dict[tuple[str, str, int, str], np.ndarray] = {}
    for exp, metrica, tam in COMPARACOES_PRINCIPAIS:
        for broker in ("kafka", "rabbitmq"):
            vals = [
                r[metrica]
                for r in registros
                if r["experimento"] == exp
                and r["broker"] == broker
                and r["tamanho_bytes"] == tam
                and r.get(metrica) is not None
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
    return comparacoes, interacoes


def _regressao_ordem(xs: np.ndarray, ys: np.ndarray) -> dict:
    n = int(xs.size)
    if n < 3 or np.ptp(xs) == 0:
        return {"disponivel": False, "n": n}
    if np.ptp(ys) == 0:
        return {
            "disponivel": True,
            "n": n,
            "inclinacao_log": 0.0,
            "intercepto_log": float(ys[0]),
            "erro_padrao": 0.0,
            "ic95_inclinacao": [0.0, 0.0],
            "ic95_contem_zero": True,
            "p_valor": 1.0,
            "r2": 0.0,
            "variacao_pct_por_posicao": 0.0,
        }
    reg = stats.linregress(xs, ys)
    slope, intercept = float(reg.slope), float(reg.intercept)
    stderr, pvalue, rvalue = float(reg.stderr), float(reg.pvalue), float(reg.rvalue)
    if not all(np.isfinite([slope, intercept, stderr, pvalue, rvalue])):
        return {"disponivel": False, "n": n}
    t_crit = float(stats.t.ppf(0.975, n - 2))
    ic_inf = slope - t_crit * stderr
    ic_sup = slope + t_crit * stderr
    return {
        "disponivel": True,
        "n": n,
        "inclinacao_log": slope,
        "intercepto_log": intercept,
        "erro_padrao": stderr,
        "ic95_inclinacao": [float(ic_inf), float(ic_sup)],
        "ic95_contem_zero": bool(ic_inf <= 0.0 <= ic_sup),
        "p_valor": pvalue,
        "r2": float(rvalue**2),
        "variacao_pct_por_posicao": float((np.exp(slope) - 1.0) * 100.0),
    }


def checar_efeito_ordem(registros: list[dict]) -> list[dict]:
    saida: list[dict] = []
    for exp, metrica, tam in COMPARACOES_PRINCIPAIS:
        for broker in ("kafka", "rabbitmq"):
            itens = sorted(
                (
                    r for r in registros
                    if r["experimento"] == exp
                    and r["broker"] == broker
                    and r["tamanho_bytes"] == tam
                    and r.get(metrica) is not None
                    and r[metrica] > 0
                    and r.get("ordem") is not None
                ),
                key=lambda r: float(r["ordem"]),
            )
            xs = np.array([float(r["ordem"]) for r in itens], dtype=float)
            ys = np.log(np.array([float(r[metrica]) for r in itens], dtype=float))
            entrada = {
                "experimento": exp,
                "metrica": metrica,
                "broker": broker,
                "tamanho_bytes": tam,
                **_regressao_ordem(xs, ys),
            }
            blocos = sorted({r.get("bloco", "") for r in itens if r.get("bloco")})
            if blocos:
                por_bloco: dict[str, dict] = {}
                for b in blocos:
                    sub = [r for r in itens if r.get("bloco") == b]
                    bxs = np.array(
                        [
                            float(r["ordem_no_bloco"] if r.get("ordem_no_bloco") is not None else r["ordem"])
                            for r in sub
                        ],
                        dtype=float,
                    )
                    bys = np.log(np.array([float(r[metrica]) for r in sub], dtype=float))
                    por_bloco[b] = _regressao_ordem(bxs, bys)
                entrada["por_bloco"] = por_bloco
            saida.append(entrada)
    return saida


def _estimar_coeficiente_ols(beta: np.ndarray, cov: np.ndarray, idx: int, df: int, s2: float) -> tuple[float, list[float], float]:
    b_val = float(beta[idx])
    se = float(np.sqrt(max(0.0, cov[idx, idx])))
    if s2 == 0.0 or se == 0.0:
        p_val = 1.0 if b_val == 0.0 else 0.0
        est = float(np.exp(b_val))
        return est, [est, est], p_val
    t_val = b_val / se
    p_val = float(2.0 * stats.t.sf(abs(t_val), df))
    t_crit = float(stats.t.ppf(0.975, df))
    return (
        float(np.exp(b_val)),
        [float(np.exp(b_val - t_crit * se)), float(np.exp(b_val + t_crit * se))],
        p_val,
    )


def checar_efeito_bloco(registros: list[dict]) -> list[dict]:
    saida: list[dict] = []
    for exp, metrica, tam in COMPARACOES_PRINCIPAIS:
        itens = [
            r for r in registros
            if r["experimento"] == exp
            and r["tamanho_bytes"] == tam
            and r.get(metrica) is not None
            and r[metrica] > 0
            and r.get("bloco")
        ]
        blocos = sorted({r["bloco"] for r in itens})
        if len(blocos) < 2:
            saida.append({
                "experimento": exp,
                "metrica": metrica,
                "tamanho_bytes": tam,
                "disponivel": False,
                "motivo": "menos de dois blocos registrados",
            })
            continue

        por_broker: dict[str, dict] = {}
        for broker in ("kafka", "rabbitmq"):
            sub_b: dict[str, dict] = {}
            arrays_log: list[np.ndarray] = []
            arrays_raw: list[np.ndarray] = []
            for b in blocos:
                vals = np.array(
                    [float(r[metrica]) for r in itens if r["broker"] == broker and r["bloco"] == b],
                    dtype=float,
                )
                if vals.size == 0:
                    continue
                q1, med, q3 = np.percentile(vals, [25, 50, 75])
                logs = np.log(vals)
                arrays_raw.append(vals)
                arrays_log.append(logs)
                sub_b[b] = {
                    "n": int(vals.size),
                    "mediana": float(med),
                    "iqr": float(q3 - q1),
                    "media_geometrica": float(np.exp(np.mean(logs))),
                }
            comp_blocos: dict[str, float | None] = {}
            if len(blocos) == 2 and len(arrays_raw) == 2 and arrays_raw[0].size >= 2 and arrays_raw[1].size >= 2:
                v1, v2 = arrays_raw
                l1, l2 = arrays_log
                if np.var(l1, ddof=1) == 0 and np.var(l2, ddof=1) == 0:
                    p_welch = None
                else:
                    p_welch = float(stats.ttest_ind(l2, l1, equal_var=False, alternative="two-sided").pvalue)
                sem_empates = np.unique(np.concatenate([v1, v2])).size == v1.size + v2.size
                p_mw = float(stats.mannwhitneyu(v2, v1, alternative="two-sided", method="exact" if sem_empates else "auto").pvalue)
                comp_blocos = {
                    "razao_b2_b1": float(np.exp(np.mean(l2) - np.mean(l1))),
                    "welch_log_p": p_welch,
                    "mann_whitney_p": p_mw,
                }
            por_broker[broker] = {"blocos": sub_b, "comparacao_blocos": comp_blocos}

        y = np.log(np.array([float(r[metrica]) for r in itens], dtype=float))
        colunas = [
            np.ones(len(itens), dtype=float),
            np.array([1.0 if r["broker"] == "kafka" else 0.0 for r in itens], dtype=float),
        ]
        for b in blocos[1:]:
            colunas.append(np.array([1.0 if r["bloco"] == b else 0.0 for r in itens], dtype=float))
        x_mat = np.column_stack(colunas)
        n_obs, p_cols = x_mat.shape
        df = n_obs - p_cols
        modelo_ajustado: dict = {"disponivel": False}
        if df > 0 and np.linalg.matrix_rank(x_mat) == p_cols:
            beta, _, _, _ = np.linalg.lstsq(x_mat, y, rcond=None)
            res = y - x_mat @ beta
            s2 = float((res @ res) / df)
            cov = s2 * np.linalg.inv(x_mat.T @ x_mat)
            razao_broker, ic_broker, p_broker = _estimar_coeficiente_ols(beta, cov, 1, df, s2)
            razao_bloco, ic_bloco, p_bloco = _estimar_coeficiente_ols(beta, cov, 2, df, s2)
            modelo_ajustado = {
                "disponivel": True,
                "blocos": blocos,
                "n_total": int(n_obs),
                "gl_residual": int(df),
                "razao_broker_ajustada": razao_broker,
                "ic95_razao_ajustada": ic_broker,
                "p_broker_ajustado": p_broker,
                "razao_bloco": razao_bloco,
                "ic95_razao_bloco": ic_bloco,
                "p_bloco": p_bloco,
                "efeito_bloco_significativo": bool(p_bloco < ALFA),
            }

        saida.append({
            "experimento": exp,
            "metrica": metrica,
            "tamanho_bytes": tam,
            "disponivel": True,
            "blocos": blocos,
            "por_broker": por_broker,
            "modelo_ajustado_bloco": modelo_ajustado,
        })
    return saida


def checar_sensibilidade_repeticoes(
    registros: list[dict],
    ids_repetidos: list[str],
    comparacoes_completas: dict,
    interacoes_completas: dict,
    repeticoes_boot: int = 5000,
    permutacoes: int = 5000,
) -> dict:
    if not ids_repetidos:
        return {
            "ha_repeticoes": False,
            "n_ids_repetidos": 0,
            "ids_repetidos": [],
            "altera_conclusao": False,
            "diferencas": {},
            "comparacoes_sem_repeticoes": None,
            "interacoes_sem_repeticoes": None,
        }

    excluir = set(ids_repetidos)
    registros_sem = [r for r in registros if r["id_execucao"] not in excluir]
    comp_sem, inter_sem = _executar_comparacoes_e_interacoes(registros_sem, repeticoes_boot, permutacoes)

    diferencas: dict[str, dict] = {}
    altera = False
    for chave, c_full in comparacoes_completas.items():
        c_sem = comp_sem.get(chave, {})
        disp_full = bool(c_full.get("disponivel"))
        disp_sem = bool(c_sem.get("disponivel"))
        if disp_full and disp_sem:
            sig_full = bool(c_full.get("p_recomendado_holm") is not None and c_full["p_recomendado_holm"] < ALFA)
            sig_sem = bool(c_sem.get("p_recomendado_holm") is not None and c_sem["p_recomendado_holm"] < ALFA)
            dir_full = c_full["razao_geometrica"] > 1.0
            dir_sem = c_sem["razao_geometrica"] > 1.0
            mudou_sig = sig_full != sig_sem
            mudou_dir = dir_full != dir_sem
            delta_razao_pct = float((c_sem["razao_geometrica"] / c_full["razao_geometrica"] - 1.0) * 100.0)
        else:
            mudou_sig = disp_full != disp_sem
            mudou_dir = False
            delta_razao_pct = None
        if mudou_sig or mudou_dir:
            altera = True
        diferencas[chave] = {
            "razao_completa": c_full.get("razao_geometrica"),
            "razao_sem_repeticoes": c_sem.get("razao_geometrica"),
            "delta_razao_pct": delta_razao_pct,
            "p_holm_completo": c_full.get("p_recomendado_holm"),
            "p_holm_sem_repeticoes": c_sem.get("p_recomendado_holm"),
            "mudou_significancia": mudou_sig,
            "mudou_direcao": mudou_dir,
        }

    return {
        "ha_repeticoes": True,
        "n_ids_repetidos": len(ids_repetidos),
        "ids_repetidos": list(ids_repetidos),
        "altera_conclusao": altera,
        "diferencas": diferencas,
        "comparacoes_sem_repeticoes": comp_sem,
        "interacoes_sem_repeticoes": inter_sem,
    }


def calcular_carga_relativa_e2(
    registros: list[dict],
    taxas_e2_manifesto: dict[int, int] | None = None,
) -> list[dict]:
    taxas_manifesto = taxas_e2_manifesto or {}
    saida: list[dict] = []
    for tam in (1024, 16384):
        for broker in ("kafka", "rabbitmq"):
            e1_vals = [
                r["throughput_msg_s"]
                for r in registros
                if r["experimento"] == "E1"
                and r["broker"] == broker
                and r["tamanho_bytes"] == tam
                and r.get("throughput_msg_s") is not None
                and r["throughput_msg_s"] > 0
            ]
            e2_rows = [
                r for r in registros
                if r["experimento"] == "E2"
                and r["broker"] == broker
                and r["tamanho_bytes"] == tam
            ]
            e2_vals = [r["throughput_msg_s"] for r in e2_rows if r.get("throughput_msg_s") is not None]
            alvos = [r["taxa_alvo_msg_s"] for r in e2_rows if r.get("taxa_alvo_msg_s") is not None]
            taxa_alvo = float(taxas_manifesto[tam]) if tam in taxas_manifesto else (float(np.median(alvos)) if alvos else None)
            e1_med = float(np.median(e1_vals)) if e1_vals else None
            e2_med = float(np.median(e2_vals)) if e2_vals else None
            saida.append({
                "broker": broker,
                "tamanho_bytes": tam,
                "taxa_alvo_e2_msg_s": taxa_alvo,
                "throughput_e1_mediano_msg_s": e1_med,
                "throughput_e2_mediano_msg_s": e2_med,
                "carga_relativa_alvo": float(taxa_alvo / e1_med) if taxa_alvo and e1_med else None,
                "carga_relativa_efetiva": float(e2_med / e1_med) if e2_med and e1_med else None,
            })
    return saida


def comparar_cv_protocolo(descritiva: list[dict]) -> list[dict]:
    indice = {
        (d["experimento"], d["metrica"], d["broker"], d["tamanho_bytes"]): d
        for d in descritiva
    }
    saida: list[dict] = []
    for exp, metrica, tam in COMPARACOES_PRINCIPAIS:
        for broker in ("kafka", "rabbitmq"):
            item = indice.get((exp, metrica, broker, tam))
            cv_obs = item["cv"] if item else None
            n_valido = item["n"] if item else 0
            if metrica == "throughput_msg_s":
                cv_prot = mod_poder.CVS_THROUGHPUT_OBSERVADOS.get((broker, tam))
                status_prot = "calculado" if cv_prot is not None else "cv_indisponivel"
            else:
                cv_prot = None
                status_prot = "cv_indisponivel"
            saida.append({
                "experimento": exp,
                "metrica": metrica,
                "broker": broker,
                "tamanho_bytes": tam,
                "n": int(n_valido),
                "cv_observado": cv_obs,
                "cv_protocolo_g1": cv_prot,
                "status_protocolo": status_prot,
                "diferenca_pp": float((cv_obs - cv_prot) * 100.0) if cv_obs is not None and cv_prot is not None else None,
                "atende_g1_20pct": (cv_obs <= 0.20) if (cv_obs is not None and metrica == "throughput_msg_s") else None,
            })
    return saida


def detectar_outliers(registros: list[dict]) -> list[dict]:
    outliers: list[dict] = []
    for exp, metrica, tam in COMPARACOES_PRINCIPAIS:
        for broker in ("kafka", "rabbitmq"):
            itens = [
                r for r in registros
                if r["experimento"] == exp
                and r["broker"] == broker
                and r["tamanho_bytes"] == tam
                and r.get(metrica) is not None
            ]
            if len(itens) < 4:
                continue
            vals = np.array([float(r[metrica]) for r in itens], dtype=float)
            q1, q3 = np.percentile(vals, [25, 75])
            iqr = float(q3 - q1)
            lim_inf = float(q1 - 1.5 * iqr)
            lim_sup = float(q3 + 1.5 * iqr)
            for r in itens:
                val = float(r[metrica])
                if val < lim_inf or val > lim_sup:
                    outliers.append({
                        "id_execucao": r["id_execucao"],
                        "experimento": exp,
                        "metrica": metrica,
                        "broker": broker,
                        "tamanho_bytes": tam,
                        "bloco": r.get("bloco") or None,
                        "ordem": int(r["ordem"]) if r.get("ordem") is not None else None,
                        "tentativa": int(r.get("tentativa") or 1),
                        "valor": val,
                        "limite_inferior": lim_inf,
                        "limite_superior": lim_sup,
                        "direcao": "baixo" if val < lim_inf else "alto",
                        "removido": False,
                    })
    return outliers


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
    validar_oficial: bool = False,
    caminho_protocolo: Path = PROTOCOLO_OFICIAL,
) -> dict:
    metadados = ler_metadados_coleta(
        caminho_csv.parent,
        validar_oficial=validar_oficial,
        caminho_protocolo=caminho_protocolo,
    )
    registros, contagens, ids_repetidos = carregar_tentativas(caminho_csv)
    descritiva = descrever_celulas(registros)
    comparacoes, interacoes = _executar_comparacoes_e_interacoes(
        registros, repeticoes_boot=repeticoes_boot, permutacoes=permutacoes
    )
    checagens = {
        "efeito_ordem": checar_efeito_ordem(registros),
        "efeito_bloco": checar_efeito_bloco(registros),
        "sensibilidade_repeticoes": checar_sensibilidade_repeticoes(
            registros,
            ids_repetidos,
            comparacoes,
            interacoes,
            repeticoes_boot=repeticoes_boot,
            permutacoes=permutacoes,
        ),
        "carga_relativa_e2": calcular_carga_relativa_e2(registros, metadados["taxas_e2"]),
        "comparacao_cv_protocolo": comparar_cv_protocolo(descritiva),
        "outliers": detectar_outliers(registros),
    }

    return {
        "arquivo": str(caminho_csv.relative_to(RAIZ)).replace("\\", "/") if caminho_csv.is_relative_to(RAIZ) else str(caminho_csv),
        "metadados_coleta": metadados,
        "contagens_status": contagens,
        "alfa": ALFA,
        "semente": SEMENTE,
        "descritiva": descritiva,
        "comparacoes": comparacoes,
        "interacoes": interacoes,
        "checagens": checagens,
        "poder_piloto": poder_piloto(descritiva, repeticoes=repeticoes_poder),
        "impacto_recursos": estimar_cpu_hora(registros),
    }


def _fmt(valor: float | None, casas: int = 3) -> str:
    if valor is None:
        return "—"
    return f"{valor:.{casas}f}".replace(".", ",")


def _fmt_p(valor: float | None) -> str:
    if valor is None:
        return "—"
    if valor < 1e-4:
        return f"{valor:.2e}".replace(".", ",")
    return f"{valor:.4f}".replace(".", ",")


def _fmt_pct(valor: float | None) -> str:
    if valor is None:
        return "—"
    return f"{valor * 100:.1f}%".replace(".", ",")


def gerar_resultados_md(resultado: dict) -> str:
    meta = resultado["metadados_coleta"]
    amb = meta["ambiente"]
    chec = resultado["checagens"]
    cv_mapa = {
        (c["experimento"], c["metrica"], c["broker"], c["tamanho_bytes"]): c
        for c in chec["comparacao_cv_protocolo"]
    }
    sens = chec["sensibilidade_repeticoes"]

    linhas = [
        "# Resultados Estatísticos — Lab05S02 (Papel C: Lorran)",
        "",
        f"- **Coleta:** `{meta['colecao_id']}` (`{resultado['arquivo']}`)",
        f"- **Portão G3:** {'aprovado' if meta['valido_g3'] else 'não exigido'}",
        f"- **Imagem OMB (timestamp ms):** `{meta['omb_imagem'] or 'não informada'}` "
        f"({'válida' if meta['omb_timestamp_ms_valido'] else 'divergente/antiga'})",
        f"- **Máquina única:** {'sim' if meta['maquina_unica'] else 'não confirmada'} "
        f"(`{amb.get('cpu') or 'não informada'}`)",
        f"- **Contagens por status:** `{resultado['contagens_status']}`",
        f"- **IDs com repetição técnica:** {sens['n_ids_repetidos']} "
        + (f"(`{', '.join(sens['ids_repetidos'])}`)" if sens["ids_repetidos"] else "(nenhum)"),
        "",
        "## 1. Estatística descritiva por célula",
        "",
        "| Exp | Métrica | Broker | Tam | n | Mediana | IQR | Média geom. | CV obs. | CV ref. (#207) |",
        "| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]

    desc_idx = {
        (d["experimento"], d["metrica"], d["broker"], d["tamanho_bytes"]): d
        for d in resultado["descritiva"]
    }
    for exp, metrica, tam in COMPARACOES_PRINCIPAIS:
        for broker in ("kafka", "rabbitmq"):
            d = desc_idx.get((exp, metrica, broker, tam))
            if not d:
                continue
            cv_ref = cv_mapa[(exp, metrica, broker, tam)]["cv_protocolo_g1"]
            linhas.append(
                f"| {exp} | `{metrica}` | {broker} | {tam // 1024} KiB | {d['n']} | "
                f"{_fmt(d['mediana'], 2)} | {_fmt(d['iqr'], 2)} | {_fmt(d['media_geometrica'], 2)} | "
                f"{_fmt_pct(d['cv'])} | {_fmt_pct(cv_ref)} |"
            )

    secundarias = [
        d for d in resultado["descritiva"]
        if d["metrica"] in ("throughput_consumo_msg_s", "cpu_percent_medio", "memoria_mib_media")
    ]
    if secundarias:
        linhas.extend([
            "",
            "### Métricas complementares (`throughput_consumo_msg_s` e recursos M4)",
            "",
            "| Exp | Métrica | Broker | Tam | n | Mediana | IQR | CV obs. |",
            "| --- | --- | --- | ---: | ---: | ---: | ---: | ---: |",
        ])
        for d in secundarias:
            linhas.append(
                f"| {d['experimento']} | `{d['metrica']}` | {d['broker']} | {d['tamanho_bytes'] // 1024} KiB | "
                f"{d['n']} | {_fmt(d['mediana'], 2)} | {_fmt(d['iqr'], 2)} | {_fmt_pct(d['cv'])} |"
            )

    linhas.extend([
        "",
        "## 2. Testes confirmatórios (H1 e H2, correção de Holm)",
        "",
        "| Comparação | Shapiro log (K / R) | Teste recomendado | Welch p | MW p | p Holm (rec.) |",
        "| --- | :---: | --- | ---: | ---: | ---: |",
    ])
    for chave, c in resultado["comparacoes"].items():
        rotulo = ROTULOS_COMPARACAO.get(chave, chave)
        if not c["disponivel"]:
            linhas.append(f"| {rotulo} | — | indisponível | — | — | — |")
            continue
        sh = f"{_fmt_p(c['shapiro_log_kafka_p'])} / {_fmt_p(c['shapiro_log_rabbitmq_p'])}"
        linhas.append(
            f"| {rotulo} | {sh} | `{c['teste_recomendado']}` | "
            f"{_fmt_p(c['welch_p'])} | {_fmt_p(c['mann_whitney_p'])} | {_fmt_p(c['p_recomendado_holm'])} |"
        )

    linhas.extend([
        "",
        "## 3. Interação broker × tamanho (H3)",
        "",
        "| Experimento | Contraste log | Razão das razões | ANOVA F | ANOVA p | Permutação p |",
        "| --- | ---: | ---: | ---: | ---: | ---: |",
    ])
    for chave, inter in resultado["interacoes"].items():
        if not inter["disponivel"]:
            linhas.append(f"| `{chave}` | — | — | — | — | — |")
            continue
        linhas.append(
            f"| `{chave}` | {_fmt(inter['contraste_log'], 4)} | {_fmt(inter['razao_das_razoes'], 3)} | "
            f"{_fmt(inter['anova_f'], 3)} | {_fmt_p(inter['anova_p'])} | {_fmt_p(inter['permutacao_p'])} |"
        )

    linhas.extend([
        "",
        "## 4. Tamanho do efeito e incerteza (Kafka / RabbitMQ)",
        "",
        "> **Nota:** os efeitos são interpretados pela magnitude e pelo intervalo de confiança; "
        "não rejeitar H₀ não significa igualdade entre os brokers.",
        "",
        "| Comparação | Razão geométrica | IC 95% (bootstrap, semente 42) | δ de Cliff | Magnitude (Romano) |",
        "| --- | ---: | :---: | ---: | --- |",
    ])
    for chave, c in resultado["comparacoes"].items():
        rotulo = ROTULOS_COMPARACAO.get(chave, chave)
        if not c["disponivel"]:
            linhas.append(f"| {rotulo} | — | — | — | — |")
            continue
        inf, sup = c["ic95_bootstrap"]
        delta_txt = f"{c['cliff_delta']:+.3f}".replace(".", ",")
        linhas.append(
            f"| {rotulo} | {_fmt(c['razao_geometrica'], 3)} | [{_fmt(inf, 3)}; {_fmt(sup, 3)}] | "
            f"{delta_txt} | {c['cliff_magnitude']} |"
        )

    linhas.extend([
        "",
        "## 5. Checagens de validade (alimentam `metodo.md` §4.2)",
        "",
        "### 5.1 Efeito de ordem (regressão do log na posição)",
        "",
        "| Exp | Métrica | Broker | Tam | n | Inclinação log | IC 95% contém 0? | p-valor |",
        "| --- | --- | --- | ---: | ---: | ---: | :---: | ---: |",
    ])
    for o in chec["efeito_ordem"]:
        if not o["disponivel"]:
            linhas.append(f"| {o['experimento']} | `{o['metrica']}` | {o['broker']} | {o['tamanho_bytes'] // 1024} KiB | {o['n']} | — | — | — |")
            continue
        contem = "sim" if o["ic95_contem_zero"] else "não"
        linhas.append(
            f"| {o['experimento']} | `{o['metrica']}` | {o['broker']} | {o['tamanho_bytes'] // 1024} KiB | "
            f"{o['n']} | {_fmt(o['inclinacao_log'], 5)} | {contem} | {_fmt_p(o['p_valor'])} |"
        )

    linhas.extend([
        "",
        "### 5.2 Efeito de bloco",
        "",
        "| Exp | Métrica | Tam | Razão broker ajustada | IC 95% ajustado | p bloco | Significativo? |",
        "| --- | --- | ---: | ---: | :---: | ---: | :---: |",
    ])
    for b in chec["efeito_bloco"]:
        if not b["disponivel"] or not b["modelo_ajustado_bloco"]["disponivel"]:
            linhas.append(f"| {b['experimento']} | `{b['metrica']}` | {b['tamanho_bytes'] // 1024} KiB | — | — | — | indisponível |")
            continue
        mod = b["modelo_ajustado_bloco"]
        ic_a = mod["ic95_razao_ajustada"]
        linhas.append(
            f"| {b['experimento']} | `{b['metrica']}` | {b['tamanho_bytes'] // 1024} KiB | "
            f"{_fmt(mod['razao_broker_ajustada'], 3)} | [{_fmt(ic_a[0], 3)}; {_fmt(ic_a[1], 3)}] | "
            f"{_fmt_p(mod['p_bloco'])} | {'sim' if mod['efeito_bloco_significativo'] else 'não'} |"
        )

    linhas.extend([
        "",
        "### 5.3 Carga relativa no E2 (taxa ÷ capacidade mediana no E1)",
        "",
        "| Broker | Tam | Taxa alvo E2 (msg/s) | Mediana E1 (msg/s) | Carga relativa (alvo / efetiva) |",
        "| --- | ---: | ---: | ---: | :---: |",
    ])
    for cr in chec["carga_relativa_e2"]:
        linhas.append(
            f"| {cr['broker']} | {cr['tamanho_bytes'] // 1024} KiB | {_fmt(cr['taxa_alvo_e2_msg_s'], 0)} | "
            f"{_fmt(cr['throughput_e1_mediano_msg_s'], 1)} | "
            f"{_fmt_pct(cr['carga_relativa_alvo'])} / {_fmt_pct(cr['carga_relativa_efetiva'])} |"
        )

    linhas.extend([
        "",
        "### 5.4 Sensibilidade às repetições e outliers preservados",
        "",
        f"- **Sensibilidade às repetições:** "
        + (
            f"{sens['n_ids_repetidos']} ID(s) repetido(s); altera conclusão (significância ou direção)? **{'sim' if sens['altera_conclusao'] else 'não'}**."
            if sens["ha_repeticoes"]
            else "nenhuma execução precisou de repetição."
        ),
        f"- **Outliers extremos (1,5 × IQR, nunca removidos):** {len(chec['outliers'])} ocorrência(s) registrada(s).",
    ])
    for out in chec["outliers"]:
        linhas.append(
            f"  - `{out['id_execucao']}` ({out['experimento']} {out['broker']} {out['tamanho_bytes'] // 1024} KiB): "
            f"`{out['metrica']} = {_fmt(out['valor'], 2)}` ({out['direcao']}, preservado na amostra)."
        )

    linhas.extend([
        "",
        "## 6. Reprodutibilidade",
        "",
        "```powershell",
        "python Lab05/analisar.py --oficial",
        "python -m pytest Lab05/tests -q",
        "```",
        "",
    ])
    return "\n".join(linhas)


def main() -> int:
    parser = argparse.ArgumentParser(description="Análise estatística e de impacto do Lab05")
    parser.add_argument("--entrada", type=Path, default=None, help="caminho para resultados.csv")
    parser.add_argument("--coleta", type=Path, default=None, help="diretório da coleta oficial")
    parser.add_argument("--oficial", action="store_true", help="valida portão G3 e analisa a coleta oficial")
    parser.add_argument("--saida", type=Path, default=None, help="opcional: salva o JSON completo")
    parser.add_argument("--relatorio", type=Path, default=None, help="opcional: salva o relatório Markdown")
    args = parser.parse_args()

    try:
        if args.oficial:
            if args.coleta:
                entrada = args.coleta.resolve() / "resultados.csv"
            elif args.entrada:
                entrada = args.entrada.resolve()
            else:
                entrada = coleta_oficial_mais_recente()
            saida = args.saida or (RAIZ / "data" / "analise" / "oficial_resumo.json")
            relatorio = args.relatorio or (RAIZ / "docs" / "resultados.md")
        else:
            entrada = args.entrada.resolve() if args.entrada else piloto_mais_recente()
            saida = args.saida
            relatorio = args.relatorio

        resultado = analisar(entrada, validar_oficial=args.oficial)
    except (FileNotFoundError, ValueError) as exc:
        print(f"ERRO: {exc}", file=sys.stderr)
        return 1

    if saida:
        saida.parent.mkdir(parents=True, exist_ok=True)
        saida.write_text(
            json.dumps(resultado, ensure_ascii=False, indent=2, allow_nan=False) + "\n",
            encoding="utf-8",
        )
    if relatorio:
        relatorio.parent.mkdir(parents=True, exist_ok=True)
        relatorio.write_text(gerar_resultados_md(resultado), encoding="utf-8")

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
