import csv
from contextlib import contextmanager
from pathlib import Path


@contextmanager
def abrir_csv(caminho, campos):
    caminho = Path(caminho)
    caminho.parent.mkdir(parents=True, exist_ok=True)
    with caminho.open("w", newline="", encoding="utf-8") as arquivo:
        writer = csv.DictWriter(arquivo, fieldnames=campos)
        writer.writeheader()
        yield writer
