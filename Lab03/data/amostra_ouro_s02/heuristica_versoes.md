# Heurística na amostra definitiva da S02

Refinamento e avaliação na mesma amostra; não é teste de generalização.

<!-- resultados:start -->
| Versão | Precisão | Recall | F1 | Suporte | TP | FP | FN | TN |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| v1 | 0.314 | 0.920 | 0.468 | 87 | 80 | 175 | 7 | 38 |
| v2 | 0.701 | 0.782 | 0.739 | 87 | 68 | 29 | 19 | 184 |
| v3 | 0.708 | 0.782 | 0.743 | 87 | 68 | 28 | 19 | 185 |
<!-- resultados:end -->

## Histórico de Refinamento

### Versão v1 (Baseline)
- **Regra**: SemVer patch estrito ou presença das palavras-chave `fix`, `hotfix`, `revert` em qualquer mensagem de commit.
- **Diagnóstico de Erros (FP=175)**: Alto volume de falsos positivos decorrente de menções superficiais a "fix" em commits de documentação (`docs: fix typo`), infraestrutura/CI (`ci: fix build`), tarefas de rotina (`chore: fix lint`) e bumps de dependência, além de releases ricas em funcionalidades (`feat`) contendo apenas uma correção marginal.

### Versão v2 (Refinamento Pedro)
- **Mudanças principais**:
  1. Suporte a tags SemVer com prefixos de monorepo e namespace (ex.: `@scope/pkg@1.0.1`, `pkg-v1.0.1`).
  2. Filtragem de ruído de manutenção: desconsideração de commits iniciados por `chore`, `docs`, `ci`, `build`, `test`, `refactor` ou termos como `typo`, `readme`, `bump`, `deps`.
  3. Inclusão de termos explícitos de defeito crítico (`cve`, `vulnerability`, `panic`, `crash`, `leak`, `regression`, `bugfix`).
  4. Ponderação de foco funcional vs. corretivo: releases com novas funcionalidades (`feat`) só são consideradas corretivas caso haja predominância expressiva de correções de defeito ($\ge 3$ fixes e razão $\ge 2.5\times$ features).

### Versão v3 (correção técnica da v2)

- A v2 foi preservada, incluindo seus resultados e comportamento, para reprodução.
  Seu contador somava cada termo encontrado, podendo contar o mesmo commit mais
  de uma vez. A v3 conta no máximo uma contribuição corretiva por commit elegível.
- Mantém os filtros de manutenção, os termos de defeito e a análise do título do
  commit da v2. Com funcionalidades presentes, exige pelo menos três commits
  corretivos e razão de 2,5 por commit de funcionalidade; sem funcionalidades,
  exige pelo menos um commit corretivo. Os limites não foram ajustados após a revisão.
- Com texto ligado, patch sozinho não basta: precisa de correção textual e ausência
  de funcionalidades. Com `usar_palavras_commits: false`, não lê nem consome as
  mensagens e aplica somente o critério patch se habilitado. Tags não-SemVer sem
  texto não são positivas por suposição.
- Novos testes cobrem contagem única, limiares, quatro combinações de controles,
  mensagens inválidas e integração com dataset/coleta simulada. O manifesto da v3
  registra SHA-256 de `metricas/cfr.py`, além de regras e consenso.
  O código é normalizado para UTF-8/LF antes do hash, preservando reprodução
  entre Windows/Linux; dados e planilhas mantêm seus hashes de bytes originais.
- Mesmas avaliações, amostra, janela e consenso de v1/v2. VP=68, FP=28, FN=19,
  VN=185: precisão=0,708333, recall=0,781609, F1=0,743169. O refinamento continua
  avaliado na mesma amostra, não em dados independentes.
