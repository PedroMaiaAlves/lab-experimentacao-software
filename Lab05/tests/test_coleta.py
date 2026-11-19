import json
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from experimento import plano  # noqa: E402
from experimento.coleta import (  # noqa: E402
    Coletor,
    criar_diretorio_coleta,
    interpretar_resultado_omb,
    interpretar_stats,
    renderizar_workload,
    taxas_e2,
)


class ExecutorFake:
    def __init__(self, diretorio, falhar=None):
        self.diretorio = diretorio
        self.falhar = set(falhar or [])
        self.limpezas = 0
        self.executadas = []

    def limpar(self):
        self.limpezas += 1

    def metadados(self):
        return {"ambiente": {"teste": True}, "imagens": {"kafka": "sha256:k", "rabbitmq": "sha256:r"}}

    def executar(self, execucao, workload, bruto, stdout, stderr):
        self.executadas.append(execucao)
        stdout.write_text("stdout", encoding="utf-8")
        stderr.write_text("stderr", encoding="utf-8")
        if execucao.id_execucao in self.falhar:
            return 7, [10.0], [100.0], ["omb", execucao.id_execucao]
        taxa = 1_000.0 if execucao.broker == "kafka" else 800.0
        bruto.write_text(
            json.dumps(
                {
                    "publishRate": [taxa, taxa + 100],
                    "aggregatedEndToEndLatency50pct": 2.5,
                    "aggregatedEndToEndLatency99pct": 9.5,
                }
            ),
            encoding="utf-8",
        )
        return 0, [10.0, 20.0], [100.0, 120.0], ["omb", execucao.id_execucao]


def test_plano_piloto_balanceado_aleatorio():
    for experimento in ("E1", "E2"):
        execucoes = plano.gerar_plano(experimento, 3)
        assert len(execucoes) == 12
        assert set(Counter((e.broker, e.tamanho_bytes) for e in execucoes).values()) == {3}
        assert [e.id_execucao for e in execucoes] != sorted(e.id_execucao for e in execucoes)


def test_diretorio_nao_sobrescreve(tmp_path):
    instante = datetime(2026, 11, 19, tzinfo=timezone.utc)
    criado = criar_diretorio_coleta(tmp_path, instante)
    assert criado.exists()
    with pytest.raises(FileExistsError):
        criar_diretorio_coleta(tmp_path, instante)


def test_workload_tem_duracoes_e_durabilidade(tmp_path):
    execucao = plano.gerar_plano("E1", 3)[0]
    caminho = renderizar_workload(execucao, 0, tmp_path / "w.yaml")
    texto = caminho.read_text(encoding="utf-8")
    assert "warmupDurationSeconds: 30" in texto
    assert "testDurationSeconds: 60" in texto
    assert f"messageSize: {execucao.tamanho_bytes}" in texto
    assert "producerRate: 0" in texto


def test_parser_omb_e_docker_stats(tmp_path):
    bruto = tmp_path / "r.json"
    bruto.write_text(
        json.dumps({"publishRate": [100, 200], "aggregatedEndToEndLatency50pct": 3, "aggregatedEndToEndLatency99pct": 8}),
        encoding="utf-8",
    )
    metricas = interpretar_resultado_omb(bruto, 1024)
    assert metricas["throughput_msg_s"] == 150
    assert metricas["throughput_mib_s"] == pytest.approx(150 / 1024, abs=1e-6)
    assert metricas["latencia_p99_ms"] == 8
    assert interpretar_stats("12.5%|256MiB / 4GiB") == (12.5, 256.0)


def test_taxa_e2_e_metade_do_menor_mediano(tmp_path):
    diretorio = criar_diretorio_coleta(tmp_path)
    coletor = Coletor(diretorio, ExecutorFake(diretorio))
    for execucao in plano.gerar_plano("E1", 3):
        coletor.executar_uma(execucao, 0)
    assert taxas_e2(coletor.resultados) == {1024: 425, 16384: 425}


def test_piloto_registra_24_tentativas_e_metadados(tmp_path):
    diretorio = criar_diretorio_coleta(tmp_path)
    executor = ExecutorFake(diretorio)
    resultados = Coletor(diretorio, executor).piloto()
    assert len(resultados) == 24
    assert all(r.status == "sucesso" for r in resultados)
    assert len(executor.executadas) == 24
    assert executor.limpezas >= 25
    assert len((diretorio / "resultados.csv").read_text(encoding="utf-8").splitlines()) == 25
    manifesto = json.loads((diretorio / "manifesto.json").read_text(encoding="utf-8"))
    assert manifesto["status"] == "concluida"
    assert manifesto["registradas"] == 24
    assert manifesto["contagens"] == {"sucesso": 24}


def test_falha_e_preservada_e_bloqueia_e2_da_celula(tmp_path):
    diretorio = criar_diretorio_coleta(tmp_path)
    falhar = {e.id_execucao for e in plano.gerar_plano("E1", 3) if e.broker == "rabbitmq" and e.tamanho_bytes == 1024}
    resultados = Coletor(diretorio, ExecutorFake(diretorio, falhar)).piloto()
    assert len(resultados) == 24
    assert sum(r.status == "falha" for r in resultados) == 3
    bloqueadas = [r for r in resultados if r.status == "bloqueada"]
    assert len(bloqueadas) == 6
    assert {r.tamanho_bytes for r in bloqueadas} == {1024}
    assert all(r.erro for r in resultados if r.status != "sucesso")
