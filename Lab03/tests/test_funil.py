import csv
from datetime import date

from pipeline.funil import contar_contribuidores, executar_funil
from tests.fakes import ClienteFalso

CFG = {"janela_inicio": date(2025, 10, 1), "janela_fim": date(2026, 9, 30),
       "criterios": {"min_releases": 5, "min_runs": 50},
       "selecao": {"meta_repositorios": 10}}
LINK_42 = ('<https://api.github.com/x?per_page=1&anon=true&page=2>; rel="next", '
           '<https://api.github.com/x?per_page=1&anon=true&page=42>; rel="last"')
RELEASES_OK = [{"draft": False, "published_at": f"2026-01-{10 + i}T10:00:00Z"} for i in range(5)]


def cand(nome):
    return {"full_name": nome, "stars": "5000", "language": "Python", "default_branch": "main",
            "created_at": "2020-01-01T00:00:00Z", "html_url": "x", "consulta": "q"}


def rotas(nome, workflows=1, releases=None, runs=None, link=""):
    releases = RELEASES_OK if releases is None else releases
    runs = {"success": 60} if runs is None else runs

    def rota_runs(params):
        if not params["created"].startswith("2026-01"):
            return {"total_count": 0, "workflow_runs": []}
        itens = []
        identificador = 1
        for conclusao, quantidade in runs.items():
            for _ in range(quantidade):
                itens.append({
                    "id": identificador,
                    "workflow_id": 10,
                    "name": "CI",
                    "conclusion": conclusao,
                    "run_started_at": f"2026-01-{1 + identificador % 20:02d}T10:00:00Z",
                    "updated_at": f"2026-01-{1 + identificador % 20:02d}T10:05:00Z",
                    "created_at": f"2026-01-{1 + identificador % 20:02d}T10:00:00Z",
                })
                identificador += 1
        return {"total_count": len(itens), "workflow_runs": itens}

    return {
        f"/repos/{nome}/actions/workflows": {"total_count": workflows},
        f"/repos/{nome}/releases": releases,
        f"/repos/{nome}/actions/runs": rota_runs,
        f"/repos/{nome}/contributors": ([{"login": "x"}], {"link": link}),
    }


def ler(caminho):
    with open(caminho, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def test_funil_conta_descartes_por_etapa(tmp_path):
    todas = {}
    todas.update(rotas("a/ok", link=LINK_42))
    todas.update(rotas("b/sem-actions", workflows=0))
    todas.update(rotas("c/poucas-releases", releases=RELEASES_OK[:2]))
    todas.update(rotas("d/poucos-runs", runs={"success": 10, "failure": 5}))
    nomes = ["a/ok", "b/sem-actions", "c/poucas-releases", "d/poucos-runs"]

    aceitos = executar_funil(ClienteFalso(todas), [cand(n) for n in nomes], CFG, tmp_path)

    assert [a["full_name"] for a in aceitos] == ["a/ok"]
    funil = {l["etapa"]: l for l in ler(tmp_path / "funil.csv")}
    assert funil["candidatos_avaliados"]["restaram"] == "4"
    assert (funil["actions"]["entraram"], funil["actions"]["descartados"]) == ("4", "1")
    assert (funil["releases"]["entraram"], funil["releases"]["descartados"]) == ("3", "1")
    assert (funil["runs"]["entraram"], funil["runs"]["descartados"]) == ("2", "1")
    assert funil["amostra_final"]["restaram"] == "1"
    motivos = {l["full_name"]: l["motivo"] for l in ler(tmp_path / "descartes.csv")}
    assert motivos["b/sem-actions"] == "sem_actions"
    assert motivos["c/poucas-releases"] == "menos_de_5_releases"
    assert motivos["d/poucos-runs"] == "menos_de_50_runs_validos"
    meta = ler(tmp_path / "metadados.csv")[0]
    assert meta["contribuidores"] == "42" and meta["idade_dias"] == str((date(2026, 9, 30) - date(2020, 1, 1)).days)


def test_releases_draft_e_fora_da_janela_nao_contam(tmp_path):
    ruins = [{"draft": True, "published_at": "2026-01-10T10:00:00Z"},
             {"draft": False, "published_at": "2024-01-10T10:00:00Z"}] + RELEASES_OK[:3]
    cli = ClienteFalso(rotas("a/x", releases=ruins))
    assert executar_funil(cli, [cand("a/x")], CFG, tmp_path) == []


def test_prereleases_nao_contam_para_o_minimo(tmp_path):
    ruins = [
        {"draft": False, "prerelease": True, "published_at": "2026-01-10T10:00:00Z"},
        *RELEASES_OK[:4],
    ]
    cli = ClienteFalso(rotas("a/x", releases=ruins))
    assert executar_funil(cli, [cand("a/x")], CFG, tmp_path) == []


def test_startup_failure_e_contada_localmente(tmp_path):
    cli = ClienteFalso(rotas("a/x", runs={"success": 49, "startup_failure": 1}))
    assert len(executar_funil(cli, [cand("a/x")], CFG, tmp_path)) == 1
    chamadas_runs = [params for caminho, params in cli.chamadas if caminho.endswith("/actions/runs")]
    assert chamadas_runs
    assert all("status" not in params for params in chamadas_runs)


def test_para_ao_atingir_a_meta(tmp_path):
    todas = {**rotas("a/ok"), **rotas("e/ok2")}
    cfg = {**CFG, "selecao": {"meta_repositorios": 1}}
    cli = ClienteFalso(todas)
    aceitos = executar_funil(cli, [cand("a/ok"), cand("e/ok2")], cfg, tmp_path)
    assert len(aceitos) == 1
    assert not any("e/ok2" in caminho for caminho, _ in cli.chamadas)


def test_contribuidores_sem_cabecalho_link_usa_tamanho_da_lista():
    cli = ClienteFalso({"/repos/a/x/contributors": ([{"login": "u"}], {})})
    assert contar_contribuidores(cli, "a/x") == 1
    cli = ClienteFalso({"/repos/a/x/contributors": ([], {})})
    assert contar_contribuidores(cli, "a/x") == 0
