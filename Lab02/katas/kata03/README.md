# Kata 03 — Agrupar Alertas

Implemente a função:

```python
agrupar_alertas(alertas, janela)
```

`alertas` é uma lista de dicionários. Cada alerta possui `instante`, um número
não negativo, e `categoria`, uma string não vazia. `janela` é um número não
negativo.

A função deve ordenar os alertas por instante dentro de cada categoria. Dois
alertas da mesma categoria pertencem ao mesmo grupo quando a diferença entre
seus instantes consecutivos é menor ou igual a `janela`. A regra é encadeada:
os instantes `1`, `4` e `7` formam um único grupo quando a janela é `3`.

O retorno deve ser uma nova lista de dicionários com as chaves `categoria`,
`inicio`, `fim` e `quantidade`. Os grupos devem ser ordenados por `inicio` e,
em caso de empate, por `categoria`. A entrada não pode ser modificada.

## Exemplo

```python
agrupar_alertas([
    {"instante": 8, "categoria": "rede"},
    {"instante": 1, "categoria": "cpu"},
    {"instante": 3, "categoria": "cpu"},
    {"instante": 5, "categoria": "rede"},
], 3)
# [
#     {"categoria": "cpu", "inicio": 1, "fim": 3, "quantidade": 2},
#     {"categoria": "rede", "inicio": 5, "fim": 8, "quantidade": 2},
# ]
```

## Regras de validação

- `janela` negativa deve gerar `ValueError`.
- Cada alerta deve ser um dicionário com `instante` e `categoria`.
- `instante` deve ser um número não negativo e não pode ser booleano.
- `categoria` deve ser uma string não vazia.
- Alertas no mesmo instante são válidos.
- A lista vazia deve retornar uma lista vazia.

## Execução dos testes

O arquivo de trabalho oficial será criado pela ferramenta de trials. Para uma
verificação local fora dos trials, copie `stub.py` para um arquivo temporário
chamado `solution.py` no mesmo diretório e execute:

```text
python -m unittest Lab02/katas/kata03/acceptance.py
```

Não coloque uma solução de referência neste diretório antes do fim do
experimento.
