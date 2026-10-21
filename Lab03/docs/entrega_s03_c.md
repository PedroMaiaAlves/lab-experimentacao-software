# Sprint 3 — RQ08 bônus: rework rate

## Escopo e escolha

Foi implementada **uma** opção do bônus: rework rate. Reutiliza a heurística v3
qualificada e a amostra congelada, sem nova coleta ou alteração dos rótulos humanos.
A alternativa temporal exigiria séries trimestrais: a janela de um ano oferece
somente quatro pontos por projeto. Mesmo uma sequência estritamente monotônica
tem p bilateral exato mínimo de 2/24 = 0,0833 no Mann–Kendall sem empates; não seria
possível obter significância de 5% nessa configuração. Essa é uma justificativa
matemática da escolha, não um teste executado sobre os dados.

Não foram inventadas combinações C2/C3 para a RQ07. A documentação de A indica essa
análise para C, mas o único trecho do enunciado fornecido nesta etapa descreve a
RQ08; a atribuição e as combinações precisam ser confirmadas antes de ampliar o escopo.

## Reprodução

Na raiz `Lab03/`, com Python e as dependências de `requirements.txt`:

```bash
python -m analises.sprint3_c
python -m analises.notebooks_c --atualizar
python -m pytest --cov=metricas --cov-report=term-missing --cov-fail-under=80
```

No PowerShell, se o ambiente não estiver ativado, substitua `python` por
`.\.venv\Scripts\python.exe`. A análise aceita `--dataset`, `--amostra`, `--pacote`,
`--config` e `--saida`; a saída deve ficar fora de `data/`.

Entradas: `data/dataset.csv`, `data/amostra_final.csv`, seus manifestos,
`data/fontes_s02.zip`, `config_s02.yaml` e
`data/amostra_ouro_s02/avaliacao_v3.manifest.json`. Não é necessário extrair o ZIP,
ter cache de API ou token. As três fontes de releases, comparações e commits são
conferidas contra seus hashes; o código v3 precisa coincidir com o da avaliação.
O processamento valida cobertura exata de releases, contagens de commits e reprodução
do CFR (b), inclusive suas ausências, antes de publicar resultados.

`results/s03_c/` contém cinco CSVs, figura PNG/PDF, tabela LaTeX, macros do texto e
manifesto com hashes de entradas, código e saídas e versões do ambiente. O notebook
`notebooks/rq08_s03_c.ipynb` recalcula a análise em um kernel novo, sem rede, e exige
igualdade exata das cinco tabelas publicadas. Sem `--atualizar`, só grava em `cache/`.

## Definições e ausências

Por projeto, rework = releases corretivas / todas as releases principais na janela
01/10/2025–30/09/2026. Não inclui drafts/pré-releases e **não censura** os últimos
sete dias. A definição principal reutiliza exatamente a v3 e a disponibilidade da
S02: 404 ou mensagem ausente sem classificação positiva gera lacuna, e uma lacuna
torna a taxa do projeto ausente. Não se troca ausência por zero.

Essa definição tem uma limitação herdada: sem antecessora ou sem commits, a v3 pode
retornar negativo sem evidência textual. Para expô-la, publicamos separadamente
`rework_conservador`, que só existe quando todas as releases do projeto têm
comparação `ok`, pelo menos um commit e mensagens completas. Até um resultado
positivo com mensagem faltante fica desconhecido nessa sensibilidade: a mensagem
ausente poderia incluir funcionalidades e mudar a decisão da v3. Os limites
inferior/superior consideram as desconhecidas respectivamente todas negativas ou
todas positivas; são limites de identificação, **não intervalos de confiança** e
não contemplam erros de classificação da heurística.

O resumo principal dá o mesmo peso a cada projeto e usa mediana e quartis.
Proporções agregadas por release dão mais peso a projetos com muitas versões e
não devem ser confundidas com a mediana por projeto. A comparação pareada usa
somente projetos com ambos os indicadores disponíveis, sem teste causal ou nova
hipótese registrada depois dos resultados.

Rework conta a **corretiva**; CFR (b) conta as **releases anteriores** seguidas de
corretiva em até sete dias. Uma corretiva pode marcar várias anteriores no CFR,
mas é contada uma vez no rework. Só CFR exige a censura final de sete dias.
O teste com quatro releases em dias consecutivos (última corretiva) demonstra
rework de 25% e CFR de 75%; não existe desigualdade garantida entre as taxas.

A [definição oficial do DORA](https://dora.dev/guides/dora-metrics/) observa
implantações não planejadas associadas a incidentes em produção. O indicador do
enunciado é um **proxy por releases corretivas**, não uma observação desses eventos.

## Resultado e validação local

As 11.453 releases principais cobrem os 300 projetos; a v3 identifica 3.673
corretivas conhecidas. A taxa principal está disponível em 289 projetos (11 ausentes),
com mediana de **37,35%** e Q1–Q3 de **20,00%–57,14%**. O CFR (b) tem mediana de
17,50% nos mesmos projetos. Rework supera CFR em 178/289 pares, com diferença
pareada mediana de 11,11 pontos percentuais; a diferença de medianas não deve ser
confundida com a mediana dessas diferenças.

A sensibilidade identifica 1.899 releases sem evidência completa: 72 sem
antecessora, nove comparações 404, 1.816 sem commits e duas com mensagem ausente.
Restam 201 projetos completos, com mediana de 40,00%. Os limites conservadores
agregados são 32,07%–48,65%, sem pressupor que as desconhecidas sejam negativas.
Não representam incerteza amostral, nem autorizam generalização causal.

A suíte local passou com **368 testes**, cobertura de **95,59% em `metricas`**
e 100% em `metricas/rework.py`. Inclui exemplos conhecidos, censura de fronteira,
ausências, fontes adulteradas, contagens inconsistentes e divergência do CFR.
O notebook foi executado em kernel novo e reproduziu exatamente os cinco CSVs.
O artigo foi compilado com Tectonic 0.17.0 e as 13 páginas renderizadas foram
inspecionadas. Isso valida a prévia, mas **não** o limite final de 10 páginas.

## Integração e limites da entrega

`docs/artigo/resultados_c.tex` é incluído pelo artigo principal e importa os números
gerados, sem transcrevê-los manualmente. Não substitui as análises de A/B nem o
dataset da S02. `artigo_s03_c.pdf` é uma prévia integrada do estado local, não uma
declaração de fechamento do artigo final do grupo.

Na sincronização desta entrega, `main@f6441c3` já continha A; a parte B estava em
branches remotas, culminando em `166-lab03-s03---b4-validar-a-entrega`, ainda sem
integração à main. A RQ07 continuava pendente. A documentação de A também registra
12 páginas antes de B/C, acima do limite final de 10, e resumo ainda sem os
resultados finais. Esses pontos são de integração do grupo e não são apresentados
como resolvidos pelo bônus. Nenhum merge, push ou republicação foi feito nesta etapa.
