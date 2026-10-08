import csv
import json
from datetime import date

from pipeline.coleta_runs import (
    coletar,
    coletar_runs_repositorio,
    contar_runs_validos_repositorio,
)

CFG = {
    "janela_inicio": date(2025, 10, 1),
    "janela_fim": date(2026, 9, 30),
}
REPO = {"full_name": "org/projeto", "default_branch": "main"}


def run(identificador, criado="2025-10-10T10:00:00Z", conclusao="success"):
    return {
        "id": identificador,
        "workflow_id": 10,
        "name": "CI",
        "conclusion": conclusao,
        "run_started_at": criado,
        "updated_at": criado,
        "created_at": criado,
        "campo_extra": "não deve ser salvo",
    }


class ClienteColeta:
    def __init__(self, responder):
        self.responder = responder
        self.chamadas = []

    def get_json(self, caminho, params=None):
        self.chamadas.append((caminho, params))
        return self.responder(caminho, params)


def test_consulta_cada_mes_com_branch_evento_e_janela():
    def responder(_caminho, params):
        itens = [run(1)] if params["created"] == "2025-10-01..2025-10-31" else []
        return {"total_count": len(itens), "workflow_runs": itens}, {}

    cliente = ClienteColeta(responder)
    resultado = coletar_runs_repositorio(cliente, REPO, CFG)
    assert len(cliente.chamadas) == 12
    assert all(params["branch"] == "main" and params["event"] == "push"
               for _, params in cliente.chamadas)
    assert resultado["complete"] is True
    assert resultado["workflow_runs"][0] == {
        "id": 1, "workflow_id": 10, "name": "CI", "conclusion": "success",
        "run_started_at": "2025-10-10T10:00:00Z",
        "updated_at": "2025-10-10T10:00:00Z",
        "created_at": "2025-10-10T10:00:00Z",
    }


def test_total_1000_subdivide_intervalo_e_remove_duplicatas():
    def responder(_caminho, params):
        intervalo = params["created"]
        if intervalo == "2025-10-01..2025-10-31":
            return {"total_count": 1000, "workflow_runs": [run(99)]}, {}
        if intervalo == "2025-10-01..2025-10-16":
            return {"total_count": 1, "workflow_runs": [run(1)]}, {}
        if intervalo == "2025-10-17..2025-10-31":
            return {"total_count": 2, "workflow_runs": [run(1), run(2)]}, {}
        return {"total_count": 0, "workflow_runs": []}, {}

    resultado = coletar_runs_repositorio(ClienteColeta(responder), REPO, CFG)
    assert [r["id"] for r in resultado["workflow_runs"]] == [1, 2]
    assert resultado["complete"] is True
    assert resultado["saturated_intervals"] == [{
        "full_name": "org/projeto", "inicio": "2025-10-01", "fim": "2025-10-31",
        "total_count": 1000, "status": "subdividido",
    }]


def test_paginacao_do_intervalo():
    proxima = "https://api.github.com/repos/org/projeto/actions/runs?page=2"

    def responder(caminho, params):
        if caminho == proxima:
            assert params is None
            return {"total_count": 2, "workflow_runs": [run(2)]}, {}
        if params["created"] == "2025-10-01..2025-10-31":
            return ({"total_count": 2, "workflow_runs": [run(1)]},
                    {"link": f'<{proxima}>; rel="next"'})
        return {"total_count": 0, "workflow_runs": []}, {}

    resultado = coletar_runs_repositorio(ClienteColeta(responder), REPO, CFG)
    assert [r["id"] for r in resultado["workflow_runs"]] == [1, 2]


def test_dia_ainda_saturado_fica_marcado_como_incompleto():
    cfg = {"janela_inicio": date(2026, 1, 1), "janela_fim": date(2026, 1, 1)}

    def responder(_caminho, _params):
        return {"total_count": 1000, "workflow_runs": [run(1)]}, {}

    resultado = coletar_runs_repositorio(ClienteColeta(responder), REPO, cfg)
    assert resultado["complete"] is False
    assert resultado["saturated_intervals"][0]["status"] == "incompleto"


def test_coletar_grava_json_e_relatorio_csv(tmp_path):
    cfg = {**CFG, "saida": {"dir_dados": str(tmp_path)}}

    def responder(_caminho, params):
        itens = [run(1)] if params["created"] == "2025-10-01..2025-10-31" else []
        return {"total_count": len(itens), "workflow_runs": itens}, {}

    coletar(ClienteColeta(responder), cfg, [REPO])
    arquivo = tmp_path / "workflow_runs" / "org__projeto.json"
    assert json.loads(arquivo.read_text(encoding="utf-8"))["workflow_runs"][0]["id"] == 1
    with open(tmp_path / "runs_saturados.csv", newline="", encoding="utf-8") as f:
        assert list(csv.DictReader(f)) == []


def test_contagem_do_funil_para_assim_que_atinge_o_limite():
    def responder(_caminho, params):
        assert params["created"] == "2025-10-01..2025-10-31"
        itens = [run(i) for i in range(1, 51)]
        return {"total_count": len(itens), "workflow_runs": itens}, {}

    cliente = ClienteColeta(responder)
    assert contar_runs_validos_repositorio(cliente, REPO, CFG, 50) == 50
    assert len(cliente.chamadas) == 1
