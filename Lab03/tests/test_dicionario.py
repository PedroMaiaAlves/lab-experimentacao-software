from validacao.dicionario import colunas_documentadas, inferir_tipos, main, verificar

DICIONARIO = """# Dicionário

## Seleção

### `funil.csv`

| Coluna | Tipo |
|---|---|
| `etapa` | texto |
| `restaram` | inteiro |

### `workflow_runs/<owner>__<repo>.json`

| Campo | Tipo |
|---|---|
| `id` | inteiro |

### `kappa_fleiss.csv`

| `dimensao` | texto |
| `kappa` | real |
"""


def test_colunas_documentadas_ignora_secoes_que_nao_sao_csv():
    docs = colunas_documentadas(DICIONARIO)
    assert docs == {"funil.csv": ["etapa", "restaram"], "kappa_fleiss.csv": ["dimensao", "kappa"]}


def test_verificar_aponta_faltas_sobras_e_arquivos_sem_secao(tmp_path):
    (tmp_path / "d.md").write_text(DICIONARIO, encoding="utf-8")
    dados = tmp_path / "data"
    (dados / "sub").mkdir(parents=True)
    (dados / "funil.csv").write_text("etapa,restaram,novo\na,1,x\n", encoding="utf-8")
    (dados / "sub" / "kappa_fleiss.csv").write_text("dimensao\nx\n", encoding="utf-8")
    (dados / "dataset.csv").write_text("full_name,mediana\na/x,1.5\n", encoding="utf-8")
    sem_secao, faltando, obsoletas = verificar(tmp_path / "d.md", dados)
    assert [p.name for p in sem_secao] == ["dataset.csv"]
    assert {p.name: c for p, c in faltando.items()} == {"funil.csv": ["novo"]}
    assert {p.name: c for p, c in obsoletas.items()} == {"kappa_fleiss.csv": ["kappa"]}


def test_main_retorna_zero_quando_completo_e_um_quando_ha_pendencia(tmp_path, capsys):
    (tmp_path / "d.md").write_text(DICIONARIO, encoding="utf-8")
    dados = tmp_path / "data"
    dados.mkdir()
    (dados / "funil.csv").write_text("etapa,restaram\na,1\n", encoding="utf-8")
    args = ["--dicionario", str(tmp_path / "d.md"), "--dados", str(dados)]
    assert main(args) == 0
    (dados / "dataset.csv").write_text("full_name,n\na/x,3\n", encoding="utf-8")
    assert main(args + ["--esqueleto"]) == 1
    saida = capsys.readouterr().out
    assert "SEM SEÇÃO: dataset.csv" in saida and "| `n` | inteiro | PREENCHER" in saida


def test_inferir_tipos(tmp_path):
    (tmp_path / "a.csv").write_text("i,r,t,v\n1,1.5,x,\n2,2,y,\n", encoding="utf-8")
    assert inferir_tipos(tmp_path / "a.csv") == {"i": "inteiro", "r": "real", "t": "texto", "v": "texto"}
