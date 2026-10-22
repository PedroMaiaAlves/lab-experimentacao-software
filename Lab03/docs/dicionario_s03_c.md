# Dicionário — Sprint 3, parte C (RQ07/RQ08)

Entradas congeladas da S02; uma observação por projeto, exceto o arquivo por release e matrizes/estatísticas agregadas. Ausências numéricas são vazias, nunca zero. Taxas são proporções 0–1, tempos em horas e frequência em entregas/semana. Limites conservadores são de identificação, não intervalos de confiança. Veja [métodos e reprodução](entrega_s03_c.md).

C1 usa principais/a/CI; C2, pré-releases/b/releases; C3, tags/b/releases. Lead time e CFR de releases continuam sobre principais nas três. Classificação exige quatro métricas; geral_minimo_3 é apenas sensibilidade. A família ampliada de Holm (6/24 testes) é separada da original de B (2/18).

### `metricas_combinacoes.csv`

| Coluna | Tipo | Unidade / definição |
|---|---|---|
| `full_name` | texto/ausente | Identificador GitHub owner/repo; unidade de análise. |
| `combinacao` | texto/ausente | C1 (principais/a/CI), C2 (com pré-releases/b/releases), C3 (tags/b/releases). Recuperação de CI nas três. |
| `deployment_frequency` | real/ausente | Entregas por semana segundo a fonte da combinação; janela inclusiva. |
| `lead_time` | real/ausente | Horas; variante (a) em C1, (b) em C2/C3, sempre sobre releases principais. |
| `cfr` | real/ausente | Proporção 0–1; CFR de CI (a) em C1, CFR de releases (b) em C2/C3. |
| `tempo_recuperacao` | real/ausente | Horas; mediana de episódios de CI concluídos, igual nas três combinações. |

### `rq07_classificacoes.csv`

| Coluna | Tipo | Unidade / definição |
|---|---|---|
| `full_name` | texto/ausente | Identificador GitHub owner/repo; unidade de análise. |
| `metricas_disponiveis` | inteiro | Contagem de métricas não ausentes, de zero a quatro. |
| `metricas_ausentes` | texto/ausente | Nomes das métricas ausentes, separados por ponto e vírgula; vazio se nenhuma. |
| `mediana_notas` | real/ausente | Mediana das quatro notas (Low=1, Medium=2, High=3, Elite=4), antes do arredondamento; ausente se faltar métrica. |
| `categoria_deployment_frequency` | texto/ausente | Low, Medium, High ou Elite, pelos cortes fixos da frequência. |
| `categoria_lead_time` | texto/ausente | Categoria pelos cortes fixos do lead time; ausente sem medida. |
| `categoria_cfr` | texto/ausente | Categoria pelos cortes fixos do CFR; ausente sem medida. |
| `categoria_tempo_recuperacao` | texto/ausente | Categoria pelos cortes fixos de recuperação; ausente sem episódio concluído. |
| `categoria_geral` | texto/ausente | Mediana das quatro notas arredondada para baixo; exige quatro métricas. |
| `categoria_geral_minimo_3` | texto/ausente | Sensibilidade que permite pelo menos três métricas; não substitui a definição principal. |
| `combinacao` | texto/ausente | C1 (principais/a/CI), C2 (com pré-releases/b/releases), C3 (tags/b/releases). Recuperação de CI nas três. |

### `rq07_concordancia.csv`

