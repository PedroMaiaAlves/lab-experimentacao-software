from copy import deepcopy
import hashlib
import json
from zipfile import ZipFile

import pandas as pd
import pytest

from analises.rq08 import analisar, avaliar_releases, carregar_releases
from analises.sprint3_c import executar
from pipeline.config import carregar_config


@pytest.fixture
def fontes():
    cfg = carregar_config("config_s02.yaml")
    releases = [{"full_name": "org/repo", "id": str(i), "tag_name": f"v1.0.{i}",
                 "published_at": f"2026-01-0{i}T00:00:00Z", "draft": "False", "prerelease": "False"}
                for i in range(1, 5)]
    comps = [{"full_name": "org/repo", "release_id": r["id"], "previous_tag_name": f"v1.0.{i}",
              "status": "ok", "commits_count": "1"} for i, r in enumerate(releases)]
    commits = [{"full_name": "org/repo", "release_id": r["id"], "message": "fix: regression" if i == 3 else "feat: new"}
               for i, r in enumerate(releases)]
    return releases, comps, commits, cfg


def test_uma_corretiva_pode_marcar_tres_releases_com_falha_sem_triplicar_rework(fontes):
    auditoria = avaliar_releases(*fontes)
    df = pd.DataFrame([{"full_name": "org/repo", "cfr_b": .75}])
    r = analisar(df, auditoria, fontes[3])
    repo = r["rq08_repositorios"].iloc[0]
    assert repo.rework_rate == .25 and repo.cfr_b == .75
    assert repo.releases_corretivas == 1 and repo.releases_falharam_cfr_b == 3
    assert r["rq08_comparacao"].diferenca_rework_menos_cfr_b.iloc[0] == -.5


def test_rework_nao_censura_as_sete_ultimas_datas(fontes):
    releases, comps, commits, cfg = deepcopy(fontes)
    releases, comps, commits = releases[:2], comps[:2], commits[:2]
    releases[0]["published_at"], releases[1]["published_at"] = "2026-09-23T00:00:00Z", "2026-09-30T00:00:00Z"
    commits[1]["message"] = "fix: crash"
    a = avaliar_releases(releases, comps, commits, cfg)
    r = analisar(pd.DataFrame([{"full_name": "org/repo", "cfr_b": 1.0}]), a, cfg)["rq08_repositorios"].iloc[0]
    assert r.rework_rate == .5 and r.releases_total == 2
    assert r.releases_avaliadas_cfr_b == 1 and r.releases_censuradas_cfr_b == 1


@pytest.mark.parametrize("status", ["erro_404", "sem_anterior"])
def test_comparacao_indisponivel_deixa_rework_ausente(fontes, status):
    releases, comps, commits, cfg = deepcopy(fontes)
    comps[0].update(status=status, commits_count="0")
    a = avaliar_releases(releases, comps, commits[1:], cfg)
    assert a.corretiva.iloc[0] is None
    assert a.motivo_ausencia.iloc[0] == status


def test_mensagens_incompletas_nao_sao_evidencia_de_ausencia_de_funcionalidades(fontes):
    releases, comps, commits, cfg = deepcopy(fontes)
    comps[3]["commits_count"] = "2"
    commits.append({"full_name": "org/repo", "release_id": "4", "message": ""})
    a = avaliar_releases(releases, comps, commits, cfg)
    assert bool(a.iloc[3].corretiva_heuristica) and a.iloc[3].corretiva is None
    assert a.iloc[3].motivo_ausencia == "mensagem_ausente"
    assert not bool(a.iloc[3].lacuna_cfr_b)
    r = analisar(pd.DataFrame([{"full_name": "org/repo", "cfr_b": .75}]), a, cfg)["rq08_repositorios"].iloc[0]
    assert r.rework_rate == .25 and pd.isna(r.rework_conservador)
    assert r.releases_sem_evidencia_completa == 1


