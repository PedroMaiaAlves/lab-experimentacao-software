# Kata 01 — Consolidar Janelas

Implemente a função:

```python
consolidar_janelas(janelas, tolerancia=0)
```

Uma janela é representada por um par `(inicio, fim)`, com `inicio <= fim`.
A função deve ordenar e consolidar janelas que:

- se sobreponham;
- sejam adjacentes; ou
- estejam separadas por uma distância menor ou igual a `tolerancia`.

O retorno deve ser uma nova lista de tuplas ordenada pelo início. A entrada não
pode ser modificada.

## Exemplos

```python
consolidar_janelas([(8, 9), (1, 2)])
# [(1, 2), (8, 9)]

consolidar_janelas([(1, 5), (3, 7), (10, 11)])
# [(1, 7), (10, 11)]

consolidar_janelas([(1, 2), (4, 6), (9, 10)], tolerancia=2)
# [(1, 6), (9, 10)]
```

## Regras de validação

- `tolerancia` negativa deve gerar `ValueError`.
- Uma janela com `inicio > fim` deve gerar `ValueError`.
- A lista vazia deve retornar uma lista vazia.
- Intervalos pontuais, como `(5, 5)`, são válidos.

## Execução dos testes

Prepare o [ambiente CPython 3.11.16](../../docs/ambiente.md) e siga o
[roteiro de execução](../../docs/execucao_sprint02.md). A ferramenta de trials
criará seu arquivo de trabalho em `Lab02/trials/PARTICIPANTE/kata01/solution.py`.
Não escreva a solução neste diretório nem altere o stub ou os testes.

Depois de iniciar o trial pelo roteiro, verifique sua solução a partir da
raiz do repositório, substituindo `PARTICIPANTE` e `TOTAL`:

```text
.\Lab02\.venv\Scripts\python.exe Lab02/tools/trial.py check PARTICIPANTE kata01 --prompts TOTAL
```

Use a contagem acumulada de prompts (zero no manual). `check` pode finalizar
o trial no primeiro verde ou após 35 minutos. Preserve a solução ao encerrar.
