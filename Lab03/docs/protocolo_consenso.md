# Protocolo de consenso da amostra-ouro (S02)

1. **Pré-condição:** os três arquivos `rotulos_A/B/C.xlsx` estão commitados e foram preenchidos de forma independente.
2. **Concordância:** `python -m validacao.concordancia` calcula o kappa de Fleiss de cada dimensão (tipo do projeto, releases são entregas reais, release corretiva).
3. **Rótulo de consenso (desempate):**
   - 3 votos iguais: rótulo unânime;
   - 2 votos iguais: **maioria simples**;
   - 3 votos diferentes (1-1-1): decidido em reunião dos três.
4. **Casos 1-1-1:** a reunião lê `data/amostra_ouro/casos_divergentes.csv` (linhas com `desempate = reuniao`) e o grupo registra a decisão em `data/amostra_ouro/decisoes_reuniao.csv`, com as colunas `dimensao,chave,rotulo`. A chave de `releases_sao_entregas` e `tipo_projeto` é o `full_name`; a de `corretiva` é `full_name|release_id`.
5. **Fechamento:** rodar o comando de novo gera `consenso_repos.csv` e `consenso_releases.csv`. O comando só termina sem aviso quando não há caso 1-1-1 pendente.
6. **Registro:** os kappas entram no artigo (`docs/artigo/tabelas/kappa.tex`). Kappa baixo indica critério ambíguo e é discutido como achado, não corrigido.