| Coluna | Tipo | Unidade / definição |
|---|---|---|
| `combinacao_a` | texto/ausente | Combinação de origem da comparação. |
| `combinacao_b` | texto/ausente | Combinação de destino da comparação. |
| `populacao` | texto/ausente | pares_disponiveis ou comuns_tres (interseção dos projetos classificados nas três). |
| `n_total` | inteiro | Projetos no universo antes de excluir ausências. |
| `n` | inteiro | Observações válidas: projetos, pares ou contagem da célula/grupo, conforme a tabela. |
| `n_excluidos` | inteiro | n_total menos n; ausentes não são mudanças de categoria. |
| `mudou` | inteiro | Pares válidos com categorias gerais diferentes. |
| `proporcao_mudou` | real/ausente | mudou / n, de 0 a 1; ausente sem pares. |
| `subiu` | inteiro | Pares em que a nota da combinação B é maior que a de A. |
| `desceu` | inteiro | Pares em que a nota de B é menor que a de A. |
| `kappa_linear` | real/ausente | Cohen ponderado linear, categorias em ordem Low<Medium<High<Elite, de −1 a 1; ausente se indefinido. |
| `status_kappa` | texto/ausente | ok, sem_pares ou denominador_zero; este último ocorre com uma única categoria compartilhada por todos. |
| `ganhou_classificacao` | inteiro | Projetos sem categoria em A e com categoria em B, na população total. |
| `perdeu_classificacao` | inteiro | Projetos com categoria em A e sem categoria em B, na população total. |
| `ambos_ausentes` | inteiro | Projetos sem categoria nas duas combinações, na população total. |

### `rq07_distribuicao.csv`

| Coluna | Tipo | Unidade / definição |
|---|---|---|
| `dimensao` | texto/ausente | Métrica, geral ou geral_minimo_3 da distribuição. |
| `categoria` | texto/ausente | Low, Medium, High, Elite ou sem_categoria; somente na distribuição, não no kappa. |
| `n` | inteiro | Observações válidas: projetos, pares ou contagem da célula/grupo, conforme a tabela. |
| `n_total` | inteiro | Projetos no universo antes de excluir ausências. |
| `n_classificados` | inteiro | Projetos com categoria disponível na dimensão e combinação. |
| `proporcao_total` | real/ausente | Contagem da categoria dividida por n_total. |
| `proporcao_classificados` | real/ausente | Contagem dividida por n_classificados; ausente para sem_categoria. |
| `combinacao` | texto/ausente | C1 (principais/a/CI), C2 (com pré-releases/b/releases), C3 (tags/b/releases). Recuperação de CI nas três. |

### `rq07_matrizes.csv`

| Coluna | Tipo | Unidade / definição |
|---|---|---|
| `combinacao_a` | texto/ausente | Combinação de origem da comparação. |
| `combinacao_b` | texto/ausente | Combinação de destino da comparação. |
| `categoria_a` | texto/ausente | Categoria de origem da célula da matriz (linhas, Low a Elite). |
| `categoria_b` | texto/ausente | Categoria de destino da célula da matriz (colunas, Low a Elite). |
| `n` | inteiro | Observações válidas: projetos, pares ou contagem da célula/grupo, conforme a tabela. |

### `rq07_resumo_metricas.csv`

| Coluna | Tipo | Unidade / definição |
|---|---|---|
| `combinacao` | texto/ausente | C1 (principais/a/CI), C2 (com pré-releases/b/releases), C3 (tags/b/releases). Recuperação de CI nas três. |
| `metrica` | texto/ausente | Indicador resumido ou testado; frequências em entregas/semana, tempos em horas e taxas em proporção. |
| `coluna_origem` | texto/ausente | Coluna do dataset congelado usada na combinação; não representa nova coleta. |
| `n_total` | inteiro | Projetos no universo antes de excluir ausências. |
| `n_ausentes` | inteiro | Observações sem valor antes da estatística descritiva. |
| `n` | inteiro | Observações válidas: projetos, pares ou contagem da célula/grupo, conforme a tabela. |
| `mediana` | real/ausente | Mediana entre projetos disponíveis, na unidade da métrica. |
| `q1` | real/ausente | Primeiro quartil, interpolação linear, na unidade da métrica. |
| `q3` | real/ausente | Terceiro quartil, interpolação linear, na unidade da métrica. |
| `iqr` | real/ausente | q3 − q1, na unidade da métrica. |

