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


def test_subdivide_por_linguagem_quando_passa_de_1000():
    def rota(params):
        total = 5000 if "language" not in params["q"] else 3
        return {"total_count": total, "items": [item("a/x")]}

    cli = ClienteFalso({"/search/repositories": rota})
    cfg = {"semente": 1, "selecao": {"faixas_estrelas": [">30000"], "linguagens": ["Python", "C++"]}}
    selecionar_candidatos(cli, cfg)
    consultas = [p["q"] for _, p in cli.chamadas]
    assert any('language:"Python"' in q for q in consultas)
    assert any('language:"C++"' in q for q in consultas)


def test_embaralhamento_e_reprodutivel_com_a_mesma_semente():
    itens = [item(f"o/r{i}") for i in range(30)]
    cli = ClienteFalso({"/search/repositories": {"total_count": 30, "items": itens}})
    cfg = {"semente": 7, "selecao": {"faixas_estrelas": ["1000..2000"], "linguagens": []}}
    a = [c["full_name"] for c in selecionar_candidatos(cli, cfg)]
    b = [c["full_name"] for c in selecionar_candidatos(cli, cfg)]
    assert a == b


def test_salvar_e_carregar_csv(tmp_path):
    cands = [{"full_name": "a/x", "stars": 10, "language": "Go", "default_branch": "main",
              "created_at": "2020-01-01T00:00:00Z", "html_url": "u", "consulta": "q"}]
    salvar_candidatos(cands, tmp_path / "candidatos.csv")
    lidos = carregar_candidatos(tmp_path / "candidatos.csv")
    assert lidos[0]["full_name"] == "a/x" and lidos[0]["stars"] == "10"
