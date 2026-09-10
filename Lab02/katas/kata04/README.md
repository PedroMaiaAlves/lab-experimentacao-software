# Kata 04 — Distribuir Cotas

Implemente a função:

```python
distribuir_cotas(demandas, estoque)
```

`demandas` é um dicionário que associa identificadores a quantidades inteiras
não negativas. Cada identificador deve ser uma string não vazia. `estoque` é
uma quantidade inteira não negativa.

A função deve distribuir `min(estoque, soma das demandas)` unidades de forma
proporcional às demandas. Primeiro, atribua a parte inteira da cota ideal de
cada identificador. Distribua as unidades restantes em ordem decrescente da
parte fracionária, conforme o método dos maiores restos. Partes fracionárias
iguais são desempatadas pela ordem alfabética dos identificadores.

Nenhuma cota pode ultrapassar a demanda correspondente. Se o estoque exceder
a demanda total, a sobra não é distribuída. O retorno deve ser um novo
dicionário com todos os identificadores em ordem alfabética, e a entrada não
pode ser modificada.

## Exemplos

```python
distribuir_cotas({"norte": 2, "sul": 6}, 4)
# {"norte": 1, "sul": 3}

distribuir_cotas({"ana": 1, "bia": 1, "caio": 1}, 2)
# {"ana": 1, "bia": 1, "caio": 0}

distribuir_cotas({"norte": 2, "sul": 0}, 5)
# {"norte": 2, "sul": 0}
```

## Regras de validação

- `estoque` deve ser um inteiro não negativo e não pode ser booleano.
- Cada demanda deve ser um inteiro não negativo e não pode ser booleana.
- Cada identificador deve ser uma string com ao menos um caractere não vazio.
- Uma demanda igual a zero é válida.
- Um dicionário vazio deve retornar um dicionário vazio.
- Dados inválidos devem gerar `ValueError`.

## Execução dos testes

O arquivo de trabalho oficial será criado pela ferramenta de trials. Para uma
verificação local fora dos trials, copie `stub.py` para um arquivo temporário
chamado `solution.py` no mesmo diretório e execute:

```text
python -m unittest Lab02/katas/kata04/acceptance.py
```

Não coloque uma solução de referência neste diretório antes do fim do
experimento.
