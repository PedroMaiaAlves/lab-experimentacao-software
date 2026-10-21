"""Comando único e offline: python -m analises.sprint3_b."""
import argparse
import importlib.metadata
import json
import platform
from pathlib import Path

import pandas as pd

from analises import rq05, rq06
from analises.artefatos import dispersao, efeitos, gerar_tabelas, salvar_figura
from analises.comum import METRICAS, carregar_dataset, descrever, motivo_ausencia, sha256


def executar(dataset="data/dataset.csv", saida="results/s03_b", amostra=None, semente=42, reamostragens=9999):
    df, origens = carregar_dataset(dataset, amostra)
    saida = Path(saida).resolve()
    fontes = Path(dataset).resolve().parent
    # Nunca escrever artefatos de análise na árvore de dados congelados.
    if saida == fontes or saida.is_relative_to(fontes) or fontes.is_relative_to(saida):
        raise ValueError("saída deve ser separada da árvore das fontes")
    a, b = rq05.analisar(df, semente, reamostragens), rq06.analisar(df)
    tabelas = {k: v for grupo in (a, b) for k, v in grupo.items() if isinstance(v, pd.DataFrame) and k != "exclusoes"}
    tabelas["exclusoes"] = pd.concat([a["exclusoes"], b["exclusoes"]], ignore_index=True)
    tabelas["cobertura"] = pd.DataFrame([
        dict(metrica=m, unidade=METRICAS[m][1], n_total=len(df), n_ausentes=int(df[m].isna().sum()),
             **descrever(df[m])) for m in METRICAS])
    tabelas["ausencias"] = pd.DataFrame([
        dict(full_name=r.full_name, metrica=m, motivo=motivo_ausencia(r, m))
        for _, r in df.iterrows() for m in METRICAS if pd.isna(r[m])],
        columns=["full_name", "metrica", "motivo"])
    saida.mkdir(parents=True, exist_ok=True)
    for nome, tabela in tabelas.items():
        tabela.to_csv(saida / f"{nome}.csv", index=False, float_format="%.17g", lineterminator="\n")
    (saida / "grupos_definicao.json").write_text(json.dumps(b["grupos_definicao"], ensure_ascii=False, indent=2)+"\n", encoding="utf-8", newline="\n")
    salvar_figura(dispersao(df, a["rq05_correlacoes"]), saida / "rq05_dispersao")
    salvar_figura(efeitos(b["rq06_testes"]), saida / "rq06_efeitos")
    gerar_tabelas(a["rq05_correlacoes"], b["rq06_testes"], saida)
    pacotes = ("numpy", "pandas", "scipy", "statsmodels", "matplotlib", "nbformat", "nbclient", "ipykernel")
    manifesto = {
        "origens": origens, "parametros": {"semente": semente, "reamostragens": reamostragens, "alpha": .05,
            "bootstrap": "BCa pareado; IC95%; batch=256", "permutacao": "pairings bilateral; batch=256",
            "familia_rq05": "2 p-valores por permutação", "familia_rq06": "18 fator x métrica",
            "minimo_por_grupo": 5, "fatores": list(rq06.FATORES), "metricas": list(METRICAS)},
        "ambiente": {"python": platform.python_version(), "sistema": platform.system(),
                     "pacotes": {p: importlib.metadata.version(p) for p in pacotes}},
        "codigo_sha256": {p.name: sha256(p) for p in sorted(Path(__file__).parent.glob("*.py"))},
        "artefatos_sha256": {p.name: sha256(p) for p in sorted(saida.iterdir())
                             if p.is_file() and p.suffix in {".csv", ".tex", ".png", ".pdf", ".json"} and p.name != "manifesto.json"},
    }
    (saida / "manifesto.json").write_text(json.dumps(manifesto, ensure_ascii=False, indent=2)+"\n", encoding="utf-8", newline="\n")
    return tabelas


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset", default="data/dataset.csv")
    parser.add_argument("--amostra")
    parser.add_argument("--saida", default="results/s03_b")
    parser.add_argument("--semente", type=int, default=42)
    parser.add_argument("--reamostragens", type=int, default=9999)
    args = parser.parse_args(argv)
    tabelas = executar(**vars(args))
    print(tabelas["rq05_correlacoes"][["variante", "n", "rho", "p_spearman", "p_permutacao_holm"]].to_string(index=False))
    print(f"RQ06: {len(tabelas['rq06_testes'])} comparações; artefatos em {args.saida}")


if __name__ == "__main__":
    main()
