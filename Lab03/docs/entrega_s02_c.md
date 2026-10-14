# Sprint 2 — integrante C (Lorran)

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
snapshots diferentes. O resultado é `data/dataset.csv`, com uma linha por
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

Valores ausentes ficam vazios, não zero. O tipo vem exclusivamente do consenso;
os demais repositórios permanecem sem classificação humana. No CFR (b), uma
comparação indisponível ou mensagem ausente que não seja suprida pelo critério
SemVer impede afirmar a ausência de correção: o indicador fica indisponível e
`releases_sem_evidencia_textual` registra a limitação. Comparações 404 continuam
excluídas do lead time. Datas inválidas são contadas conforme o cálculo existente.

## Rotulagem C e dependência de A

Não consulte rótulos de A/B, consenso ou previsões da heurística ao avaliar.
Use apenas os links e definições do guia de rotulagem de A. A avaliação precisa
ser realizada individualmente pelo integrante; o pipeline não cria rótulos.

A amostra-ouro atualmente versionada veio dos 100 repositórios da S01, antes do
congelamento de C1. Ela não é automaticamente a amostra-ouro definitiva da S02.
Depois do congelamento dos 300, A precisa conferir/refazer seu sorteio de 60
repositórios e 5 releases por repositório, com as fontes S02. Preserve o material
anterior para rastreabilidade. O grupo precisa confirmar a autoria dos rótulos C
já publicados antes de considerá-los avaliações independentes de Lorran.

Para conferir somente formato e completude de uma planilha C, pode-se reutilizar
a função `validar_arquivo` de `scripts.validar_rotulos_b`; a validação não comprova
autoria, leitura das páginas ou independência. Não copie avaliações de outro
integrante para preencher lacunas.

## Evidência e estado da entrega

O piloto real consultou `dtcooper/raspotify`: histórico de releases/tags, cinco
comparações e coleta de runs concluíram. Isso não comprova a coleta de 300.
A execução completa só está concluída quando o manifesto de congelamento e o
dataset existirem e forem validados. Os logs locais e o checkpoint mostram o
andamento; não substitua esses resultados por dados simulados.

`python -m pipeline.dataset` também gera `docs/artigo/tabelas/coleta_s02.tex`, com
os números efetivos. A subseção `docs/artigo/metodologia_coleta.tex` pode ser
incluída no artigo sem substituir a metodologia de A/B. Antes da submissão,
reconcilie com A a descrição da amostra-ouro e com B a avaliação correspondente.
