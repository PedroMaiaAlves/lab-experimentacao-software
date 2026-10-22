# Sprint 3 — parte C: RQ07 e RQ08

## Escopo e escolha

Foi implementada **uma** opção do bônus: rework rate. Reutiliza a heurística v3
qualificada e a amostra congelada, sem nova coleta ou alteração dos rótulos humanos.
A alternativa temporal exigiria séries trimestrais: a janela de um ano oferece
somente quatro pontos por projeto. Mesmo uma sequência estritamente monotônica
tem p bilateral exato mínimo de 2/24 = 0,0833 no Mann–Kendall sem empates; não seria
possível obter significância de 5% nessa configuração. Essa é uma justificativa
matemática da escolha, não um teste executado sobre os dados.

A orientação em `scripts/issues.csv` (S03-C1–C4) permite ao grupo definir ao menos
três combinações. Após autorização de Lorran para concluir toda a entrega,
implementamos C2/C3 e a integração das partes A/B/C, sem atribuir essas escolhas
a uma tabela obrigatória do professor.

## RQ07 — combinações e concordância

| Combinação | Frequência | Lead time | CFR | Recuperação |
|---|---|---|---|---|
| C1 | Releases principais | a | CI (a) | CI |
| C2 | Principais + pré-releases | b | Releases (b) | CI |
| C3 | Tags | b | Releases (b) | CI |

Lead time e CFR por releases continuam sobre as principais: não alegamos ter
coletado novos pares entre tags/pré-releases. As notas/cortes são os de A, sem
reestimativa. A categoria geral exige quatro métricas. C1 precisa coincidir com
`data/classificacao_C1.csv`, que é preservado.

Em 269 projetos comparáveis, C1–C2 muda 39,4% (κ linear 0,455); C1–C3, 40,1%
(κ 0,437); C2–C3, 4,5% (κ 0,931). Nove projetos perdem classificação por CFR (b)
ausente; os outros 22 já não tinham recuperação. Ausência não é quinta categoria
nem troca. Os denominadores por par e comuns às três são registrados separadamente
e coincidem nesta amostra. Kappa indefinido permanece ausente, não recebe 1.

A robustez preserva as análises originais de B e usa famílias exploratórias próprias:
seis correlações (três frequências × dois CFR), e 24 testes fator × métrica únicos
(18 originais + seis para as duas frequências adicionais). Não duplicamos os testes
invariantes. CI continua sem evidência de associação; CFR (b) permanece positivo
(rho 0,599–0,660, p Holm 0,0012). Nenhuma frequência tem associação com os fatores
após Holm. Cinco associações de B persistem; tipo–recuperação cruza o limiar de 5%
na família ampliada, sem invalidar retrospectivamente seu teste original.

## Reprodução

Na raiz `Lab03/`, com Python e as dependências de `requirements.txt`:

```bash
python -m analises.sprint3_c
python -m analises.notebooks_c --atualizar
python -m validacao.entrega_s03 --reproduzir
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

`results/s03_c/` contém 13 CSVs, duas figuras PNG/PDF, tabelas LaTeX, macros do texto e
manifesto com hashes de entradas, código e saídas e versões do ambiente. O notebook
`notebooks/rq07_s03_c.ipynb` e `notebooks/rq08_s03_c.ipynb` recalculam a análise em
kernels novos, sem rede, exigindo igualdade exata das 13 tabelas publicadas.
Sem `--atualizar`, só gravam em `cache/`.

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

A validação abrange exemplos conhecidos, censura de fronteira, ausências, fontes
adulteradas, contagens inconsistentes, divergência do CFR, kappa manual, famílias
de Holm e reprodução das 13 tabelas. O resultado integrado está documentado em
`entrega_s03_integrada.md`; a versão preliminar do bônus tinha 368 testes.
O artigo consolidado foi compilado com Tectonic 0.17.0: 9 páginas no SBC, incluindo
referências. As nove páginas renderizadas foram inspecionadas.

## Integração e limites da entrega

Os quatro commits de Pedro até `f69b2ab` foram integrados por merge local,
preservando autoria e A. O artigo principal usa as seções compactas `*_final.tex`
e os artefatos das três partes; os textos extensos e PDFs anteriores são históricos.
`artigo_final.pdf` é a versão consolidada de 9 páginas, com RQ01–08 e resumo atualizado.

A Sprint 3 técnica não equivale à etapa FIN de replicação cruzada ou à publicação
na main. Não foram fabricados repositório sorteado, execução externa, Issues ou
atualização de Projects. Consulte `entrega_s03_integrada.md`.
