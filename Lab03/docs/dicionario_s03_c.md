# Dicionário — RQ08 (parte C)

As taxas são proporções de 0 a 1, sem unidade; gráficos/tabelas LaTeX exibem
porcentagens. Campos numéricos vazios significam indisponíveis, nunca zero.
`full_name` identifica o projeto, e `(full_name, release_id)` identifica uma release.

## `results/s03_c/rq08_repositorios.csv`

Uma linha por projeto, cobrindo os 300 itens da amostra congelada.

| Coluna | Tipo | Unidade / definição |
|---|---|---|
| full_name | texto | Identificador GitHub |
| releases_total | inteiro | Releases principais na janela, sem censura final |
| releases_corretivas | inteiro | Positivas conhecidas da v3, com regra de disponibilidade da S02 |
| releases_sem_evidencia | inteiro | Lacunas pela regra S02 (404/mensagem ausente e negativa) |
| rework_rate | real/ausente | Corretivas / total; ausente se total zero ou qualquer lacuna S02 |
| rework_limite_inferior | real/ausente | Corretivas / total, desconhecidas negativas |
| rework_limite_superior | real/ausente | (Corretivas + lacunas S02) / total |
| rework_conservador | real/ausente | Mesmo quociente, somente projetos com evidência completa em todas as releases |
| releases_sem_evidencia_completa | inteiro | Comparação não `ok`, zero commits ou mensagem faltante |
| limite_inferior_conservador | real/ausente | Positivas com evidência completa / total |
| limite_superior_conservador | real/ausente | (Positivas completas + desconhecidas conservadoras) / total |
| cfr_b | real/ausente | Reprodução exata do CFR (b) da S02 |
| releases_avaliadas_cfr_b | inteiro | Denominador CFR, até 23/09/2026 inclusive |
| releases_censuradas_cfr_b | inteiro | Releases de 24/09 a 30/09, excluídas só do denominador CFR |
| releases_falharam_cfr_b | inteiro/ausente | Releases anteriores seguidas de corretiva em até sete dias |

Os quatro limites são de identificação, não intervalos de confiança. A versão
conservadora não corrige erros de classificação e não altera o dataset congelado.

## `rq08_releases.csv`

Uma linha por release principal. `tag_name` é texto; `published_at` é o instante de
publicação com fuso. `status_comparacao` é `ok`, `sem_anterior` ou `erro_404`.
`commits` e `mensagens_ausentes` são contagens inteiras. Os booleanos
`criterio_patch`, `criterio_texto` e `corretiva_heuristica` expõem a v3 inalterada.
`lacuna_cfr_b` registra a insuficiência pela regra S02. A classificação principal
usa `corretiva_heuristica` quando essa lacuna é falsa.

`evidencia_rework_suficiente` é booleano para a sensibilidade de evidência completa;
`motivo_ausencia` identifica `sem_anterior`, `erro_404`, `sem_commits` ou
`mensagem_ausente` (vazio se suficiente). `corretiva` é booleano/ausente e contém a
classificação **conservadora**, não uma nova heurística ou um rótulo humano.

## Demais CSVs

- `rq08_resumo.csv`: uma linha por indicador principal, CFR e sensibilidade;
  `metrica`, `n_total`, `n_ausentes`, `n`, `mediana`, `q1`, `q3`, `iqr`, `minimo`,
  `maximo`. Quartis lineares; `iqr = q3 - q1`; igual peso por projeto.
- `rq08_comparacao.csv`: projetos com ambos os indicadores; `full_name`,
  `rework_rate`, `cfr_b`, `diferenca_rework_menos_cfr_b` (diferença de proporções;
  multiplicar por 100 para pontos percentuais).
- `rq08_cobertura.csv`: uma linha para toda a amostra. `repositorios`,
  `releases_total`, `corretivas_heuristica`, `releases_sem_evidencia`,
  `releases_sem_evidencia_completa` e `repositorios_pareados` são contagens.
  `rework_agregado`, `limite_inferior_agregado`, `limite_superior_agregado` usam a
  regra S02; os limites conservadores usam apenas positivas completas e todas as
  desconhecidas conservadoras. O agregado é ausente se houver lacunas S02.

`manifesto.json` registra hashes SHA-256 e versões, não avaliações humanas.
`numeros_c.tex` e `rq08_tabela.tex` são gerados dos CSVs; não editar à mão.
