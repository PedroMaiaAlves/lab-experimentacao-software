# Artigo no formato SBC

O arquivo principal é `artigo.tex`. Os arquivos `sbc-template.sty`, `sbc.bst` e
`caption2.sty` acompanham o projeto para que ele possa ser importado e compilado no
Overleaf sem depender de arquivos externos.

O template é atribuído à Sociedade Brasileira de Computação (SBC) e foi obtido a partir
do [SBC Conferences Template](https://www.overleaf.com/latex/templates/sbc-conferences-template/blbxwjwzdngr),
disponibilizado sob a licença [Creative Commons Attribution 4.0 International
(CC BY 4.0)](https://creativecommons.org/licenses/by/4.0/). Os autores estão identificados
no documento; e-mails não informados não foram inventados.

O comando `python -m validacao.fechamento_s02 --config config_s02.yaml`, executado
em `Lab03/`, gera as tabelas da coleta somente após validar o congelamento. A
opção `--validar-avaliacoes` exige três planilhas com proveniência e avalia a
heurística contra o novo consenso. Os números do piloto permanecem nos artefatos
históricos e não são reutilizados como validação definitiva. Veja
`../fechamento_s02.md` para o contrato e as pendências de aceitação.

Para compilar localmente, execute dentro deste diretório:

```text
pdflatex artigo.tex
bibtex artigo
pdflatex artigo.tex
pdflatex artigo.tex
```

Na ausência de uma distribuição LaTeX local, defina `artigo.tex` como documento principal
no Overleaf e confirme que a compilação termina sem erros.

Verificação local da S02: Tectonic 0.17.0 compilou o documento completo, com
conferência visual das seis páginas. O PDF é uma versão de acompanhamento,
explicitamente sem resultados definitivos de kappa/F1. Para reproduzir com esse
compilador, execute `tectonic artigo.tex`; não é necessário instalá-lo no projeto.
