import pytest

from metricas.cfr import (
    calcular_cfr_a,
    calcular_cfr_b,
    classificar_conclusao,
    classificar_release_corretiva,
    contar_conclusoes,
    explicar_release_corretiva,
)

REGRAS = {
    "usar_patch_semver": True,
    "usar_palavras_commits": True,
    "palavras_chave": ["fix", "hotfix", "revert"],
}


@pytest.fixture
def runs_mistos():
    return [
        {"conclusion": "success"},
        {"conclusion": "success"},
        {"conclusion": "failure"},
        {"conclusion": "timed_out"},
        {"conclusion": "startup_failure"},
        {"conclusion": "cancelled"},
        {"conclusion": None},
    ]


def test_classificacao_da_tabela_do_enunciado():
    assert classificar_conclusao("success") == "sucesso"
    for valor in ("failure", "timed_out", "startup_failure"):
        assert classificar_conclusao(valor) == "falha"
    for valor in ("cancelled", "skipped", "neutral", "action_required", "stale", "", None, "nova"):
        assert classificar_conclusao(valor) == "ignorar"


def test_cfr_fixture_calculada_a_mao(runs_mistos):
    assert contar_conclusoes(runs_mistos) == {"sucessos": 2, "falhas": 3, "ignoradas": 2}
    assert calcular_cfr_a(runs_mistos) == pytest.approx(3 / 5)


def test_so_sucessos_da_zero_e_cancelados_nao_alteram():
    assert calcular_cfr_a([{"conclusion": "success"}, {"conclusion": "cancelled"}]) == 0


def test_nenhum_run_valido_devolve_none():
    assert calcular_cfr_a([{"conclusion": "cancelled"}, {"conclusion": None}]) is None


@pytest.mark.parametrize(
    ("anterior", "atual", "esperado"),
    [
        ("v2.3.0", "v2.3.1", True),
        ("2.3.1", "2.3.5", True),
        ("v2.3.1", "v2.4.0", False),
        ("v2.3.1", "v3.3.2", False),
        ("v2.3.2", "v2.3.1", False),
        ("checker-framework-4.2.2", "checker-framework-4.2.3", False),
        ("v01.2.2", "v01.2.3", False),
        ("v1.2.2+build.1", "v1.2.3-rc.1", True),
    ],
)
def test_criterio_patch_semver_estrito(anterior, atual, esperado):
    assert classificar_release_corretiva(anterior, atual, [], REGRAS) is esperado


@pytest.mark.parametrize("mensagem", [
    "fix: crash ao abrir arquivo",
    "HOTFIX urgente\nmais detalhes",
    "Revert \"mudança incompatível\"",
])
def test_criterio_textual_ignora_caixa_e_aceita_multilinha(mensagem):
    assert classificar_release_corretiva("release-a", "release-b", [mensagem], REGRAS)


@pytest.mark.parametrize("mensagem", [None, "", "adiciona fixture", "erro já fixed"])
def test_criterio_textual_exige_tokens_exatos(mensagem):
    assert not classificar_release_corretiva("release-a", "release-b", [mensagem], REGRAS)


def test_criterios_podem_ser_desabilitados_e_evidencias_sao_explicadas():
    regras = {**REGRAS, "usar_patch_semver": False}
    resultado = explicar_release_corretiva("v1.0.0", "v1.0.1", ["fix: falha"], regras)
    assert resultado == {
        "tag_anterior_semver": True,
        "tag_atual_semver": True,
        "criterio_patch": False,
        "criterio_texto": True,
        "palavras_encontradas": ["fix"],
        "corretiva": True,
    }
    regras["usar_palavras_commits"] = False
    assert not classificar_release_corretiva("v1.0.0", "v1.0.1", ["fix: falha"], regras)


def release(numero, data, corretiva=False, **campos):
    return {"id": numero, "published_at": data, "corretiva": corretiva, **campos}


def test_cfr_b_exemplos_do_enunciado():
    releases = [
        release(1, "2026-05-10T10:00:00Z"),
        release(2, "2026-05-12T10:00:00Z", True),
        release(3, "2026-06-01T10:00:00Z"),
        release(4, "2026-06-20T10:00:00Z"),
    ]
    resultado = calcular_cfr_b(releases, "2026-06-30")
    assert resultado["releases_falharam"] == 1
    assert resultado["releases_avaliadas"] == 4
    assert resultado["cfr_b"] == pytest.approx(0.25)


def test_cfr_b_limite_de_sete_dias_e_inclusivo():
    releases = [release(1, "2026-09-01T12:00:00Z"),
                release(2, "2026-09-08T12:00:00Z", True)]
    assert calcular_cfr_b(releases, "2026-09-30")["releases_falharam"] == 1
    releases[1]["published_at"] = "2026-09-08T12:00:01Z"
    assert calcular_cfr_b(releases, "2026-09-30")["releases_falharam"] == 0


def test_cfr_b_censura_as_ultimas_sete_datas_e_reporta_contagem():
    releases = [release(1, "2026-09-23T12:00:00Z"),
                release(2, "2026-09-24T12:00:00Z", True),
                release(3, "2026-09-30T12:00:00Z")]
    assert calcular_cfr_b(releases, "2026-09-30") == {
        "cfr_b": 1.0,
        "releases_avaliadas": 1,
        "releases_falharam": 1,
        "releases_censuradas": 2,
    }


