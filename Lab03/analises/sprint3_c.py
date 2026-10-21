"""Entrega offline da RQ08 (rework rate): python -m analises.sprint3_c."""
import argparse
import hashlib
import importlib.metadata
import json
from pathlib import Path
import platform

from analises.artefatos_c import escrever_artefatos
from analises.entrada import carregar_dataset, ler_json, sha256
from analises.rq08 import analisar, carregar_releases
from analises.sprint3_a import validar_saida
from pipeline.config import carregar_config


def executar(dataset="data/dataset.csv", amostra=None, pacote=None, config="config_s02.yaml", saida="results/s03_c"):
    saida = validar_saida(saida, dataset)
    cfg = carregar_config(config)
    df, origens = carregar_dataset(dataset, amostra)
    manifesto_dataset = ler_json(Path(dataset).with_suffix(".manifest.json"))
    if manifesto_dataset["heuristica"] != cfg["heuristica_release"]:
        raise ValueError("heurística configurada diverge do dataset congelado")
    if (str(cfg["janela_inicio"]), str(cfg["janela_fim"])) != (origens["janela_inicio"], origens["janela_fim"]):
        raise ValueError("janela configurada diverge da amostra congelada")
    if set(df.heuristica_versao) != {cfg["heuristica_release"]["versao"]}:
        raise ValueError("versão da heurística divergente nas linhas do dataset")
    base = Path(__file__).resolve().parents[1]
    registro = Path(dataset).parent / "amostra_ouro_s02/avaliacao_v3.manifest.json"
    fonte = (base / "metricas/cfr.py").read_text(encoding="utf-8")
    avaliacao = ler_json(registro)
    if (avaliacao["regras"] != cfg["heuristica_release"] or
            avaliacao["implementacao_sha256"] != hashlib.sha256(fonte.encode("utf-8")).hexdigest()):
        raise ValueError("implementação diferente da heurística v3 validada")
    auditoria, pacote_sha = carregar_releases(df, cfg, dataset, amostra, pacote)
    tabelas = analisar(df, auditoria, cfg)
    saida.mkdir(parents=True, exist_ok=True)
    for nome, tabela in tabelas.items():
        tabela.to_csv(saida / f"{nome}.csv", index=False, float_format="%.17g", lineterminator="\n")
    escrever_artefatos(tabelas, saida)
    modulos = ("analises/rq08.py", "analises/artefatos_c.py", "analises/sprint3_c.py", "analises/entrada.py",
               "analises/rq01_04.py", "analises/graficos_a.py", "analises/sprint3_a.py",
               "metricas/cfr.py", "metricas/rework.py", "pipeline/coleta_releases.py", "pipeline/dataset.py")
    manifesto = {"origens": {**origens, "fontes_s02_zip_sha256": pacote_sha,
                             "avaliacao_v3_manifest_sha256": sha256(registro)},
                 "parametros": {"rq08_opcao": "rework_rate", "heuristica": cfg["heuristica_release"],
                                "denominador": "todas as releases principais na janela, sem censura de sete dias",
                                "ausencias": "mesma regra da RQ03 (b) congelada: lacuna textual sem classificação positiva",
                                "sensibilidade": "evidência completa: exclui sem_anterior, 404, sem commits ou mensagem ausente",
                                "limites": "limites de identificação: desconhecidas todas negativas/todas positivas; não são IC",
                                "comparacao_cfr_b": "reprodução das regras da S02, sem modificar o dataset"},
                 "ambiente": {"python": platform.python_version(), "sistema": platform.system(),
                              "pacotes": {p: importlib.metadata.version(p) for p in ("pandas", "numpy", "matplotlib")}},
                 "codigo_sha256": {p: hashlib.sha256((base / p).read_text(encoding="utf-8").encode()).hexdigest()
                                   for p in modulos},
                 "artefatos_sha256": {p.name: sha256(p) for p in sorted(saida.iterdir())
                                      if p.is_file() and p.suffix in {".csv", ".tex", ".png", ".pdf"}}}
    (saida / "manifesto.json").write_text(json.dumps(manifesto, ensure_ascii=False, indent=2) + "\n",
                                         encoding="utf-8", newline="\n")
    return tabelas


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset", default="data/dataset.csv")
    parser.add_argument("--amostra")
    parser.add_argument("--pacote")
    parser.add_argument("--config", default="config_s02.yaml")
    parser.add_argument("--saida", default="results/s03_c")
    args = parser.parse_args(argv)
    tabelas = executar(**vars(args))
    print(tabelas["rq08_resumo"].to_string(index=False))
    print(tabelas["rq08_cobertura"].to_string(index=False))


if __name__ == "__main__":
    main()
