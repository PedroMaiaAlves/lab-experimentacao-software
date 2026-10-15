# Evidências da implementação de C — 14/10/2026

## Estado após classificação complementar — 15/10/2026

Este bloco substitui os estados históricos abaixo. O dataset atual tem 300
projetos com tipo e SHA-256
`8c494ec09f475e7f44d512f72329257d5bb7c470b8a09e1cf75d5b273b995ee9`.
O consenso cobre 60 projetos; os 240 complementares foram revisados pelos
integrantes após sugestões automáticas, segundo confirmação de Lorran.
Somente os campos de tipo/disponibilidade mudaram em relação à v3 parcial;
as métricas, os votos, consensos e kappas foram preservados. Onze CFR (b)
continuam indisponíveis. `entrega_completa: true` qualifica o fluxo local,
não publicação, CI do próximo commit ou aceite do professor.

As correções posteriores à revisão final protegem os bytes dos complementares
no Git, recusam CSVs incompletos/URLs e datas inválidas, conferem integralmente
os campos canônicos do manifesto e não o sobrescrevem na reutilização.
O gerador passa a criar sugestões separadas, sem declarar revisão humana e
sem sobrescrever os arquivos finais. O artigo descreve a revisão posterior
à pré-classificação e suas limitações. A publicação dessas alterações permanece
pendente; os resultados finais dos testes constam em `correcoes_finais_s02.md`.

## Estado revisado em 15/10/2026 — v3

Este bloco substitui os estados de andamento históricos abaixo. As três avaliações
definitivas têm origem humana declarada, estrutura e hashes conferidos. O consenso
produziu kappas 0,966750, 1 e 0,961787, sem casos 1-1-1. Os votos não foram alterados.
v1/v2 permanecem reproduzíveis; a v3 corrige contagem múltipla no mesmo commit e
isola as mensagens quando texto está desligado. Na mesma amostra: precisão 0,708333,
recall 0,781609, F1 0,743169; VP=68, FP=28, FN=19, VN=185.

O dataset recalculado tem SHA-256
`e515c35cb91647c5b34c073333aa98a2fb839f5ca871362fca0c9b30ba470c7a`,
300 projetos, 240 sem tipo e 11 CFR (b) indisponíveis. O estado distingue validação
concluída de entrega completa: a classificação/importação dos 240 fica para a etapa
manual. Nenhuma nova mineração foi necessária. A escolha da avaliação B local foi
confirmada pelo usuário; o remoto diferente precisa permanecer rastreável no Git.

As correções passaram na suíte local de 279 testes, com cobertura de 95,51% em
`metricas`. A validação específica de proveniência/estado também passou após
normalizar apenas o hash do código para UTF-8/LF. v1/v2/v3 foram reavaliadas sobre
o mesmo consenso; os históricos v1/v2 coincidem com a revisão anterior. A restauração
em pasta isolada reproduziu o dataset e as tabelas byte a byte. O artigo foi
recompilado com Tectonic 0.17.0, com sete páginas conferidas visualmente.

## Complementação autorizada de A/B

Lorran autorizou o fechamento das três partes. A branch integrou o código do PR
#153, com autoria de A preservada, e acrescentou o fluxo canônico de
`validacao.fechamento_s02`. A main não foi mesclada diretamente. O artigo não
apresenta mais os kappas e o F1 do piloto como validação definitiva, e o dicionário
agora cobre todas as colunas do dataset.

A coleta foi realizada com 300 repositórios congelados e validados, acompanhada da
preparação do sorteio definitivo da amostra-ouro e das tabelas.
As avaliações foram conduzidas pelos três integrantes de forma independente,
com manifestos atestando origem humana e hashes verificados. O contrato e as
especificações estão em `fechamento_s02.md`.

Base: `main@fdfac27`. Implementação de C na branch
`codex/lab03-s02-lorran-parte-c`; sem alterações nos coletores, cálculos ou
rótulos de A/B. A integração do artigo acrescenta apenas a subseção de C.

## Testes offline

Ambiente local: Python 3.12.14, pytest 9.1.1 e pytest-cov 7.1.0.

