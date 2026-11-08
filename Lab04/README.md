# Lab04 — Testes de hipótese: compilação com e sem cache

Par P2: **t pareado × Wilcoxon pareado**, usando tempos de compilação de
bytecode do Django 5.2.8. A sprint 1 vale 7 pontos.

Esta entrega reúne a base da Sprint 1 e a parte independente de Pedro na Sprint 2.
Pedro implementou coleta, calibração, simulação e Q1/G3; Diogo implementou os
testes estatísticos e G2. O dashboard e G1, que não haviam sido entregues na
Sprint 1, foram recuperados nesta integração. Q2, Q3 e G4 continuam atribuídos
às issues #186–#189. Não há reutilização de dados ou resultados de outros laboratórios.

Issues de Pedro: [P1 — #173](https://github.com/PedroMaiaAlves/lab-experimentacao-software/issues/173)
e [P2 — #174](https://github.com/PedroMaiaAlves/lab-experimentacao-software/issues/174).
A branch da #174 inclui a coleta da #173 e acrescenta a simulação. Integrar
primeiro a PR da #173; depois, direcionar a PR da #174 para `main`, se necessário,
e integrar a simulação. As issues foram cadastradas com títulos iguais; o
escopo correto de cada uma está em `docs/issues_s01.md`.

## Por onde começar

- [Issues prontas para copiar no Projects](docs/issues_s01.md).
- [Cenário, hipóteses e expectativa anterior à simulação](docs/cenario.md).
- [Protocolo de coleta](docs/protocolo_coleta.md).
- [Interfaces e instruções para Diogo e Lorran](docs/contratos.md).
- [Evidências da entrega P1/P2](docs/entrega_pedro.md).
- [Evidências da entrega D1/D2](docs/entrega_diogo.md).

## Ambiente isolado

Comandos no PowerShell, a partir da raiz do repositório. A coleta oficial usa
CPython **3.13.5**, disponível nesta máquina pelo launcher `py -3.13`.
Não é preciso ativar o ambiente nem alterar os ambientes dos laboratórios anteriores.

```powershell
py -3.13 -m venv Lab04/.venv
.\Lab04\.venv\Scripts\python.exe -m pip install -r Lab04/requirements.lock.txt
```

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
integrados; Q2, Q3, G4 e a recomendação final permanecem explicitamente pendentes.

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
Q2 e Q3. Q2 usará diferenças normais com efeitos não nulos; Q3 usará Student t
com três graus de liberdade, padronizada para a mesma variância.

Repositório: https://github.com/PedroMaiaAlves/lab-experimentacao-software

O link do Projects ainda deve ser preenchido em `protocolo.json` quando Pedro
cadastrar as issues. Não foi assumido que o Projects histórico seja o do Lab04.
Como o protocolo foi preservado no manifesto da coleta, futuras alterações
administrativas não devem reescrever o manifesto histórico.

## GitHub Projects e entrega acadêmica

Use milestone `Lab04S01`, labels `lab04` / `sprint-01`, responsável individual e
WIP de uma issue por pessoa. Cada integrante deve produzir código e ter pelo
menos uma issue com commit que a referencie. Quando autorizado, use o número
real: `feat(lab04): descrição #NUMERO`.

As implementações locais não substituem commits vinculados, revisão ou atualização
dos cartões. Nenhuma issue, commit, pull ou push é realizado pelos scripts deste Lab.
