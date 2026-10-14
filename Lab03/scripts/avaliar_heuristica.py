"""Compara a heurística ativa com o consenso manual de releases corretivas."""
from __future__ import annotations

import argparse
import csv
import json
from collections import defaultdict
from collections.abc import Iterable, Mapping
from pathlib import Path
import sys

# Permite tanto `python -m scripts.avaliar_heuristica` quanto a execução direta
# documentada a partir de Lab03/.
RAIZ_LAB03 = Path(__file__).resolve().parents[1]
if str(RAIZ_LAB03) not in sys.path:
    sys.path.insert(0, str(RAIZ_LAB03))

from sklearn.metrics import confusion_matrix, precision_recall_fscore_support

from metricas.cfr import explicar_release_corretiva
from pipeline.config import carregar_config

CAMPOS_CONSENSO = ("full_name", "release_id", "corretiva")
CAMPOS_COMPARACOES = (
    "full_name", "release_id", "tag_name", "previous_tag_name", "status"
)
CAMPOS_COMMITS = ("full_name", "release_id", "message")
CAMPOS_HISTORICO = (
    "versao", "precisao", "recall", "f1", "suporte", "tp", "fp", "fn", "tn", "regras"
)


def _chave(linha: Mapping[str, str]) -> tuple[str, str]:
    return str(linha["full_name"]).strip(), str(linha["release_id"]).strip()


def _mapa_unico(
    linhas: Iterable[Mapping[str, str]], origem: str
) -> dict[tuple[str, str], Mapping[str, str]]:
    resultado = {}
    for linha in linhas:
        chave = _chave(linha)
        if not all(chave):
            raise ValueError(f"{origem}: full_name/release_id vazio")
        if chave in resultado:
            raise ValueError(f"{origem}: chave duplicada: {chave[0]}#{chave[1]}")
        resultado[chave] = linha
    return resultado


def _rotulo_booleano(valor: str) -> bool:
    normalizado = str(valor).strip().lower()
    if normalizado == "sim":
        return True
    if normalizado in {"nao", "não"}:
        return False
    raise ValueError(f"rótulo de release corretiva inválido: {valor!r}")


def calcular_metricas(
    consenso: Iterable[bool], previsoes: Iterable[bool]
) -> dict[str, int | float]:
    verdadeiros, previstos = list(consenso), list(previsoes)
    if not verdadeiros or len(verdadeiros) != len(previstos):
        raise ValueError("consenso e previsões devem ter o mesmo tamanho não vazio")
    precisao, recall, f1, _ = precision_recall_fscore_support(
        verdadeiros,
        previstos,
        average="binary",
        pos_label=True,
        zero_division=0,
    )
    tn, fp, fn, tp = confusion_matrix(
        verdadeiros, previstos, labels=[False, True]
    ).ravel()
    return {
        "precisao": float(precisao),
        "recall": float(recall),
        "f1": float(f1),
        "suporte": sum(verdadeiros),
        "tp": int(tp),
        "fp": int(fp),
        "fn": int(fn),
        "tn": int(tn),
    }


def avaliar_linhas(
    consenso: Iterable[Mapping[str, str]],
    comparacoes: Iterable[Mapping[str, str]],
    commits: Iterable[Mapping[str, str]],
    regras: Mapping[str, object],
) -> tuple[list[dict[str, object]], dict[str, int | float]]:
    """Junta as fontes por release e devolve auditoria e métricas da classe positiva."""
    mapa_consenso = _mapa_unico(consenso, "consenso")
    if not mapa_consenso:
        raise ValueError("consenso vazio")
    mapa_comparacoes = _mapa_unico(comparacoes, "comparações")
    mensagens: dict[tuple[str, str], list[str]] = defaultdict(list)
    for commit in commits:
        mensagens[_chave(commit)].append(str(commit.get("message", "")))

    auditoria = []
    verdadeiros, previstos = [], []
    nomes_resultado = {
        (True, True): "VP",
        (False, True): "FP",
        (True, False): "FN",
        (False, False): "VN",
    }
    for chave, rotulo in mapa_consenso.items():
        if chave not in mapa_comparacoes:
            raise ValueError(f"release do consenso sem comparação: {chave[0]}#{chave[1]}")
        comparacao = mapa_comparacoes[chave]
        esperado = _rotulo_booleano(rotulo["corretiva"])
        evidencia = explicar_release_corretiva(
            comparacao.get("previous_tag_name"),
            comparacao.get("tag_name"),
            mensagens.get(chave, ()),
            regras,
        )
        previsto = bool(evidencia["corretiva"])
        verdadeiros.append(esperado)
        previstos.append(previsto)
        auditoria.append({
            "full_name": chave[0],
            "release_id": chave[1],
            "tag_name": comparacao.get("tag_name", ""),
            "previous_tag_name": comparacao.get("previous_tag_name", ""),
            "status_comparacao": comparacao.get("status", ""),
            "consenso": "sim" if esperado else "nao",
            "predicao": "sim" if previsto else "nao",
            "criterio_patch": evidencia["criterio_patch"],
            "criterio_texto": evidencia["criterio_texto"],
            "palavras_encontradas": "|".join(evidencia["palavras_encontradas"]),
            "tipo_resultado": nomes_resultado[(esperado, previsto)],
        })
    return auditoria, calcular_metricas(verdadeiros, previstos)


