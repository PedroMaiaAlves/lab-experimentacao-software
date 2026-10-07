"""Funções compartilhadas sobre a janela de observação (usadas por A, B e C)."""
from datetime import date, timedelta


def para_data(iso):
    """'2026-01-10T12:00:00Z' -> date(2026, 1, 10)."""
    return date.fromisoformat(iso[:10])


def na_janela(iso, cfg):
    """True se o timestamp ISO cai dentro da janela (extremos incluídos)."""
    if not iso:
        return False
    return cfg["janela_inicio"] <= para_data(iso) <= cfg["janela_fim"]


def intervalo_created(cfg):
    """Valor do filtro `created=` da API de workflow runs."""
    return f"{cfg['janela_inicio']}..{cfg['janela_fim']}"


def meses_da_janela(cfg):
    """Lista de (inicio, fim) mês a mês; útil para dividir a coleta de runs."""
    atual, fim = cfg["janela_inicio"], cfg["janela_fim"]
    saida = []
    while atual <= fim:
        proximo = date(atual.year + (atual.month == 12), atual.month % 12 + 1, 1)
        saida.append((atual, min(proximo - timedelta(days=1), fim)))
        atual = proximo
    return saida
