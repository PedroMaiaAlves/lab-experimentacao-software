# Lab03 — Mineração de métricas DORA

Pipeline reprodutível que seleciona repositórios open-source populares com GitHub Actions,
coleta releases, commits e workflow runs na janela de observação e calcula as métricas DORA
(deployment frequency, lead time for changes, change failure rate e tempo de recuperação).

Disciplina: Laboratório de Experimentação de Software — PUC Minas.

## Requisitos

- Python 3.12 (ou superior)
- Um *personal access token* do GitHub (sem escopos especiais para repositórios públicos)

## Instalação

```bash
git clone <URL-DO-REPOSITORIO>
cd <PASTA-DO-REPOSITORIO>
python -m venv .venv
# Linux/macOS
source .venv/bin/activate
# Windows (PowerShell)
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

## Token do GitHub

O token é lido da variável de ambiente `GITHUB_TOKEN` e **nunca** deve ser commitado.

```bash
# Linux/macOS
export GITHUB_TOKEN="ghp_seu_token"
# Windows (PowerShell)
$env:GITHUB_TOKEN = "ghp_seu_token"
```

## Execução (comando único)

```bash
python -m pipeline --config config.yaml
```

Teste rápido com poucos repositórios (recomendado antes da execução completa):

```bash
python -m pipeline --config config.yaml --meta 5
```

Opções: `--config` (padrão `config.yaml`), `--meta N` (sobrescreve a meta de repositórios),
`-v` (logs detalhados).

### Retomada e cache

Toda resposta da API é salva em `cache/`. Se a execução for interrompida (rate limit, queda de
rede ou `Ctrl+C`), basta rodar o mesmo comando de novo: as chamadas já feitas são lidas do cache.
Para recomeçar do zero, apague a pasta `cache/`.

## Configuração (`config.yaml`)

| Chave | Significado |
|---|---|
| `janela_inicio`, `janela_fim` | Janela de observação de 12 meses (datas fixadas pelo professor) |
| `semente` | Semente de qualquer sorteio do pipeline |
| `criterios.min_releases` / `min_runs` | Critério mínimo de inclusão (5 releases e 50 runs válidos) |
| `selecao.meta_repositorios` | Quantos repositórios devem restar após os filtros |
| `selecao.faixas_estrelas` | Faixas de estrelas das consultas de busca (cada uma devolve até 1.000) |
| `selecao.linguagens` | Linguagens usadas para subdividir faixas com mais de 1.000 resultados |
| `saida.dir_dados` / `dir_cache` | Pastas de saída e de cache |
| `etapas_coleta` | Módulos de coleta executados após o funil (`coletar(client, cfg, repos)`) |

## Saídas (`data/`)

| Arquivo | Conteúdo |
|---|---|
| `candidatos.csv` | Repositórios candidatos (únicos, embaralhados com a semente) |
| `funil.csv` | Quantos repositórios restaram em cada etapa e o motivo dos descartes |
| `descartes.csv` | Cada repositório descartado, a etapa e o motivo |
| `metadados.csv` | Estrelas, linguagem, idade em dias e nº de contribuidores da amostra |

O dicionário de dados completo estará em `docs/dicionario_dados.md`.

## Testes

```bash
pytest --cov=metricas --cov-report=term-missing
```

Os testes também rodam a cada push no GitHub Actions (`.github/workflows/testes.yml`).

## Estrutura

```
config.yaml            configuração
pipeline/              coleta (python -m pipeline)
metricas/              funções de cálculo das métricas e classificação DORA
tests/                 testes automatizados
data/                  CSVs gerados
docs/                  artigo, dicionário de dados e documentação
notebooks/             análises (S03)
scripts/               utilitários (criação das Issues)
```

## Observações de método

- Apenas o *default branch*; deploy = release publicada (`draft = false`); CI = runs com
  `event = push`.
- Repositórios arquivados e forks ficam fora da busca.
- Os candidatos são embaralhados com a semente e avaliados em ordem até atingir a meta; por isso o
  funil registra quantos candidatos foram de fato avaliados.
