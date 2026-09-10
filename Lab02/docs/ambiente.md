# Ambiente reproduzível — LAB02

Este documento descreve o ambiente utilizado para executar os trials, os
testes automatizados e a ferramenta de métricas do LAB02, permitindo que
qualquer integrante do grupo reproduza o setup em outra máquina.

## 1. Python

- Versão utilizada: **Python 3.11** (recomenda-se 3.10 ou superior).
- Verificar a versão instalada com:

  ```bash
  python --version
  ```

## 2. Sistema operacional

- Sistema utilizado: **Windows 10/11** (o procedimento também funciona em
  Linux/macOS, ajustando os comandos de ativação do ambiente virtual).

## 3. IDE

- IDE utilizada: **Visual Studio Code**, com a extensão oficial "Python"
  (ms-python.python) para execução e depuração dos testes.

## 4. Criação do ambiente virtual

No diretório raiz do repositório:

```bash
python -m venv .venv
```

Ativação:

- Windows (PowerShell):

  ```powershell
  .\.venv\Scripts\Activate.ps1
  ```

- Windows (cmd):

  ```cmd
  .\.venv\Scripts\activate.bat
  ```

- Linux/macOS:

  ```bash
  source .venv/bin/activate
  ```

## 5. Instalação de dependências

Com o ambiente virtual ativo:

```bash
pip install -r Lab02/requirements.txt
```

A única dependência externa é o **Radon**, usada em `tools/metrics.py` para
calcular complexidade ciclomática e índice de manutenibilidade.

## 6. Comandos de execução

### Rodar a suíte de testes automatizados

```bash
.\.venv\Scripts\python.exe -m pytest Lab02/tests -q -p no:cacheprovider
```

### Validar o pacote experimental

```bash
python Lab02/tools/trial.py validate
```

> Este comando só deve passar depois que todos os handoffs (ambiente,
> métricas, katas e validação) estiverem concluídos e integrados.

### Iniciar, concluir e vincular um trial

```bash
python Lab02/tools/trial.py start --participant <id> --kata <kataXX> --issue <numero>
python Lab02/tools/trial.py conclude --participant <id> --kata <kataXX> --prompts <n>
python Lab02/tools/trial.py link-commit --participant <id> --kata <kataXX> --commit HEAD
```

### Coletar métricas de um arquivo de solução

```bash
python -c "from Lab02.tools.metrics import collect; print(collect('caminho/para/solution.py'))"
```

## 7. Observações

- Não versionar o diretório `.venv/`.
- Manter `requirements.txt` atualizado sempre que uma nova dependência for
  introduzida por qualquer integrante.
- Qualquer divergência de versão do Python ou do Radon deve ser registrada
  neste arquivo antes da execução de trials oficiais.
