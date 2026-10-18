# Dicionário — análises da Sprint 3, parte B

Entradas: dataset congelado e manifestos da S02. Uma observação por projeto.
Ausência numérica é célula vazia, nunca zero. Identidade: `full_name` = owner/repo.
Taxas são proporções 0–1, tempos em horas e frequência em releases/semana.
Quartis descritivos usam interpolação linear; IQR = Q3 − Q1.

### `rq05_correlacoes.csv`

| Coluna | Tipo | Unidade / definição |
|---|---|---|
| `variante` | texto | cfr_a ou cfr_b; cada uma correlacionada com deployment_frequency |
| `n_total` | inteiro | Projetos da população |
| `n` | inteiro | Pares completos, incluindo taxas zero |
| `n_excluidos` | inteiro | n_total − n |
| `rho` | real/vazio | Spearman bilateral, de −1 a 1 |
| `p_spearman` | real/vazio | P-valor assintótico retornado por scipy.stats.spearmanr |
| `p_permutacao` | real/vazio | P-valor bilateral por permutação dos pareamentos; correção de contagem do SciPy evita zero |
| `ic95_inferior` | real/vazio | Limite inferior do bootstrap BCa pareado de rho |
| `ic95_superior` | real/vazio | Limite superior do bootstrap BCa pareado de rho |
| `status` | texto | ok, amostra_insuficiente (n < 5) ou dados_constantes |
| `status_ic` | texto | ok, nao_estimavel ou distribuicao_degenerada |
| `rho_loo_min` | real/vazio | Menor rho definido ao retirar um projeto por vez |
| `rho_loo_max` | real/vazio | Maior rho definido ao retirar um projeto por vez |
| `delta_loo_max` | real/vazio | Maior diferença absoluta entre rho sem um projeto e rho completo |
| `repo_maior_influencia` | texto/vazio | Projeto que produz delta_loo_max; primeiro em ordem de nome em caso de empate |
| `mudancas_sinal` | inteiro | Retiradas com sinal diferente do rho completo; zero é um sinal distinto |
| `loo_indefinidos` | inteiro | Retiradas cujo rho ficou indefinido |
| `p_permutacao_holm` | real/vazio | P-valor por permutação ajustado na família das duas variantes |
| `p_permutacao_holm_familia_n` | inteiro | Quantidade de testes estimáveis ajustados; 2 na amostra atual |

### `rq05_influencia.csv`

| Coluna | Tipo | Unidade / definição |
|---|---|---|
| `variante` | texto | Proxy de CFR |
| `full_name` | texto | Projeto retirado somente nesta análise de influência |
| `rho_sem_repo` | real/vazio | Spearman nos demais projetos do conjunto de pares completos |
| `delta_rho` | real/vazio | rho_sem_repo − rho completo, com sinal |
| `mudou_sinal` | booleano | Indica mudança de sinal; interpretar apenas quando status=ok |
| `status` | texto | ok ou dados_constantes |

### `rq06_testes.csv`

| Coluna | Tipo | Unidade / definição |
|---|---|---|
| `fator` | texto | tipo_projeto, contribuidores_quartil ou linguagem_grupo |
| `metrica` | texto | Uma das seis colunas métricas do dataset |
| `n_total` | inteiro | Projetos da população |
| `n` | inteiro | Observações com fator e métrica disponíveis |
| `n_excluidos` | inteiro | n_total − n, sem contar duas vezes o mesmo projeto |
| `grupos_n` | inteiro | Grupos definidos antes das exclusões por métrica |
| `ordem_grupos` | texto | Grupos separados por barra; define o sinal de Cliff se houver dois grupos |
| `teste` | texto/vazio | Kruskal-Wallis ou Mann-Whitney; vazio se não estimável |
| `estatistica` | real/vazio | H corrigido por empates, ou U do primeiro grupo |
| `p` | real/vazio | P-valor original; Mann-Whitney bilateral assintótico com continuidade |
| `efeito` | real/vazio | H/(n−1) para Kruskal-Wallis; 2U/(n1·n2)−1 para Mann-Whitney |
| `tipo_efeito` | texto/vazio | epsilon_quadrado ou Cliff_delta |
| `interpretacao_efeito` | texto/vazio | Cliff: desprezível, pequeno, médio, grande nos cortes 0,147/0,33/0,474 de abs(delta); sem cortes para epsilon |
| `status` | texto | ok, grupos_insuficientes, grupo_com_menos_de_5 ou dados_constantes |
| `p_holm` | real/vazio | Ajuste conjunto de todos os testes estimáveis da família de 18 combinações |
| `p_holm_familia_n` | inteiro | Tamanho efetivamente ajustado; 18 na amostra atual |
| `significativo_holm` | booleano/vazio | p_holm < 0,05; vazio para teste não estimável |