def test_cfr_b_sem_release_avaliavel_devolve_none_e_exclui_pre_e_draft():
    releases = [release(1, "2026-09-25T00:00:00Z"),
                release(2, "2026-09-10T00:00:00Z", draft=True),
                release(3, "2026-09-10T00:00:00Z", prerelease=True)]
    assert calcular_cfr_b(releases, "2026-09-30") == {
        "cfr_b": None,
        "releases_avaliadas": 0,
        "releases_falharam": 0,
        "releases_censuradas": 1,
    }


def test_cfr_b_rejeita_data_sem_fuso_e_janela_invalida():
    with pytest.raises(ValueError, match="fuso"):
        calcular_cfr_b([release(1, "2026-09-01T00:00:00")], "2026-09-30")
    with pytest.raises(ValueError, match="inteiro positivo"):
        calcular_cfr_b([], "2026-09-30", dias=0)


def test_cfr_v2_rejeita_falsos_positivos_de_manutencao_e_chore():
    regras_v2 = {
        "versao": "v2",
        "usar_patch_semver": True,
        "usar_palavras_commits": True,
        "palavras_chave": ["fix", "hotfix", "revert"],
    }
    mensagens_chore = [
        "chore: fix typo in README",
        "docs: fix typo in documentation",
        "ci: fix build script",
        "build(deps): bump library and fix dependencies",
    ]
    assert not classificar_release_corretiva("v1.0.0", "v1.0.1", mensagens_chore, regras_v2)


def test_cfr_v2_identifica_correcao_genuina():
    regras_v2 = {
        "versao": "v2",
        "usar_patch_semver": True,
        "usar_palavras_commits": True,
        "palavras_chave": ["fix", "hotfix", "revert"],
    }
    mensagens_fix = [
        "fix: resolve memory leak on shutdown",
        "fix: prevent crash when file is missing",
    ]
    assert classificar_release_corretiva("v1.0.0", "v1.0.1", mensagens_fix, regras_v2)


def test_cfr_v2_release_mista_com_feature_predominante():
    regras_v2 = {
        "versao": "v2",
        "usar_patch_semver": True,
        "usar_palavras_commits": True,
        "palavras_chave": ["fix", "hotfix", "revert"],
    }
    mensagens_mistas = [
        "feat: add export to excel",
        "feat: support dark theme",
        "fix: small alignment glitch",
    ]
    assert not classificar_release_corretiva("v1.0.0", "v1.1.0", mensagens_mistas, regras_v2)


def test_cfr_v2_semver_com_prefixo_monorepo():
    regras_v2 = {
        "versao": "v2",
        "usar_patch_semver": True,
        "usar_palavras_commits": True,
        "palavras_chave": ["fix", "hotfix", "revert"],
    }
    mensagens = ["fix: resolve crash on startup"]
    assert classificar_release_corretiva("@scope/pkg@1.2.0", "@scope/pkg@1.2.1", mensagens, regras_v2)


def test_v3_conta_cada_commit_uma_vez_e_preserva_v2():
    mensagens = ["feat: novo painel", "fix: hotfix revert regression"]
    assert classificar_release_corretiva("1.0.0", "1.0.1", mensagens, {**REGRAS, "versao": "v2"})
    assert not classificar_release_corretiva("1.0.0", "1.0.1", mensagens, {**REGRAS, "versao": "v3"})


@pytest.mark.parametrize("patch,texto", [(True, True), (True, False), (False, True), (False, False)])
def test_v3_controles_e_texto_desligado_nao_consulta_mensagens(patch, texto):
    regras = {**REGRAS, "versao": "v3", "usar_patch_semver": patch, "usar_palavras_commits": texto}
    resultado = explicar_release_corretiva("1.0.0", "1.0.1", ["fix: crash"], regras)
    assert resultado["corretiva"] is (patch or texto)
    assert resultado["criterio_texto"] is texto
    if not texto:
        def mensagens_proibidas():
            raise AssertionError("Texto desativado não deve consumir mensagens")
            yield
        assert explicar_release_corretiva("1.0.0", "1.0.1", mensagens_proibidas(), regras) == resultado
        assert resultado["palavras_encontradas"] == []


@pytest.mark.parametrize("features,fixes,esperado", [(1, 2, False), (1, 3, True), (2, 4, False), (2, 5, True)])
def test_v3_limiar_e_razao_por_commits(features, fixes, esperado):
    mensagens = ["feat: novidade"] * features + ["fix: crash regression"] * fixes
    assert classificar_release_corretiva("1.0.0", "1.1.0", mensagens, {**REGRAS, "versao": "v3"}) is esperado


@pytest.mark.parametrize("mensagens", [[], [None, "", "  "], ["docs: fix typo"], ["feat: novidade"]])
def test_v3_nao_aceita_patch_isolado_com_analise_textual(mensagens):
    assert not classificar_release_corretiva("1.0.0", "1.0.1", mensagens, {**REGRAS, "versao": "v3"})


def test_v3_tags_com_namespace_tokens_e_configuracao_invalida():
    regras = {**REGRAS, "versao": "v3"}
    assert classificar_release_corretiva("@scope/pkg@1.0.0", "@scope/pkg@1.0.1", ["fix: falha"], regras)
    assert not classificar_release_corretiva("x", "y", ["fixed fixture"], regras)
    assert classificar_release_corretiva("x", "y", ["Security: CVE vulnerability"], regras)
    with pytest.raises(ValueError, match="palavras_chave"):
        classificar_release_corretiva("x", "y", [], {**regras, "palavras_chave": "fix"})
