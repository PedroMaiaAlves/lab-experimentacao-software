"""Valida e interpreta Q2: regeneração idêntica, conferência com SciPy e texto do dashboard."""

from __future__ import annotations

import argparse
import json

from experimento.dados import ROOT, ler_json
from experimento.q2_interpretacao import conferir_scipy, salvar_interpretacao, validar_interpretacao


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--validar", action="store_true", help="Confere a interpretação preservada.")
    parser.add_argument("--scipy", action="store_true",
                        help="Refaz as 140.000 decisões com chamadas individuais ao SciPy (cerca de 1 min).")
    args = parser.parse_args()
    if args.scipy:
        conferencia = conferir_scipy(ler_json(ROOT / "data/simulado/parametros.json"))
        total = sum(c["divergencias_t"] + c["divergencias_wilcoxon"] for c in conferencia)
        resultado = {"status": "ok" if total == 0 else "divergente", "divergencias": total, "por_razao": conferencia}
    elif args.validar:
        resultado = validar_interpretacao()
    else:
        resultado = salvar_interpretacao()
    print(json.dumps(resultado, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
