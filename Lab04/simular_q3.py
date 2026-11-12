"""Gera, reproduz ou confere Q3 contra chamadas individuais do SciPy."""

import argparse
import json

from experimento.q3 import salvar_conferencia, salvar_q3, validar_q3


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    grupo = parser.add_mutually_exclusive_group()
    grupo.add_argument("--validar", action="store_true", help="Regenera em memória e valida hashes e bytes.")
    grupo.add_argument("--scipy", action="store_true", help="Confere e registra as 140.000 decisões individuais.")
    args = parser.parse_args()
    resultado = validar_q3() if args.validar else salvar_conferencia() if args.scipy else salvar_q3()
    print(json.dumps(resultado, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
