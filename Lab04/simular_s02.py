"""Executa ou valida a simulação oficial de Q1 da Lab04S02."""

from __future__ import annotations

import argparse
import json

from experimento.dados import ROOT
from experimento.monte_carlo import salvar_q1, validar_q1


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--validar", action="store_true", help="Regenera Q1 em memória e confere os artefatos.")
    args = parser.parse_args()
    if args.validar:
        resultado = validar_q1()
    else:
        manifesto = salvar_q1()
        resultado = {
            "status": "gerado",
            "pergunta": manifesto["pergunta"],
            "saida": str((ROOT / "data/s02").resolve()),
            "configuracao": manifesto["configuracao"],
        }
    print(json.dumps(resultado, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
