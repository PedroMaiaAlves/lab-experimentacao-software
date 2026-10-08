from datetime import datetime, timezone
from statistics import median


def _instante(valor):
    instante = datetime.fromisoformat(valor)
    if instante.tzinfo is None:
        raise ValueError("o timestamp deve incluir o fuso horário")
    return instante.astimezone(timezone.utc)


def data_commit_valida(publicado, autoria):
    """Indica se os timestamps permitem um lead time não negativo."""
    try:
        return (_instante(publicado) - _instante(autoria)).total_seconds() >= 0
    except (TypeError, ValueError):
        return False


def _tempos_por_release(releases, ignorar_invalidos=False):
    for release in releases:
        if release.get("status", "ok") != "ok" or not release["commits"]:
            continue
        publicado = _instante(release["published_at"])
        tempos = []
        for commit in release["commits"]:
            try:
                tempo = (publicado - _instante(commit["author_date"])).total_seconds() / 3600
            except (TypeError, ValueError):
                if ignorar_invalidos:
                    continue
                raise
            if tempo < 0:
                if ignorar_invalidos:
                    continue
                raise ValueError("há commit com data posterior à publicação da release")
            tempos.append(tempo)
        if tempos:
            yield tempos


def calcular_lead_time(releases, ignorar_invalidos=False):
    tempos = list(_tempos_por_release(releases, ignorar_invalidos))
    por_release = [max(valores) for valores in tempos]
    por_commit = [valor for valores in tempos for valor in valores]
    return {"lead_time_a_horas": median(por_release) if por_release else None,
            "lead_time_b_horas": median(por_commit) if por_commit else None}


def lead_time_por_release(releases):
    return calcular_lead_time(releases)["lead_time_a_horas"]


def lead_time_por_commit(releases):
    return calcular_lead_time(releases)["lead_time_b_horas"]
