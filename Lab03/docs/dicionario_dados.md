# Dicionário de dados — Lab03

Os CSVs são gravados em UTF-8, separados por vírgula e com cabeçalho. Números usam
ponto decimal; valores indisponíveis ficam vazios. Timestamps vindos da API estão em
ISO 8601, normalmente em UTC (`Z`). A janela tem extremos inclusivos.

## Seleção e funil

### `candidatos.csv`

| Coluna | Tipo | Unidade/formato | Origem ou definição |
|---|---|---|---|
| `full_name` | texto | `owner/repo` | `repository.full_name` da Search API; identificador do repositório |
| `stars` | inteiro | estrelas | `stargazers_count` no momento da coleta |
| `language` | texto | nome da linguagem | Linguagem principal informada pelo GitHub; vazio quando ausente |
| `default_branch` | texto | nome do branch | `default_branch` informado pela API |
| `created_at` | timestamp | ISO 8601 | Data de criação do repositório |
| `html_url` | texto | URL | Página do repositório no GitHub |
| `consulta` | texto | consulta Search API | Partição de estrelas/linguagem que encontrou o candidato |

### `funil.csv`

| Coluna | Tipo | Unidade/formato | Origem ou definição |
|---|---|---|---|
| `etapa` | texto | categoria | Busca, candidatos avaliados, Actions, releases, runs ou amostra final |
| `entraram` | inteiro | repositórios | Quantidade que iniciou a etapa; vazio quando não se aplica |
| `descartados` | inteiro | repositórios | Quantidade rejeitada na etapa; vazio quando não se aplica |
| `restaram` | inteiro | repositórios | Quantidade restante registrada para a etapa |
| `motivo_descarte` | texto | categoria/descrição | Regra aplicada aos descartes da etapa |

### `descartes.csv`

| Coluna | Tipo | Unidade/formato | Origem ou definição |
|---|---|---|---|
| `full_name` | texto | `owner/repo` | Repositório descartado |
| `etapa` | texto | categoria | Etapa em que ocorreu o descarte |
| `motivo` | texto | categoria | Motivo do descarte, inclusive eventual código HTTP |

### `metadados.csv`

| Coluna | Tipo | Unidade/formato | Origem ou definição |
|---|---|---|---|
| `full_name` | texto | `owner/repo` | Repositório da amostra final |
| `stars` | inteiro | estrelas | `stargazers_count` obtido na seleção |
| `language` | texto | nome da linguagem | Linguagem principal informada pelo GitHub |
| `default_branch` | texto | nome do branch | Branch usado nas coletas de CI |
| `created_at` | data | `AAAA-MM-DD` | Data de criação do repositório |
| `idade_dias` | inteiro | dias | `janela_fim - created_at` |
| `contribuidores` | inteiro | pessoas/entradas | Total estimado pela última página de `/contributors?per_page=1&anon=true`; vazio se indisponível |

## Releases, tags e commits

### `releases.csv`

Uma linha por release retornada pela API, inclusive registros fora da janela, drafts
visíveis ao token e pré-releases. Isso preserva o histórico necessário às variantes.

| Coluna | Tipo | Unidade/formato | Origem ou definição |
|---|---|---|---|
| `full_name` | texto | `owner/repo` | Repositório da release |
| `id` | inteiro | identificador GitHub | `release.id` |
| `tag_name` | texto | nome da tag | `release.tag_name` |
| `target_commitish` | texto | branch/SHA | Alvo informado na release |
| `draft` | booleano | `True`/`False` | Indica rascunho; drafts não entram na definição principal |
| `prerelease` | booleano | `True`/`False` | Indica pré-release; não entra na definição principal |
| `published_at` | timestamp | ISO 8601 | Data de publicação; usada como instante do deploy proxy |
| `created_at` | timestamp | ISO 8601 | Data de criação do objeto release |
| `html_url` | texto | URL | Página da release |
| `name` | texto | livre | Título da release |
| `body` | texto | livre/Markdown | Notas da release |

### `tags.csv`

| Coluna | Tipo | Unidade/formato | Origem ou definição |
|---|---|---|---|
| `full_name` | texto | `owner/repo` | Repositório da tag |
| `tag_name` | texto | nome da tag | Nome retornado por `/tags` |
| `commit_sha` | texto | SHA Git | Commit apontado pela tag |
| `commit_author_date` | timestamp | ISO 8601 | `commit.author.date` do commit apontado; não é a data de criação da tag |
| `status` | texto | `ok`/`erro_404` | Resultado da consulta do commit apontado |

### `comparacoes_releases.csv`

| Coluna | Tipo | Unidade/formato | Origem ou definição |
|---|---|---|---|
| `full_name` | texto | `owner/repo` | Repositório comparado |
| `release_id` | inteiro | identificador GitHub | Release atual dentro da janela |
| `tag_name` | texto | nome da tag | Head da comparação |
| `published_at` | timestamp | ISO 8601 | Publicação da release atual |
| `previous_tag_name` | texto | nome da tag | Release principal imediatamente anterior, inclusive fora da janela |
| `status` | texto | `ok`/`sem_anterior`/`erro_404` | Resultado da comparação |
| `commits_count` | inteiro | commits | Commits únicos obtidos na comparação; zero pode ser válido |

