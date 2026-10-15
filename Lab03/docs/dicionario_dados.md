# Dicionário de dados — LAB03

## Dataset consolidado da Sprint 2

`data/dataset.csv` contém uma linha por repositório da amostra congelada. Números
ausentes ficam vazios; zero é um resultado observado. Datas são UTC. A duração
da janela é inclusiva: `W = (fim - início + 1 dia) / 7`. Releases principais não
são draft nem pré-release e têm `published_at` na janela. CI é `event=push` no
default branch. O manifesto identifica fontes, versão da heurística e consenso
efetivamente utilizado; não se misturam amostra-ouro piloto e definitiva.

| Coluna | Tipo | Unidade | Definição ou fórmula |
|---|---|---|---|
| `full_name` | texto | owner/repo | Chave única da amostra |
| `stars` | inteiro | estrelas | Contagem de estrelas coletada nos metadados |
| `language` | texto/vazio | linguagem | Linguagem principal informada pelo GitHub |
| `default_branch` | texto | branch | Branch padrão consultado na coleta |
| `created_at` | timestamp | ISO 8601 UTC | Criação do repositório |
| `idade_dias` | inteiro | dias | Diferença entre criação e fim da janela, conforme coletor de metadados |
| `contribuidores` | inteiro/vazio | entradas | Contagem fornecida pelo coletor de contribuidores; vazio se indisponível |
| `tipo_projeto` | categoria/vazio | categoria | Consenso validado: biblioteca/framework, aplicação/serviço, ferramenta CLI ou outro |
| `releases_sao_entregas` | categoria/vazio | sim/não/incerto | Consenso sobre releases representarem entregas consumíveis |
| `rotulo_disponivel` | booleano | lógico | Há tipo do projeto no consenso utilizado; não comprova avaliação humana |
| `heuristica_versao` | texto | versão | Regra efetivamente utilizada no CFR (b) |
| `deployment_frequency` | real | entregas/semana | Releases principais / W |
| `deployment_frequency_prereleases` | real | entregas/semana | Releases não draft, incluindo pré-releases, na janela / W |
| `deployment_frequency_tags` | real | tags/semana | Tags cuja autoria do commit está na janela / W; não é data de criação da tag |
| `lead_time_a_horas` | real/vazio | horas | Mediana por release do maior tempo válido entre autoria do commit e publicação |
| `lead_time_b_horas` | real/vazio | horas | Mediana de todas as relações release/commit válidas até a publicação |
| `cfr_a` | real/vazio | proporção 0–1 | runs_falhas / runs_validos; ausente se denominador zero |
| `cfr_b` | real/vazio | proporção 0–1 | releases_falharam / releases_avaliadas; ausente sem denominador ou evidência suficiente |
| `tempo_recuperacao_horas` | real/vazio | horas | Mediana dos episódios concluídos: início da primeira falha após sucesso até término do próximo sucesso, por workflow |
| `releases_principais` | inteiro | releases | Número de releases principais na janela |
| `releases_com_prereleases` | inteiro | releases | Releases não draft na janela, incluindo pré-releases |
| `tags_na_janela` | inteiro | tags | Tags com data de autoria válida na janela |
| `tags_sem_data` | inteiro | tags | Tags sem status ok ou sem data de autoria disponível |
| `releases_comparadas` | inteiro | comparações | Comparações com status ok, inclusive vazias |
| `releases_sem_anterior` | inteiro | releases | Primeira release do histórico principal, sem antecessora |
| `releases_erro_404` | inteiro | comparações | Comparações indisponíveis com erro HTTP 404 |
| `releases_sem_commits` | inteiro | comparações | Comparações ok com zero commits retornados |
| `commits_data_invalida` | inteiro | relações release/commit | Data inválida, sem fuso ou posterior à publicação; excluída do lead time |
| `releases_sem_evidencia_textual` | inteiro | releases | Comparação 404 ou mensagem ausente sem evidência positiva alternativa; impede afirmar CFR (b) |
| `cfr_b_disponivel` | booleano | lógico | Não há lacunas textuais impeditivas; ainda pode faltar denominador válido |
| `releases_avaliadas` | inteiro | releases | Releases principais até fim da janela menos sete dias, inclusive |
| `releases_falharam` | inteiro/vazio | releases | Avaliadas com alguma corretiva posterior em até sete dias; ausente se há lacuna impeditiva |
| `releases_censuradas` | inteiro | releases | Releases das sete últimas datas da janela, fora do denominador |
| `runs_total` | inteiro | runs | Todas as execuções coletadas na janela, evento e branch definidos |
| `runs_validos` | inteiro | runs | runs_sucessos + runs_falhas |
| `runs_sucessos` | inteiro | runs | conclusion=success |
| `runs_falhas` | inteiro | runs | conclusion=failure, timed_out ou startup_failure |
| `runs_ignorados` | inteiro | runs | runs_total - runs_validos; cancelados, pulados e demais estados |
| `episodios_total` | inteiro | episódios | Episódios concluídos + censurados; não inclui falhas iniciais sem sucesso anterior |
| `episodios_concluidos` | inteiro | episódios | Falhas observadas após um sucesso e encerradas por outro sucesso do workflow |
| `episodios_censurados` | inteiro | episódios | Falhas abertas após sucesso sem recuperação observada até o fim |
| `proporcao_censurados` | real/vazio | proporção 0–1 | episodios_censurados / episodios_total; ausente sem episódios |
| `intervalos_saturados` | inteiro | intervalos | Consultas com teto atingido, incluindo intervalos posteriormente subdivididos |
| `intervalos_incompletos` | inteiro | intervalos | Intervalos diários ainda saturados; qualquer ocorrência impede congelamento |

O tipo não é imputado aos repositórios não cobertos pelo consenso. Classificações
adicionais, se produzidas, devem ser identificadas como tal e não confundidas com
a amostra-ouro. As datas e contagens detalhadas da mineração permanecem nas fontes.

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
| `n_adjudicacao_IA` | inteiro | itens | Itens 1-1-1 submetidos a adjudicação por IA; não são reuniões humanas |

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
