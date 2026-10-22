import re
from pathlib import Path


ARTIGO = Path(__file__).parents[1] / "docs" / "artigo"


def test_documento_principal_usa_estrutura_sbc():
    texto = (ARTIGO / "artigo.tex").read_text(encoding="utf-8")
    assert "\\usepackage{sbc-template}" in texto
    for secao in ("introducao_final", "metodologia_final", "resultados_final", "discussao_final"):
        assert f"\\input{{{secao}}}" in texto
    assert "\\bibliographystyle{sbc}" in texto
    assert "\\bibliography{referencias}" in texto
    assert "\\begin{abstract}" in texto
    assert "\\begin{resumo}" in texto


def test_todas_as_citacoes_das_secoes_atuais_existem_na_bibliografia():
    secoes = "\n".join(p.read_text(encoding="utf-8") for p in ARTIGO.glob("*_final.tex"))
    bibliografia = (ARTIGO / "referencias.bib").read_text(encoding="utf-8")
    citadas = {
        chave.strip()
        for grupo in re.findall(r"\\cite\{([^}]+)\}", secoes)
        for chave in grupo.split(",")
    }
    cadastradas = set(re.findall(r"@\w+\{([^,]+),", bibliografia))
    assert citadas
    assert citadas <= cadastradas


def test_arquivos_do_template_foram_versionados():
    for nome in ("sbc-template.sty", "sbc.bst", "caption2.sty"):
        assert (ARTIGO / nome).stat().st_size > 1000


def test_artigo_preserva_proveniencia_da_classificacao_e_atualiza_os_resumos():
    texto = (ARTIGO / "artigo.tex").read_text(encoding="utf-8")
    assert "remain incomplete" not in texto
    assert "permanecem pendentes" not in texto
    assert "300 open-source repositories" in texto
    assert "Changing operational definitions" in texto
    metodo = " ".join((ARTIGO / "metodologia_final.tex").read_text(encoding="utf-8").split())
    assert "240 tipos foram revisados individualmente" in metodo
    assert "após sugestões automáticas" in metodo
    assert "proveniência separadas do consenso triplo" in metodo
