"""CLI da coleta piloto do Lab05."""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict
from pathlib import Path

RAIZ = Path(__file__).resolve().parent
sys.path.insert(0, str(RAIZ))

from experimento import plano  # noqa: E402
from experimento.coleta import Coletor, DockerExecutor, criar_diretorio_coleta  # noqa: E402


def argumentos() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Coleta reproduzível Kafka × RabbitMQ")
    parser.add_argument("--piloto", action="store_true", help="executa 3 repetições por célula em E1 e E2")
    parser.add_argument("--saida", type=Path, default=RAIZ / "data" / "piloto", help="raiz das coletas")
    parser.add_argument("--dry-run", action="store_true", help="mostra as 24 execuções sem usar Docker")
    return parser.parse_args()


def main() -> int:
    args = argumentos()
    if not args.piloto:
        print("Use --piloto para confirmar a coleta completa.", file=sys.stderr)
        return 2
    if args.dry_run:
        execucoes = plano.gerar_plano("E1", 3) + plano.gerar_plano("E2", 3)
        print(json.dumps([asdict(e) for e in execucoes], ensure_ascii=False, indent=2))
        return 0

    diretorio = criar_diretorio_coleta(args.saida)
    print(f"Coleta: {diretorio}", flush=True)
    resultados = Coletor(diretorio, DockerExecutor(diretorio)).piloto()
    sucessos = sum(r.status == "sucesso" for r in resultados)
    falhas = len(resultados) - sucessos
    print(f"Finalizada: {len(resultados)} registros, {sucessos} sucessos, {falhas} falhas/bloqueios")
    return 0 if falhas == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
