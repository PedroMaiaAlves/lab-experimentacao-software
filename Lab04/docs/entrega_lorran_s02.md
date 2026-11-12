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
- PR #191 consta como mesclada, mas `app.py`, G1, G3 e seus testes não estão
  na main consultada. Sua implementação válida será reaproveitada de `28d571d`.
- Implementação e validações de Q3/G4 ainda pendentes neste commit de planejamento.
