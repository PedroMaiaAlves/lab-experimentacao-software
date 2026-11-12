# Evidências de Pedro — Lab04S02, Q1 e G3

## Escopo

Esta entrega implementa a infraestrutura Monte Carlo compartilhada, responde à
Q1 sobre erro tipo I e integra o G3 ao dashboard. Também recupera G1 e o dashboard
da Sprint 1, que não estavam presentes na `main` antes da Sprint 2.

Issues: [#184](https://github.com/PedroMaiaAlves/lab-experimentacao-software/issues/184)
e [#185](https://github.com/PedroMaiaAlves/lab-experimentacao-software/issues/185).

## Configuração de Q1

- Distribuição das diferenças: normal com média zero.
- Desvio calibrado: `0.18309179292385067` na escala logarítmica.
- Tamanhos: 10, 20, 30, 50 e 100 pares.
- Repetições: 10.000 por tamanho.
- Testes: t pareado e Wilcoxon pareado, bicaudais, `alpha = 0,05`.
- Semente-base: 42, com fluxos derivados independentes por configuração.
- Incerteza: intervalo de Wilson de 95% para cada taxa de rejeição.

As taxas observadas ficaram entre 4,72% e 5,27%. Os dez intervalos de Wilson
incluem 5%, portanto os resultados são compatíveis com o nível nominal dentro
da incerteza de Monte Carlo desta execução. Isso não prova controle universal
fora do cenário normal simulado.

## Reproduzir

```powershell
.\Lab04\.venv\Scripts\python.exe Lab04/simular_s02.py
.\Lab04\.venv\Scripts\python.exe Lab04/simular_s02.py --validar
.\Lab04\.venv\Scripts\python.exe -m pytest -c Lab04/pytest.ini Lab04/tests -q
.\Lab04\.venv\Scripts\python.exe -m streamlit run Lab04/app.py
```

`data/s02/q1_resultados.csv` contém somente resultados agregados. O manifesto
registra configuração, versões, hashes da calibração, código e CSV.

## Contrato para Q2 e Q3

`simular_grade` recebe distribuição, tamanhos, deltas logarítmicos, quantidade de
repetições, alpha, semente e desvio calibrado. O retorno mantém uma linha por
teste e configuração com contagens, taxa de rejeição e intervalo de Wilson.

Q2 deve usar `distribuicao="normal"`, 30 pares e os efeitos definidos na issue
#186. Q3 deve usar `distribuicao="t3"` com a mesma grade. Nenhuma dessas respostas
foi antecipada nesta entrega.