@pytest.mark.parametrize("status", ["sem_anterior", "ok"])
def test_sem_commits_preserva_definicao_s02_e_expoe_sensibilidade(fontes, status):
    releases, comps, commits, cfg = deepcopy(fontes)
    comps[0].update(status=status, commits_count="0")
    a = avaliar_releases(releases, comps, commits[1:], cfg)
    r = analisar(pd.DataFrame([{"full_name": "org/repo", "cfr_b": .75}]), a, cfg)["rq08_repositorios"].iloc[0]
    assert r.rework_rate == .25 and pd.isna(r.rework_conservador)
    assert r.limite_inferior_conservador == .25 and r.limite_superior_conservador == .5


def test_lacuna_s02_nao_e_imputada_com_zero(fontes):
    releases, comps, commits, cfg = deepcopy(fontes)
    comps[0].update(status="erro_404", commits_count="0")
    a = avaliar_releases(releases, comps, commits[1:], cfg)
    r = analisar(pd.DataFrame([{"full_name": "org/repo", "cfr_b": float("nan")}]), a, cfg)
    assert pd.isna(r["rq08_repositorios"].rework_rate.iloc[0])
    assert r["rq08_comparacao"].empty
    assert r["rq08_cobertura"].limite_superior_agregado.iloc[0] == .5


def test_cfr_recalculado_precisa_reproduzir_o_dataset(fontes):
    with pytest.raises(ValueError, match="CFR.*diverge"):
        analisar(pd.DataFrame([{"full_name": "org/repo", "cfr_b": 0.0}]), avaliar_releases(*fontes), fontes[3])


@pytest.mark.parametrize("erro", ["comparacao_duplicada", "comparacao_ausente", "commit_extra", "contagem", "status"])
def test_erros_de_estrutura_nao_viram_classificacoes(fontes, erro):
    releases, comps, commits, cfg = deepcopy(fontes)
    if erro == "comparacao_duplicada":
        comps.append(dict(comps[0]))
    elif erro == "comparacao_ausente":
        comps = comps[1:]
    elif erro == "commit_extra":
        commits.append({**commits[0], "release_id": "999"})
    elif erro == "contagem":
        comps[0]["commits_count"] = "42"
    else:
        comps[0]["status"] = "desconhecido"
    with pytest.raises(ValueError):
        avaliar_releases(releases, comps, commits, cfg)


def test_fontes_zip_e_contagens_sao_conferidas(fontes, tmp_path):
    releases, comps, commits, cfg = fontes
    pacote, amostra = tmp_path / "fontes.zip", tmp_path / "amostra_final.csv"
    arquivos = {"releases.csv": pd.DataFrame(releases).to_csv(index=False).encode(),
                "comparacoes_releases.csv": pd.DataFrame(comps).to_csv(index=False).encode(),
                "commits_entre_releases.csv": pd.DataFrame(commits).to_csv(index=False).encode()}
    with ZipFile(pacote, "w") as zipado:
        for nome, bruto in arquivos.items():
            zipado.writestr(nome, bruto)
    manifesto = {"fontes_sha256": {n: hashlib.sha256(b).hexdigest() for n, b in arquivos.items()}}
    caminho = amostra.with_suffix(".manifest.json")
    caminho.write_text(json.dumps(manifesto), encoding="utf-8")
    df = pd.DataFrame([{"full_name": "org/repo", "releases_principais": "4"}])
    a, _ = carregar_releases(df, cfg, tmp_path / "dataset.csv", amostra, pacote)
    assert len(a) == 4
    with pytest.raises(ValueError, match="contagens"):
        carregar_releases(df.assign(releases_principais="5"), cfg, tmp_path / "dataset.csv", amostra, pacote)
    manifesto["fontes_sha256"]["commits_entre_releases.csv"] = "outro"
    caminho.write_text(json.dumps(manifesto), encoding="utf-8")
    with pytest.raises(ValueError, match="hash divergente"):
        carregar_releases(df, cfg, tmp_path / "dataset.csv", amostra, pacote)


def test_saida_nao_pode_sobrescrever_os_dados_congelados():
    with pytest.raises(ValueError, match="fora da pasta"):
        executar(saida="data/resultados_rq08")
