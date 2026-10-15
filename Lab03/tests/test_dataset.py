from copy import deepcopy
import csv
import json
from pathlib import Path
import shutil

import pytest

from pipeline.config import carregar_config
from pipeline.dataset import CAMPOS, CAMPOS_COMPLEMENTARES, calcular_linha, carregar_complementar, carregar_rotulos, gerar_dataset
from pipeline.sprint2 import fontes_repo, ler_csv, pasta_repo, salvar_csv, sha256


@pytest.fixture
def fontes():
    cfg = carregar_config("config_s02.yaml")
    cfg["heuristica_release"]["versao"] = "v1"
    repo = {"full_name": "o/r", "stars": "1000", "language": "Python", "default_branch": "main",
            "created_at": "2020-01-01", "idade_dias": "1000", "contribuidores": "10"}
    datas = ["2026-01-01T00:00:00Z", "2026-01-05T00:00:00Z", "2026-09-29T00:00:00Z"]
    releases = [{"id": str(i), "tag_name": tag, "published_at": data, "draft": False, "prerelease": False}
                for i, (tag, data) in enumerate(zip(["v1.0.0", "v1.0.1", "v2.0.0"], datas), 1)]
    comps = [{"release_id": r["id"], "previous_tag_name": anterior, "status": "ok", "commits_count": "1"}
             for r, anterior in zip(releases, ["v0.9.0", "v1.0.0", "v1.0.1"])]
    commits = [{"release_id": str(i), "author_date": data, "message": texto, "sha": str(i)}
               for i, (data, texto) in enumerate(zip(["2025-12-31T00:00:00Z", "2026-01-02T00:00:00Z",
                                                     "2026-09-28T00:00:00Z"], ["feat: a", "fix: b", "feat: c"]), 1)]
    tags = [{"status": "ok", "commit_author_date": "2026-01-02T00:00:00Z"},
            {"status": "erro_404", "commit_author_date": ""}]
    runs = [{"workflow_id": 1, "conclusion": conclusao, "run_started_at": inicio, "updated_at": fim}
            for conclusao, inicio, fim in [
                ("success", "2026-01-01T09:00:00Z", "2026-01-01T09:05:00Z"),
                ("failure", "2026-01-01T10:00:00Z", "2026-01-01T10:05:00Z"),
                ("success", "2026-01-01T11:15:00Z", "2026-01-01T11:20:00Z"),
                ("cancelled", "2026-01-01T12:00:00Z", "2026-01-01T12:05:00Z"),
                ("failure", "2026-09-30T10:00:00Z", "2026-09-30T10:05:00Z")]]
    return repo, releases, comps, commits, tags, runs, cfg


def test_variantes_censura_contagens_e_tipos_ausentes(fontes):
    resultado = calcular_linha(*fontes)
    assert set(resultado) == set(CAMPOS)
    assert resultado["cfr_a"] == 0.5 and resultado["cfr_b"] == 0.5
    assert resultado["releases_censuradas"] == 1 and resultado["releases_avaliadas"] == 2
    assert resultado["tempo_recuperacao_horas"] == pytest.approx(4 / 3)
    assert resultado["episodios_total"] == 2 and resultado["proporcao_censurados"] == 0.5
    assert resultado["runs_ignorados"] == 1 and resultado["runs_validos"] == 4
    assert resultado["lead_time_a_horas"] == resultado["lead_time_b_horas"] == 24
    assert resultado["deployment_frequency"] == pytest.approx(3 * 7 / 365)
    assert resultado["deployment_frequency_tags"] == pytest.approx(7 / 365)
    assert resultado["tipo_projeto"] is None and not resultado["rotulo_disponivel"]
    assert resultado["tags_sem_data"] == 1


