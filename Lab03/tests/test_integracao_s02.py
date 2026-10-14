from pathlib import Path

from pipeline.config import carregar_config
from pipeline.dataset import gerar_dataset
import pipeline.sprint2 as sprint
from tests.fakes import ClienteFalso


def test_300_repositorios_simulados_coleta_congelamento_dataset_e_recalculo(tmp_path, monkeypatch):
    cfg = carregar_config("config_s02.yaml")
    cfg["saida"] = {"dir_dados": str(tmp_path / "dados"), "dir_cache": str(tmp_path / "cache")}
    candidatos, rotas = [], {}
    for i in range(300):
        nome = f"org/repo{i:03d}"
        candidatos.append({"full_name": nome, "stars": 1500, "language": "Python", "default_branch": "main",
                           "created_at": "2020-01-01T00:00:00Z", "html_url": f"https://github.com/{nome}",
                           "consulta": "fixture offline"})
        releases = [{"id": n, "tag_name": f"v1.0.{n}", "published_at": f"2026-01-{n:02d}T00:00:00Z",
                     "draft": False, "prerelease": False} for n in range(1, 6)]
        releases.insert(0, {"id": 0, "tag_name": "v1.0.0", "published_at": "2025-09-01T00:00:00Z",
                            "draft": False, "prerelease": False})
        rotas[f"/repos/{nome}/releases"] = releases
        rotas[f"/repos/{nome}/tags"] = [{"name": "v1.0.5", "commit": {"sha": "abc"}}]
        commit = {"sha": "abc", "commit": {"author": {"date": "2025-12-31T00:00:00Z"}, "message": "feat: baseline"}}
        rotas[f"/repos/{nome}/commits/abc"] = commit
        for n in range(1, 6):
            rotas[f"/repos/{nome}/compare/v1.0.{n-1}...v1.0.{n}"] = {"commits": [commit]}
        runs = [{"id": n, "workflow_id": 1, "conclusion": "success", "name": "testes",
                 "created_at": f"2026-01-01T10:{n:02d}:00Z", "run_started_at": f"2026-01-01T10:{n:02d}:00Z",
                 "updated_at": f"2026-01-01T10:{n:02d}:10Z"} for n in range(50)]
        def resposta(params, runs=runs):
            itens = runs if params["created"].startswith("2026-01") else []
            return {"workflow_runs": itens, "total_count": len(itens)}
        rotas[f"/repos/{nome}/actions/runs"] = resposta
    monkeypatch.setattr(sprint, "usa_actions", lambda *args: True)
    monkeypatch.setattr(sprint, "contar_releases_janela", lambda *args: 5)
    monkeypatch.setattr(sprint, "contar_runs_validos", lambda *args: 50)
    monkeypatch.setattr(sprint, "coletar_metadados", lambda cli, r, cfg: {
        **{c: r[c] for c in sprint.CAMPOS_META if c in r}, "idade_dias": 2464, "contribuidores": 10})
    origem = tmp_path / "candidatos.csv"
    sprint.salvar_candidatos(candidatos, origem)
    amostra = tmp_path / "amostra_final.csv"
    client = ClienteFalso(rotas)
    checkpoint = sprint.executar(client, cfg, origem, amostra)
    assert len(checkpoint["coletados"]) == len(sprint.ler_csv(amostra)) == 300
    chamadas = len(client.chamadas)
    sprint.executar(client, cfg, origem, amostra)
    assert len(client.chamadas) == chamadas
    destino, relato = tmp_path / "dataset.csv", tmp_path / "coleta.tex"
    resumo = gerar_dataset(cfg, amostra, tmp_path / "sem-consenso.csv", destino, relato)
    assert resumo["repositorios"] == resumo["repositorios_sem_tipo"] == 300
    assert resumo["totais"]["runs_validos"] == 15000
    assert resumo["totais"]["releases_principais"] == 1500
    assert {r["cfr_b"] for r in sprint.ler_csv(destino)} == {"0.8"}
    assert "300 repositórios" in relato.read_text(encoding="utf-8")
    cfg["heuristica_release"].update(versao="v2-fixture", usar_patch_semver=False)
    gerar_dataset(cfg, amostra, tmp_path / "sem-consenso.csv", destino)
    assert {r["cfr_b"] for r in sprint.ler_csv(destino)} == {"0.0"}
    assert len(client.chamadas) == chamadas
