"""Mostra o t pareado e o Wilcoxon na amostra simulada preservada, sem gravar arquivos."""

from experimento.analise import analisar_pares
from experimento.dados import ROOT, ler_pares

if __name__ == "__main__":
    pares = ler_pares(ROOT / "data/simulado/pares_simulados.csv")
    print(f"Amostra SIMULADA (data/simulado/pares_simulados.csv): {len(pares)} pares\n")
    for chave, r in analisar_pares(pares).items():
        print(f"== {chave} ==")
        for campo in ("metodo", "estatistica", "p_valor", "n_pares", "alpha", "alternativa", "decisao"):
            print(f"  {campo}: {r[campo]}")
        print(f"  H0: {r['hipoteses']['H0']}\n  H1: {r['hipoteses']['H1']}")
        print(f"  interpretacao: {r['interpretacao']}\n")
