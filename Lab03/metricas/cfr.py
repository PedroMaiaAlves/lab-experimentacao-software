"""Variantes do change failure rate usando CI ou releases como proxies."""
from __future__ import annotations

from collections.abc import Iterable, Mapping
from datetime import date, datetime, timedelta, timezone
import re
from typing import Any, Literal

SUCESSOS = frozenset({"success"})
FALHAS = frozenset({"failure", "timed_out", "startup_failure"})
IGNORADAS = frozenset({
    "cancelled", "skipped", "neutral", "action_required", "stale", None, ""
})

Classificacao = Literal["sucesso", "falha", "ignorar"]

_SEMVER = re.compile(
    r"^v?(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)"
    r"(?:-[0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*)?"
    r"(?:\+[0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*)?$"
)


def classificar_conclusao(conclusao: str | None) -> Classificacao:
    """Classifica uma conclusion; valores novos/desconhecidos são ignorados."""
    if conclusao in SUCESSOS:
        return "sucesso"
    if conclusao in FALHAS:
        return "falha"
    return "ignorar"


def contar_conclusoes(runs: Iterable[Mapping[str, Any]]) -> dict[str, int]:
    contagens = {"sucessos": 0, "falhas": 0, "ignoradas": 0}
    for run in runs:
        classe = classificar_conclusao(run.get("conclusion"))
        contagens[{"sucesso": "sucessos", "falha": "falhas", "ignorar": "ignoradas"}[classe]] += 1
    return contagens


def calcular_cfr_a(runs: Iterable[Mapping[str, Any]]) -> float | None:
    """Calcula falhas / (falhas + sucessos), ou None sem observações válidas."""
    contagens = contar_conclusoes(runs)
    validas = contagens["falhas"] + contagens["sucessos"]
    if validas == 0:
        return None
    return contagens["falhas"] / validas


def _versao_semver(tag: str | None) -> tuple[int, int, int] | None:
    if not isinstance(tag, str):
        return None
    correspondencia = _SEMVER.fullmatch(tag.strip())
    if not correspondencia:
        return None
    return tuple(map(int, correspondencia.groups()[:3]))


def _versao_semver_v2(tag: str | None) -> tuple[int, int, int] | None:
    if not isinstance(tag, str):
        return None
    m = re.search(r"(?:^|[@/v_])(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)(?:[-+][0-9A-Za-z.-]+)?$", tag.strip())
    if not m:
        return None
    return tuple(map(int, m.groups()[:3]))


def _explicar_release_v3(tag_anterior, tag_atual, mensagens, regras):
    anterior, atual = _versao_semver_v2(tag_anterior), _versao_semver_v2(tag_atual)
    palavras = regras.get("palavras_chave", ())
    if isinstance(palavras, (str, bytes)) or not palavras or not all(
        isinstance(palavra, str) and palavra.strip() for palavra in palavras
    ):
        raise ValueError("palavras_chave deve ser uma coleção de textos não vazios")
    usar_texto = regras.get("usar_palavras_commits") is True
    patch = bool(regras.get("usar_patch_semver") is True and anterior is not None
                 and atual is not None and atual[:2] == anterior[:2] and atual[2] > anterior[2])
    correcoes, funcionalidades, encontradas = 0, 0, set()
    padroes = {p: re.compile(rf"\b{re.escape(p)}\b", re.I) for p in palavras}
    for mensagem in mensagens if usar_texto else ():
        if not isinstance(mensagem, str) or not mensagem.strip():
            continue
        titulo = mensagem.strip().split("\n", 1)[0]
        if re.search(r"^(?:feat|add|feature)\b", titulo, re.I):
            funcionalidades += 1
            continue
        if re.search(r"^(?:chore|docs?|ci|build|test|refactor)\b", titulo, re.I):
            continue
        if re.search(r"\b(?:typo|readme|bump|deps?|dependency|dependencies)\b", titulo, re.I):
            continue
        termos = {p for p, padrao in padroes.items() if padrao.search(titulo)}
        if re.search(r"\b(?:cve|vulnerability|panic|crash|leak|regression|bugfix)\b", titulo, re.I):
            termos.add("fix")
        correcoes += bool(termos)
        encontradas.update(termos)
    criterio_texto = bool(usar_texto and correcoes and (
        funcionalidades == 0 or (correcoes >= 3 and 2 * correcoes >= 5 * funcionalidades)))
    criterio_patch = bool(patch and (not usar_texto or (funcionalidades == 0 and correcoes >= 1)))
    return {"tag_anterior_semver": anterior is not None, "tag_atual_semver": atual is not None,
            "criterio_patch": criterio_patch, "criterio_texto": criterio_texto,
            "palavras_encontradas": sorted(encontradas), "corretiva": criterio_patch or criterio_texto}


