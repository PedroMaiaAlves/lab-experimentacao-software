# Entrega de Diogo — Lab04S01, D1 + D2

## Escopo

- **D1 — #175:** `experimento/analise.py`, `analisar.py` e `tests/test_analise.py`.
- **D2 — #176:** `experimento/g2.py` e `tests/test_g2.py`.
- Dependências fixadas: `scipy==1.18.1` e `plotly==7.1.0` (requirements e lock).

PRs integradas: #181 (D2) e #182 (D1). A PR do D2 entrou antes da do D1; enquanto
isso, os testes do G2 usavam o SciPy direto como substituto de D1. A integração
posterior (este ajuste) faz o G2 consumir `analisar_pares` e mantém o SciPy direto
como referência independente. Os commits das PRs #181/#182 não citavam o número
da issue; o commit de integração referencia #175 e #176.

Integração no dashboard (Streamlit, seção 3) fica com Lorran (L2).

## Resultados na amostra simulada (P2, 30 pares, semente 42)

Dados **simulados**, não medições reais. Comando: `cd Lab04; .\.venv\Scripts\python.exe analisar.py`.

| Teste | Estatística | p-valor | Método | Decisão (alpha 0,05) |
| --- | --- | --- | --- | --- |
| t pareado | t = 47,53 (29 gl) | 4,60e-29 | t de Student sobre log-tempos | rejeitar H0 |
| Wilcoxon pareado | W = min(W+, W−) = 0 | 1,86e-09 | exato (sem empates nem zeros) | rejeitar H0 |

Hipóteses distintas: o t testa média zero de `log(sem) − log(com)`; o Wilcoxon
testa simetria dessas diferenças em torno de zero. O p-valor é calculado supondo
H0; não é a probabilidade de H0, e não rejeitar não provaria igualdade.

W = 0 significa que todas as 30 diferenças são positivas; o p-valor exato é
2 / 2^30. No t, o p-valor é tão pequeno que o G2 o mostra em escala log.

## Conferência numérica do G2

`figura_g2` recalcula a área (t) e a massa (Wilcoxon) destacadas e as compara com
o p-valor de D1 (`rtol=1e-6`), gerando erro se divergirem. Na amostra simulada:

| Teste | Área/massa no G2 | p-valor de D1 |
| --- | --- | --- |
| t pareado | 4,6040584252045335e-29 | 4,6040584252045335e-29 |
| Wilcoxon | 1,862645149230957e-09 | 1,862645149230957e-09 |

## Critérios de aceite

D1:

- [x] Mesma amostra simulada de P2, pares preservados (teste de quebra do pareamento).
- [x] t pareado sobre os logs; Wilcoxon sobre `log(sem) − log(com)`.
- [x] Bicaudais, alpha 0,05, hipóteses distintas por teste.
- [x] Comparação com SciPy direto e com exemplo calculado à mão.
- [x] Empates/zeros (aproximação normal explícita), diferenças constantes e todas
  zero (`None` com motivo), dados inválidos e alpha inválido (erro).
- [x] Método exato/aproximado informado.
- [x] Interpretação sem confundir p-valor com probabilidade de H0.

D2:

- [x] Distribuição sob H0 identificada em cada painel (t com n−1 gl; min(W+, W−) exata).
- [x] Região de rejeição (cinza) e p-valor (cor do teste) destacados separadamente.
- [x] Área/massa coincide com o p-valor de D1.
- [x] Caudas pequenas explicadas por ampliação em escala log e anotação, sem trocar a semente.
- [x] Título, eixos adimensionais, legenda; cores fixas t `#2563eb`, Wilcoxon `#ea580c`.
- [x] Empates/zeros: curva rotulada como aproximação, nunca como distribuição exata.
- [x] Texto de 2–4 frases (`texto_g2`).

Pendências do grupo: revisor de cada PR e cartões do Projects, que são atualizados no
GitHub, e exibição do G2 no Streamlit (L2).

## Verificação

```powershell
.\Lab04\.venv\Scripts\python.exe -m pytest -c Lab04/pytest.ini Lab04/tests -q
.\Lab04\.venv\Scripts\python.exe Lab04/validar.py
```

Resultado: 55 testes passando e `validar.py` com `status: ok` e `reproducao_exata: true`.
