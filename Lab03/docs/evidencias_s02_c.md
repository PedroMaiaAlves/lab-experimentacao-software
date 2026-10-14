# Evidências da implementação de C — 14/10/2026

Base: `main@fdfac27`. Implementação de C na branch
`codex/lab03-s02-lorran-parte-c`; sem alterações nos coletores, cálculos ou
rótulos de A/B. A integração do artigo acrescenta apenas a subseção de C.

## Testes offline

Ambiente local: Python 3.12.14, pytest 9.1.1 e pytest-cov 7.1.0.

```bash
python -m pytest --cov=metricas --cov-report=term-missing --cov-fail-under=80 -p no:cacheprovider
```

Resultado: 223 testes passaram, com cobertura de 95,45% em `metricas`.
O teste integrado usa 300 repositórios **simulados** e percorre os coletores
existentes, o congelamento, a consolidação e o recálculo offline da heurística.
Não é evidência de coleta real dos 300. Há testes para concorrência, retomada,
integridade dos hashes, 404, propagação de erros transitórios, ausentes e censura.

## Piloto real

Fonte: `dtcooper/raspotify`, API pública do GitHub, janela confirmada de
01/10/2025 a 30/09/2026. Arquivos do piloto preservados localmente em
`cache/s02_piloto/`, sem tokens e fora do Git.

- 116 releases históricas; 5 comparações principais na janela, sem erro 404.
- 139 tags e 45 relações release/commit.
- 56 workflow runs, coleta marcada como completa, sem intervalo saturado.

O piloto comprova a integração real das três etapas para um repositório,
não o término da coleta completa. As respostas aproveitáveis permanecem no cache.

## Execução completa e pendências

A coleta real está em execução separada da S01, com checkpoint em
`data/s02/checkpoint.json` e log em `cache/s02/retomada.stderr.log`. Os contadores
de andamento não são resultados finais; consulte o checkpoint atual.

C1 somente fecha depois de validar e congelar pelo menos 300 repositórios.
C2 e os números de C4 dependem desse congelamento. A rotulagem C não foi
preenchida por IA: faltam confirmar a autoria do arquivo já existente e alinhar
com A a amostra-ouro posterior ao congelamento. Não foram alterados rótulos,
consensos ou resultados de validação dos colegas.
