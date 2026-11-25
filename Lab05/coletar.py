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
from experimento.coleta import Coletor, DockerExecutor, criar_diretorio_coleta, execucoes_a_repetir, sem_suspensao  # noqa: E402


def argumentos() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Coleta reproduzível Kafka × RabbitMQ")
    parser.add_argument("--piloto", action="store_true", help="executa 3 repetições por célula em E1 e E2")
    parser.add_argument(
        "--mini-piloto-e1", type=int, metavar="N", default=None,
        help="só E1 com taxa aberta, N repetições por célula (portão G1, #209)",
    )
    parser.add_argument(
        "--medicao-s", type=int, default=None,
        help="só com --mini-piloto-e1: duração medida por execução (padrão: plano)",
    )
    parser.add_argument(
        "--repetir-falhas", type=Path, metavar="COLETA", default=None,
        help="repete (numa coleta nova) as execuções de E1 que falharam na COLETA indicada",
    )
    parser.add_argument("--saida", type=Path, default=RAIZ / "data" / "piloto", help="raiz das coletas")
    parser.add_argument("--dry-run", action="store_true", help="mostra as 24 execuções sem usar Docker")
    return parser.parse_args()


def main() -> int:
    args = argumentos()
    if args.repetir_falhas is not None:
        origem = args.repetir_falhas.resolve()
        execucoes = execucoes_a_repetir(origem / "resultados.csv")
        print("Repetir:", ", ".join(e.id_execucao for e in execucoes) or "nada", flush=True)
        if args.dry_run or not execucoes:
            return 0
        diretorio = criar_diretorio_coleta(origem.parent)
        print(f"Repetição: {diretorio}", flush=True)
        resultados = Coletor(diretorio, DockerExecutor(diretorio)).repetir(execucoes, origem.name)
        falhas = sum(r.status != "sucesso" for r in resultados)
        print(f"Finalizada: {len(resultados)} registros, {falhas} falhas")
        return 0 if falhas == 0 else 1
    if args.mini_piloto_e1 is not None:
        if args.dry_run:
            print(json.dumps([asdict(e) for e in plano.gerar_plano("E1", args.mini_piloto_e1)], ensure_ascii=False, indent=2))
            return 0
        # Pasta própria: não confundir com os pilotos completos lidos pelo analisar.py.
        saida = args.saida if args.saida != RAIZ / "data" / "piloto" else RAIZ / "data" / "piloto_g1"
        diretorio = criar_diretorio_coleta(saida)
        print(f"Mini-piloto E1: {diretorio}", flush=True)
        resultados = Coletor(diretorio, DockerExecutor(diretorio)).mini_piloto_e1(args.mini_piloto_e1, args.medicao_s)
        falhas = sum(r.status != "sucesso" for r in resultados)
        print(f"Finalizada: {len(resultados)} registros, {falhas} falhas")
        print(f"Verifique o portão: python Lab05/portao_g1.py {diretorio / 'resultados.csv'}")
        return 0 if falhas == 0 else 1
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
    with sem_suspensao():
        raise SystemExit(main())
