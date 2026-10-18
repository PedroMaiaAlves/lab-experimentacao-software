# Dicionário — análises da Sprint 3, parte A

Entradas: `data/dataset.csv`, `data/amostra_final.csv`, seus manifestos e
`data/fontes_s02.zip`, todos conferidos por hash. Uma observação por projeto,
exceto em `rq04_episodios.csv`. Ausência numérica é célula vazia, nunca zero.
Identidade: `full_name` = owner/repo. Taxas são proporções de 0 a 1, tempos em
horas e frequências em entregas por semana, na janela inclusiva de 01/10/2025 a
30/09/2026. Quartis usam interpolação linear; IQR = Q3 − Q1.

### `rq01_04_descritivas.csv`

| Coluna | Tipo | Unidade / definição |
|---|---|---|
| `rq` | texto | RQ01 a RQ04 |
| `metrica` | texto | Coluna do dataset; `tempo_recuperacao_episodio_horas` agrega os episódios concluídos |
| `rotulo` | texto | Nome da métrica e da variante usado nas tabelas |
| `unidade` | texto | releases/semana, tags/semana, horas ou proporção |
| `unidade_analise` | texto | repositorio (um valor por projeto) ou episodio |
| `n_total` | inteiro | Projetos da amostra; para episódios, concluídos + censurados |
| `n_ausentes` | inteiro | Projetos sem valor; para episódios, os censurados, que não têm duração |
| `n` | inteiro | Valores observados = n_total − n_ausentes |
| `mediana` | real/vazio | Mediana dos valores observados |
| `q1` | real/vazio | Primeiro quartil |
| `q3` | real/vazio | Terceiro quartil |
| `iqr` | real/vazio | q3 − q1 |
| `minimo` | real/vazio | Menor valor observado |
| `maximo` | real/vazio | Maior valor observado |

### `rq01_04_pareadas.csv`

| Coluna | Tipo | Unidade / definição |
|---|---|---|
| `rq` | texto | RQ da variante comparada |
| `hipotese` | texto/vazio | H2 ou H3 quando a comparação testa uma hipótese; vazio nas descritivas |
| `x` | texto | Variante do minuendo |
| `y` | texto | Variante do subtraendo |
| `n` | inteiro | Projetos com x e y observados |
| `n_ausentes` | inteiro | Projetos sem x ou sem y |
| `n_x_maior` | inteiro | Projetos com x > y |
| `n_iguais` | inteiro | Projetos com x = y |
| `n_x_menor` | inteiro | Projetos com x < y |
| `mediana_diferenca` | real | Mediana de x − y, na unidade da métrica |
| `q1_diferenca` | real | Primeiro quartil de x − y |
| `q3_diferenca` | real | Terceiro quartil de x − y |
| `mediana_razao` | real/vazio | Mediana de x / y; vazio se algum y for zero |
| `teste` | texto/vazio | wilcoxon_pareado nas hipóteses; vazio nas descritivas |
| `estatistica` | real/vazio | Estatística W do Wilcoxon (menor soma de postos), sem diferenças nulas |
| `p` | real/vazio | P-valor bilateral do Wilcoxon |
| `efeito_rank_biserial` | real/vazio | (W+ − W−)/(W+ + W−), de −1 a 1; positivo quando x tende a ser maior |
| `p_holm` | real/vazio | P-valor ajustado por Holm na família das comparações testadas |
| `p_holm_familia_n` | inteiro | Tamanho da família de Holm; 2 (H2 e H3) |

### `rq04_censura.csv`

| Coluna | Tipo | Unidade / definição |
|---|---|---|
| `indicador` | texto | Nome do indicador de censura ou de cauda |
| `valor` | real | Contagem, proporção de 0 a 1 ou horas, conforme o indicador |
| `descricao` | texto | Fórmula ou significado do indicador |

Os indicadores `mediana_*_pior_caso_horas` supõem que cada episódio censurado
dure mais que todos os concluídos (do mesmo projeto, na versão por projeto). É um
limite superior simples para o efeito da censura sobre a mediana, não uma estimativa.

### `rq04_episodios.csv`

| Coluna | Tipo | Unidade / definição |
|---|---|---|
| `full_name` | texto | Projeto do episódio |
| `ordem` | inteiro | Posição do episódio na saída de `metricas.recuperacao`, por projeto |
| `horas` | real | Do início da primeira falha após um sucesso ao término do sucesso seguinte |
