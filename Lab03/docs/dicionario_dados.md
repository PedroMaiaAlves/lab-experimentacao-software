
## Amostra-ouro e validação manual (Sprint 2)

Os rótulos humanos são preenchidos em planilhas `data/amostra_ouro/rotulos/rotulos_<A|B|C>.xlsx`
(abas `repositorios` e `releases`, geradas a partir de `modelo/rotulos_modelo.xlsx`). Os arquivos abaixo
são gerados por `python -m validacao.amostra_ouro` e `python -m validacao.concordancia`.

### `repos_sorteados.csv`

Os 60 repositórios sorteados com `df.sample(n=60, random_state=semente)`, depois de ordenar a amostra por
`full_name`. Mantém as colunas de `metadados.csv`, mais `repo_url`.

| Coluna | Tipo | Unidade/formato | Origem ou definição |
|---|---|---|---|
| `full_name` | texto | `owner/repo` | Repositório sorteado |
| `stars` | inteiro | estrelas | Igual a `metadados.csv` |
| `language` | texto | nome da linguagem | Igual a `metadados.csv` |
| `default_branch` | texto | nome do branch | Igual a `metadados.csv` |
| `created_at` | data | `AAAA-MM-DD` | Igual a `metadados.csv` |
| `idade_dias` | inteiro | dias | Igual a `metadados.csv` |
| `contribuidores` | inteiro | pessoas/entradas | Igual a `metadados.csv` |
| `repo_url` | texto | URL | `https://github.com/` + `full_name` |

### `releases_sorteadas.csv`

Até 5 releases por repositório sorteado, entre as da definição principal (`draft=false`,
`prerelease=false`, publicadas na janela).

| Coluna | Tipo | Unidade/formato | Origem ou definição |
|---|---|---|---|
| `full_name` | texto | `owner/repo` | Repositório da release |
| `release_id` | inteiro | identificador GitHub | `id` em `releases.csv` |
| `tag_name` | texto | nome da tag | `tag_name` em `releases.csv` |
| `published_at` | timestamp | ISO 8601 | `published_at` em `releases.csv` |
| `release_url` | texto | URL | `html_url` em `releases.csv`; página com as notas |
| `compare_url` | texto/vazio | URL | Comparação com a release anterior (`previous_tag_name` em `comparacoes_releases.csv`); vazio se não há anterior |

### `decisoes_reuniao.csv`

Decisões do grupo para os casos em que os três avaliadores discordaram entre si (1-1-1).

| Coluna | Tipo | Unidade/formato | Origem ou definição |
|---|---|---|---|
| `dimensao` | texto | `tipo_projeto`, `releases_sao_entregas` ou `corretiva` | Dimensão rotulada |
| `chave` | texto | `full_name` ou `full_name\|release_id` | Item decidido |
| `rotulo` | texto | categoria | Rótulo escolhido em reunião |

### `kappa_fleiss.csv`

| Coluna | Tipo | Unidade/formato | Origem ou definição |
|---|---|---|---|
| `dimensao` | texto | categoria | Dimensão rotulada |
| `n_itens` | inteiro | itens | Repositórios (tipo, entregas) ou releases (corretiva) rotulados |
| `kappa` | real | −1 a 1 | Kappa de Fleiss com três avaliadores; vazio se todos usaram uma só categoria |
| `interpretacao` | texto | categoria | Faixa de Landis & Koch (1977) |
| `concordancia_unanime_pct` | real | % | Itens em que os três avaliadores concordaram |
| `n_maioria` | inteiro | itens | Itens decididos por maioria 2-1 |
| `n_reuniao` | inteiro | itens | Itens 1-1-1, decididos em reunião |

### `consenso_repos.csv`

| Coluna | Tipo | Unidade/formato | Origem ou definição |
|---|---|---|---|
| `full_name` | texto | `owner/repo` | Repositório rotulado |
| `tipo_projeto_A`, `tipo_projeto_B`, `tipo_projeto_C` | texto | categoria | Rótulo de cada avaliador: biblioteca/framework, aplicação/serviço, ferramenta CLI ou outro |
| `tipo_projeto` | texto | categoria | Rótulo de consenso; usado como fator na RQ 06 |
| `tipo_projeto_decisao` | texto | `unanime`/`maioria`/`reuniao` | Como o consenso foi obtido |
| `releases_sao_entregas_A`, `releases_sao_entregas_B`, `releases_sao_entregas_C` | texto | `sim`/`não`/`incerto` | Rótulo de cada avaliador |
| `releases_sao_entregas` | texto | `sim`/`não`/`incerto` | Rótulo de consenso |
| `releases_sao_entregas_decisao` | texto | `unanime`/`maioria`/`reuniao` | Como o consenso foi obtido |

### `consenso_releases.csv`

| Coluna | Tipo | Unidade/formato | Origem ou definição |
|---|---|---|---|
| `full_name` | texto | `owner/repo` | Repositório da release |
| `release_id` | inteiro | identificador GitHub | Release rotulada |
| `tag_name` | texto | nome da tag | Tag da release |
| `corretiva_A`, `corretiva_B`, `corretiva_C` | texto | `sim`/`não` | A release tem como objetivo principal corrigir defeito recente, segundo cada avaliador |
| `corretiva` | texto | `sim`/`não` | Rótulo de consenso; referência para precisão, recall e F1 da heurística |
| `corretiva_decisao` | texto | `unanime`/`maioria`/`reuniao` | Como o consenso foi obtido |

### `casos_divergentes.csv`

Itens em que os avaliadores não foram unânimes, para a reunião de consenso.

| Coluna | Tipo | Unidade/formato | Origem ou definição |
|---|---|---|---|
| `dimensao` | texto | categoria | Dimensão rotulada |
| `chave` | texto | `full_name` ou `full_name\|release_id` | Item com divergência |
| `A`, `B`, `C` | texto | categoria | Rótulo de cada avaliador |
| `desempate` | texto | `maioria`/`reuniao` | Regra aplicada |
| `rotulo_final` | texto | categoria | Rótulo resultante; vazio enquanto um caso 1-1-1 não tem decisão |

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
| `message` | texto | livre | Mensagem integral de `commit.message`, usada pela heurística de release corretiva |

O snapshot S01 versionado antes da heurística não possui a coluna `message`. Ela é
materializada ao reexecutar a coleta de commits para a S02; o cache HTTP evita repetir
chamadas já armazenadas.
