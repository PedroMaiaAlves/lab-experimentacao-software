"""Executa os notebooks da parte A em kernels novos; cada um confere os CSVs publicados."""
import argparse
from pathlib import Path

import nbformat
from nbclient import NotebookClient

NOTEBOOKS = ("rq01_04_s03_a.ipynb", "classificacao_c1_s03_a.ipynb")


def executar_notebooks(saida="cache/notebooks_s03", atualizar=False):
    base = Path(__file__).resolve().parents[1]
    saida = Path(saida).resolve()
    saida.mkdir(parents=True, exist_ok=True)
    for nome in NOTEBOOKS:
        origem = base / "notebooks" / nome
        notebook = nbformat.read(origem, as_version=4)
        for celula in notebook.cells:
            if celula.cell_type == "code":
                celula.outputs, celula.execution_count = [], None
        # Sem horários de execução nos metadados: o notebook só muda quando o resultado muda.
        NotebookClient(notebook, timeout=300, kernel_name="python3", record_timing=False,
                       resources={"metadata": {"path": str(base)}}).execute()
        # A versão apresentada em notebooks/ só é sobrescrita quando pedido.
        nbformat.write(notebook, origem if atualizar else saida / nome)
        print(f"{nome}: executado em kernel novo; resultados conferidos")


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--saida", default="cache/notebooks_s03")
    parser.add_argument("--atualizar", action="store_true",
                        help="grava as saídas no próprio notebook em notebooks/")
    args = parser.parse_args(argv)
    executar_notebooks(args.saida, args.atualizar)


if __name__ == "__main__":
    main()
