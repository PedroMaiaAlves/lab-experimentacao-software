# Evidências da implementação de C — 14/10/2026

## Complementação autorizada de A/B

Lorran autorizou o fechamento das três partes. A branch integrou o código do PR
#153, com autoria de A preservada, e acrescentou o fluxo canônico de
`validacao.fechamento_s02`. A main não foi mesclada diretamente. O artigo não
apresenta mais os kappas e o F1 do piloto como validação definitiva, e o dicionário
agora cobre todas as colunas do dataset.

A coleta foi retomada com 65 repositórios completos preservados para aplicar a
preparação automática do novo sorteio e das tabelas. O log ativo é
`cache/s02/fechamento.stderr.log`; cache, checkpoint e log anterior foram mantidos.
A coleta e os resultados definitivos ainda não estão concluídos. Lorran escolheu
manter as avaliações dos integrantes, sem três agentes de IA substitutos. O
reaproveitamento depende da correspondência dos itens e da origem dos rótulos;
o C legado não foi confirmado como avaliação de Lorran. O contrato e as pendências
estão em `fechamento_s02.md`.

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

## Execução completa e pendências — registro inicial, superado abaixo

A coleta real está em execução separada da S01, com checkpoint em
`data/s02/checkpoint.json` e log em `cache/s02/retomada.stderr.log`. Os contadores
de andamento não são resultados finais; consulte o checkpoint atual.

C1 somente fecha depois de validar e congelar pelo menos 300 repositórios.
C2 e os números de C4 dependem desse congelamento. Lorran confirmou não ter
preenchido o arquivo C legado; Pedro o adicionou no commit `8f7bd93`, junto do B.
O histórico não estabelece a origem de seus rótulos. Não foram alterados esses
arquivos, consensos ou resultados de validação dos colegas.

## Revisão C assistida por IA

`data/revisao_c_provisoria/` preserva notas, mensagens de commits, descrições e
README públicos, sem ler avaliações A/B ou previsões da heurística. Foram
examinadas 300 releases e classificados os 60 repositórios da amostra atual.
Há 281 rótulos provisórios e 19 ausentes; 109 análises usam evidência parcial
e 27 registram ambiguidade. São 145 consultas completas e 19 insuficientes.
Consulta completa descreve o material de evidência examinado, não auditoria de
todo o código do repositório. As justificativas e hashes acompanham as decisões.
O arquivo Excel identifica a origem por IA e não atesta avaliação humana.
Sua exportação foi reimportada e conferida; identificadores e listas suspensas
do modelo foram preservados, e as três abas foram inspecionadas visualmente.

Essa amostra veio da S01; a revisão definitiva depende do alinhamento da
amostra-ouro por A após o congelamento. A consolidação C agora exige vínculo
explícito e proveniência do consenso antes de incorporá-lo ao dataset. Dados
insuficientes não são convertidos em negativos, nem em tipos imputados.

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

C1 e a metodologia de coleta de C4 estão concluídas; C2 ainda depende da heurística
qualificada e dos tipos, e C3 depende da avaliação independente real de Lorran.
O dataset mantém 300 tipos ausentes e sete CFR (b) indisponíveis. As dependências
de A/B, hashes e instruções de fechamento estão em `fechamento_s02.md`.