### `rq07_robustez_rq05.csv`

| Coluna | Tipo | Unidade / definição |
|---|---|---|
| `variante` | texto/ausente | Proxy de falha cfr_a ou cfr_b usado na correlação. |
| `n_total` | inteiro | Projetos no universo antes de excluir ausências. |
| `n` | inteiro | Observações válidas: projetos, pares ou contagem da célula/grupo, conforme a tabela. |
| `n_excluidos` | inteiro | n_total menos n; ausentes não são mudanças de categoria. |
| `rho` | real/ausente | Spearman bilateral, de −1 a 1, incluindo taxas iguais a zero. |
| `p_spearman` | real/ausente | P-valor assintótico, preservado para conferência; a inferência principal usa permutação. |
| `p_permutacao` | real/ausente | P-valor bilateral por 9.999 permutações de pareamentos, semente 42; nunca arredondado para zero. |
| `ic95_inferior` | real/ausente | Limite inferior do IC95% BCa pareado de rho. |
| `ic95_superior` | real/ausente | Limite superior do IC95% BCa pareado de rho. |
| `status` | texto/ausente | ok ou motivo de teste não estimável: dados_constantes, amostra/grupos_insuficientes ou grupo_com_menos_de_5. |
| `status_ic` | texto/ausente | ok, nao_estimavel ou distribuicao_degenerada no bootstrap. |
| `rho_loo_min` | real/ausente | Menor rho estimável ao retirar um projeto por vez. |
| `rho_loo_max` | real/ausente | Maior rho estimável ao retirar um projeto por vez. |
| `delta_loo_max` | real/ausente | Maior diferença absoluta entre rho leave-one-out e rho completo. |
| `repo_maior_influencia` | texto/ausente | Projeto cuja retirada mais altera rho; primeiro em ordem em caso de empate. |
| `mudancas_sinal` | inteiro | Retiradas que mudam o sinal de rho; zero é sinal distinto. |
| `loo_indefinidos` | inteiro | Retiradas com rho não estimável. |
| `p_permutacao_holm` | real/ausente | Ajuste original de dois proxies para esta fonte da frequência; não é o ajuste ampliado de robustez. |
| `p_permutacao_holm_familia_n` | inteiro | Número de testes/proxies estimáveis na família original, normalmente dois. |
| `fonte_frequencia` | texto/ausente | Coluna do dataset usada como frequência nesta análise. |
| `combinacao_frequencia` | texto/ausente | C1/C2/C3 identifica só a fonte de frequência; as duas variantes de CFR são testadas em cada fonte. |
| `p_holm_sensibilidade` | real/ausente | P-valor ajustado por Holm: seis correlações em RQ05 ou 24 testes únicos em RQ06. |
| `p_holm_sensibilidade_familia_n` | inteiro | Número de testes estimáveis na família ampliada; não substitui a família original de B. |

### `rq07_robustez_rq06.csv`