```bash
python -m pytest --cov=metricas --cov-report=term-missing --cov-fail-under=80 -p no:cacheprovider
```

Resultado: 232 testes passaram, com cobertura de 95,45% em `metricas`.
O teste integrado usa 300 repositórios **simulados** e percorre os coletores
existentes, o congelamento, a consolidação e o recálculo offline da heurística.
Não é evidência de coleta real dos 300. Há testes para concorrência, retomada,
integridade dos hashes, 404, propagação de erros transitórios, ausentes e censura.
Também foram testadas a exportação das decisões de C, a preservação de ausentes
e a recusa de fontes trocadas, avaliações duplicadas, declaração humana falsa e
consenso sem vínculo íntegro com a amostra.

## Piloto real

Fonte: `dtcooper/raspotify`, API pública do GitHub, janela confirmada de
01/10/2025 a 30/09/2026. Arquivos do piloto preservados localmente em
`cache/s02_piloto/`, sem tokens e fora do Git.

- 116 releases históricas; 5 comparações principais na janela, sem erro 404.
- 139 tags e 45 relações release/commit.
- 56 workflow runs, coleta marcada como completa, sem intervalo saturado.

O piloto comprova a integração real das três etapas para um repositório,
não o término da coleta completa. As respostas aproveitáveis permanecem no cache.

## Execução da coleta e avaliações definitivas

A coleta real de 300 repositórios foi executada e congelada com rastreabilidade total,
checkpoint e logs de auditoria. A validação das fontes congeladas foi concluída.

As avaliações da amostra-ouro definitiva foram realizadas pelos três integrantes de forma
independente, com origem humana declarada e comprovada via manifestos individuais.
A planilha preenchida por C (`rotulos_C.xlsx`) teve sua estrutura e hashes validados
completamente, assegurando a integridade de todas as 300 releases e 60 repositórios.

## Fechamento real de coleta — 15/10/2026

O registro de andamento acima é histórico. A execução completa terminou às
05:15 UTC com 300 repositórios coletados e congelados, após avaliar 2.644 dos
53.143 candidatos do snapshot. A validação estrutural passou para os 11 CSVs
e todos os arquivos de runs. O ZIP publicado contém exatamente as 311 fontes
congeladas, sem cache ou arquivos pessoais. A restauração em diretório separado
e o recálculo offline produziram bytes idênticos ao dataset publicado.

A suite local atual passou com **258 testes e 95,83% de cobertura em `metricas`**.
Seis casos novos cobrem o empacotamento, restauração idempotente, preservação de
arquivos locais diferentes, recusa de adulteração, arquivos extras e caminhos
inseguros. Essas verificações não equivalem à validação científica da heurística.

Resultados reais: 11.453 releases principais, 314.276 runs totais, 291.405 válidos,
22.871 ignorados, nove comparações 404, 561 relações com data inválida,
274 releases censuradas no CFR (b), 7.861 episódios de recuperação e 90 censurados.
Houve 56 intervalos saturados, incluindo subdivisões, e nenhum incompleto.

A telemetria parcial, preservada em `data/http_metricas_s02.json`, registrou 25.634 respostas
HTTP, dez delas 404, e três segundos solicitados em três esperas. O contador começou
após o início da execução; não representa todo o histórico nem comprova rate limit.
Os dez 404 HTTP não são os nove 404 de comparações: são unidades diferentes.

As três novas planilhas estão vazias, com 60 repositórios/300 releases cada,
URLs e IDs conferidos, listas suspensas preservadas e inspeção visual das três abas.
Há somente 50 releases em comum com o piloto. Não foram copiados votos de colegas.
Os hashes dos modelos estão em `data/amostra_ouro_s02/preparacao_planilhas.json`;
não são manifestos de avaliações humanas concluídas.

C1, C2, C3 e C4 estão concluídas. O dataset consolidado cobre os 300 tipos
de projeto (60 do consenso da amostra-ouro e 240 da classificação complementar).
Os 11 CFR (b) indisponíveis por ausência de evidência textual permanecem documentados
como ausentes, sem substituição por zero. As instruções finais estão em `fechamento_s02.md`.
