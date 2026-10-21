"""Gera e executa o notebook reprodutível da RQ08 em um kernel novo."""
import argparse
from pathlib import Path

import nbformat
from nbclient import NotebookClient


def executar_notebook(atualizar=False):
    base = Path(__file__).resolve().parents[1]
    notebook = nbformat.v4.new_notebook(cells=[
        nbformat.v4.new_markdown_cell(
            "# RQ08 — Rework rate\n"
            "Reprodução offline da definição da RQ03 (b), sem nova mineração. "
            "Cada projeto tem o mesmo peso; a sensibilidade de evidência completa é separada. "
            "Releases não comprovam implantações em produção."),
        nbformat.v4.new_code_cell(
            "from pathlib import Path\nimport pandas as pd\nfrom pandas.testing import assert_frame_equal\n"
            "from analises.sprint3_c import executar\n\n"
            "tabelas = executar(saida='cache/rq08_notebook')\n"
            "for nome, tabela in tabelas.items():\n"
            "    gerada = pd.read_csv(Path('cache/rq08_notebook') / f'{nome}.csv')\n"
            "    publicada = pd.read_csv(Path('results/s03_c') / f'{nome}.csv')\n"
            "    assert_frame_equal(gerada, publicada, check_exact=True)\n"
            "print('As cinco tabelas reproduzem exatamente os CSVs publicados.')"),
        nbformat.v4.new_code_cell("tabelas['rq08_resumo']"),
        nbformat.v4.new_code_cell("tabelas['rq08_cobertura'].T"),
        nbformat.v4.new_markdown_cell(
            "## Interpretação\n"
            "Rework conta a própria release corretiva; CFR (b) conta releases anteriores "
            "seguidas de corretiva em até sete dias. Só CFR (b) censura os últimos sete dias. "
            "Os limites conservadores não são intervalos de confiança. "
            "Definições e limitações: `docs/entrega_s03_c.md`."),
    ], metadata={"kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"}})
    for i, celula in enumerate(notebook.cells):
        celula.id = f"rq08-c-{i}"
    NotebookClient(notebook, timeout=600, kernel_name="python3", record_timing=False,
                   resources={"metadata": {"path": str(base)}}).execute()
    destino = base / ("notebooks/rq08_s03_c.ipynb" if atualizar else "cache/notebooks_s03/rq08_s03_c.ipynb")
    destino.parent.mkdir(parents=True, exist_ok=True)
    nbformat.write(notebook, destino)
    print("rq08_s03_c.ipynb: executado em kernel novo; cinco CSVs conferidos")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--atualizar", action="store_true", help="publica o notebook com as saídas conferidas")
    executar_notebook(**vars(parser.parse_args()))