| Coluna | Tipo | Unidade / definição |
|---|---|---|
| `fator` | texto/ausente | tipo_projeto, contribuidores_quartil ou linguagem_grupo; grupos fixados antes das exclusões. |
| `metrica` | texto/ausente | Indicador resumido ou testado; frequências em entregas/semana, tempos em horas e taxas em proporção. |
| `n_total` | inteiro | Projetos no universo antes de excluir ausências. |
| `n` | inteiro | Observações válidas: projetos, pares ou contagem da célula/grupo, conforme a tabela. |
| `n_excluidos` | inteiro | n_total menos n; ausentes não são mudanças de categoria. |
| `grupos_n` | inteiro | Número de grupos do fator considerado. |
| `ordem_grupos` | texto/ausente | Categorias na ordem do teste; determina a orientação de Cliff delta se houver dois grupos. |
| `teste` | texto/ausente | Kruskal-Wallis (três ou mais grupos) ou Mann-Whitney bilateral (dois). |
| `estatistica` | real/ausente | H de Kruskal-Wallis ou U do primeiro grupo. |
| `p` | real/ausente | P-valor bruto do teste entre grupos. |
| `efeito` | real/ausente | epsilon_quadrado = H/(n−1) ou Cliff_delta = 2U/(n1*n2)−1, conforme tipo_efeito. |
| `tipo_efeito` | texto/ausente | epsilon_quadrado ou Cliff_delta. |
| `interpretacao_efeito` | texto/ausente | Sem cortes convencionados para epsilon; limites 0,147/0,33/0,474 para módulo de Cliff delta. |
| `status` | texto/ausente | ok ou motivo de teste não estimável: dados_constantes, amostra/grupos_insuficientes ou grupo_com_menos_de_5. |
| `p_holm_sensibilidade` | real/ausente | P-valor ajustado por Holm: seis correlações em RQ05 ou 24 testes únicos em RQ06. |
| `p_holm_sensibilidade_familia_n` | inteiro | Número de testes estimáveis na família ampliada; não substitui a família original de B. |

### `rq08_cobertura.csv`

| Coluna | Tipo | Unidade / definição |
|---|---|---|
| `repositorios` | inteiro | Quantidade total de projetos na análise. |
| `releases_total` | inteiro | Releases principais na janela, sem censura final para rework. |
| `corretivas_heuristica` | inteiro | Positivas conhecidas segundo a v3 e a disponibilidade da S02. |
| `releases_sem_evidencia` | inteiro | Lacunas da regra S02: 404 ou mensagem ausente sem classificação positiva. |
| `rework_agregado` | real/ausente | Corretivas conhecidas / total de releases, somente se não houver lacunas S02; não é mediana por projeto. |
| `limite_inferior_agregado` | real/ausente | Corretivas conhecidas / total, tratando lacunas S02 como negativas. |
| `limite_superior_agregado` | real/ausente | (Corretivas conhecidas + lacunas S02) / total. |
| `releases_sem_evidencia_completa` | inteiro | Comparação não ok, zero commits ou pelo menos uma mensagem incompleta. |
| `limite_inferior_conservador` | real/ausente | Positivas com evidência completa / total, desconhecidas conservadoras negativas. |
| `limite_superior_conservador` | real/ausente | (Positivas completas + desconhecidas conservadoras) / total. |
| `repositorios_pareados` | inteiro | Projetos com rework principal e CFR (b) disponíveis. |

### `rq08_comparacao.csv`

| Coluna | Tipo | Unidade / definição |
|---|---|---|
| `full_name` | texto/ausente | Identificador GitHub owner/repo; unidade de análise. |
| `rework_rate` | real/ausente | Corretivas / total de releases principais, disponibilidade herdada da S02; ausente se houver lacuna. |
| `cfr_b` | real/ausente | CFR (b) reproduzido exatamente do dataset congelado, inclusive suas ausências. |
| `diferenca_rework_menos_cfr_b` | real/ausente | rework_rate − cfr_b; multiplicar por 100 para pontos percentuais. |

### `rq08_releases.csv`

