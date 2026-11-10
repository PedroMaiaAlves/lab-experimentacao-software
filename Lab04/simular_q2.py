"""Executa ou valida a simulação oficial de Q2 da Lab04S02."""

from __future__ import annotations

import argparse
import json

from experimento.dados import ROOT
from experimento.q2 import salvar_q2, validar_q2


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--validar", action="store_true", help="Regenera Q2 em memória e confere os artefatos.")
    args = parser.parse_args()
    if args.validar:
        resultado = validar_q2()
    else:
        manifesto = salvar_q2()
        resultado = {
            "status": "gerado",
            "pergunta": manifesto["pergunta"],
            "saida": str((ROOT / "data/s02").resolve()),
            "configuracao": manifesto["configuracao"],
        }
    print(json.dumps(resultado, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
