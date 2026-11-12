# Lorran — Lab04S02: Q3, G4 e integração do dashboard

## Escopo e plano inicial

Responsável: Lorran Avelar. Issues: #188 e #189.
Base: `origin/main` em `a44883e`, consultada em 11/11/2026.

1. **#188 — Q3:** reutilizar `simular_grade` para diferenças t de Student com
   três graus de liberdade, divididas por `sqrt(3)` para preservar a variância
   calibrada. Manter os 30 pares, 10.000 repetições, alpha 0,05, alternativa
   bicaudal e razões 1,00/1,02/1,05/1,10/1,15/1,20/1,25 da Q2. Usar a política
   `SeedSequence([42, 3])`, definida antes de observar os resultados.
2. Preservar resultados agregados, intervalos de Wilson e manifesto com hashes;
   verificar reprodução, hipóteses sob H0 e equivalência com o SciPy.
3. **#189 — G4:** recuperar o dashboard/G1/G3 já entregue na PR #191, ausente
   da árvore atual da main. Integrar Q2/Q3 em painéis comparáveis, com eixo de
   razão geométrica e taxa entre zero e um, sem modificar resultados dos colegas.
4. Completar as seções de poder, dados reais e conclusão. Distinguir simulação,
   efeito observado e p-valor; evitar recomendação universal de um teste.
5. Executar testes offline, conferir G1–G4 e as sete seções do Streamlit,
   documentar resultados e publicar somente as alterações deste escopo.

Os dados reais, o protocolo histórico, os artefatos de Q1/Q2 e seus geradores
serão preservados. Nenhuma nova coleta de tempos será iniciada.

## Situação inicial

- PR #190 (Q1) e PRs #192/#193 (Q2) integradas à main.
- PR #191 foi mesclada na branch da #190, depois de a #190 já ter entrado na
  main. Por isso `d6411e2` não é ancestral da main consultada, e `app.py`, G1,
  G3 e seus testes não chegaram à sua árvore. Reaproveitamos esses arquivos
  de `28d571d`, preservando a autoria e o histórico existentes.
- Implementação e validações de Q3/G4 ainda pendentes neste commit de planejamento.

## Implementação e resultados — 12/11/2026

- `experimento/q3.py` e `simular_q3.py`: execução, manifesto, reprodução exata
  e conferência individual com SciPy. Reutilizam as constantes/grade de Q2
  e o gerador de Pedro, sem modificá-los.
- `data/s02/q3_resultados.csv`: 14 resultados agregados, sem amostras brutas.
  Manifesto registra variância, distribuição, padronização, sementes, versões
  e hashes. `q3_conferencia_scipy.json` registra 140.000 decisões verificadas
  e zero divergências, com vínculo aos resultados e ao manifesto.
- `experimento/g4.py`: painéis normal/t3 com mesma escala de efeito, poder
  entre zero e um, cores preservadas, Wilson e identificação de H0. Rejeita
  grades incompletas/duplicadas, taxas inválidas e configurações incompatíveis.
- `app.py`: G1–G4 e sete seções integrados. Q2 e sua interpretação permanecem
  de Diogo; os arquivos recuperados de Pedro são identificados como tais.
  Corrigido contraste dos indicadores também no tema escuro.
- `experimento/resumo_real.py`: razão geométrica, IC t e resultados dos dois
  testes nos pares reais preservados, separados da avaliação Monte Carlo.
- README e CI específico de Lab04 atualizados; nenhum arquivo de outro Lab
  é alterado. O protocolo histórico e os dados reais/simulados permanecem iguais.

### Interpretação

| Razão | t: taxa [Wilson 95%] | Wilcoxon: taxa [Wilson 95%] |
| --- | --- | --- |
| 1,00 (erro tipo I) | 4,19% [3,81; 4,60] | 4,59% [4,20; 5,02] |
| 1,02 | 10,05% [9,48; 10,65] | 12,75% [12,11; 13,42] |
| 1,05 | 38,39% [37,44; 39,35] | 48,83% [47,85; 49,81] |
| 1,10 | 84,07% [83,34; 84,77] | 93,93% [93,44; 94,38] |
| 1,15 | 96,55% [96,17; 96,89] | 99,63% [99,49; 99,73] |
| 1,20 | 98,84% [98,61; 99,03] | 99,99% [99,94; 100,00] |
| 1,25 | 99,53% [99,38; 99,65] | 100% [99,96; 100,00] |

