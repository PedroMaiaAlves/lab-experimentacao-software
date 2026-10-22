# Sprint 3 — entrega da parte A

## Execução

Dentro de `Lab03/`, com as dependências de `requirements.txt` instaladas:

```bash
python -m analises.sprint3_a
python -m analises.notebooks_a
```

Não é preciso token, cache de coleta nem restaurar o ZIP. O primeiro comando lê
`data/dataset.csv`, `data/amostra_final.csv`, seus manifestos e `data/fontes_s02.zip`,
conferindo os hashes de cada fonte. Recalcula os 7.771 episódios de recuperação a partir
dos runs e os 291.792 pares release/commit do lead time; ambos precisam reproduzir o
dataset em todos os 300 projetos, senão o comando para. A saída precisa ficar fora de
`data/`, com uma exceção deliberada: `data/classificacao_C1.csv`, entrada de C1 para a RQ07
(`--classificacao` muda o destino).

O segundo comando executa os dois notebooks em kernels novos e confere os CSVs
publicados; `--atualizar` grava as saídas em `notebooks/`. Os notebooks não guardam
horário de execução, então só mudam quando o resultado muda.

## O que foi entregue

| Item | Artefatos |
|---|---|
| S03-A1 | `analises/rq01_04.py`, `notebooks/rq01_04_s03_a.ipynb`; mediana e IQR de todas as variantes, comparações pareadas (Wilcoxon e Holm para H2/H3), censura e figura |
| S03-A2 | `analises/classificacao_c1.py`, `notebooks/classificacao_c1_s03_a.ipynb`, `data/classificacao_C1.csv`; categoria por métrica e geral, distribuição e ausências |
| S03-A3 | `docs/artigo/resultados_a.tex` e `docs/artigo/discussao.tex`; ponderação do lead time que explica a divergência (a) × (b) |

CSVs, figuras PNG/PDF, tabelas LaTeX, macros dos números do texto (`numeros_a.tex`) e
manifesto ficam em `results/s03_a/`. As colunas estão no [dicionário da parte A](dicionario_s03_a.md).
Todo número citado nas seções da parte A vem dessas macros, não de digitação manual.

## Resultados

| RQ | Resultado principal | Hipótese |
|---|---|---|
| RQ01 | Mediana de 0,326 release/semana (0,153–0,825); 3 projetos com 7 ou mais | H1 sustentada |
| RQ02 | (a) 196,7 h e (b) 178,3 h; (a) maior em 191/300, razão mediana 1,49 | H2 parcial |
| RQ03 | CFR (a) 0,055 e CFR (b) 0,175; (b) maior em 186/289 | H3 não sustentada (inversa) |
| RQ04 | 3,20 h por projeto; P90 dos episódios 73,4 h; 1,1% censurados | H4 parcial |
| C1 | Geral: 17 Elite, 122 High, 110 Medium, 29 Low, 22 sem categoria | — |

A divergência pequena entre os lead times tem explicação medida: dentro de cada projeto,
releases com mais commits têm o commit mais antigo mais distante (Spearman mediano 0,75,
positivo em 98,3% dos 296 projetos avaliáveis), o que aproxima (b) de (a).

## Decisões

- Unidade de análise: o projeto. Os episódios só aparecem agregados na RQ04.
- Ausências: os 11 CFR (b) e os 22 tempos de recuperação ausentes não viram zero.
- Censura: limite de pior caso (censurados mais longos que todos os concluídos), em vez de
  imputar durações.
- C1 exige as quatro métricas para a categoria geral, como em `metricas/classificacao.py`;
  a regra com três métricas é registrada só como sensibilidade.

## Pendências registradas originalmente (superadas na integração local de 21/10)

- **H7**: a linha da RQ07 na tabela de hipóteses está como pendente até a sensibilidade
  C1 × C2 × C3 de C. `classificacao_c1.classificar(df, combinacao)` já aceita C2 e C3.
- **Parte B**: a discussão cita números de `results/s03_b/` (RQ05 e RQ06). Na integração,
  `\input{resultados_b}` deve entrar entre `resultados_a` e `discussao` em `artigo.tex`.
- **Tamanho**: com a parte A, o artigo compilado tem 12 páginas antes da parte B; o limite
  final é 10. O resumo ainda não menciona resultados. Ambos ficam para a revisão final.

Atualização: RQ07 e bônus foram concluídos em C; os commits de B foram integrados
localmente preservando autoria. O artigo consolidado usa `*_final.tex`, atualiza
os resumos e tem 9 páginas, sem alterar fonte/margens SBC. As análises e os textos
extensos de A continuam disponíveis. Veja `entrega_s03_integrada.md`; publicação
na main e replicação cruzada não são comprovadas por essa integração local.
