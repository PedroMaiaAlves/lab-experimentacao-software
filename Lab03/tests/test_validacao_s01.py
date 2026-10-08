import csv
import json
from datetime import date

import pytest

from pipeline.validacao_s01 import CSVS_OBRIGATORIOS, validar_artefatos_s01


@pytest.fixture
def execucao_completa(tmp_path):
    repos = [
        {"full_name": "org/um", "default_branch": "main"},
        {"full_name": "org/dois", "default_branch": "trunk"},
    ]
    cfg = {
        "janela_inicio": date(2025, 10, 1),
        "janela_fim": date(2026, 9, 30),
        "criterios": {"min_releases": 5, "min_runs": 50},
        "saida": {"dir_dados": str(tmp_path)},
    }

    def csv_saida(nome, campos, linhas=()):
        with (tmp_path / nome).open("w", newline="", encoding="utf-8") as arquivo:
            escritor = csv.DictWriter(arquivo, fieldnames=campos)
            escritor.writeheader()
            escritor.writerows(linhas)

    nomes = [{"full_name": repo["full_name"]} for repo in repos]
    csv_saida("candidatos.csv", ["full_name"], nomes)
    csv_saida(
        "funil.csv",
        ["etapa", "restaram"],
        [{"etapa": "amostra_final", "restaram": str(len(repos))}],
    )
    csv_saida("descartes.csv", ["full_name", "etapa", "motivo"])
    csv_saida("metadados.csv", ["full_name"], nomes)
    releases = []
    for repo in repos:
        releases.extend(
            {
                "full_name": repo["full_name"],
                "draft": "False",
                "prerelease": "False",
                "published_at": f"2026-0{mes}-01T00:00:00Z",
            }
            for mes in range(1, 6)
        )
    csv_saida(
        "releases.csv",
        ["full_name", "draft", "prerelease", "published_at"],
        releases,
    )
    csv_saida("tags.csv", ["full_name"])
    csv_saida("comparacoes_releases.csv", ["full_name"])
    csv_saida("commits_entre_releases.csv", ["full_name"])
    csv_saida("lead_time.csv", ["full_name"], nomes)
    csv_saida("deployment_frequency.csv", ["full_name"], nomes)
    csv_saida(
        "runs_saturados.csv",
        ["full_name", "inicio", "fim", "total_count", "status"],
    )

    runs_dir = tmp_path / "workflow_runs"
    runs_dir.mkdir()
    for repo in repos:
        dados = {
            "full_name": repo["full_name"],
            "default_branch": repo["default_branch"],
            "janela_inicio": "2025-10-01",
            "janela_fim": "2026-09-30",
            "complete": True,
            "saturated_intervals": [],
            "workflow_runs": [
                {"id": numero, "conclusion": "success"} for numero in range(50)
            ],
        }
        nome = repo["full_name"].replace("/", "__") + ".json"
        (runs_dir / nome).write_text(json.dumps(dados), encoding="utf-8")
    return cfg, repos, tmp_path


def test_aceita_execucao_completa_e_coerente(execucao_completa):
    cfg, repos, _ = execucao_completa
    assert validar_artefatos_s01(cfg, repos) == {
        "repositorios": 2,
        "arquivos_csv": len(CSVS_OBRIGATORIOS),
    }


def test_rejeita_arquivo_obrigatorio_ausente(execucao_completa):
    cfg, repos, diretorio = execucao_completa
    (diretorio / "lead_time.csv").unlink()
    with pytest.raises(RuntimeError, match="lead_time.csv"):
        validar_artefatos_s01(cfg, repos)


def test_rejeita_coleta_de_runs_incompleta(execucao_completa):
    cfg, repos, diretorio = execucao_completa
    caminho = diretorio / "workflow_runs" / "org__um.json"
    dados = json.loads(caminho.read_text(encoding="utf-8"))
    dados["complete"] = False
    caminho.write_text(json.dumps(dados), encoding="utf-8")
    with pytest.raises(RuntimeError, match="marcada como incompleta"):
        validar_artefatos_s01(cfg, repos)


def test_rejeita_resumo_sem_toda_a_amostra(execucao_completa):
    cfg, repos, diretorio = execucao_completa
    with (diretorio / "metadados.csv").open("w", newline="", encoding="utf-8") as arquivo:
        escritor = csv.DictWriter(arquivo, fieldnames=["full_name"])
        escritor.writeheader()
        escritor.writerow({"full_name": "org/um"})
    with pytest.raises(RuntimeError, match="metadados.csv.*org/dois"):
        validar_artefatos_s01(cfg, repos)


def test_rejeita_repositorio_abaixo_dos_criterios(execucao_completa):
    cfg, repos, diretorio = execucao_completa
    caminho = diretorio / "workflow_runs" / "org__dois.json"
    dados = json.loads(caminho.read_text(encoding="utf-8"))
    dados["workflow_runs"] = dados["workflow_runs"][:49]
    caminho.write_text(json.dumps(dados), encoding="utf-8")
    with pytest.raises(RuntimeError, match="49 válidos; mínimo 50"):
        validar_artefatos_s01(cfg, repos)
