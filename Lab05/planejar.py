"""Gera o plano de execuções randomizado e a tabela de poder a priori (issue #197).

Uso: python Lab05/planejar.py
Saídas:
  Lab05/data/plano/plano_E1.csv e plano_E2.csv  — ordem das execuções (semente 42)
  Lab05/data/plano/poder_a_priori.csv          — poder por n, razão e CV
"""

from __future__ import annotations

import csv
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent
sys.path.insert(0, str(RAIZ))

from experimento import plano, poder  # noqa: E402

SAIDA = RAIZ / "data" / "plano"


def main() -> None:
    for exp in plano.EXPERIMENTOS:
        execs = plano.gerar_plano(exp)
        destino = plano.salvar_plano(execs, SAIDA / f"plano_{exp}.csv")
        print(f"{exp}: {len(execs)} execuções -> {destino.relative_to(RAIZ)}")

    linhas = poder.tabela()
    destino = SAIDA / "poder_a_priori.csv"
    with destino.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(linhas[0].keys()))
        w.writeheader()
        w.writerows(linhas)
    print(f"poder -> {destino.relative_to(RAIZ)} (alfa efetivo {poder.ALFA_HOLM_PIOR_CASO})")

    print("\nMenor n por célula para poder >= 80% (Mann-Whitney | Welch-log):")
    print("  CV    " + "  ".join(f"r={r:<5}" for r in (1.05, 1.10, 1.20, 1.50)))
    for cv in (0.05, 0.10, 0.20):
        cel = []
        for r in (1.05, 1.10, 1.20, 1.50):
            mw = poder.menor_n(linhas, cv, r, teste="mann_whitney")
            we = poder.menor_n(linhas, cv, r, teste="welch_log")
            cel.append(f"{mw or '>20'}|{we or '>20'}".ljust(7))

        print(f"  {cv:<5} " + "  ".join(cel))


if __name__ == "__main__":
    main()