def test_v3_integrada_no_dataset_com_texto_e_censura(fontes):
    repo, releases, comps, commits, tags, runs, cfg = deepcopy(fontes)
    cfg["heuristica_release"]["versao"] = "v3"
    resultado = calcular_linha(repo, releases, comps, commits, tags, runs, cfg)
    assert resultado["heuristica_versao"] == "v3" and resultado["cfr_b"] == 0.5
    assert resultado["releases_censuradas"] == 1 and resultado["cfr_b_disponivel"]
    cfg["heuristica_release"]["usar_palavras_commits"] = False
    for commit in commits:
        commit["message"] = ""
    resultado = calcular_linha(repo, releases, comps, commits, tags, runs, cfg)
    assert resultado["cfr_b"] == 0.5 and resultado["cfr_b_disponivel"]


def test_404_sem_evidencia_nao_vira_sucesso_no_cfr_b(fontes):
    repo, releases, comps, commits, tags, runs, cfg = deepcopy(fontes)
    comps[2].update(status="erro_404", commits_count="0")
    resultado = calcular_linha(repo, releases, comps, commits[:2], tags, runs, cfg)
    assert resultado["cfr_b"] is None and not resultado["cfr_b_disponivel"]
    assert resultado["releases_erro_404"] == resultado["releases_sem_evidencia_textual"] == 1
    assert resultado["releases_falharam"] is None


def test_patch_comprovado_independe_de_texto_e_datas_invalidas_sao_contadas(fontes):
    repo, releases, comps, commits, tags, runs, cfg = deepcopy(fontes)
    commits[1]["message"] = ""
    commits[0]["author_date"] = "2027-01-01T00:00:00Z"
    resultado = calcular_linha(repo, releases, comps, commits, tags, runs, cfg,
                              {"tipo_projeto": "biblioteca/framework", "releases_sao_entregas": "sim"})
    assert resultado["cfr_b_disponivel"] and resultado["commits_data_invalida"] == 1
    assert resultado["rotulo_disponivel"] and resultado["tipo_projeto"] == "biblioteca/framework"


def test_sem_runs_ou_episodios_nao_inventa_zero(fontes):
    valores = list(fontes)
    valores[5] = []
    resultado = calcular_linha(*valores)
    assert resultado["cfr_a"] is None and resultado["tempo_recuperacao_horas"] is None
    assert resultado["proporcao_censurados"] is None and resultado["runs_validos"] == 0


def test_consenso_antigo_nao_e_reutilizado_sem_proveniencia(tmp_path, caplog):
    caminho = tmp_path / "consenso_repos.csv"
    salvar_csv(caminho, ["full_name", "tipo_projeto"], [{"full_name": "o/r", "tipo_projeto": "outro"}])
    assert carregar_rotulos(caminho, "amostra") == {}
    assert "sem vínculo" in caplog.text


def test_dicionario_cobre_todas_as_colunas_do_dataset():
    texto = (Path(__file__).parents[1] / "docs/dicionario_dados.md").read_text(encoding="utf-8")
    assert all(f"`{campo}`" in texto for campo in CAMPOS)


def test_consenso_exige_hashes_vinculo_e_origem_declarada(tmp_path):
    caminho = tmp_path / "consenso_repos.csv"
    salvar_csv(caminho, ["full_name", "tipo_projeto"], [{"full_name": "o/r", "tipo_projeto": "outro"}])
    manifesto = {"amostra_sha256": "amostra", "consenso_sha256": sha256(caminho),
                 "rotulagem_independente_confirmada": True, "origem_rotulagem": "assistida_por_IA"}
    atestado = caminho.with_suffix(".manifest.json")
    atestado.write_text(json.dumps(manifesto), encoding="utf-8")
    assert carregar_rotulos(caminho, "amostra")["o/r"]["tipo_projeto"] == "outro"
    for campo, errado in [("amostra_sha256", "outra"), ("consenso_sha256", "outro"),
                          ("rotulagem_independente_confirmada", False), ("origem_rotulagem", "desconhecida")]:
        atestado.write_text(json.dumps({**manifesto, campo: errado}), encoding="utf-8")
        with pytest.raises(ValueError, match="consenso sem integridade"):
            carregar_rotulos(caminho, "amostra")


