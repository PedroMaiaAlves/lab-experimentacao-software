# Lab04 — Testes de hipótese: compilação com e sem cache

Par P2: **t pareado × Wilcoxon pareado**, usando tempos de compilação de
bytecode do Django 5.2.8.

Esta entrega integra as Sprints 1 e 2.
Pedro implementou coleta, calibração, simulação e Q1/G3; Diogo implementou os
testes estatísticos e G2. O dashboard e G1, que não haviam sido entregues na
Sprint 1, foram recuperados da PR #191. Diogo entregou Q2 e sua interpretação
(#186/#187); Lorran implementou Q3, G4, dados reais e conclusão (#188/#189).
Não há reutilização de dados ou resultados de outros laboratórios.

Issues de Pedro: [P1 — #173](https://github.com/PedroMaiaAlves/lab-experimentacao-software/issues/173)
e [P2 — #174](https://github.com/PedroMaiaAlves/lab-experimentacao-software/issues/174).
As issues da S01 foram cadastradas com títulos iguais; o escopo histórico de
cada uma está em `docs/issues_s01.md`.

## Por onde começar

- [Issues prontas para copiar no Projects](docs/issues_s01.md).
- [Cenário, hipóteses e expectativa anterior à simulação](docs/cenario.md).
- [Protocolo de coleta](docs/protocolo_coleta.md).
- [Interfaces e instruções para Diogo e Lorran](docs/contratos.md).
- [Evidências da entrega P1/P2](docs/entrega_pedro.md).
- [Evidências da entrega D1/D2](docs/entrega_diogo.md).
- [Evidências de Q1/G3 e recuperação do dashboard](docs/entrega_pedro_s02.md).
- [Evidências de Q2 e sua interpretação](docs/entrega_diogo_s02.md).
- [Evidências de Q3/G4 e integração final](docs/entrega_lorran_s02.md).

## Ambiente isolado

Comandos no PowerShell, a partir da raiz do repositório. A coleta oficial usa
CPython **3.13.5**. A reprodução e o dashboard desta integração foram validados
em Windows com **Python 3.12.0**, NumPy 2.2.6 e SciPy 1.18.1; o CI usa Python 3.12.
Não é preciso ativar o ambiente nem alterar os ambientes dos laboratórios anteriores.

```powershell
py -3.12 -m venv Lab04/.venv
.\Lab04\.venv\Scripts\python.exe -m pip install -r Lab04/requirements.lock.txt
```

Para reprodução bit a bit da simulação bivariada da S01, o CI também fixa
o despacho de CPU do NumPy sem AVX-512. Antes das validações em outra CPU:

```powershell
$env:NPY_DISABLE_CPU_FEATURES = 'AVX512F,AVX512CD,AVX512_SKX,AVX512_CLX,AVX512_CNL,AVX512_ICL'
```

O ambiente vale para novos processos Python. Sem esse ajuste, CPUs diferentes
podem produzir diferenças no último dígito de `exp`, apesar das mesmas versões
e semente. Os hashes dos artefatos e a validação estrita continuam obrigatórios;
não regravamos os dados oficiais nem afrouxamos suas comparações para passar o CI.

`requirements.txt` contém as dependências diretas da entrega integrada. O lock
registra as versões completas efetivamente usadas, incluindo SciPy, Plotly e
Streamlit.

## Reproduzir sua parte, sem coletar novamente

O comando abaixo lê a coleta preservada, confere os hashes, recalibra o modelo
e gera a mesma amostra simulada com semente 42. Funciona offline:

```powershell
.\Lab04\.venv\Scripts\python.exe Lab04/simular.py
```

Conferir os artefatos e a reprodução exata, sem modificá-los:

```powershell
.\Lab04\.venv\Scripts\python.exe Lab04/validar.py
.\Lab04\.venv\Scripts\python.exe -m pytest -c Lab04/pytest.ini Lab04/tests -q
```

Reprodutibilidade significa reconstruir a análise e a simulação a partir dos
tempos preservados. **Uma nova medição real não terá tempos idênticos.**

## Nova coleta — somente quando desejado

Uma coleta executa três pares de aquecimento e 30 pares oficiais. O coletor
recusa sobrescrever um diretório existente. Para realizar outra sessão, use um
nome novo e preserve a coleta original:

```powershell
.\Lab04\.venv\Scripts\python.exe Lab04/coletar.py --saida Lab04/data/nova_sessao
```

O download oficial é verificado por SHA-256. A fonte extraída fica em `.cache/`,
fora do versionamento. Não são necessários token GitHub, instalação do Django
ou execução de uma aplicação Django. Falhas técnicas são registradas; o par
inteiro é repetido, até três tentativas. Falha persistente encerra a sessão como
incompleta, sem fabricar as observações restantes.

## Dados e saídas

| Local | Conteúdo |
| --- | --- |
| `data/real/pares_reais.csv` | 30 pares oficiais, ordem, tentativa e horários |
| `data/real/aquecimento.csv` | Três pares excluídos da análise |
| `data/real/medicoes.jsonl` | Log individual das execuções e estados do cache |
| `data/real/falhas.jsonl` | Falhas técnicas; vazio significa nenhuma falha |
| `data/real/arquivos_fonte.csv` | Caminho e hash de cada arquivo Python compilado |
| `data/real/manifesto.json` | Fonte, ambiente, comando, protocolo e hashes |
| `data/simulado/parametros.json` | Médias e covariância dos log-tempos, origem e semente |
| `data/simulado/pares_simulados.csv` | Amostra simulada; não são medições reais |
| `data/simulado/manifesto.json` | Hashes dos resultados e do gerador |

Atributos Git locais preservam os bytes dos dados, inclusive quebras de linha,
para que os hashes permaneçam válidos após checkout.

## Testes estatísticos e G2: entrega de Diogo

D1 (#175) implementa `experimento/analise.py`: t pareado sobre os log-tempos e
Wilcoxon pareado sobre `log(sem) − log(com)`, bicaudais, alpha 0,05. D2 (#176)
implementa `experimento/g2.py`: distribuição sob H0, região de rejeição e p-valor
dos dois testes, em figura Plotly. Ver o resultado na amostra simulada:

```powershell
cd Lab04; .\.venv\Scripts\python.exe analisar.py; cd ..
```

Uso no dashboard:

```python
from experimento.analise import analisar_pares
from experimento.g2 import figura_g2, texto_g2

resultados = analisar_pares(simulados)
fig = figura_g2(simulados, resultados)   # gera erro se o p-valor desenhado divergir de D1
texto = texto_g2(simulados, resultados)  # 4 frases para acompanhar o G2
```

Evidências em [docs/entrega_diogo.md](docs/entrega_diogo.md).

## Dashboard integrado

Instale as dependências e abra o dashboard local:

```powershell
.\Lab04\.venv\Scripts\python.exe -m streamlit run Lab04/app.py
```

O aplicativo carrega os dados preservados e usa as funções científicas sem
iniciar uma coleta. As sete seções são: cenário; dados/G1; funcionamento dos
testes/G2; erro tipo I/G3; poder/G4; dados reais; conclusão. G1, G2 e G3 estão
integrados, com G4, análise real e conclusão. O aplicativo não executa Monte Carlo
na abertura: lê os resultados agregados e usa os pares preservados.

## Sprint 2 — Q1 e G3 (Pedro)

Q1 estima o erro tipo I sob diferenças logarítmicas normais com média zero.
São 10.000 repetições para cada tamanho `n = 10, 20, 30, 50, 100`, com alpha
0,05, testes bicaudais e semente-base 42. O desvio das diferenças vem da
covariância calibrada nos dados reais.

Gerar e validar os resultados agregados:

```powershell
.\Lab04\.venv\Scripts\python.exe Lab04/simular_s02.py
.\Lab04\.venv\Scripts\python.exe Lab04/simular_s02.py --validar
```

Os artefatos ficam em `data/s02/`: somente dez linhas agregadas e um manifesto
de proveniência são versionados; as 50.000 amostras Monte Carlo não são salvas.
G3 mostra a taxa empírica de rejeição, intervalo de Wilson de 95% e a referência
nominal de 5%.

A API `experimento.monte_carlo.simular_grade` é o contrato compartilhado para
Q2 e Q3. Q2 usa diferenças normais com efeitos não nulos; Q3 usa Student t
com três graus de liberdade, padronizada para a mesma variância.

## Sprint 2 — Q2 (Diogo), Q3 e G4 (Lorran)

Ambos os cenários usam 30 pares, 10.000 repetições por efeito, alpha 0,05,
alternativa bicaudal e razões geométricas sem/com cache de
1,00; 1,02; 1,05; 1,10; 1,15; 1,20; 1,25. Em 1,00 medimos erro tipo I;
nas outras razões, poder. Os intervalos de Wilson de 95% descrevem a incerteza
de Monte Carlo de cada taxa, não do efeito real nem da diferença entre testes.

Q3 gera `d = log(razão) + sigma_d * T3/sqrt(3)`, preservando a variância
populacional de Q2, pois `Var(T3) = 3`. A distribuição continua simétrica,
com média e variância finitas, mas não é normal e tem quarto momento infinito.
Não normalizamos pela variância observada de cada amostra. As sementes seguem
`SeedSequence([42, 2])` e `SeedSequence([42, 3])`, com fluxos independentes
entre perguntas e a mesma amostra para os dois testes dentro de cada ponto.

```powershell
.\Lab04\.venv\Scripts\python.exe Lab04/simular_q2.py --validar
.\Lab04\.venv\Scripts\python.exe Lab04/interpretar_q2.py --validar
.\Lab04\.venv\Scripts\python.exe Lab04/simular_q3.py --validar
```

Para regenerar somente Q3: `python Lab04/simular_q3.py`. Para conferir e
registrar as 140.000 decisões contra chamadas individuais do SciPy:
`python Lab04/simular_q3.py --scipy`. Usar o Python do ambiente isolado acima.
Q1/Q2 e a coleta não são reescritas por esses comandos.

| Razão | Q2: t | Q2: Wilcoxon | Q3: t | Q3: Wilcoxon |
| --- | --- | --- | --- | --- |
| 1,00 (H0) | 4,98% | 4,97% | 4,19% | 4,59% |
| 1,02 | 8,52% | 8,16% | 10,05% | 12,75% |
| 1,05 | 29,51% | 28,04% | 38,39% | 48,83% |
| 1,10 | 78,73% | 77,50% | 84,07% | 93,93% |
| 1,15 | 98,06% | 97,67% | 96,55% | 99,63% |
| 1,20 | 99,97% | 99,95% | 98,84% | 99,99% |
| 1,25 | 100% | 100% | 99,53% | 100% |

Sob normalidade, t tem pequena vantagem nos efeitos intermediários. Em Q3,
Wilcoxon tem maior poder estimado nos efeitos não nulos, até 10,44 p.p. de
diferença. Sob H0, porém, t é conservador: 4,19%, IC 95% 3,81–4,60%; Wilcoxon
tem 4,59%, IC 4,20–5,02%. As hipóteses nulas de média zero e simetria em zero
valem, mas a distribuição t exata da estatística exige normalidade, violada
em Q3. Não concluímos superioridade universal nem que caudas pesadas sempre
reduzem o poder; a forma central da distribuição também mudou.

G4 mostra os dois cenários lado a lado, nas mesmas escalas, com as quatro
curvas e seus intervalos. A comparação de Q3 é descritiva; sobreposição de
intervalos não é um teste de diferença. A comparação pareada e a interpretação
originais de Q2 são exibidas separadamente, sem alteração.

Os dados reais favorecem cache nesta etapa local: razão geométrica 3,944,
IC t de 95% 3,684–4,223; ambos os testes rejeitam H0. A inferência depende
das hipóteses dos testes e da independência dos pares, não demonstrada por
significância. Não extrapolamos para todo build, outras máquinas ou projetos.

O workflow `Testes LAB04` verifica instalação, suíte completa, Streamlit via
AppTest e reprodução offline de Q1/Q2/Q3. `Testes LAB03` permanece intacto.

Repositório: https://github.com/PedroMaiaAlves/lab-experimentacao-software

O link do Projects ainda deve ser preenchido em `protocolo.json` quando Pedro
cadastrar as issues. Não foi assumido que o Projects histórico seja o do Lab04.
Como o protocolo foi preservado no manifesto da coleta, futuras alterações
administrativas não devem reescrever o manifesto histórico.

## GitHub Projects e entrega acadêmica

Na S02, use milestone `Lab04S02`, labels correspondentes, responsável individual e
WIP de uma issue por pessoa. Cada integrante deve produzir código e ter pelo
menos uma issue com commit que a referencie. Quando autorizado, use o número
real: `feat(lab04): descrição #NUMERO`.

As implementações locais não substituem commits vinculados, revisão ou atualização
dos cartões. Nenhuma issue, commit, pull ou push é realizado pelos scripts deste Lab.
