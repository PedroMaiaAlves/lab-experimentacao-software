from pathlib import Path
import json
import subprocess

import pytest

from experimento.coleta import CONDICOES, Medidor, coletar_par, ordens_balanceadas


def test_ordem_balanceada_reproduzivel():
    orders = ordens_balanceadas(30, 42)
    assert orders == ordens_balanceadas(30, 42)
    assert orders.count(CONDICOES) == orders.count(CONDICOES[::-1]) == 15
    assert orders != ordens_balanceadas(30, 43)


@pytest.mark.parametrize("n", [0, 1, 3, -2])
def test_recusa_tamanho_nao_balanceavel(n):
    with pytest.raises(ValueError):
        ordens_balanceadas(n, 42)


def test_cache_real_vazio_preenchido_e_reutilizado(tmp_path):
    source = tmp_path / "fonte"
    source.mkdir()
    (source / "exemplo.py").write_text("RESULTADO = sum(range(100))\n", encoding="utf-8")
    medidor = Medidor(source, tmp_path)
    cold = medidor.medir("sem_cache")
    warm = medidor.medir("com_cache")
    assert cold["cache_antes"] == 0
    assert cold["cache_depois"] == warm["cache_antes"] == warm["cache_depois"] == 1
    assert warm["cache_reutilizado"]
    assert cold["duracao_ns"] > 0 and warm["duracao_ns"] > 0
    assert medidor.command[1:4] == ["-I", "-m", "compileall"]
    # Não se afirma que warm < cold: durações reais contêm ruído do SO.
    medidor.limpar_cache()
    assert not list(source.rglob("*.pyc"))
    assert (source / "exemplo.py").exists()


def test_preparacao_antes_do_cronometro(tmp_path, monkeypatch):
    source = tmp_path / "fonte"
    source.mkdir()
    (source / "exemplo.py").write_text("X = 1\n", encoding="utf-8")
    medidor = Medidor(source, tmp_path)
    events = []
    original = medidor.executar

    def execute():
        events.append("execucao")
        return original()

    ticks = iter([100, 1100])

    def timer():
        events.append("relogio")
        return next(ticks)

    monkeypatch.setattr(medidor, "executar", execute)
    monkeypatch.setattr("experimento.coleta.time.perf_counter_ns", timer)
    result = medidor.medir("com_cache")
    assert events == ["execucao", "relogio", "execucao", "relogio"]
    assert result["duracao_ns"] == 1000


def test_fonte_fora_do_cache_nao_pode_ser_limpa(tmp_path):
    with pytest.raises(ValueError, match="isolada"):
        Medidor(tmp_path, tmp_path / "outra_area")


def test_falha_repete_par_inteiro_e_preserva_log(tmp_path):
    class FakeMedidor:
        calls = []

        def medir(self, condition):
            self.calls.append(condition)
            if len(self.calls) == 2:
                raise subprocess.CalledProcessError(1, ["compilador"], stderr="erro de teste")
            return {"condicao": condition, "duracao_s": float(len(self.calls)), "inicio_utc": "teste"}

    medidor = FakeMedidor()
    row = coletar_par(medidor, CONDICOES, 1, "real", tmp_path, 3)
    assert medidor.calls == ["sem_cache", "com_cache", "sem_cache", "com_cache"]
    assert row["tentativa"] == 2 and row["sem_cache_s"] == 3 and row["com_cache_s"] == 4
    failure = json.loads((tmp_path / "falhas.jsonl").read_text(encoding="utf-8"))
    assert failure["tentativa"] == 1 and failure["condicao"] == "com_cache"
    assert "erro de teste" in failure["stderr"]
    assert len((tmp_path / "medicoes.jsonl").read_text(encoding="utf-8").splitlines()) == 4


def test_falha_persistente_interrompe_sem_inventar_par(tmp_path):
    class SempreFalha:
        def medir(self, condition):
            raise OSError("falha sintética")

    with pytest.raises(RuntimeError, match="sessão incompleta"):
        coletar_par(SempreFalha(), CONDICOES, 1, "real", tmp_path, 2)
    assert len((tmp_path / "falhas.jsonl").read_text(encoding="utf-8").splitlines()) == 2