def test_comparacoes_ausentes_duplicadas_e_contagens_erradas_falham(fontes):
    for comps in (fontes[2][1:], fontes[2] + fontes[2][:1]):
        valores = list(fontes)
        valores[2] = comps
        with pytest.raises(ValueError, match="comparaç"):
            calcular_linha(*valores)
    valores = deepcopy(list(fontes))
    valores[2][0]["commits_count"] = "10"
    with pytest.raises(ValueError, match="contagem"):
        calcular_linha(*valores)


def test_dataset_reexecutavel_e_fontes_congeladas(fontes, tmp_path):
    repo, releases, comps, commits, tags, runs, cfg = fontes
    cfg["saida"]["dir_dados"] = str(tmp_path / "dados")
    dados = tmp_path / "dados"
    pasta = pasta_repo(dados, repo["full_name"])
    pasta.mkdir(parents=True)
    for nome, registros in [("releases.csv", releases), ("comparacoes_releases.csv", comps),
                            ("commits_entre_releases.csv", commits), ("tags.csv", tags)]:
        registros = [{"full_name": repo["full_name"], **r} for r in registros]
        salvar_csv(pasta / nome, list(registros[0]), registros)
        shutil.copyfile(pasta / nome, dados / nome)
    run_path = pasta / "workflow_runs" / "o__r.json"
    run_path.parent.mkdir()
    run_path.write_text(json.dumps({"complete": True, "workflow_runs": runs, "saturated_intervals": []}), encoding="utf-8")
    (dados / "workflow_runs").mkdir()
    shutil.copyfile(run_path, dados / "workflow_runs" / run_path.name)
    amostra = tmp_path / "amostra.csv"
    salvar_csv(amostra, list(repo), [repo])
    manifesto = {"amostra_sha256": sha256(amostra), "repositorios": 1,
                 "janela_inicio": str(cfg["janela_inicio"]), "janela_fim": str(cfg["janela_fim"]),
                 "fontes_sha256": {nome: sha256(dados / nome) for nome in (
                     "releases.csv", "comparacoes_releases.csv", "commits_entre_releases.csv", "tags.csv")},
                 "fontes_repos_sha256": {"o/r": fontes_repo(dados, "o/r")}}
    amostra.with_suffix(".manifest.json").write_text(json.dumps(manifesto), encoding="utf-8")
    destino = tmp_path / "dataset.csv"
    resumo = gerar_dataset(cfg, amostra, tmp_path / "consenso-ausente.csv", destino)
    assert resumo["repositorios"] == resumo["repositorios_sem_tipo"] == 1
    assert resumo["totais"]["releases_censuradas"] == 1
    primeiro = destino.read_bytes()
    gerar_dataset(cfg, amostra, tmp_path / "consenso-ausente.csv", destino)
    assert destino.read_bytes() == primeiro and len(ler_csv(destino)) == 1
    (dados / "commits_entre_releases.csv").write_text("alterado", encoding="utf-8")
    with pytest.raises(ValueError, match="fonte alterada"):
        gerar_dataset(cfg, amostra, tmp_path / "consenso-ausente.csv", destino)
    assert destino.read_bytes() == primeiro


@pytest.fixture
def complementar(tmp_path):
    pasta = tmp_path / "complementar"
    pasta.mkdir()
    linha = {"full_name": "org/r2", "tipo_projeto": "biblioteca/framework",
             "evidencia_url": "https://github.com/org/r2", "justificativa": "Biblioteca Python",
             "avaliador": "Diogo", "origem": "humana", "data_avaliacao": "2026-10-15"}
    salvar_csv(pasta / "tipos_A.csv", CAMPOS_COMPLEMENTARES, [linha])
    return pasta, linha


def ler_complementar(pasta):
    return carregar_complementar(pasta, "sha_teste", ["org/r1", "org/r2"], {"org/r1"})


def test_carregar_complementar_preserva_manifesto_na_reutilizacao(complementar):
    pasta, _ = complementar
    resultado, manifesto = ler_complementar(pasta)
    assert resultado["org/r2"]["tipo_projeto"] == "biblioteca/framework"
    assert resultado["org/r2"]["releases_sao_entregas"] is None
    assert manifesto["amostra_sha256"] == "sha_teste"
    caminho = pasta / "manifesto.json"
    antes = caminho.read_bytes(), caminho.stat().st_mtime_ns
    res2, man2 = ler_complementar(pasta)
    assert res2 == resultado
    assert man2 == manifesto
    assert (caminho.read_bytes(), caminho.stat().st_mtime_ns) == antes