Em Q3, Wilcoxon tem maior poder estimado nos seis efeitos não nulos, com
maior diferença de 10,44 p.p. na razão 1,05. Ambos ultrapassam 80% na razão
1,10; em Q2 isso ocorre na grade a partir de 1,15. A comparação de Q3 é
descritiva: não usamos sobreposição de Wilson como teste pareado nem
reescrevemos os testes de McNemar de Q2.

Com delta zero, a média da t3 é zero e a distribuição é simétrica em zero;
as hipóteses nulas dos dois testes valem. Porém, a normalidade das diferenças,
necessária à referência t exata, é violada. O t fica conservador em Q3,
enquanto o Wilson do Wilcoxon inclui 5%. Não afirmamos controle nominal
exato do t nem superioridade universal do Wilcoxon.

Caudas pesadas não significam somente valores extremos: a forma central
também muda. A variância é preservada na população, não forçada em cada
amostra. A calibração usa 30 pares reais, e os intervalos Monte Carlo não
incluem essa incerteza. O cenário não representa toda distribuição não normal.

Nos dados reais, razão geométrica sem/com cache = 3,944; IC t 95% =
[3,684; 4,223]. t = 41,053, p = 3,03e-27; Wilcoxon W = 0, p = 1,86e-09,
sem zeros ou empates. Ambos rejeitam H0, sujeitos às suas hipóteses.
O resultado descreve compilação local de bytecode, não desempenho universal.

### Evidências

- Suíte integrada local: **103 testes aprovados**, incluindo os testes
  preservados de Pedro/Diogo, a Q3, G4, resumo real e AppTest do Streamlit.
- `validar.py`, `simular_s02.py --validar`, `simular_q2.py --validar`,
  `interpretar_q2.py --validar` e `simular_q3.py --validar`: aprovados.
- `pip check`: sem dependências quebradas; `git diff --check`: aprovado.
- Ambiente da integração: Windows, Python 3.12.0, NumPy 2.2.6, SciPy 1.18.1,
  Plotly 7.1.0 e Streamlit 1.67.0, isolado em `Lab04/.venv`.
- Conferência visual no navegador local: G1–G4, sete seções, dados reais e
  conclusão renderizados; indicadores legíveis no tema escuro. P-valores
  pequenos são exibidos em notação científica, sem arredondá-los para zero.
- O AppTest bloqueia coleta, Monte Carlo e `urlopen` durante a abertura;
  as quatro figuras e as sete seções permanecem disponíveis offline.
- CI remoto da implementação `764a3b3`: [Testes LAB04 aprovados](https://github.com/PedroMaiaAlves/lab-experimentacao-software/actions/runs/43146783845)
  e [Testes LAB03 aprovados](https://github.com/PedroMaiaAlves/lab-experimentacao-software/actions/runs/43146783720).
  Lab04 executou os 103 testes e todas as reproduções offline, com instalação
  limpa no Windows/Python 3.12. As revisões seguintes reexecutam os checks.
- A execução de `f6a7205` revelou variação de último dígito na exponenciação
  da simulação bivariada S01 em outro runner: 101 testes passaram, e os dois
  testes estritos dessa reprodução falharam. Os testes de Q1/Q2/Q3 e G4
  passaram. A integração fixa `NPY_DISABLE_CPU_FEATURES=AVX512F` no ambiente
  de referência e registra `numpy.show_runtime()` no CI para conferir essa
  hipótese de despacho numérico. Não altera geradores, validadores dos colegas,
  dados, hashes, tolerâncias ou critérios de aprovação. O README registra
  esse requisito; igualdade bit a bit em ambientes arbitrários não é prometida.
- Publicação: branch `lorran-q3-g4`, [PR #194](https://github.com/PedroMaiaAlves/lab-experimentacao-software/pull/194)
  para main, com `Closes #188` e `Closes #189`. A main não foi alterada por
  esta execução; o fechamento das issues ocorre no merge da PR.

### Fontes metodológicas

- [SciPy: distribuição Student t](https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.t.html).
- [SciPy: Wilcoxon e hipótese de simetria](https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.wilcoxon.html).
- [Streamlit: AppTest](https://docs.streamlit.io/develop/api-reference/app-testing/st.testing.v1.apptest).