### `commits_entre_releases.csv`

| Coluna | Tipo | Unidade/formato | Origem ou definição |
|---|---|---|---|
| `full_name` | texto | `owner/repo` | Repositório do commit |
| `release_id` | inteiro | identificador GitHub | Release atual da comparação |
| `tag_name` | texto | nome da tag | Release atual |
| `published_at` | timestamp | ISO 8601 | Publicação da release atual |
| `previous_tag_name` | texto | nome da tag | Base da comparação |
| `sha` | texto | SHA Git | Identificador do commit |
| `author_date` | timestamp | ISO 8601 | `commit.author.date`, conforme definição obrigatória |

## Métricas já materializadas na Sprint 1

### `deployment_frequency.csv`

| Coluna | Tipo | Unidade/formato | Origem ou fórmula |
|---|---|---|---|
| `full_name` | texto | `owner/repo` | Repositório da amostra |
| `deployment_frequency` | real | releases/semana | `releases_principais / semanas_janela` |
| `releases_principais` | inteiro | releases | Releases na janela com `draft=false` e `prerelease=false` |
| `semanas_janela` | real | semanas | `(janela_fim - janela_inicio + 1 dia) / 7` |

### `lead_time.csv`

| Coluna | Tipo | Unidade/formato | Origem ou fórmula |
|---|---|---|---|
| `full_name` | texto | `owner/repo` | Repositório da amostra |
| `lead_time_a_horas` | real | horas | Mediana, entre releases válidas, de `published_at - commit mais antigo` |
| `lead_time_b_horas` | real | horas | Mediana dos tempos de todos os commits de todas as comparações válidas |
| `releases_comparadas` | inteiro | releases | Comparações com status `ok`, inclusive as sem commits novos |
| `releases_sem_anterior` | inteiro | releases | Releases sem uma antecessora histórica válida |
| `releases_erro_404` | inteiro | releases | Comparações indisponíveis por HTTP 404 |
| `releases_sem_commits` | inteiro | releases | Comparações `ok` que não retornaram commits novos |

## Workflow runs

### `workflow_runs/<owner>__<repo>.json`

Cada arquivo representa um repositório. O objeto raiz contém:

| Campo | Tipo | Unidade/formato | Origem ou definição |
|---|---|---|---|
| `full_name` | texto | `owner/repo` | Repositório coletado |
| `default_branch` | texto | nome do branch | Branch enviado ao filtro da API |
| `janela_inicio` | data | `AAAA-MM-DD` | Início inclusivo da coleta |
| `janela_fim` | data | `AAAA-MM-DD` | Fim inclusivo da coleta |
| `complete` | booleano | `true`/`false` | `false` se algum intervalo diário ainda atingiu o teto de 1.000 resultados |
| `saturated_intervals` | lista | objetos | Intervalos subdivididos ou irredutivelmente incompletos |
| `workflow_runs` | lista | objetos | Runs únicos, deduplicados por `id` |

Cada item de `workflow_runs` contém:

| Campo | Tipo | Unidade/formato | Origem ou definição |
|---|---|---|---|
| `id` | inteiro | identificador GitHub | ID único do run |
| `workflow_id` | inteiro | identificador GitHub | Workflow usado para agrupar episódios de recuperação |
| `name` | texto | livre | Nome do workflow |
| `conclusion` | texto/vazio | categoria GitHub | `success`; falhas; ou valores ignorados segundo o enunciado |
| `run_started_at` | timestamp | ISO 8601 | Início usado no tempo de recuperação |
| `updated_at` | timestamp | ISO 8601 | Fim do sucesso que encerra um episódio |
| `created_at` | timestamp | ISO 8601 | Data usada pela API para limitar a janela |

### `runs_saturados.csv`

| Coluna | Tipo | Unidade/formato | Origem ou definição |
|---|---|---|---|
| `full_name` | texto | `owner/repo` | Repositório consultado |
| `inicio` | data | `AAAA-MM-DD` | Primeiro dia inclusivo do intervalo |
| `fim` | data | `AAAA-MM-DD` | Último dia inclusivo do intervalo |
| `total_count` | inteiro | runs | Total informado pela API antes da subdivisão |
| `status` | texto | `subdividido`/`incompleto` | `incompleto` significa que um único dia ainda atingiu 1.000 resultados |

## Cache

Os arquivos em `cache/` não integram o dataset. Cada JSON armazena a resposta e os
cabeçalhos de uma combinação de URL e parâmetros, identificada por SHA-256. Eles permitem
retomada sem repetir chamadas, mas podem conter campos adicionais da API e não devem ser
usados diretamente na análise.
