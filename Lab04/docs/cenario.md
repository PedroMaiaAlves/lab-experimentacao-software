# Cenário e expectativa anterior à simulação

Este texto é registrado antes da coleta e da primeira simulação. O manifesto
da coleta guarda seu SHA-256 e o instante UTC do registro. A previsão abaixo
não deve ser reescrita à luz dos resultados; conclusões futuras serão separadas.

## Pergunta e unidade experimental

Como a reutilização do cache de bytecode altera o tempo da etapa de compilação
dos arquivos Python do Django?

Uma observação pareada é um bloco de duas execuções locais dos mesmos arquivos
do Django 5.2.8: uma com cache de bytecode vazio, outra com cache preenchido.
Serão 30 blocos na mesma máquina, após três blocos de aquecimento excluídos.
O tempo inclui a inicialização do subprocesso e a execução do `compileall`, em
segundos. A preparação do cache fica fora da medição. O efeito avaliado é a
reutilização de bytecode `.pyc`, não o cache de downloads nem o cache de disco.

## Hipóteses e interpretação

Para o par i, A_i é o tempo sem cache e B_i é o tempo com cache. Definimos
`d_i = ln(A_i) - ln(B_i) = ln(A_i / B_i)`. A transformação foi escolhida antes
de observar a coleta: durações são positivas e razões expressam ganhos relativos.
Os histogramas de G1 continuarão mostrando segundos, sem transformação.

- **t pareado:** H0: E[d] = 0; H1: E[d] != 0. Compara a média das diferenças
  logarítmicas, equivalente a comparar a razão das médias geométricas com 1.
- **Wilcoxon pareado:** H0: distribuição de d simétrica em torno de zero;
  H1: centro diferente de zero, no modelo de deslocamento simétrico.
- Ambos bicaudais, alpha = 0,05. Valores positivos de d indicam menor tempo
  com cache. `exp(mean(d))` é a razão geométrica sem cache / com cache.
- Não rejeitar H0 não comprova igualdade. O p-valor não é a probabilidade de H0
  ser verdadeira. Significância não substitui avaliação do tamanho do efeito.

Os dois testes respondem à pergunta sobre deslocamento no modelo simétrico,
mas suas hipóteses não são intercambiáveis em distribuições arbitrárias.
A normalidade relevante para o t pareado é a das **diferenças**, não a dos
tempos brutos isoladamente. Wilcoxon também exige cuidado com simetria.

## Expectativa registrada antes de simular

Esperamos que o t pareado seja competitivo e possivelmente mais poderoso quando
as diferenças logarítmicas forem normais. Esperamos possível vantagem do Wilcoxon
com diferenças simétricas de caudas pesadas. Não assumimos que um teste não
paramétrico sempre vence quando há não normalidade. Essa comparação exige Q1–Q3
na sprint 2; uma única amostra da sprint 1 não permite concluir qual teste é melhor.

## Modelo de simulação

Cada linha é `z_i = [ln(A_i), ln(B_i)]`. Estimamos o vetor de médias por médias
amostrais e a matriz de covariância amostral com divisor `n-1`. Geramos pares
`Z ~ Normal_bivariada(mu, Sigma)` com `numpy.random.default_rng(42)` e aplicamos
`exp` a cada coordenada. Isso fornece marginais lognormais positivas e preserva
a dependência estimada na escala logarítmica (não a correlação amostral exata).

Por padrão, mu e Sigma vêm integralmente dos dados reais. Para experimentos
futuros, um deslocamento delta pode substituir `mu[0]-mu[1]`, mantendo o ponto
médio das duas médias e a covariância. Delta=0 produz diferenças normais com
média zero: ambas as hipóteses nulas valem nesse modelo. Delta está em unidades
de log-razão; `exp(delta)` é a razão geométrica populacional.

O modelo é uma aproximação de trabalho, não uma demonstração de ajuste perfeito.
G1 deverá mostrar suas limitações. Não ajustaremos parâmetros para forçar
significância nem selecionaremos sementes pelo p-valor obtido.

## Limitações e continuidade

As medições repetem o mesmo projeto na mesma máquina. Carga do sistema,
antivírus, aquecimento, autocorrelação e cache do sistema operacional podem
influenciar os tempos. O balanceamento de ordem reduz um confundimento, mas
não elimina esses fatores nem transforma os blocos em projetos independentes.
O cenário mede uma etapa específica de compilação, não o build completo ou o
tempo de execução de uma aplicação Django. Ganhos grandes neste cenário não
demonstram vantagem universal de um teste sobre o outro.

Na S02, Q1–Q3 e G3/G4 serão implementados separadamente. Uma opção coerente para
Q3 é introduzir caudas pesadas simétricas nas diferenças logarítmicas, mantendo
claras as hipóteses comuns sob H0. Ainda não há resultados dessa etapa.

## Fontes metodológicas

- Python: https://docs.python.org/3.13/library/compileall.html
- SciPy t pareado: https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.ttest_rel.html
- SciPy Wilcoxon: https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.wilcoxon.html
- Fonte Django: https://www.djangoproject.com/weblog/2025/nov/05/security-releases/

O Django é apenas o objeto de medição. O código não instala nem inicia uma
aplicação web Django. Seus fontes não serão adicionados ao repositório do grupo.