@pytest.mark.parametrize("nome,erro", [("org/r1", "sobreposição"), ("org/r2", "duplicado"),
                                      ("org/desconhecido", "não pertence")])
def test_complementar_recusa_chaves_invalidas(complementar, nome, erro):
    pasta, linha = complementar
    salvar_csv(pasta / "tipos_B.csv", CAMPOS_COMPLEMENTARES, [{**linha, "full_name": nome}])
    with pytest.raises(ValueError, match=erro):
        ler_complementar(pasta)
    assert not (pasta / "manifesto.json").exists()


@pytest.mark.parametrize("campo", CAMPOS_COMPLEMENTARES)
def test_complementar_recusa_cada_campo_vazio(complementar, campo):
    pasta, linha = complementar
    salvar_csv(pasta / "tipos_A.csv", CAMPOS_COMPLEMENTARES, [{**linha, campo: " "}])
    with pytest.raises(ValueError, match=f"{campo} ausente"):
        ler_complementar(pasta)


@pytest.mark.parametrize("campo,valor,erro", [
    ("tipo_projeto", "invalido", "tipo_projeto inválido"),
    ("origem", "nao_confirmada", "origem inválida"),
    ("data_avaliacao", "20261015", "data_avaliacao inválida"),
    ("data_avaliacao", "2026-02-30", "data_avaliacao inválida"),
    ("evidencia_url", "nao-e-um-link", "URL HTTP"),
    ("evidencia_url", "ftp://docs.example.org", "URL HTTP"),
    ("evidencia_url", "https:///readme", "URL HTTP"),
    ("evidencia_url", "https://docs.example.org/espaco aqui", "URL HTTP"),
    ("evidencia_url", "https://usuario:senha@docs.example.org", "URL HTTP"),
    ("evidencia_url", "https://[ipv6-invalido", "URL HTTP"),
    ("evidencia_url", "https://docs.example.org:invalida", "URL HTTP"),
])
def test_complementar_recusa_valores_invalidos(complementar, campo, valor, erro):
    pasta, linha = complementar
    salvar_csv(pasta / "tipos_A.csv", CAMPOS_COMPLEMENTARES, [{**linha, campo: valor}])
    with pytest.raises(ValueError, match=erro):
        ler_complementar(pasta)


@pytest.mark.parametrize("modo", ["cabecalho_ausente", "cabecalho_duplicado", "linha_curta", "linha_longa"])
def test_complementar_recusa_estrutura_csv_invalida(complementar, modo):
    pasta, linha = complementar
    cabecalho = list(CAMPOS_COMPLEMENTARES)
    valores = [linha[c] for c in cabecalho]
    if modo == "cabecalho_ausente":
        cabecalho, valores = cabecalho[:-1], valores[:-1]
    elif modo == "cabecalho_duplicado":
        cabecalho.append(cabecalho[0])
        valores.append(valores[0])
    elif modo == "linha_curta":
        valores = valores[:-1]
    else:
        valores.append("extra")
    with (pasta / "tipos_A.csv").open("w", newline="", encoding="utf-8") as arquivo:
        escritor = csv.writer(arquivo)
        escritor.writerow(cabecalho)
        escritor.writerow(valores)
    with pytest.raises(ValueError, match="cabeçalho"):
        ler_complementar(pasta)


@pytest.mark.parametrize("campo,valor", [("amostra_sha256", "outra"), ("arquivos_sha256", {}),
                                        ("repositorios", 999), ("repositorios", True),
                                        ("origem", "assistida_por_IA")])
def test_complementar_recusa_manifesto_divergente_sem_modificar(complementar, campo, valor):
    pasta, _ = complementar
    _, manifesto = ler_complementar(pasta)
    caminho = pasta / "manifesto.json"
    caminho.write_text(json.dumps({**manifesto, campo: valor}), encoding="utf-8")
    antes = caminho.read_bytes()
    with pytest.raises(ValueError, match="manifesto|amostra congelada"):
        ler_complementar(pasta)
    assert caminho.read_bytes() == antes