### `rq06_descritivas.csv`

| Coluna | Tipo | Unidade / definição |
|---|---|---|
| `fator` | texto | Fator de agrupamento |
| `grupo` | texto | Categoria fixada antes das exclusões |
| `metrica` | texto | Coluna métrica analisada |
| `unidade` | texto | horas, proporção ou releases/semana |
| `n_total` | inteiro | Projetos do grupo, antes de excluir a métrica ausente |
| `n_ausentes` | inteiro | Projetos do grupo com métrica ausente |
| `n` | inteiro | Projetos com métrica observada |
| `mediana` | real/vazio | Percentil 50; unidade da métrica |
| `q1` | real/vazio | Percentil 25; unidade da métrica |
| `q3` | real/vazio | Percentil 75; unidade da métrica |
| `iqr` | real/vazio | q3 − q1; unidade da métrica |

### `rq06_grupos.csv`

| Coluna | Tipo | Unidade / definição |
|---|---|---|
| `full_name` | texto | Chave única do projeto |
| `tipo_projeto` | texto/vazio | Quatro categorias do dataset; 60 consensos e 240 revisões individuais |
| `contribuidores` | inteiro/vazio | Contagem original do dataset |
| `language` | texto/vazio | Linguagem original do GitHub |
| `linguagem_grupo` | texto/vazio | Linguagem original se n ≥ 10; Outras se n < 10; ausência preservada |
| `contribuidores_quartil` | texto/vazio | Q1–Q4, limites calculados nos valores disponíveis da população completa; limites repetidos removidos |

### `exclusoes.csv`

| Coluna | Tipo | Unidade / definição |
|---|---|---|
| `analise` | texto | RQ05 ou RQ06 |
| `fator` | texto/vazio | Fator na RQ06; vazio na RQ05 |
| `metrica` | texto | Métrica da análise afetada |
| `full_name` | texto | Projeto excluído somente daquela combinação |
| `campo` | texto | Campo ausente que motivou a exclusão |
| `motivo` | texto | evidencia_textual_insuficiente, sem_releases_avaliaveis, sem_episodios, somente_episodios_censurados ou valor_ausente |

Um projeto pode aparecer em várias análises e, se dois campos faltarem, em duas
linhas da mesma análise. Os denominadores dos testes contam projetos únicos.

### `ausencias.csv`

| Coluna | Tipo | Unidade / definição |
|---|---|---|
| `full_name` | texto | Projeto com valor ausente |
| `metrica` | texto | Métrica ausente; uma linha por projeto e métrica |
| `motivo` | texto | Mesmo vocabulário de exclusoes.csv |

### `cobertura.csv`

| Coluna | Tipo | Unidade / definição |
|---|---|---|
| `metrica` | texto | Coluna métrica do dataset |
| `unidade` | texto | Unidade original da métrica |
| `n_total` | inteiro | Projetos na população |
| `n_ausentes` | inteiro | Valores ausentes daquela métrica |
| `n` | inteiro | Valores observados |
| `mediana` | real/vazio | Percentil 50; unidade da métrica |
| `q1` | real/vazio | Percentil 25; unidade da métrica |
| `q3` | real/vazio | Percentil 75; unidade da métrica |
| `iqr` | real/vazio | q3 − q1; unidade da métrica |

## Outros artefatos

- `grupos_definicao.json`: limites dos quartis, regra dos empates, linguagens agrupadas e ordem dos tipos.
- `manifesto.json`: hashes das quatro entradas, janela, heurística, parâmetros, versões do ambiente, hashes dos módulos de análise e de cada saída.
- `rq05_dispersao.png/pdf`: mesmos pares usados em Spearman; CFR linear preserva zeros; frequência logarítmica na amostra atual.
- `rq06_efeitos.png/pdf`: todos os efeitos; asterisco corresponde a p_holm < 0,05, não a teste post-hoc.
- `rq05_tabela.tex`, `rq06_tabela.tex`, `rq06_significativos.tex`: tabelas derivadas dos CSVs; a última exibe somente as seis comparações significativas, identificadas como subconjunto de 18 no artigo.

Verificação automática:

```bash
python -m validacao.dicionario --dicionario docs/dicionario_s03_b.md --dados results/s03_b
```