def explicar_release_corretiva(
    tag_anterior: str | None,
    tag_atual: str | None,
    mensagens_commits: Iterable[str | None],
    regras: Mapping[str, Any],
) -> dict[str, Any]:
    """Aplica a heurística e expõe quais evidências acionaram a decisão."""
    versao = str(regras.get("versao", "v1")).strip().lower()
    if versao == "v3":
        return _explicar_release_v3(tag_anterior, tag_atual, mensagens_commits, regras)

    if versao == "v2":
        anterior = _versao_semver_v2(tag_anterior)
        atual = _versao_semver_v2(tag_atual)
        usar_patch = regras.get("usar_patch_semver") is True
        usar_texto = regras.get("usar_palavras_commits") is True
        palavras = regras.get("palavras_chave", ("fix", "hotfix", "revert"))

        is_patch = bool(
            usar_patch
            and anterior is not None
            and atual is not None
            and atual[:2] == anterior[:2]
            and atual[2] > anterior[2]
        )

        real_fixes = 0
        feat_count = 0
        encontradas = set()

        for m in mensagens_commits:
            if not m or not isinstance(m, str):
                continue
            first_line = m.strip().split("\n")[0]
            if re.search(r'^(?:feat|add|feature)\b', first_line, re.I):
                feat_count += 1
                continue
            if re.search(r'^(?:chore|docs?|ci|build|test|refactor)\b', first_line, re.I):
                continue
            if re.search(r'\b(?:typo|readme|bump|deps?|dependency|dependencies)\b', first_line, re.I):
                continue
            for palavra in palavras:
                if re.search(rf"\b{re.escape(palavra)}\b", first_line, re.IGNORECASE):
                    real_fixes += 1
                    encontradas.add(palavra)
            if re.search(r'\b(?:cve|vulnerability|panic|crash|leak|regression|bugfix)\b', first_line, re.I):
                real_fixes += 1
                encontradas.add("fix")

        criterio_texto = bool(
            usar_texto and real_fixes >= 1 and (
                feat_count == 0 or (real_fixes >= 3 and real_fixes >= 2.5 * feat_count)
            )
        )
        criterio_patch = bool(is_patch and feat_count == 0 and real_fixes >= 1)
        corretiva = criterio_patch or criterio_texto
        return {
            "tag_anterior_semver": anterior is not None,
            "tag_atual_semver": atual is not None,
            "criterio_patch": criterio_patch,
            "criterio_texto": criterio_texto,
            "palavras_encontradas": sorted(encontradas),
            "corretiva": corretiva,
        }

    anterior = _versao_semver(tag_anterior)
    atual = _versao_semver(tag_atual)
    usar_patch = regras.get("usar_patch_semver") is True
    usar_texto = regras.get("usar_palavras_commits") is True
    palavras = regras.get("palavras_chave", ())
    if isinstance(palavras, (str, bytes)) or not palavras or not all(
        isinstance(palavra, str) and palavra.strip() for palavra in palavras
    ):
        raise ValueError("palavras_chave deve ser uma coleção de textos não vazios")

    criterio_patch = bool(
        usar_patch
        and anterior is not None
        and atual is not None
        and atual[:2] == anterior[:2]
        and atual[2] > anterior[2]
    )
    padroes = {
        palavra: re.compile(rf"\b{re.escape(palavra)}\b", re.IGNORECASE)
        for palavra in palavras
    }
    encontradas = sorted({
        palavra
        for mensagem in mensagens_commits
        if isinstance(mensagem, str)
        for palavra, padrao in padroes.items()
        if padrao.search(mensagem)
    }) if usar_texto else []
    criterio_texto = bool(encontradas)
    return {
        "tag_anterior_semver": anterior is not None,
        "tag_atual_semver": atual is not None,
        "criterio_patch": criterio_patch,
        "criterio_texto": criterio_texto,
        "palavras_encontradas": encontradas,
        "corretiva": criterio_patch or criterio_texto,
    }


def classificar_release_corretiva(
    tag_anterior: str | None,
    tag_atual: str | None,
    mensagens_commits: Iterable[str | None],
    regras: Mapping[str, Any],
) -> bool:
    """Classifica conforme a versão e os controles configurados."""
    return explicar_release_corretiva(
        tag_anterior, tag_atual, mensagens_commits, regras
    )["corretiva"]


def _instante(valor: str | datetime) -> datetime:
    if isinstance(valor, datetime):
        instante = valor
    else:
        instante = datetime.fromisoformat(valor)
    if instante.tzinfo is None:
        raise ValueError("published_at deve incluir o fuso horário")
    return instante.astimezone(timezone.utc)


def _fim_da_janela(valor: str | date | datetime) -> date:
    if isinstance(valor, datetime):
        return valor.date()
    if isinstance(valor, date):
        return valor
    return date.fromisoformat(valor)


def calcular_cfr_b(
    releases: Iterable[Mapping[str, Any]],
    janela_fim: str | date | datetime,
    dias: int = 7,
) -> dict[str, int | float | None]:
    """Calcula CFR (b) em releases principais já limitadas ao início da janela.

    Cada item deve fornecer ``published_at`` e ``corretiva``. Se presentes, itens
    com ``draft`` ou ``prerelease`` verdadeiros são excluídos. As últimas
    ``dias`` datas da janela são censuradas; o intervalo de falha é inclusivo.
    """
    if isinstance(dias, bool) or not isinstance(dias, int) or dias <= 0:
        raise ValueError("dias deve ser um inteiro positivo")
    fim = _fim_da_janela(janela_fim)
    limite_censura = fim - timedelta(days=dias)
    principais = []
    for ordem, release in enumerate(releases):
        if release.get("draft", False) or release.get("prerelease", False):
            continue
        publicado = _instante(release["published_at"])
        if publicado.date() > fim:
            continue
        principais.append((publicado, str(release.get("id", ordem)), release))
    principais.sort(key=lambda item: (item[0], item[1]))

    avaliadas = [item for item in principais if item[0].date() <= limite_censura]
    censuradas = len(principais) - len(avaliadas)
    intervalo = timedelta(days=dias)
    falhas = 0
    for indice, (publicado, _id, _release) in enumerate(avaliadas):
        falhou = False
        for posterior, _id_posterior, release_posterior in principais[indice + 1:]:
            diferenca = posterior - publicado
            if diferenca > intervalo:
                break
            if release_posterior.get("corretiva") is True:
                falhou = True
                break
        falhas += int(falhou)

    total = len(avaliadas)
    return {
        "cfr_b": falhas / total if total else None,
        "releases_avaliadas": total,
        "releases_falharam": falhas,
        "releases_censuradas": censuradas,
    }
