# RQ3 — Estrutura do código

Fonte: trials preservados; comparação exploratória em três participantes.

| Métrica | Tratamento | n | Mediana | Q1 | Q3 | IQR |
|---|---|---:|---:|---:|---:|---:|
| Complexidade ciclomática média | ia | 6 | 15.000 | 8.750 | 16.750 | 8.000 |
| Duplicação intrarquivo | ia | 6 | 0.000 | 0.000 | 19.567 | 19.567 |
| Tamanho do código (SLOC) | ia | 6 | 36.000 | 23.000 | 43.750 | 20.750 |
| Índice de manutenibilidade | ia | 6 | 61.660 | 60.203 | 69.778 | 9.575 |
| Complexidade ciclomática média | manual | 6 | 8.000 | 7.000 | 14.250 | 7.250 |
| Duplicação intrarquivo | manual | 6 | 0.000 | 0.000 | 0.000 | 0.000 |
| Tamanho do código (SLOC) | manual | 6 | 19.500 | 18.250 | 35.000 | 16.750 |
| Índice de manutenibilidade | manual | 6 | 58.365 | 48.883 | 60.580 | 11.697 |

## Inferência pareada

Um par por participante, usando a mediana dos dois trials de cada condição. Diferença IA − Manual. Wilcoxon bilateral exato; diferenças zero removidas, empates com postos médios. Holm em uma família de duas hipóteses, alfa 0,05.

- Complexidade ciclomática média: W=3.000; pares efetivos=3; p=1.000; p de Holm=1.000; diferença pareada mediana=-0.500.
- Duplicação intrarquivo: W=0.000; pares efetivos=2; p=0.500; p de Holm=1.000; diferença pareada mediana=13.045.

Não há rejeição das hipóteses nulas no nível adotado quando os valores ajustados são maiores que 0,05. Isso não demonstra equivalência nem ausência de efeito. Com três pares, a inferência tem poder muito baixo. Se todas as diferenças são zero, o teste fica indisponível.

## Interpretação e LOC

A mediana global por tratamento e a mediana das diferenças individuais respondem a perguntas distintas. Comparar os katas e os tamanhos evita atribuir automaticamente à IA diferenças de dificuldade ou verbosidade. O gráfico de LOC é descritivo, não uma regressão nem evidência de controle causal.

A duplicação mede blocos literais de pelo menos três linhas significativas normalizadas dentro de cada arquivo. Não mede similaridade entre participantes e não é fornecida pelo Radon. O índice de manutenibilidade é complementar, não uma medida absoluta de qualidade.

## Sensibilidade e auditoria

sensitivity.csv repete os resumos excluindo cada participante por vez. Os testes desses cenários estão no JSON. Nenhuma exclusão modifica o conjunto principal. Valores além de 1,5 IQR são apenas sinalizados em outliers.csv e permanecem na análise.

Auditoria: 12/12 soluções com métricas reproduzidas a partir dos commits.

## Ressalvas

- Somente três participantes; pareamento controla participante, mas não a dificuldade dos diferentes katas.
- README registra início dos trials sem a baseline congelada prevista.
- As confirmações individuais de ambiente não estão todas documentadas.
- diogo/kata02: issue_number=0 no CSV original.
- diogo/kata03: issue_number=0 no CSV original.
- diogo/kata04: issue_number=0 no CSV original.
- diogo/kata01: issue_number=0 no CSV original.

## Referências

- Radon: https://radon.readthedocs.io/en/latest/intro.html
- Wilcoxon: https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.wilcoxon.html
