# Artigo no formato SBC

A versão da Sprint 3, parte B, acrescenta resultados e discussão de RQ05/RQ06
em `resultados_b.tex`. O PDF atualizado é `artigo_s03_b.pdf`; o PDF da S02 foi
preservado como histórico. A, C e a replicação cruzada ainda precisam ser integradas.

Antes de compilar, execute `python -m analises.sprint3_b` dentro de `Lab03/`.
Tabelas e figuras são importadas de `Lab03/results/s03_b/`. Para usar Overleaf,
envie a árvore de `Lab03` mantendo os caminhos relativos, incluindo essa pasta;
não basta enviar apenas `docs/artigo/` na versão S03.

O arquivo principal é `artigo.tex`; o PDF consolidado atual é `artigo_final.pdf`,
com 9 páginas incluindo referências. As seções são `introducao_final.tex`,
`metodologia_final.tex`, `resultados_final.tex` e `discussao_final.tex`.
Os arquivos `sbc-template.sty`, `sbc.bst` e
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

### Versões anteriores (histórico)

O documento foi atualizado na S02 com a validação da amostra definitiva, a heurística
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

A prévia inicial de C, `artigo_s03_c.pdf`, continha só o bônus, antes da integração
de B/RQ07. Esses PDFs históricos não são a versão consolidada atual.

### Reprodução da versão consolidada

Dentro de `Lab03/`, execute `python -m validacao.entrega_s03 --reproduzir` para
conferir entradas, artefatos e números; os comandos `analises.sprint3_a`,
`analises.sprint3_b` e `analises.sprint3_c` regeneram as saídas publicadas.
Compile `artigo.tex` com os comandos acima ou Tectonic 0.17.0, e copie o PDF
gerado para `artigo_final.pdf`. O código de validação verifica até 10 páginas
e a presença das oito RQ, mas não substitui inspeção visual.

Os resultados numéricos completos permanecem em `results/` e nos seis notebooks;
a concisão do artigo não remove resultados não significativos dos artefatos.
Os textos extensos de A/B/C são preservados como material suplementar, não usados
simultaneamente no artigo compacto. O estado da etapa FIN de replicação cruzada
é separado em `../entrega_s03_integrada.md`.
