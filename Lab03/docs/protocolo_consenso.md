# Protocolo de consenso da amostra-ouro (S02)

Para a população definitiva, use `data/amostra_ouro_s02/`, preparada a partir de
`data/amostra_final.csv`. O material em `data/amostra_ouro/` é legado do piloto.
O fechamento integrado exige a proveniência dos três avaliadores e verifica a
correspondência exata dos itens; veja `fechamento_s02.md`. Se houver três execuções
de IA separadas e cegas, a origem é declarada e não equivale a três avaliações
humanas. Uma análise única copiada três vezes não satisfaz independência.

1. **Pré-condição:** os três arquivos `rotulos_A/B/C.xlsx` estão commitados e foram preenchidos de forma independente.
2. **Concordância:** `python -m validacao.concordancia` calcula o kappa de Fleiss de cada dimensão (tipo do projeto, releases são entregas reais, release corretiva).
3. **Rótulo de consenso (desempate):**
   - 3 votos iguais: rótulo unânime;
   - 2 votos iguais: **maioria simples**;
   - 3 votos diferentes (1-1-1): decidido em reunião dos três.
4. **Casos 1-1-1:** a reunião lê `data/amostra_ouro/casos_divergentes.csv` (linhas com `desempate = reuniao`) e o grupo registra a decisão em `data/amostra_ouro/decisoes_reuniao.csv`, com as colunas `dimensao,chave,rotulo`. A chave de `releases_sao_entregas` e `tipo_projeto` é o `full_name`; a de `corretiva` é `full_name|release_id`.
5. **Fechamento:** rodar o comando de novo gera `consenso_repos.csv` e `consenso_releases.csv`. O comando só termina sem aviso quando não há caso 1-1-1 pendente.
6. **Registro:** os kappas entram no artigo (`docs/artigo/tabelas/kappa.tex`). Kappa baixo indica critério ambíguo e é discutido como achado, não corrigido.

O fechamento definitivo gera `kappa_s02.tex`, para não confundir os resultados
com os do piloto. `--tipo-desempate adjudicacao_IA` permite registrar uma
adjudicação efetiva de IA em `decisoes_adjudicacao.csv`, sem inventar uma reunião.
O modo padrão mantém as decisões efetivamente tomadas em reunião do grupo.
