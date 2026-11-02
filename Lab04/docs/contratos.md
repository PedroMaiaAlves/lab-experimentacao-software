# Integração da S01 — contratos de Pedro, Diogo e Lorran

## Responsabilidades

| Responsável | Código que mantém |
| --- | --- |
| Pedro | `experimento/dados.py`, `coleta.py`, `simulacao.py`, `validacao.py` e os três comandos da raiz de Lab04 |
| Diogo | Novo `experimento/analise.py`, novo `experimento/g2.py` e testes desses módulos |
| Lorran | Novo `app.py`, novo `experimento/g1.py`, integração e verificações do Streamlit |

As dependências extras devem ser adicionadas ao requirements e ao lock na
integração. Preservar arquivos de dados reais e cenário prévio; correções de
interpretação posteriores devem ir em outro texto, com justificativa.

## Entrada compartilhada

`experimento.dados.ler_pares(path)` retorna um `numpy.ndarray` de formato `(n, 2)`:

1. coluna 0: `sem_cache_s`;
2. coluna 1: `com_cache_s`.

Cada linha permanece pareada. Tempos inválidos e IDs ausentes/duplicados geram
erro; o carregador não descarta observações silenciosamente. O CSV real tem
também `ordem`, `tentativa` e horários; o simulado contém apenas ID e tempos.

Os dados oficiais estão em `data/real/pares_reais.csv` e
`data/simulado/pares_simulados.csv`. Não usar `aquecimento.csv` na análise.
O módulo `experimento.dados.ROOT` resolve a raiz de Lab04 sem depender do diretório
de trabalho; usar esse caminho no dashboard.

## API entregue por Pedro

```python
from experimento.dados import ROOT, ler_json, ler_pares
from experimento.simulacao import calibrar, gerar_pares

reais = ler_pares(ROOT / "data/real/pares_reais.csv")
parametros = ler_json(ROOT / "data/simulado/parametros.json")
simulados = gerar_pares(parametros, n=30, semente=42)
# Para a S02: delta_log=0 configura H0, sem modificar parametros.
```

- `calibrar(pares) -> dict`: médias e covariância dos log-tempos, usando ddof=1.
- `gerar_pares(parametros, n=30, semente=42, delta_log=None) -> ndarray`:
  None mantém o efeito observado. Valor numérico define a média populacional de
  `log(sem/com)`, preservando o ponto médio das médias e a covariância.
- As funções não escrevem arquivos nem coletam dados. A CLI `simular.py` faz a
  validação da origem e exporta os artefatos.
- O gerador usa NumPy 2.2.6 e semente local; não depende de estado aleatório global.
- O teste t deve operar em `log(pares[:, 0])` e `log(pares[:, 1])`. O Wilcoxon
  recebe a diferença desses logs, para manter exatamente o pareamento definido.

## API a implementar por Diogo

`analisar_pares(pares, alpha=0.05) -> dict`, em `experimento/analise.py`.

Retornar chaves `t_pareado` e `wilcoxon`, cada uma com `estatistica`, `p_valor`,
`metodo`, `n_pares`, `alpha`, `alternativa`, `decisao` e `interpretacao`.
Uma estatística indisponível deve ter motivo explícito, nunca zero inventado.
Usar alternativa `two-sided` e decisão `p < alpha` quando o resultado for válido.
Acrescentar medidas de efeito e a tabela real será trabalho posterior; não é
necessário antecipar a análise final dos dados reais em D1.

`figura_g2(pares, resultados) -> plotly.graph_objects.Figure`, em `experimento/g2.py`.

- Um painel t com distribuição Student, n−1 graus de liberdade, duas caudas de
  rejeição e área mais extrema que a estatística observada.
- Um painel Wilcoxon para a estatística bicaudal `W=min(W+, W-)`, com massas
  discretas sob H0 e destaque da probabilidade tão ou mais extrema que W observado.
- Usar cálculo exato no exemplo contínuo sem empates/zeros; conferir que a
  probabilidade desenhada coincide com o p-valor retornado.
- Explicitar o método alternativo e suas limitações em casos com empates/zeros;
  não apresentar uma curva contínua como distribuição exata do Wilcoxon.
- Se o exemplo produzir caudas muito pequenas, usar ampliação ou painel auxiliar
  e anotação numérica; não trocar de semente para escolher significância.

## API a implementar por Lorran

`figura_g1(reais, simulados) -> plotly.graph_objects.Figure`, em `experimento/g1.py`.

Histogramas reais ao lado dos simulados, para cada condição, em segundos; manter
os mesmos limites de bins dentro de cada comparação. Acrescentar descrição da
forma observada e dos limites do ajuste, sem declarar normalidade não verificada.

O `app.py` carregará as amostras, usará as APIs e abrirá o dashboard com:

```powershell
.\Lab04\.venv\Scripts\python.exe -m streamlit run Lab04/app.py
```

Não importar nem chamar a coleta no aplicativo. Para recalcular a amostra na
abertura, usar `gerar_pares` com os parâmetros preservados e semente 42.
G1 e G2 devem estar dentro do Streamlit, e não apenas em arquivos externos.

Seções, nesta ordem:

1. Cenário: pergunta, hipóteses por teste, fonte e 30 pares / 60 observações.
2. Os dados: G1 e justificativa dos parâmetros.
3. Como os testes funcionam: resultados simulados, G2 e interpretação.
4. Erro tipo I: sinalizar entrega na S02, sem números provisórios.
5. Poder: sinalizar entrega na S02, sem números provisórios.
6. Dados reais: sinalizar tabela prevista para entrega final.
7. Conclusão: mostrar expectativa prévia; comparação e recomendação ainda pendentes.

Cada gráfico precisa de 2–4 frases, título, legenda e eixos com unidades
(estatísticas de teste são adimensionais). Cores por teste: t `#2563eb`,
Wilcoxon `#ea580c`. G1 distingue dados reais e simulados, não os testes.
No topo: links do dashboard local, repositório e Projects; enquanto o último
estiver nulo, mostrar "Projects: link ainda não informado", sem inventar URL.

## Critério de integração

Diogo pode validar seus módulos com a amostra simulada entregue por Pedro.
Lorran integra somente após conferir o contrato e a saída de `validar.py`.
O aceite final requer G1/G2 visíveis, p-valores consistentes com G2, execução pelo
README e ausência de coleta involuntária. Dados reais, simulados e exemplos de
teste devem ser identificados claramente em toda a apresentação.
