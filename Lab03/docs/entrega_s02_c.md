# Sprint 2 — integrante C (Lorran)

Este documento registra a implementação inicial de C. Depois dela, Lorran
autorizou complementar também A/B. O fluxo integrado atual está em
`fechamento_s02.md`; ele preserva o legado e usa `data/amostra_ouro_s02/`.

## Escopo

C1: coleta completa e congelamento; C2: dataset reexecutável; C3: rotulagem
independente do avaliador C; C4: metodologia da coleta com números reais.
Os módulos e rótulos de A e B são reutilizados, não reescritos.

## Coleta e retomada

Execute a partir de `Lab03/`, com as dependências de `requirements.txt` e
`GITHUB_TOKEN` no ambiente. A janela confirmada é 01/10/2025 a 30/09/2026.
`config_s02.yaml` mantém os filtros (5 releases principais e 50 runs válidos),
a semente 42 e a heurística v1 de B; a meta passa a 300 repositórios.

```bash
python -m pipeline.sprint2 --config config_s02.yaml --candidatos data/candidatos.csv
```

Esse comando reutiliza o snapshot versionado de 53.143 candidatos, na mesma ordem,
sem repetir a Search API. Isso amplia a amostra aceita, não a população de busca.
O snapshot contém a consulta de origem de cada candidato. Sem `--candidatos`, o
comando faz nova busca, incluindo as faixas adicionais do config. Não misture
snapshots ou janelas no mesmo diretório de execução.

As respostas ficam em `cache/s02/`, fora do Git. Compartilhe essa pasta por um
meio privado, sem tokens ou arquivos de configuração pessoal. O cache evita
repetir chamadas; `data/s02/checkpoint.json` registra a posição da seleção e as
coletas concluídas. Retome com o mesmo comando após uma interrupção. Um lock do
sistema operacional impede duas coletas no mesmo diretório; ele é liberado se o
processo morrer. Não apague o arquivo de lock para contornar uma execução ativa.

Na seleção, 404/410 são descartes registrados. Erros transitórios, rate limit e
problemas de autorização não viram evidência de ausência: após as tentativas do
cliente, a execução para sem avançar aquele candidato. O log informa progresso
e esperas. `cache/s02/http_metricas.json` registra respostas HTTP, status e
esperas desde o início da instrumentação; acertos de cache não são requests.
Se a instrumentação começou após uma execução anterior, esses contadores não
representam todo o histórico da coleta.

As saídas da S01 e os arquivos preenchidos de A/B/C permanecem intactos. Cada
repositório é coletado separadamente em `data/s02/coletas/`, evitando repetir
coletas concluídas e manter toda a amostra na memória. Os coletores existentes
de releases/tags, commits e runs são chamados sem alteração. Ao final, suas
saídas são reunidas em `data/s02/` e passam pela validação integrada da S01.
Somente depois são publicados `data/amostra_final.csv` e seu manifesto SHA-256.
Menos de 300, runs incompletos ou filtros não satisfeitos impedem o congelamento.
Uma amostra diferente nunca sobrescreve um congelamento anterior.

## Dataset e contrato

Após o congelamento, o coletor executa a consolidação automaticamente. Para
recalcular com a versão final da heurística de B ou com novo consenso de A:

```bash
python -m pipeline.dataset --config config_s02.yaml
```

O cálculo é offline. Os arquivos agregados são lidos em ordem por repositório,
sem precisar do cache ou das pastas intermediárias de coleta. Os hashes das
fontes e a janela precisam coincidir com o congelamento. Não é permitido juntar
snapshots diferentes. Os atributos Git dos artefatos de C preservam seus bytes,
inclusive quebras de linha, para que os hashes continuem válidos entre Windows e Linux.
O resultado é `data/dataset.csv`, com uma linha por
repositório, e `data/dataset.manifest.json`, com versão da heurística, hashes,
contagens reais e quantidade de tipos ausentes. Uma nova regra de B recalcula
o CFR (b) a partir dos mesmos commits, sem nova mineração.

As colunas estáveis estão em `pipeline.dataset.CAMPOS`:

- Identificação: metadados existentes, `tipo_projeto`, `releases_sao_entregas`,
  `rotulo_disponivel` e `heuristica_versao`.
- Frequência, em entregas/semana: `deployment_frequency` (releases principais),
  `deployment_frequency_prereleases` (inclui pré-releases) e
  `deployment_frequency_tags` (data de autoria do commit da tag, não criação da tag).
- Tempos em horas: `lead_time_a_horas`, `lead_time_b_horas` e
  `tempo_recuperacao_horas`.
- Proporções de 0 a 1: `cfr_a`, `cfr_b` e `proporcao_censurados`.
- Contagens: releases principais/com pré-releases, tags na janela/sem data,
  comparações válidas/sem anterior/404/vazias, commits com data inválida,
  releases avaliadas/com falha/censuradas, runs válidos/sucessos/falhas/ignorados,
  episódios concluídos/censurados e intervalos saturados/incompletos.

