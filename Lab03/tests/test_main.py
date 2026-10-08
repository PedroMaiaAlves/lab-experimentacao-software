import pytest

import pipeline.__main__ as pipeline_main
from pipeline.__main__ import (
    executar_etapas_de_coleta,
    executar_pipeline,
    validar_tamanho_amostra,
)


def test_amostra_menor_que_meta_falha_claramente():
    with pytest.raises(RuntimeError, match="2 repositórios aceitos.*meta configurada: 3"):
        validar_tamanho_amostra([{}, {}], 3)


def test_amostra_com_meta_atingida_e_valida():
    validar_tamanho_amostra([{}, {}], 2)


def test_modulo_de_coleta_ausente_nao_e_ignorado():
    cfg = {"etapas_coleta": ["pipeline.modulo_que_nao_existe"]}
    with pytest.raises(ModuleNotFoundError):
        executar_etapas_de_coleta(object(), cfg, [])


def test_meta_da_linha_de_comando_deve_ser_positiva(capsys):
    with pytest.raises(SystemExit):
        pipeline_main.main(["--meta", "0"])
    assert "--meta deve ser um inteiro positivo" in capsys.readouterr().err


def test_pipeline_preserva_ordem_e_passa_a_mesma_amostra(monkeypatch, tmp_path):
    eventos = []
    candidatos = [{"full_name": "org/candidato"}]
    aprovados = [{"full_name": "org/aprovado"}]

    def selecionar(client, cfg):
        eventos.append(("selecao", client, cfg))
        return candidatos

    def salvar(recebidos, caminho):
        eventos.append(("salvar", recebidos, caminho))

    def funil(client, recebidos, cfg, dados):
        eventos.append(("funil", recebidos, dados))
        return aprovados

    def coletas(client, cfg, recebidos):
        eventos.append(("coletas", recebidos, cfg))

    monkeypatch.setattr(pipeline_main, "selecionar_candidatos", selecionar)
    monkeypatch.setattr(pipeline_main, "salvar_candidatos", salvar)
    monkeypatch.setattr(pipeline_main, "executar_funil", funil)
    monkeypatch.setattr(pipeline_main, "executar_etapas_de_coleta", coletas)
    cfg = {"saida": {"dir_dados": str(tmp_path)}, "selecao": {"meta_repositorios": 1}}
    client = object()

    resultado = executar_pipeline(client, cfg)

    assert [evento[0] for evento in eventos] == ["selecao", "salvar", "funil", "coletas"]
    assert eventos[1][1] is candidatos
    assert eventos[2][1] is candidatos
    assert eventos[3][1] is aprovados
    assert resultado is aprovados
