# Artigo no formato SBC

O arquivo principal é `artigo.tex`. Os arquivos `sbc-template.sty`, `sbc.bst` e
`caption2.sty` acompanham o projeto para que ele possa ser importado e compilado no
Overleaf sem depender de arquivos externos.

O template é atribuído à Sociedade Brasileira de Computação (SBC) e foi obtido a partir
do [SBC Conferences Template](https://www.overleaf.com/latex/templates/sbc-conferences-template/blbxwjwzdngr),
disponibilizado sob a licença [Creative Commons Attribution 4.0 International
(CC BY 4.0)](https://creativecommons.org/licenses/by/4.0/). Os nomes e e-mails dos
autores marcados com `PREENCHER` precisam ser completados pelo grupo antes da entrega.

Para compilar localmente, execute dentro deste diretório:

```text
pdflatex artigo.tex
bibtex artigo
pdflatex artigo.tex
pdflatex artigo.tex
```

Na ausência de uma distribuição LaTeX local, defina `artigo.tex` como documento principal
no Overleaf e confirme que a compilação termina sem erros.
