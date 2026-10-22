"""Confere a integração S03; --reproduzir recalcula A/B/C fora dos dados congelados."""
import argparse
import hashlib
import json
from pathlib import Path

import pandas as pd
from pandas.testing import assert_frame_equal
from pypdf import PdfReader

from analises.entrada import carregar_dataset, ler_json, sha256
from validacao.dicionario import verificar

BASE = Path(__file__).resolve().parents[1]


def conferir_manifesto(parte, base=BASE):
    saida = base / "results" / f"s03_{parte}"
    manifesto = ler_json(saida / "manifesto.json")
    for nome, esperado in manifesto["artefatos_sha256"].items():
        if sha256(saida / nome) != esperado:
            raise ValueError(f"artefato divergente: {parte}/{nome}")
    for nome, esperado in manifesto["codigo_sha256"].items():
        caminho = base / nome if parte == "c" else base / "analises" / nome
        obtido = (hashlib.sha256(caminho.read_text(encoding="utf-8").encode()).hexdigest()
                  if parte == "c" else sha256(caminho))
        if obtido != esperado:
            raise ValueError(f"código mudou depois da geração: {parte}/{nome}")
    for nome, esperado in manifesto.get("artefatos_fora_da_saida_sha256", {}).items():
        if sha256(base / "data" / nome) != esperado:
            raise ValueError(f"artefato externo divergente: {nome}")
    for nome, chave in (("dataset.csv", "dataset_sha256"), ("amostra_final.csv", "amostra_sha256")):
        if sha256(base / "data" / nome) != manifesto["origens"][chave]:
            raise ValueError(f"fonte divergente: {parte}/{nome}")
    return manifesto


def conferir_pdf(caminho):
    leitor = PdfReader(caminho)
    if not 1 <= len(leitor.pages) <= 10:
        raise ValueError(f"artigo deve ter até 10 páginas; encontrado: {len(leitor.pages)}")
    texto = "\n".join(p.extract_text() or "" for p in leitor.pages)
    if any(f"RQ{i:02d}" not in texto for i in range(1, 9)) or "??" in texto:
        raise ValueError("artigo incompleto ou com referências não resolvidas")
    return len(leitor.pages)


def reproduzir(saida):
    from analises.sprint3_a import executar as executar_a
    from analises.sprint3_b import executar as executar_b
    from analises.sprint3_c import executar as executar_c

    for parte, executar in (("a", executar_a), ("b", executar_b), ("c", executar_c)):
        destino = saida / parte
        kwargs = {"classificacao": destino / "classificacao_C1.csv"} if parte == "a" else {}
        tabelas = executar(saida=destino, **kwargs)
        for nome in tabelas:
            publicada = (BASE / "data" / f"{nome}.csv" if nome == "classificacao_C1" else
                         BASE / "results" / f"s03_{parte}" / f"{nome}.csv")
            if not publicada.exists():
                raise ValueError(f"tabela publicada ausente: {publicada}")
            assert_frame_equal(pd.read_csv(destino / f"{nome}.csv"), pd.read_csv(publicada),
                               check_exact=False, rtol=1e-10, atol=1e-12)
        print(f"Parte {parte.upper()}: tabelas reproduzidas em {destino}")


def executar(pdf="docs/artigo/artigo_final.pdf", refazer=False):
    df, origens = carregar_dataset()
    manifestos = {parte: conferir_manifesto(parte) for parte in "abc"}
    for parte in "bc":
        erros = verificar(f"docs/dicionario_s03_{parte}.md", f"results/s03_{parte}")
        if any(erros):
            raise ValueError(f"dicionário incompleto: parte {parte}")
    c = Path("results/s03_c")
    metricas = pd.read_csv(c / "metricas_combinacoes.csv")
    if (set(metricas.combinacao) != {"C1", "C2", "C3"} or len(metricas) != 3 * len(df)
            or metricas.duplicated(["full_name", "combinacao"]).any()
            or any(set(g.full_name) != set(df.full_name) for _, g in metricas.groupby("combinacao"))):
        raise ValueError("combinações não cobrem a amostra")
    pares = pd.read_csv(c / "rq07_concordancia.csv")
    if len(pares) != 6 or not (pares.n + pares.n_excluidos).eq(len(df)).all():
        raise ValueError("denominadores de concordância inconsistentes")
    paginas = conferir_pdf(pdf)
    if refazer:
        reproduzir(Path("cache/entrega_s03/reproducao"))
    resultado = {"analises_s03_concluidas": True, "artigo_s03_valido": True, "pdf_paginas": paginas,
                 "origens": origens, "pdf_sha256": sha256(pdf),
                 "manifestos_sha256": {p: sha256(Path(f"results/s03_{p}/manifesto.json")) for p in manifestos},
                 "reproducao_offline_executada": refazer,
                 "replicacao_cruzada": "nao_comprovada_por_esta_validacao",
                 "publicacao_github": "nao_comprovada_por_esta_validacao"}
    destino = Path("cache/entrega_s03/validacao.json")
    destino.parent.mkdir(parents=True, exist_ok=True)
    destino.write_text(json.dumps(resultado, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
    print(f"S03 integrada validada; artigo com {paginas} páginas; diagnóstico: {destino}")
    return resultado


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pdf", default="docs/artigo/artigo_final.pdf")
    parser.add_argument("--reproduzir", action="store_true", dest="refazer")
    executar(**vars(parser.parse_args()))
