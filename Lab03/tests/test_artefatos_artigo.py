import pytest
import pandas as pd

from validacao.artefatos_artigo import (
    calcular_macros, escapar, fmt_int, limites_estrelas, main, tabela_funil, texto_faixa)

FUNIL = ("etapa,entraram,descartados,restaram,motivo_descarte\n"
         "candidatos_na_busca,53143,,53143,\n"
         "candidatos_avaliados,747,,747,parou ao atingir a meta\n"
         "actions,747,328,419,sem_actions\n"
         "releases,419,284,135,menos_de_5_releases\n"
         "runs,135,35,100,menos_de_50_runs_validos\n"
         "amostra_final,,,100,\n")
CONFIG = ("janela_inicio: 2025-10-01\njanela_fim: 2026-09-30\nsemente: 42\n"
          "criterios: {min_releases: 5, min_runs: 50}\n"
          "selecao:\n  faixas_estrelas: ['1000..1500', '5000..8000']\n")


def test_formatos():
    assert fmt_int(53143) == "53.143" and fmt_int("100") == "100"
    assert escapar("menos_de_5") == "menos\\_de\\_5"


def test_limites_e_texto_da_faixa():
    assert limites_estrelas(["1000..1500", "5000..8000"]) == (1000, 8000)
    assert limites_estrelas(["1000..1500", ">30000"]) == (1000, None)
    assert texto_faixa(1000, 8000) == "1.000 a 8.000 estrelas"
    assert texto_faixa(1000, None) == "mais de 1.000 estrelas"
    with pytest.raises(ValueError):
        limites_estrelas(["abc"])


def test_main_gera_tabela_e_macros(tmp_path):
    (tmp_path / "config.yaml").write_text(CONFIG, encoding="utf-8")
    dados = tmp_path / "data"
    dados.mkdir()
    (dados / "funil.csv").write_text(FUNIL, encoding="utf-8")
    (dados / "runs_saturados.csv").write_text(
        "full_name,inicio,fim,total_count,status\na/x,2026-09-01,2026-09-30,1050,subdividido\n"
        "a/x,2026-08-01,2026-08-31,1100,incompleto\nb/y,2026-07-01,2026-07-31,1045,subdividido\n", encoding="utf-8")
    (dados / "lead_time.csv").write_text(
        "full_name,releases_comparadas,releases_sem_anterior,releases_erro_404,releases_sem_commits,commits_data_invalida\n"
        "a/x,14,1,0,2,0\nb/y,1200,0,3,5,7\n", encoding="utf-8")
    saida = tmp_path / "tabelas"
    assert main(["--config", str(tmp_path / "config.yaml"), "--dados", str(dados), "--saida", str(saida)]) == 0
    tabela = (saida / "funil.tex").read_text(encoding="utf-8")
    assert "53.143" in tabela and "Amostra final" in tabela and "-- & -- & 100" in tabela
    assert "$\\geq$ 50 execuções" in tabela
    numeros = (saida / "numeros.tex").read_text(encoding="utf-8")
    assert "\\newcommand{\\labJanelaInicio}{01/10/2025}" in numeros
    assert "\\newcommand{\\labReposAmostra}{100}" in numeros
    assert "\\newcommand{\\labFaixaEstrelas}{1.000 a 8.000 estrelas}" in numeros
    assert "\\newcommand{\\labReposSaturados}{2}" in numeros
    assert "\\newcommand{\\labIntervalosIncompletos}{1}" in numeros
    assert "\\newcommand{\\labReleasesComparadas}{1.214}" in numeros
    assert "\\newcommand{\\labReleasesErroHttp}{3}" in numeros


def test_arquivos_ausentes_viram_pendencia(tmp_path, capsys):
    (tmp_path / "config.yaml").write_text(CONFIG, encoding="utf-8")
    (tmp_path / "data").mkdir()
    assert main(["--config", str(tmp_path / "config.yaml"), "--dados", str(tmp_path / "data"),
                 "--saida", str(tmp_path / "t")]) == 0
    assert "[PREENCHER]" in (tmp_path / "t" / "numeros.tex").read_text(encoding="utf-8")
    assert not (tmp_path / "t" / "funil.tex").exists()
    assert "Macros pendentes" in capsys.readouterr().out


def test_faixa_do_snapshot_prevalece_sobre_expansao_nao_executada():
    cfg = {"janela_inicio": "2025-10-01", "janela_fim": "2026-09-30", "semente": 42,
           "criterios": {"min_releases": 5, "min_runs": 50},
           "selecao": {"faixas_estrelas": ["1000..1500", ">30000"]}}
    candidatos = pd.DataFrame({"consulta": ["stars:1000..1500 fork:false", "stars:5000..8000 fork:false"]})
    macros = calcular_macros(cfg, None, None, None, candidatos)
    assert macros["FaixaEstrelas"] == "1.000 a 8.000 estrelas"
    with pytest.raises(ValueError, match="sem faixas"):
        calcular_macros(cfg, None, None, None, pd.DataFrame({"consulta": ["fork:false"]}))
