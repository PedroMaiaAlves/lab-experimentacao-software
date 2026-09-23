# Análise estatística de RQ1 e RQ2

Esta seção cobre somente tempo e taxa de sucesso dos testes. A fonte é
[`results/trials.csv`](../results/trials.csv), integrada em `main` no commit
`ae69e1bc3cc79627c17d1f9965a2cdca78ddf70c` (SHA-256 do CSV:
`f9a5dc4082ce86320370d6a5eae512d5ae256dfc7f72525d138d8f8e3a105947`).
O script [`tools/analyze_rq1_rq2.py`](../tools/analyze_rq1_rq2.py) reproduz os
cálculos sem dependências adicionais:

```powershell
.\Lab02\.venv\Scripts\python.exe -B Lab02/tools/analyze_rq1_rq2.py
```

## Método

Foram analisados os 12 trials do protocolo: três participantes, quatro katas
por participante, dois com IA e dois manuais. Todos ficaram verdes antes do
limite de 2.100 segundos; não houve censura. Para a descrição por tratamento,
calculamos a mediana e o intervalo interquartil (IQR = Q3 − Q1) dos seis
trials, com quartis por interpolação linear.

O teste inferencial respeita a unidade experimental: cada participante gera
um par. Em cada condição, usamos a mediana dos seus dois trials. Para RQ1,
calculamos `Manual − IA` em segundos; para RQ2, `IA − Manual` em pontos
percentuais. Diferenças positivas favorecem a hipótese direcional de cada RQ.
Aplicamos o teste unilateral de postos sinalizados de Wilcoxon, com valores
`p` exatos obtidos pela enumeração de todas as atribuições de sinais aos
postos das diferenças não nulas. Diferenças zero são excluídas do teste.
O nível de significância adotado é 5%. A definição do teste e o tratamento
de diferenças zero seguem a [documentação do Wilcoxon na SciPy](https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.wilcoxon.html).

## RQ1 — A IA reduz o tempo de resolução?

**H0₁:** não há redução pareada de tempo com IA. **H1₁:** a IA reduz o tempo.

| Tratamento | Trials | Mediana do Time-to-Green | Q1 | Q3 | IQR |
| --- | ---: | ---: | ---: | ---: | ---: |
| IA | 6 | 254,447 s | 231,994 s | 261,165 s | 29,171 s |
| Manual | 6 | 1.164,882 s | 954,184 s | 1.486,277 s | 532,093 s |

| Participante | Mediana IA | Mediana manual | Manual − IA |
| --- | ---: | ---: | ---: |
| Pedro | 243,9570 s | 1.676,9935 s | 1.433,0365 s |
| Diogo | 201,2440 s | 946,2575 s | 745,0135 s |
| Lorran | 285,8765 s | 1.238,6800 s | 952,8035 s |

A mediana das três diferenças pareadas é **952,8035 s** (aproximadamente
15 min 53 s) a favor da IA. O Wilcoxon exato unilateral resultou em
`W+ = 6`, `n = 3` e `p = 0,125`. Todos os participantes foram mais rápidos
com IA, mas o resultado não atinge 5% de significância. Com três pares, mesmo
o caso extremo de três diferenças na mesma direção tem `p = 1/8 = 0,125`.
Portanto, os dados são descritivamente favoráveis à IA, mas não permitem
rejeitar H0₁ no nível adotado.

## RQ2 — A IA reduz defeitos observados pelos testes?

**H0₂:** não há aumento pareado da taxa de sucesso com IA. **H1₂:** a IA
aumenta essa taxa.

| Tratamento | Trials | Testes aprovados | Mediana da taxa | IQR |
| --- | ---: | ---: | ---: | ---: |
| IA | 6 | 48/48 | 100% | 0 ponto percentual |
| Manual | 6 | 48/48 | 100% | 0 ponto percentual |

As três diferenças pareadas `IA − Manual` são zero. O Wilcoxon não é
calculável nesse caso porque não há diferenças não nulas para ranquear; por
isso, **não existe valor `p` informativo para RQ2**. Não foram observados
defeitos pelos oito testes de aceitação de cada kata em nenhum tratamento.
Isso não demonstra equivalência entre IA e Manual nem ausência de defeitos
fora dos testes. Há um efeito de teto: a taxa já é 100% nas duas condições.

## Limitações para a discussão final

Há somente três pares independentes. Como cada pessoa resolveu katas
diferentes em IA e Manual, o pareamento controla a pessoa, mas não elimina
diferenças de dificuldade entre katas nem efeitos de ordem. Os oito testes de
aceitação por kata medem apenas os defeitos que conseguem detectar.

O [`README`](../README.md) registra que os trials começaram sem a tag de
baseline congelada prevista no protocolo. Além disso, as quatro linhas de
Diogo no CSV têm `issue_number=0`, embora existam Issues correspondentes; a
[#85](https://github.com/PedroMaiaAlves/lab-experimentacao-software/issues/85)
traz “Manual” no título, enquanto o protocolo, o CSV e a evidência
da execução indicam IA para Diogo/kata03. A análise usa o tratamento do
protocolo e do CSV e não corrige esses registros. Essas inconsistências devem
ser preservadas como ressalvas de rastreabilidade no relatório do grupo.
