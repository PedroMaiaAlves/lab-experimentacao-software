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

Prepare o [ambiente CPython 3.11.16](../../docs/ambiente.md) e siga o
[roteiro de execução](../../docs/execucao_sprint02.md). A ferramenta de trials
criará seu arquivo de trabalho em `Lab02/trials/PARTICIPANTE/kata04/solution.py`.
Não escreva a solução neste diretório nem altere o stub ou os testes.

Depois de iniciar o trial pelo roteiro, verifique sua solução a partir da
raiz do repositório, substituindo `PARTICIPANTE` e `TOTAL`:

```text
.\Lab02\.venv\Scripts\python.exe Lab02/tools/trial.py check PARTICIPANTE kata04 --prompts TOTAL
```

Use a contagem acumulada de prompts (zero no manual). `check` pode finalizar
o trial no primeiro verde ou após 35 minutos. Preserve a solução ao encerrar.