| Coluna | Tipo | Unidade / definição |
|---|---|---|
| `full_name` | texto/ausente | Identificador GitHub owner/repo; unidade de análise. |
| `release_id` | identificador | Identificador estável da release no GitHub; chave com full_name, sem interpretação aritmética. |
| `tag_name` | texto/ausente | Nome original da tag da release. |
| `published_at` | texto/ausente | Instante de publicação com fuso; filtro da janela inclusiva. |
| `status_comparacao` | texto/ausente | ok, sem_anterior ou erro_404 na fonte congelada. |
| `commits` | inteiro | Quantidade de commits da comparação, conferida contra a fonte. |
| `mensagens_ausentes` | inteiro | Quantidade de mensagens nulas ou vazias após remover espaços. |
| `criterio_patch` | booleano | Critério patch acionado pela v3; com texto ligado requer correção e ausência de funcionalidades. |
| `criterio_texto` | booleano | Critério textual acionado pelo balanço de correções/funcionalidades da v3. |
| `corretiva_heuristica` | booleano | Resultado bruto booleano da v3, sem modificar seus parâmetros. |
| `evidencia_rework_suficiente` | booleano | Evidência completa para a sensibilidade: comparação ok, commits presentes e mensagens completas. |
| `motivo_ausencia` | texto/ausente | sem_anterior, erro_404, sem_commits ou mensagem_ausente; vazio se evidência completa. |
| `corretiva` | booleano/ausente | Classificação conservadora: booleano ou ausente se evidência incompleta; não é rótulo humano. |
| `lacuna_cfr_b` | booleano | Insuficiência pela regra S02; a taxa principal usa corretiva_heuristica quando falso. |

### `rq08_repositorios.csv`

| Coluna | Tipo | Unidade / definição |
|---|---|---|
| `full_name` | texto/ausente | Identificador GitHub owner/repo; unidade de análise. |
| `releases_total` | inteiro | Releases principais na janela, sem censura final para rework. |
| `releases_corretivas` | inteiro | Positivas conhecidas da v3 no projeto, com a regra de disponibilidade S02. |
| `releases_sem_evidencia` | inteiro | Lacunas da regra S02: 404 ou mensagem ausente sem classificação positiva. |
| `rework_rate` | real/ausente | Corretivas / total de releases principais, disponibilidade herdada da S02; ausente se houver lacuna. |
| `rework_limite_inferior` | real/ausente | Corretivas / total do projeto, lacunas S02 negativas. |
| `rework_limite_superior` | real/ausente | (Corretivas + lacunas S02) / total do projeto. |
| `rework_conservador` | real/ausente | Taxa do projeto somente quando todas as releases têm evidência completa. |
| `releases_sem_evidencia_completa` | inteiro | Comparação não ok, zero commits ou pelo menos uma mensagem incompleta. |
| `limite_inferior_conservador` | real/ausente | Positivas com evidência completa / total, desconhecidas conservadoras negativas. |
| `limite_superior_conservador` | real/ausente | (Positivas completas + desconhecidas conservadoras) / total. |
| `cfr_b` | real/ausente | CFR (b) reproduzido exatamente do dataset congelado, inclusive suas ausências. |
| `releases_avaliadas_cfr_b` | inteiro | Denominador do CFR (b): releases até 23/09/2026, inclusive. |
| `releases_censuradas_cfr_b` | inteiro | Releases de 24 a 30/09/2026, excluídas só do denominador CFR. |
| `releases_falharam_cfr_b` | real/ausente | Releases anteriores seguidas de corretiva em até sete dias; ausente quando CFR indisponível. |

### `rq08_resumo.csv`

| Coluna | Tipo | Unidade / definição |
|---|---|---|
| `metrica` | texto/ausente | Indicador resumido ou testado; frequências em entregas/semana, tempos em horas e taxas em proporção. |
| `n_total` | inteiro | Projetos no universo antes de excluir ausências. |
| `n_ausentes` | inteiro | Observações sem valor antes da estatística descritiva. |
| `n` | inteiro | Observações válidas: projetos, pares ou contagem da célula/grupo, conforme a tabela. |
| `mediana` | real/ausente | Mediana entre projetos disponíveis, na unidade da métrica. |
| `q1` | real/ausente | Primeiro quartil, interpolação linear, na unidade da métrica. |
| `q3` | real/ausente | Terceiro quartil, interpolação linear, na unidade da métrica. |
| `iqr` | real/ausente | q3 − q1, na unidade da métrica. |
| `minimo` | inteiro | Menor valor observado, na unidade da métrica. |
| `maximo` | inteiro | Maior valor observado, na unidade da métrica. |