Valores ausentes ficam vazios, não zero. O tipo vem exclusivamente do consenso
validado para a amostra congelada; os demais repositórios permanecem sem tipo.
O arquivo `consenso_repos.manifest.json`, ao lado do CSV, precisa registrar
`amostra_sha256`, `consenso_sha256`, `rotulagem_independente_confirmada: true`
e `origem_rotulagem` (`humana`, `assistida_por_IA` ou `mista`). Esses campos
atestam o vínculo e a origem, não autorizam fabricar confirmação. Sem manifesto,
o consenso legado não é utilizado; com manifesto inconsistente, o cálculo falha.
O manifesto do dataset registra se houve consenso efetivamente utilizado.
No CFR (b), uma
comparação indisponível ou mensagem ausente que não seja suprida pelo critério
SemVer impede afirmar a ausência de correção: o indicador fica indisponível e
`releases_sem_evidencia_textual` registra a limitação. Comparações 404 continuam
excluídas do lead time. Datas inválidas são contadas conforme o cálculo existente.

## Rotulagem C e dependência de A

Não consulte rótulos de A/B, consenso ou previsões da heurística ao avaliar.
Use os links e definições do guia de rotulagem de A. Lorran solicitou análise
assistida por IA; ela não deve ser descrita como avaliação humana que ele realizou.
O código organiza fontes e exporta decisões explícitas, sem usar a heurística
para inventar a avaliação independente.

A amostra-ouro legada em `data/amostra_ouro/` veio dos 100 repositórios da S01.
Após o congelamento dos 300, o novo sorteio definitivo foi gerado em
`data/amostra_ouro_s02/`, com 60 repositórios e 5 releases por repositório.
As três planilhas definitivas estão preparadas em branco; somente 50 releases
coincidem com o piloto. O material anterior foi preservado para rastreabilidade.
Lorran confirmou que não preencheu os rótulos C
publicados. O histórico mostra que Pedro adicionou `rotulos_B.xlsx` e
`rotulos_C.xlsx` no commit `8f7bd93`; isso não demonstra como as avaliações C
foram produzidas. O arquivo não foi sobrescrito e não é tratado como revisão
independente de Lorran.

A revisão separada está em `data/revisao_c_provisoria/rotulos_C_ia_provisorios.xlsx`,
com CSVs, fontes públicas preservadas, justificativas e hashes. Foram examinados
60 repositórios e 300 releases da amostra piloto: 281 decisões provisórias e
19 casos sem rótulo por evidência insuficiente. O campo `escopo_evidencia` distingue
consulta integral, parcial, ambiguidade e insuficiência. Trechos de notas longas
não são apresentados como investigação integral. Nenhuma linha atesta revisão
humana ou confirmação definitiva. Esses arquivos **não** são automaticamente
incorporados ao kappa, consenso ou avaliação F1 de A/B.

```bash
python -m pipeline.revisao_c --documentacao
python -m pipeline.revisao_c --exportar
```

O primeiro comando reúne as fontes sem rótulos dos colegas ou previsões; o
segundo valida e exporta as decisões de `avaliacao_c.json` e
`avaliacao_repos_c.json`. Não preenche ausentes com negativos. Antes de C3 ser
concluída, é preciso realizar a avaliação individual na amostra definitiva.
A decisão mais recente foi manter as avaliações dos integrantes, não gerar três
substitutas por IA. Essa é uma pendência explícita,
não uma revisão humana simulada nem uma validação-ouro já concluída.

Para conferir somente formato e completude de uma planilha C, pode-se reutilizar
a função `validar_arquivo` de `scripts.validar_rotulos_b`; a validação não comprova
autoria, leitura das páginas ou independência. Não copie avaliações de outro
integrante para preencher lacunas.

## Evidência e estado da entrega

O piloto real consultou `dtcooper/raspotify`; posteriormente, a coleta completa
terminou em 15/10/2026, às 05:15 UTC, com 300 repositórios validados e congelados,
dataset reproduzido offline e fontes publicadas em `data/fontes_s02.zip`.
Consulte `fechamento_s02.md` para hashes, comandos de restauração e pendências.
A coleta terminou, mas a validação manual e o refinamento da heurística não.
Após a retomada para aplicar o fechamento integrado, o log final é
`cache/s02/fechamento.stderr.log`; `retomada.stderr.log` preserva a execução anterior.

`python -m pipeline.dataset` também gera `docs/artigo/tabelas/coleta_s02.tex`, com
os números efetivos. A subseção `docs/artigo/metodologia_coleta.tex` pode ser
incluída no artigo sem substituir a metodologia de A/B. Antes da submissão,
reconcilie com A a descrição da amostra-ouro e com B a avaliação correspondente.
