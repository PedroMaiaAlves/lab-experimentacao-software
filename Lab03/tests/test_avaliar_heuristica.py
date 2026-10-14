import csv
from pathlib import Path
import subprocess
import sys

import pytest

from scripts.avaliar_heuristica import (
    CAMPOS_CONSENSO,
    _ler_csv,
    avaliar_linhas,
    calcular_metricas,
    registrar_resultado,
)

REGRAS = {
    "versao": "v1",
    "usar_patch_semver": True,
    "usar_palavras_commits": True,
    "palavras_chave": ["fix", "hotfix", "revert"],
    "janela_dias": 7,
    "politica_tag_nao_semver": "fallback_textual",
}


def comparacao(numero, anterior, atual):
    return {"full_name": "o/r", "release_id": str(numero), "tag_name": atual,
            "previous_tag_name": anterior, "status": "ok"}


def rotulo(numero, valor):
    return {"full_name": "o/r", "release_id": str(numero), "corretiva": valor}


def test_metricas_conhecidas_incluem_matriz_e_suporte():
    assert calcular_metricas([True, True, False, False], [True, False, True, False]) == {
        "precisao": 0.5,
        "recall": 0.5,
        "f1": 0.5,
        "suporte": 2,
        "tp": 1,
        "fp": 1,
        "fn": 1,
        "tn": 1,
    }


def test_avaliacao_junta_fontes_e_classifica_quatro_resultados():
    consenso = [rotulo(1, "sim"), rotulo(2, "nao"), rotulo(3, "sim"), rotulo(4, "nao")]
    comparacoes = [
        comparacao(1, "v1.0.0", "v1.0.1"),
        comparacao(2, "release-a", "release-b"),
        comparacao(3, "v1.0.1", "v1.1.0"),
        comparacao(4, "v1.1.0", "v1.2.0"),
    ]
    commits = [{"full_name": "o/r", "release_id": "2", "message": "hotfix urgente"}]
    auditoria, metricas = avaliar_linhas(consenso, comparacoes, commits, REGRAS)
    assert [linha["tipo_resultado"] for linha in auditoria] == ["VP", "FP", "FN", "VN"]
    assert metricas["f1"] == pytest.approx(0.5)
    assert auditoria[0]["criterio_patch"] is True
    assert auditoria[1]["palavras_encontradas"] == "hotfix"


def test_avaliacao_rejeita_chave_duplicada_ou_ausente():
    consenso = [rotulo(1, "sim"), rotulo(1, "nao")]
    with pytest.raises(ValueError, match="chave duplicada"):
        avaliar_linhas(consenso, [comparacao(1, "v1.0.0", "v1.0.1")], [], REGRAS)
    with pytest.raises(ValueError, match="sem comparação"):
        avaliar_linhas([rotulo(9, "sim")], [comparacao(1, "v1.0.0", "v1.0.1")], [], REGRAS)


def test_leitura_rejeita_schema_sem_identificador(tmp_path):
    caminho = tmp_path / "consenso.csv"
    caminho.write_text("full_name,corretiva\no/r,sim\n", encoding="utf-8")
    with pytest.raises(ValueError, match="release_id"):
        _ler_csv(caminho, CAMPOS_CONSENSO, "consenso")


def test_registro_e_idempotente_e_atualiza_markdown(tmp_path):
    historico = tmp_path / "historico.csv"
    documento = tmp_path / "versoes.md"
    documento.write_text(
        "Antes\n<!-- resultados:start -->\ntabela antiga\n<!-- resultados:end -->\nDepois\n",
        encoding="utf-8",
    )
    metricas = calcular_metricas([True, False], [True, False])
    registrar_resultado(historico, documento, "v1", metricas, REGRAS)
    metricas_atualizadas = calcular_metricas([True, True], [True, False])
    registrar_resultado(historico, documento, "v1", metricas_atualizadas, REGRAS)

    with historico.open(newline="", encoding="utf-8") as arquivo:
        linhas = list(csv.DictReader(arquivo))
    assert len(linhas) == 1 and float(linhas[0]["f1"]) == pytest.approx(2 / 3)
    texto = documento.read_text(encoding="utf-8")
    assert texto.count("| v1 |") == 1
    assert "| 0.667 |" in texto


def test_cli_documentado_pode_ser_executado_diretamente():
    raiz = Path(__file__).resolve().parents[1]
    resultado = subprocess.run(
        [sys.executable, "scripts/avaliar_heuristica.py", "--help"],
        cwd=raiz,
        capture_output=True,
        text=True,
        check=False,
    )
    assert resultado.returncode == 0
    assert "--consenso" in resultado.stdout
