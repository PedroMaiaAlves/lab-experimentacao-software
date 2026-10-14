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

Os resultados serão inseridos somente depois que `consenso.csv` for produzido por A3.

<!-- resultados:start -->
| Versão | Precisão | Recall | F1 | Suporte | TP | FP | FN | TN |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| v1 | pendente | pendente | pendente | pendente | pendente | pendente | pendente | pendente |
<!-- resultados:end -->
