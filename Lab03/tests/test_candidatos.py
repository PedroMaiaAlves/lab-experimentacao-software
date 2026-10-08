import pytest

from pipeline.candidatos import carregar_candidatos, salvar_candidatos, selecionar_candidatos
from tests.fakes import ClienteFalso


def item(nome, estrelas=2000, lang="Python"):
    return {"full_name": nome, "stargazers_count": estrelas, "language": lang,
            "default_branch": "main", "created_at": "2020-01-01T00:00:00Z",
            "html_url": f"https://github.com/{nome}"}


def test_remove_duplicatas_entre_faixas_ignorando_caixa():
    def rota(params):
        if "stars:1000..2000" in params["q"]:
            return {"total_count": 2, "items": [item("a/x"), item("b/y")]}
        return {"total_count": 2, "items": [item("A/X"), item("c/z")]}

    cli = ClienteFalso({"/search/repositories": rota})
    cfg = {"semente": 1, "selecao": {"faixas_estrelas": ["1000..2000", "2000..3000"],
                                     "linguagens": ["Python"]}}
    nomes = sorted(c["full_name"].lower() for c in selecionar_candidatos(cli, cfg))
    assert nomes == ["a/x", "b/y", "c/z"]


def test_subdivide_por_estrelas_quando_passa_de_1000():
    def rota(params):
        if "stars:1000..1003" in params["q"]:
            return {"total_count": 2000, "items": [item("a/x", 1003)]}
        return {"total_count": 2, "items": [item(params["q"], 1001)]}

    cli = ClienteFalso({"/search/repositories": rota})
    cfg = {"semente": 1, "selecao": {"faixas_estrelas": ["1000..1003"], "linguagens": []}}
    selecionar_candidatos(cli, cfg)
    consultas = [p["q"] for _, p in cli.chamadas]
    assert consultas.count("stars:1000..1003 archived:false fork:false") == 1
    assert any("stars:1000..1001" in q for q in consultas)
    assert any("stars:1002..1003" in q for q in consultas)


def test_embaralhamento_e_reprodutivel_com_a_mesma_semente():
    itens = [item(f"o/r{i}") for i in range(30)]
    cli = ClienteFalso({"/search/repositories": {"total_count": 30, "items": itens}})
    cfg = {"semente": 7, "selecao": {"faixas_estrelas": ["1000..2000"], "linguagens": []}}
    a = [c["full_name"] for c in selecionar_candidatos(cli, cfg)]
    b = [c["full_name"] for c in selecionar_candidatos(cli, cfg)]
    assert a == b


def test_faixa_saturada_irredutivel_falha_em_vez_de_truncar():
    cli = ClienteFalso({
        "/search/repositories": {
            "total_count": 2000,
            "items": [item("a/x", estrelas=1000)],
        }
    })
    cfg = {"semente": 1, "selecao": {"faixas_estrelas": ["1000..1000"], "linguagens": []}}
    with pytest.raises(RuntimeError, match="saturada"):
        selecionar_candidatos(cli, cfg)


def test_faixa_unitaria_saturada_usa_fallback_por_linguagem():
    def rota(params):
        q = params["q"]
        if 'language:"Python"' in q:
            return {"total_count": 1, "items": [item("py/projeto", 1000, "Python")]}
        if 'language:"Go"' in q:
            return {"total_count": 1, "items": [item("go/projeto", 1000, "Go")]}
        return {"total_count": 1000, "items": [item("limite/inicial", 1000)]}

    cli = ClienteFalso({"/search/repositories": rota})
    cfg = {"semente": 1, "selecao": {
        "faixas_estrelas": ["1000..1000"], "linguagens": ["Python", "Go"]}}

    nomes = {c["full_name"] for c in selecionar_candidatos(cli, cfg)}

    assert nomes == {"py/projeto", "go/projeto"}
    consultas = [params["q"] for _, params in cli.chamadas]
    assert any('language:"Python"' in q for q in consultas)
    assert any('language:"Go"' in q for q in consultas)


def test_fallback_por_linguagem_remove_duplicatas_entre_particoes():
    compartilhado = item("org/compartilhado", 1000)

    def rota(params):
        if "language:" in params["q"]:
            return {"total_count": 1, "items": [compartilhado]}
        return {"total_count": 1000, "items": [compartilhado]}

    cli = ClienteFalso({"/search/repositories": rota})
    cfg = {"semente": 1, "selecao": {
        "faixas_estrelas": ["1000..1000"], "linguagens": ["Python", "Go"]}}

    candidatos = selecionar_candidatos(cli, cfg)

    assert [c["full_name"] for c in candidatos] == ["org/compartilhado"]


def test_fallback_por_linguagem_ainda_saturado_falha_claramente():
    def rota(params):
        total = 1000 if "language:" in params["q"] else 1500
        return {"total_count": total, "items": [item("org/projeto", 1000)]}

    cli = ClienteFalso({"/search/repositories": rota})
    cfg = {"semente": 1, "selecao": {
        "faixas_estrelas": ["1000..1000"], "linguagens": ["Python"]}}

    with pytest.raises(RuntimeError, match="estrelas e linguagem"):
        selecionar_candidatos(cli, cfg)
    consultas = [params["q"] for _, params in cli.chamadas]
    assert consultas.count(
        'stars:1000..1000 archived:false fork:false language:"Python"'
    ) == 1


def test_salvar_e_carregar_csv(tmp_path):
    cands = [{"full_name": "a/x", "stars": 10, "language": "Go", "default_branch": "main",
              "created_at": "2020-01-01T00:00:00Z", "html_url": "u", "consulta": "q"}]
    salvar_candidatos(cands, tmp_path / "candidatos.csv")
    lidos = carregar_candidatos(tmp_path / "candidatos.csv")
    assert lidos[0]["full_name"] == "a/x" and lidos[0]["stars"] == "10"
