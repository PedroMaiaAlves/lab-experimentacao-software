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

O arquivo de trabalho oficial será criado pela ferramenta de trials. Para uma
verificação local fora dos trials, copie `stub.py` para um arquivo temporário
chamado `solution.py` no mesmo diretório e execute:

```text
python -m unittest Lab02/katas/kata01/acceptance.py
```

Não coloque uma solução de referência neste diretório antes do fim do
experimento.
