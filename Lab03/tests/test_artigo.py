import re
from pathlib import Path


ARTIGO = Path(__file__).parents[1] / "docs" / "artigo"


def test_documento_principal_usa_estrutura_sbc():
    texto = (ARTIGO / "artigo.tex").read_text(encoding="utf-8")
    assert "\\usepackage{sbc-template}" in texto
    assert "\\input{introducao}" in texto
    assert "\\bibliographystyle{sbc}" in texto
    assert "\\bibliography{referencias}" in texto
    assert "\\begin{abstract}" in texto
    assert "\\begin{resumo}" in texto


def test_todas_as_citacoes_da_introducao_existem_na_bibliografia():
    introducao = (ARTIGO / "introducao.tex").read_text(encoding="utf-8")
    bibliografia = (ARTIGO / "referencias.bib").read_text(encoding="utf-8")
    citadas = {
        chave.strip()
        for grupo in re.findall(r"\\cite\{([^}]+)\}", introducao)
        for chave in grupo.split(",")
    }
    cadastradas = set(re.findall(r"@\w+\{([^,]+),", bibliografia))
    assert citadas
    assert citadas <= cadastradas


def test_arquivos_do_template_foram_versionados():
    for nome in ("sbc-template.sty", "sbc.bst", "caption2.sty"):
        assert (ARTIGO / nome).stat().st_size > 1000