def _ler_csv(caminho: Path, campos: Iterable[str], origem: str) -> list[dict[str, str]]:
    with caminho.open(newline="", encoding="utf-8") as arquivo:
        leitor = csv.DictReader(arquivo)
        ausentes = sorted(set(campos) - set(leitor.fieldnames or ()))
        if ausentes:
            raise ValueError(f"{origem}: colunas ausentes: {', '.join(ausentes)}")
        return list(leitor)


def _gravar_csv(caminho: Path, linhas: list[Mapping[str, object]]) -> None:
    caminho.parent.mkdir(parents=True, exist_ok=True)
    with caminho.open("w", newline="", encoding="utf-8") as arquivo:
        writer = csv.DictWriter(arquivo, fieldnames=list(linhas[0]))
        writer.writeheader()
        writer.writerows(linhas)


def registrar_resultado(
    caminho_historico: Path,
    caminho_documentacao: Path,
    versao: str,
    metricas: Mapping[str, int | float],
    regras: Mapping[str, object],
) -> None:
    """Atualiza a versão de forma idempotente e regenera a tabela Markdown."""
    anteriores = []
    if caminho_historico.is_file():
        anteriores = _ler_csv(caminho_historico, CAMPOS_HISTORICO, "histórico")
    registro = {
        "versao": versao,
        **{campo: metricas[campo] for campo in CAMPOS_HISTORICO[1:-1]},
        "regras": json.dumps(dict(regras), ensure_ascii=False, sort_keys=True),
    }
    por_versao = {linha["versao"]: linha for linha in anteriores}
    por_versao[versao] = registro
    ordem = [linha["versao"] for linha in anteriores]
    if versao not in ordem:
        ordem.append(versao)
    linhas = [por_versao[item] for item in ordem]
    caminho_historico.parent.mkdir(parents=True, exist_ok=True)
    with caminho_historico.open("w", newline="", encoding="utf-8") as arquivo:
        writer = csv.DictWriter(arquivo, fieldnames=CAMPOS_HISTORICO)
        writer.writeheader()
        writer.writerows(linhas)

    texto = caminho_documentacao.read_text(encoding="utf-8")
    inicio, fim = "<!-- resultados:start -->", "<!-- resultados:end -->"
    if inicio not in texto or fim not in texto:
        raise ValueError("documentação sem marcadores da tabela de resultados")
    tabela = [
        inicio,
        "| Versão | Precisão | Recall | F1 | Suporte | TP | FP | FN | TN |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for linha in linhas:
        tabela.append(
            f"| {linha['versao']} | {float(linha['precisao']):.3f} | "
            f"{float(linha['recall']):.3f} | {float(linha['f1']):.3f} | "
            f"{linha['suporte']} | {linha['tp']} | {linha['fp']} | "
            f"{linha['fn']} | {linha['tn']} |"
        )
    tabela.append(fim)
    antes, restante = texto.split(inicio, 1)
    _antigo, depois = restante.split(fim, 1)
    caminho_documentacao.write_text(
        antes + "\n".join(tabela) + depois, encoding="utf-8"
    )


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", default="config.yaml")
    parser.add_argument(
        "--consenso", default="data/amostra_ouro/consenso_releases.csv"
    )
    parser.add_argument("--comparacoes", default="data/comparacoes_releases.csv")
    parser.add_argument("--commits", default="data/commits_entre_releases.csv")
    parser.add_argument("--saida", help="CSV de auditoria; padrão inclui a versão ativa")
    parser.add_argument("--historico", default="data/heuristica_metricas.csv")
    parser.add_argument("--documentacao", default="docs/heuristica_versoes.md")
    args = parser.parse_args(argv)
    try:
        cfg = carregar_config(args.config)
        regras = cfg["heuristica_release"]
        versao = regras["versao"]
        consenso = _ler_csv(Path(args.consenso), CAMPOS_CONSENSO, "consenso")
        comparacoes = _ler_csv(Path(args.comparacoes), CAMPOS_COMPARACOES, "comparações")
        commits = _ler_csv(Path(args.commits), CAMPOS_COMMITS, "commits")
        auditoria, metricas = avaliar_linhas(consenso, comparacoes, commits, regras)
        saida = Path(args.saida or f"data/avaliacao_heuristica_{versao}.csv")
        _gravar_csv(saida, auditoria)
        registrar_resultado(
            Path(args.historico), Path(args.documentacao), versao, metricas, regras
        )
    except (OSError, ValueError) as erro:
        parser.exit(1, f"Erro: {erro}\n")

    situacao = "meta atingida" if metricas["f1"] >= 0.70 else "refinamento necessário"
    print(
        f"{versao}: precisão={metricas['precisao']:.3f}, "
        f"recall={metricas['recall']:.3f}, F1={metricas['f1']:.3f} ({situacao})."
    )
    print(f"Auditoria: {saida}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
