# Checklist de revisão da análise (#208 → PR da #211)

Revisor: Diogo. Objetivo: garantir que a análise segue o que foi **pré-registrado**
(`proposta.md`, `metodo.md`, `plano_analise.md` e o protocolo final da #207), sem análises
escolhidas depois de ver os dados.

## Dados de entrada
- [ ] Lê só coletas de `data/oficial/` com `validar.py` aprovado (portão G3); nenhum dado de `data/piloto/` ou `data/piloto_g1/`.
- [ ] Imagem do OMB no manifesto = `lab05/openmessaging-benchmark:5b1fa709-ts-ms` (latência do RabbitMQ em ms).
- [ ] Todas as execuções oficiais vieram da mesma máquina (manifesto).
- [ ] Falhas excluídas só por status técnico registrado; nenhuma exclusão por "valor estranho"; repetições conforme a regra da #207.

## Hipóteses pré-registradas
- [ ] H1 (throughput, E1) e H2 (latência p99, E2) testadas **em cada tamanho**, bicaudais, α = 0,05.
- [ ] A escolha entre Welch sobre log e Mann-Whitney segue a regra do `plano_analise.md` (decidida pela normalidade, não pelo p-valor).
- [ ] Correção de Holm sobre as 4 comparações principais (H1 e H2 × 2 tamanhos).
- [ ] H3 (interação broker × tamanho) com ANOVA sobre log ou permutação, como pré-registrado.
- [ ] Nenhuma hipótese nova apresentada como confirmatória; o que for exploratório está rotulado.

## Efeito e incerteza
- [ ] Razão geométrica Kafka/RabbitMQ com IC de 95% por bootstrap (semente 42) e δ de Cliff, por célula.
- [ ] Interpretação pelo tamanho do efeito, não só pelo p-valor; não rejeitar H0 não significa "iguais".

## Checagens de validade (alimentam a seção 4.2 do `metodo.md`)
- [ ] Efeito de ordem e de bloco testados.
- [ ] Sensibilidade com e sem as execuções repetidas.
- [ ] Carga relativa do E2 (taxa ÷ capacidade do E1) reportada por broker.
- [ ] CV observado por célula comparado ao usado no cálculo de n (#207).

## Reprodutibilidade
- [ ] `python -m pytest Lab05/tests -q` passa.
- [ ] Resultado regenerado do zero com um comando documentado; JSON de saída versionado.
