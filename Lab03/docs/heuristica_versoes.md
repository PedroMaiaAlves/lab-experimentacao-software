# Versões da heurística de release corretiva

## Protocolo

A heurística é configurada em `config.yaml`. Tags fora de SemVer estrito, admitindo
somente o prefixo `v`, não fornecem evidência de versão e usam apenas o fallback textual.
Cada versão avaliada deve permanecer registrada, inclusive quando não atingir o F1 alvo.
O refinamento usa a mesma amostra empregada na avaliação e, portanto, favorece o F1;
essa limitação deve ser reportada no artigo.

## Regras registradas

### v1

- Patch SemVer: mesma versão major/minor e patch crescente.
- Texto dos commits: tokens completos `fix`, `hotfix` ou `revert`, sem diferença de caixa.
- Combinação: release corretiva quando ao menos um dos critérios for verdadeiro.
- Política não-SemVer: fallback textual.

## Resultados

Este histórico pertence à amostra-ouro obtida no piloto de 100 repositórios.
O F1 abaixo não certifica a população definitiva da S02 nem a independência dos
rótulos C, cuja autoria Lorran informou não ser sua. O fechamento definitivo usa
`data/amostra_ouro_s02/heuristica_metricas.csv`, mantém cada versão e recalcula o
dataset. Os resultados anteriores são preservados, não promovidos automaticamente.

Os resultados abaixo usam `data/amostra_ouro/consenso_releases.csv`. Para a v1,
19.836 assuntos de commits foram recuperados dos patches públicos de 294 das 300
comparações; cinco releases não tinham `compare_url` e uma comparação retornou erro HTTP.
Como a v1 já superou a meta de F1, não houve refinamento posterior.

<!-- resultados:start -->
| Versão | Precisão | Recall | F1 | Suporte | TP | FP | FN | TN |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| v1 | 0.589 | 0.906 | 0.714 | 160 | 145 | 101 | 15 | 39 |
<!-- resultados:end -->
