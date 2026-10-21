"""Rework rate do enunciado: releases corretivas / releases principais na janela."""


def calcular_rework_rate(releases):
    flags = [r["corretiva"] for r in releases if not r.get("draft") and not r.get("prerelease")]
    if any(f is not None and type(f) is not bool for f in flags):
        raise ValueError("corretiva deve ser True, False ou None (evidência insuficiente)")
    total, corretivas, ausentes = len(flags), sum(f is True for f in flags), sum(f is None for f in flags)
    return {"releases_total": total, "releases_corretivas": corretivas,
            "releases_sem_evidencia": ausentes,
            "rework_rate": corretivas / total if total and not ausentes else None,
            "rework_limite_inferior": corretivas / total if total else None,
            "rework_limite_superior": (corretivas + ausentes) / total if total else None}
