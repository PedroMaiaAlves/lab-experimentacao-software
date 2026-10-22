"""Gera e executa os notebooks reprodutíveis das RQ07/RQ08 em kernels novos."""
import argparse
from pathlib import Path

import nbformat
from nbclient import NotebookClient


def criar_notebook(rq):
    titulo = "Sensibilidade das classificações" if rq == "rq07" else "Rework rate"
    tabelas = ("rq07_concordancia", "rq07_robustez_rq05", "rq07_robustez_rq06") if rq == "rq07" else (
        "rq08_resumo", "rq08_cobertura")
    notebook = nbformat.v4.new_notebook(cells=[
        nbformat.v4.new_markdown_cell(f"# {rq.upper()} — {titulo}\n"
            "Reprodução offline sobre as fontes congeladas. Ausências não viram zero. "
            "Definições, combinações e limitações: `docs/entrega_s03_c.md`."),
        nbformat.v4.new_code_cell(
            "from pathlib import Path\nimport pandas as pd\nfrom pandas.testing import assert_frame_equal\n"
            "from analises.sprint3_c import executar\n\n"
            f"destino = Path('cache/{rq}_notebook')\n"
            "tabelas = executar(saida=destino)\n"
            "for nome in tabelas:\n"
            "    gerada = pd.read_csv(destino / f'{nome}.csv')\n"
            "    publicada = pd.read_csv(Path('results/s03_c') / f'{nome}.csv')\n"
            "    assert_frame_equal(gerada, publicada, check_exact=True)\n"
            "print(f'{len(tabelas)} tabelas reproduzem exatamente os CSVs publicados.')"),
        *[nbformat.v4.new_code_cell(f"tabelas['{nome}']") for nome in tabelas],
    ], metadata={"kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"}})
    for i, celula in enumerate(notebook.cells):
        celula.id = f"{rq}-c-{i}"
    return notebook


def executar_notebook(atualizar=False):
    base = Path(__file__).resolve().parents[1]
    for rq in ("rq07", "rq08"):
        notebook = criar_notebook(rq)
        NotebookClient(notebook, timeout=600, kernel_name="python3", record_timing=False,
                       resources={"metadata": {"path": str(base)}}).execute()
        destino = base / ("notebooks" if atualizar else "cache/notebooks_s03") / f"{rq}_s03_c.ipynb"
        destino.parent.mkdir(parents=True, exist_ok=True)
        nbformat.write(notebook, destino)
        print(f"{destino.name}: executado em kernel novo; 13 CSVs conferidos")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--atualizar", action="store_true", help="publica o notebook com as saídas conferidas")
    executar_notebook(**vars(parser.parse_args()))
