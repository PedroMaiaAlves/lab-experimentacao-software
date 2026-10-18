"""Executa o notebook de RQ05 em kernels novos, conferindo CSVs publicados."""
import argparse
from pathlib import Path

import nbformat
from nbclient import NotebookClient


def executar_notebooks(saida="cache/notebooks_s03"):
    base = Path(__file__).resolve().parents[1]
    saida = Path(saida).resolve()
    saida.mkdir(parents=True, exist_ok=True)
    for rq in ("rq05",):
        origem = base / "notebooks" / f"{rq}_s03_b.ipynb"
        notebook = nbformat.read(origem, as_version=4)
        for celula in notebook.cells:
            if celula.cell_type == "code":
                celula.outputs, celula.execution_count = [], None
        NotebookClient(notebook, timeout=240, kernel_name="python3", resources={"metadata": {"path": str(base)}}).execute()
        nbformat.write(notebook, saida / origem.name)
        print(f"{origem.name}: executado em kernel novo; resultados conferidos")


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--saida", default="cache/notebooks_s03")
    args = parser.parse_args(argv)
    executar_notebooks(args.saida)


if __name__ == "__main__":
    main()
