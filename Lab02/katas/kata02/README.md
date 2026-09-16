# Kata 02 — Planejar Recargas

Implemente a função:

```python
planejar_recargas(consumos, capacidade)
```

`consumos` é uma lista de números não negativos representando o consumo em
cada etapa de um percurso. `capacidade` é a capacidade máxima do reservatório,
que começa cheio.

A função deve retornar os **índices** (posições na lista `consumos`, base 0)
em que uma recarga precisa acontecer **antes** do consumo daquela etapa, para
que o reservatório nunca fique negativo. Cada recarga restaura a capacidade
ao valor total (`capacidade`).

O retorno deve ser uma nova lista de índices em ordem crescente. A entrada
não pode ser modificada.

## Exemplos

```python
planejar_recargas([1, 1, 1], 5)
# []  -> a capacidade inicial cobre todo o percurso, nenhuma recarga necessária

planejar_recargas([2, 2, 2], 5)
# [2]  -> restam 5-2-2=1 antes da 3ª etapa; como 2 > 1, recarrega antes do índice 2

planejar_recargas([3, 1, 3], 5)
# [2]  -> restam 5-3-1=1 antes da 3ª etapa; como 3 > 1, recarrega antes do índice 2

planejar_recargas([0, 0, 0], 1)
# []  -> consumo zero nunca exige recarga

planejar_recargas([5], 5)
# []  -> consumo exatamente igual à capacidade total é permitido sem recarga
```

## Regras de validação

- `capacidade` deve ser um número positivo; caso contrário, gerar `ValueError`.
- Qualquer valor em `consumos` menor que zero deve gerar `ValueError`.
- Qualquer valor em `consumos` maior que `capacidade` deve gerar `ValueError`
  (nenhuma recarga é suficiente para cobrir uma única etapa que exceda a
  capacidade máxima).
- Consumo igual a zero é permitido e nunca exige recarga.
- Uma lista vazia de consumos deve retornar uma lista vazia de índices.

## Execução dos testes

Prepare o [ambiente CPython 3.11.16](../../docs/ambiente.md) e siga o
[roteiro de execução](../../docs/execucao_sprint02.md). A ferramenta de trials
criará seu arquivo de trabalho em `Lab02/trials/PARTICIPANTE/kata02/solution.py`.
Não escreva a solução neste diretório nem altere o stub ou os testes.

Depois de iniciar o trial pelo roteiro, verifique sua solução a partir da
raiz do repositório, substituindo `PARTICIPANTE` e `TOTAL`:

```text
.\Lab02\.venv\Scripts\python.exe Lab02/tools/trial.py check PARTICIPANTE kata02 --prompts TOTAL
```

Use a contagem acumulada de prompts (zero no manual). `check` pode finalizar
o trial no primeiro verde ou após 35 minutos. Preserve a solução ao encerrar.
