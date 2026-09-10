"""Coleta métricas estruturais de um arquivo-fonte Python.

Interface pública: ``collect(path)``.

Retorna um dicionário com:

- ``loc``: linhas de código, ignorando linhas vazias e comentários.
- ``mean_complexity``: complexidade ciclomática média dos blocos
  (funções/métodos/classes) do arquivo, calculada via Radon.
- ``maintainability_index``: índice de manutenibilidade (Radon, escala 0-100).
- ``duplication_percent``: percentual de linhas normalizadas que fazem parte
  de algum bloco duplicado de pelo menos três linhas.

Quando uma métrica não puder ser calculada (arquivo vazio, código
sintaticamente inválido para as ferramentas do Radon, etc.), o valor
correspondente é ``None`` — nunca ``0`` — para não fabricar dados.
"""

from __future__ import annotations

from pathlib import Path
from typing import Optional

from radon.complexity import cc_visit
from radon.metrics import mi_visit
from radon.raw import analyze


def _read_source(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _compute_loc(source: str) -> Optional[int]:
    """LOC ignorando linhas vazias e comentários.

    Usa ``radon.raw.analyze``, que já separa LOC lógico/físico de
    comentários e linhas em branco (blank).
    """
    if source.strip() == "":
        return 0
    try:
        raw = analyze(source)
    except SyntaxError:
        return None
    # sloc = "source lines of code": exclui linhas vazias e comentários.
    return raw.sloc


def _compute_mean_complexity(source: str) -> Optional[float]:
    """Complexidade ciclomática média dos blocos do arquivo."""
    try:
        blocks = cc_visit(source)
    except SyntaxError:
        return None
    if not blocks:
        return None
    total = sum(block.complexity for block in blocks)
    return round(total / len(blocks), 2)


def _compute_maintainability_index(source: str) -> Optional[float]:
    """Índice de manutenibilidade (0-100) via Radon."""
    if source.strip() == "":
        return None
    try:
        mi = mi_visit(source, multi=True)
    except SyntaxError:
        return None
    if mi is None:
        return None
    return round(mi, 2)


def _normalize_line(line: str) -> str:
    return line.strip()


def _significant_lines(source: str) -> list[str]:
    """Linhas normalizadas, sem vazias e sem comentários de linha inteira."""
    lines = []
    for raw_line in source.splitlines():
        stripped = _normalize_line(raw_line)
        if stripped == "" or stripped.startswith("#"):
            continue
        lines.append(stripped)
    return lines


def _compute_duplication_percent(source: str, min_block: int = 3) -> Optional[float]:
    """Percentual de linhas significativas cobertas por blocos duplicados.

    Um bloco duplicado é uma sequência contígua de ao menos ``min_block``
    linhas normalizadas que se repete em outro ponto do arquivo (janela
    deslizante simples, sem dependências externas).
    """
    lines = _significant_lines(source)
    total = len(lines)
    if total < min_block:
        return None

    seen_blocks: dict[tuple[str, ...], list[int]] = {}
    for start in range(total - min_block + 1):
        block = tuple(lines[start : start + min_block])
        seen_blocks.setdefault(block, []).append(start)

    duplicated_indices: set[int] = set()
    for block, occurrences in seen_blocks.items():
        if len(occurrences) > 1:
            for start in occurrences:
                duplicated_indices.update(range(start, start + min_block))

    if not duplicated_indices:
        return 0.0

    return round((len(duplicated_indices) / total) * 100, 2)


def collect(path: str) -> dict:
    """Coleta as métricas estruturais do arquivo em ``path``.

    Nunca fabrica ``0`` para uma métrica que não pôde ser calculada: nesse
    caso o valor correspondente é ``None``.
    """
    file_path = Path(path)
    if not file_path.exists():
        raise FileNotFoundError(f"Arquivo não encontrado: {path}")

    source = _read_source(file_path)

    return {
        "loc": _compute_loc(source),
        "mean_complexity": _compute_mean_complexity(source),
        "maintainability_index": _compute_maintainability_index(source),
        "duplication_percent": _compute_duplication_percent(source),
    }


if __name__ == "__main__":
    import argparse
    import json

    parser = argparse.ArgumentParser(description="Coleta métricas estruturais de um arquivo Python")
    parser.add_argument("path", help="Caminho do arquivo-fonte a analisar")
    args = parser.parse_args()

    print(json.dumps(collect(args.path), ensure_ascii=False, indent=2))
