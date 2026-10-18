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

O documento foi atualizado com a validação da amostra definitiva, a heurística
v3 (F1 >= 0,70) e a consolidação dos 300 tipos de projetos (amostra-ouro e
classificação complementar com proveniência). Os valores ausentes de CFR permanecem
documentados como não observados por insuficiência textual. Tectonic 0.17.0 permite
reproduzir a compilação com `tectonic artigo.tex`. O PDF compilado está disponível em
`artigo_s02_parcial.pdf`.

O nome do PDF foi mantido por compatibilidade com os links existentes; seu conteúdo
inclui a revisão dos 240 tipos complementares e não anuncia essa etapa como pendente.
O método distingue a pré-classificação automática da revisão humana posterior,
confirmada pelos integrantes, sem atribuir consenso triplo aos 240 projetos.

A Sprint 3, parte A, acrescenta `resultados_a.tex` (RQ01 a RQ04 e classificação C1) e
`discussao.tex` (hipóteses × resultados). Antes de compilar, execute
`python -m analises.sprint3_a` dentro de `Lab03/`: tabelas, figuras e as macros dos números
do texto são importadas de `Lab03/results/s03_a/`. No Overleaf, envie a árvore de `Lab03`
mantendo os caminhos relativos. O PDF desta versão é `artigo_s03_a.pdf`.
