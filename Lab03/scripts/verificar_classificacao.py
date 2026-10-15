import csv
from pathlib import Path
import sys

if sys.stdout.encoding.lower() != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8")

counts = {}
for name in ["tipos_A.csv", "tipos_B.csv", "tipos_C.csv"]:
    with open(Path("data/classificacao_complementar") / name, encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    for r in rows:
        cat = r["tipo_projeto"]
        counts[cat] = counts.get(cat, 0) + 1

print("Contagens finais da classificacao complementar:", counts)
print("Total itens verificados:", sum(counts.values()))
