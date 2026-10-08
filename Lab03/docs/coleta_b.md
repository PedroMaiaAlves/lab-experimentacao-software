# LAB03 S01 — Entregas do integrante B

Releases/tags, commits entre releases, lead time, deployment frequency, CI e hipóteses
RQ05–RQ07. Os testes usam fixtures; as funções de métricas não chamam a API.

## Coleta e integração

Execute os comandos do README a partir de `Lab03/`. As etapas registradas no config são
`pipeline.coleta_releases`, `pipeline.coleta_commits` e a coleta de runs do integrante C.
Cada módulo de coleta recebe `coletar(client, cfg, repos)`. O cliente compartilhado deve
expor `get_json(caminho, params=None)` e `paginate(caminho, params=None, chave=None)`,
com cache, rate limit e paginação por `Link`. A integração utiliza o `GitHubClient`
de `pipeline.http_client`, entregue por C. As respostas completas ficam no cache HTTP;
os CSVs preservam os campos usados pelo estudo.

As coletas recebem apenas a amostra aprovada pelo funil. Releases e tags são paginadas
até o fim, inclusive antes da janela. Para cada SHA de tag, consultamos a data
`commit.author.date`; tags diferentes com o mesmo SHA compartilham uma consulta.
Essa data não é a data de criação da tag. Um 404 fica registrado em `tags.csv`.
Drafts são preservados quando acessíveis ao token: a API só os mostra a quem tem
permissão de escrita no repositório.

`filtrar_releases` exclui drafts e publicações fora da janela. Por padrão também exclui
pré-releases, que ficam preservadas e podem ser incluídas com `incluir_prereleases=True`.
As datas de início e fim são inclusivas. A janela do config deve ser confirmada com o
enunciado antes da coleta oficial; o arquivo original ainda contém essa pendência.

## Comparações e métricas

Ordenamos as releases publicadas da definição escolhida por `published_at` (UTC na API),
com ID como desempate. Cada release na janela é comparada à sua antecessora histórica,
mesmo quando esta está fora da janela. Pré-releases não são antecessoras na definição
principal. As tags são codificadas na URL e `compare` usa `per_page=100`, seguindo todas
as páginas para ultrapassar o limite de 250 commits da resposta sem paginação.

`comparacoes_releases.csv` contém uma linha por release principal na janela:

- `ok`: comparação concluída; `commits_count` pode ser zero.
- `sem_anterior`: primeira release da história nessa definição, sem base para lead time.
- `erro_404`: tag/comparação indisponível; commits parciais são descartados.

`commits_entre_releases.csv` contém uma linha por relação release/commit, com SHA e
`author_date`. Duplicatas de SHA dentro da mesma comparação são removidas. O mesmo
commit presente em releases diferentes continua em cada relação.

Lead time (a) é a mediana dos tempos entre cada publicação e seu commit mais antigo;
(b) é a mediana de todos os tempos por relação release/commit. Ambos usam horas e
timestamps com fuso. Releases sem antecessora, com 404 ou sem commits não entram nas
medianas; suas contagens ficam em `lead_time.csv`. Sem observações válidas, a mediana
fica vazia (`None`), não zero. Datas sem fuso ou commits posteriores à publicação
geram erro explícito, evitando tempos negativos ou correções silenciosas.

`deployment_frequency(datas_deploy, cfg)` recebe uma lista genérica de datas, conta as
que pertencem à janela e divide pelo número de semanas, calculado como
`(dias entre os extremos + 1) / 7`. A função pode receber datas de tags ou pré-releases;
a coleta principal passa apenas datas de releases não draft e não prerelease.

Os CSVs são UTF-8, separados por vírgula, com ponto decimal e valores ausentes vazios.
Cada nova execução recria os CSVs; as chamadas já respondidas são reutilizadas pelo
cache do cliente. Os arquivos são escritos por repositório para limitar o uso de memória.

## Verificação

`python -m pytest --cov=metricas --cov-report=term-missing --cov-fail-under=80`
é o mesmo comando do CI. Os testes cobrem o exemplo de 13/5/1 dias, limites da janela,
pré-releases/drafts, mais de 250 commits paginados, 404, duplicatas, datas inconsistentes,
ausência de observações e integração das etapas com uma amostra simulada de 100 repositórios.
Uma amostra simulada valida a integração, mas não substitui a coleta oficial do grupo.

## Referências da API

- [Releases e visibilidade de drafts](https://docs.github.com/en/rest/releases/releases#list-releases).
- [Tags e SHA do commit apontado](https://docs.github.com/en/rest/repos/repos#list-repository-tags).
- [Compare e paginação de mais de 250 commits](https://docs.github.com/en/rest/commits/commits#compare-two-commits).
