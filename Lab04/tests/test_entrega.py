from experimento.dados import ROOT
from experimento.simulacao import executar
from experimento.validacao import validar_entrega


def test_entrega_preservada_tem_30_pares_e_reproducao_exata():
    result = validar_entrega()
    assert result == {"status": "ok", "pares_reais": 30, "pares_simulados": 30,
                      "aquecimento_separado": 3, "reproducao_exata": True}


def test_regeracao_completa_offline_produz_mesmos_artefatos(tmp_path, monkeypatch):
    def sem_rede(*args, **kwargs):
        raise AssertionError("Reprodução não deve acessar a rede.")

    monkeypatch.setattr("urllib.request.urlopen", sem_rede)
    executar(ROOT / "data/real", tmp_path)
    for name in ("parametros.json", "pares_simulados.csv", "manifesto.json"):
        assert (tmp_path / name).read_bytes() == (ROOT / "data/simulado" / name).read_bytes()
