# Lab04 — P1: estrutura e coleta pareada

Entrega de Pedro vinculada à [issue #173](https://github.com/PedroMaiaAlves/lab-experimentacao-software/issues/173).
O cenário compara a compilação de bytecode do Django 5.2.8 com cache vazio e
preenchido, para o par t pareado × Wilcoxon pareado da Lab04S01.

Esta etapa entrega o coletor, **30 pares reais**, três pares de aquecimento
separados, logs, origem e hashes. A simulação é a etapa P2, vinculada à #174;
testes estatísticos/G2 ficam com Diogo e dashboard/G1/integração com Lorran.

## Ambiente e conferência

Na raiz do repositório, em PowerShell:

```powershell
py -3.13 -m venv Lab04/.venv
.\Lab04\.venv\Scripts\python.exe -m pip install -r Lab04/requirements.lock.txt
.\Lab04\.venv\Scripts\python.exe Lab04/validar.py
.\Lab04\.venv\Scripts\python.exe -m pytest -c Lab04/pytest.ini Lab04/tests -q
```

A coleta oficial usa CPython 3.13.5. A validação usa os dados preservados e
funciona offline; não executa uma nova coleta. Ambiente, fontes extraídos e
caches estão ignorados pelo Git. Os bytes dos dados são preservados pelos
atributos Git para manter os hashes após checkout.

## Nova coleta

Somente para realizar outra sessão, preservando a original:

```powershell
.\Lab04\.venv\Scripts\python.exe Lab04/coletar.py --saida Lab04/data/nova_sessao
```

O destino deve ser novo. A fonte oficial é verificada por SHA-256. Cache vazio
e preenchido são preparados fora da medição; falhas técnicas repetem o par
inteiro e são preservadas em log. Novas medições terão tempos diferentes.

## Documentação e dados

- [Divisão das tarefas e critérios de aceite de cada integrante](docs/issues_s01.md).
- [Protocolo de coleta e limitações](docs/protocolo_coleta.md).
- [Cenário e expectativa registrados antes da simulação](docs/cenario.md).
- `data/real/pares_reais.csv`: os 30 pares oficiais.
- `data/real/aquecimento.csv`: três pares excluídos da análise.
- `data/real/medicoes.jsonl` e `falhas.jsonl`: evidências individuais.
- `data/real/arquivos_fonte.csv` e `manifesto.json`: fonte, ambiente, comando e hashes.

O registro prévio do manifesto é o snapshot da preparação local completa;
também registra hashes de módulos da etapa P2, que serão publicados na branch
da #174. Não reescrever esse histórico para simular uma coleta posterior aos commits.

O dashboard Streamlit e a comparação dos testes ainda não estão implementados.
Esta branch é a base da entrega P2; integrar primeiro a PR da #173 e depois a da #174.
