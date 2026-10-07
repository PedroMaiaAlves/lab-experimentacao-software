from datetime import date

from pipeline.janela import intervalo_created, meses_da_janela, na_janela

CFG = {"janela_inicio": date(2025, 10, 1), "janela_fim": date(2026, 9, 30)}


def test_na_janela_inclui_extremos_e_exclui_fora():
    assert na_janela("2025-10-01T00:00:00Z", CFG)
    assert na_janela("2026-09-30T23:59:59Z", CFG)
    assert not na_janela("2025-09-30T23:59:59Z", CFG)
    assert not na_janela("2026-10-01T00:00:00Z", CFG)
    assert not na_janela(None, CFG)


def test_meses_da_janela_tem_12_meses_contiguos():
    meses = meses_da_janela(CFG)
    assert len(meses) == 12
    assert meses[0] == (date(2025, 10, 1), date(2025, 10, 31))
    assert meses[-1] == (date(2026, 9, 1), date(2026, 9, 30))


def test_intervalo_created():
    assert intervalo_created(CFG) == "2025-10-01..2026-09-30"