def test_complementar_aceita_bom_documentacao_externa_e_origem_mista(complementar):
    pasta, linha = complementar
    arquivo = pasta / "tipos_A.csv"
    salvar_csv(arquivo, CAMPOS_COMPLEMENTARES, [
        {**linha, "evidencia_url": "https://docs.example.org/uso"},
        {**linha, "full_name": "org/r3", "origem": "assistida_por_IA"}])
    arquivo.write_bytes(b"\xef\xbb\xbf" + arquivo.read_bytes())
    dados, manifesto = carregar_complementar(pasta, "sha", ["org/r1", "org/r2", "org/r3"], {"org/r1"})
    assert manifesto["origem"] == "mista"
    assert dados["org/r3"]["origem"] == "assistida_por_IA"


def test_complementar_recusa_cobertura_incompleta(complementar):
    pasta, _ = complementar
    with pytest.raises(ValueError, match="faltam 1"):
        carregar_complementar(pasta, "sha", ["org/r1", "org/r2", "org/r3"], {"org/r1"})
    assert not (pasta / "manifesto.json").exists()


def test_dataset_com_classificacao_complementar(fontes, tmp_path):
    repo, releases, comps, commits, tags, runs, cfg = fontes
    cfg["saida"]["dir_dados"] = str(tmp_path / "dados")
    dados = tmp_path / "dados"
    pasta = pasta_repo(dados, repo["full_name"])
    pasta.mkdir(parents=True)
    for nome, registros in [("releases.csv", releases), ("comparacoes_releases.csv", comps),
                            ("commits_entre_releases.csv", commits), ("tags.csv", tags)]:
        registros = [{"full_name": repo["full_name"], **r} for r in registros]
        salvar_csv(pasta / nome, list(registros[0]), registros)
        shutil.copyfile(pasta / nome, dados / nome)
    run_path = pasta / "workflow_runs" / "o__r.json"
    run_path.parent.mkdir()
    run_path.write_text(json.dumps({"complete": True, "workflow_runs": runs, "saturated_intervals": []}), encoding="utf-8")
    (dados / "workflow_runs").mkdir()
    shutil.copyfile(run_path, dados / "workflow_runs" / run_path.name)
    amostra = tmp_path / "amostra.csv"
    salvar_csv(amostra, list(repo), [repo])
    manifesto = {"amostra_sha256": sha256(amostra), "repositorios": 1,
                 "janela_inicio": str(cfg["janela_inicio"]), "janela_fim": str(cfg["janela_fim"]),
                 "fontes_sha256": {nome: sha256(dados / nome) for nome in (
                     "releases.csv", "comparacoes_releases.csv", "commits_entre_releases.csv", "tags.csv")},
                 "fontes_repos_sha256": {"o/r": fontes_repo(dados, "o/r")}}
    amostra.with_suffix(".manifest.json").write_text(json.dumps(manifesto), encoding="utf-8")

    compl = tmp_path / "complementar"
    compl.mkdir()
    salvar_csv(compl / "tipos_A.csv",
               ["full_name", "tipo_projeto", "evidencia_url", "justificativa", "avaliador", "origem", "data_avaliacao"],
               [{"full_name": "o/r", "tipo_projeto": "ferramenta CLI", "evidencia_url": "https://github.com/o/r",
                 "justificativa": "CLI tool", "avaliador": "Diogo", "origem": "humana", "data_avaliacao": "2026-10-15"}])

    destino = tmp_path / "dataset.csv"
    resumo = gerar_dataset(cfg, amostra, tmp_path / "consenso-ausente.csv", destino, complementar=compl)
    assert resumo["repositorios"] == 1
    assert resumo["repositorios_sem_tipo"] == 0
    linhas = ler_csv(destino)
    assert linhas[0]["tipo_projeto"] == "ferramenta CLI"
    assert linhas[0]["rotulo_disponivel"] == "True"
