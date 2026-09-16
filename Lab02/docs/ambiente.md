# Ambiente reproduzível — LAB02

Todos os participantes devem executar o experimento com **CPython 3.11.16**
e as versões fixadas em [`../requirements.txt`](../requirements.txt):

| Pacote | Versão | Uso |
| --- | --- | --- |
| radon | 6.0.1 | Métricas estáticas |
| colorama | 0.4.6 | Dependência do Radon |
| mando | 0.7.1 | Dependência do Radon |
| six | 1.17.0 | Dependência do Mando |

O ambiente do experimento fica em **`Lab02/.venv`**. O `.venv` da raiz e o
Python instalado no computador são independentes e não devem ser substituídos.
Os testes usam `unittest`, incluído no Python; não é necessário instalar pytest.

## 1. Instalação no Windows (PowerShell)

Abra o terminal **na raiz do repositório**. É necessário Git e um Python
existente com pip apenas para obter a ferramenta de instalação. Este Python
inicial pode ser 3.13; os trials serão executados pelo Python 3.11.16 isolado.

Execute os blocos em ordem e só prossiga quando o anterior terminar sem erro.

### Instalar o uv localmente

```powershell
python -m pip install --disable-pip-version-check --target Lab02/.tools uv==0.12.15
.\Lab02\.tools\bin\uv.exe --version
```

Se `python` não estiver no PATH, use o caminho do Python existente. No computador
de Pedro, também pode ser usado `.\.venv\Scripts\python.exe -m pip` para
esse primeiro comando. `--target` grava o uv em `Lab02/.tools`; não instala
pacotes no ambiente da raiz. Se a ferramenta local já informar `uv 0.12.15`,
não é necessário reinstalá-la.

### Baixar o Python do experimento

```powershell
.\Lab02\.tools\bin\uv.exe python install 3.11.16 --install-dir Lab02/.python --no-bin --no-registry --cache-dir Lab02/.uv-cache
$env:UV_PYTHON_INSTALL_DIR = Join-Path (Get-Location).Path 'Lab02/.python'
```

O download fica em `Lab02/.python`, sem alterar o PATH nem o registro do Windows.
O uv utiliza as distribuições do projeto `python-build-standalone` da Astral.
Referências: [Python 3.11.16](https://www.python.org/downloads/release/python-31116/)
e [instalação de Python com uv](https://docs.astral.sh/uv/guides/install-python/).

### Criar o ambiente exclusivo

```powershell
.\Lab02\.tools\bin\uv.exe venv --python 3.11.16 --managed-python --no-python-downloads --cache-dir Lab02/.uv-cache Lab02/.venv
```

Esse passo é para a primeira instalação. Se `Lab02/.venv` já existir, confira
sua versão antes de continuar; não o apague nem o recrie durante um trial.

### Instalar as dependências fixadas

```powershell
.\Lab02\.tools\bin\uv.exe pip sync --python Lab02/.venv/Scripts/python.exe --cache-dir Lab02/.uv-cache Lab02/requirements.txt
```

`sync` torna **somente o ambiente `Lab02/.venv`** igual à lista fixada. Não use
esse comando com o Python da raiz ou do sistema. Faça a instalação antes das
medições e não altere pacotes durante os trials.

## 2. Conferência que cada participante deve executar

```powershell
.\Lab02\.venv\Scripts\python.exe --version
.\Lab02\.tools\bin\uv.exe pip freeze --python Lab02/.venv/Scripts/python.exe --cache-dir Lab02/.uv-cache
.\Lab02\.tools\bin\uv.exe pip check --python Lab02/.venv/Scripts/python.exe --cache-dir Lab02/.uv-cache
.\Lab02\.venv\Scripts\python.exe -m unittest discover -s Lab02/tests -v -b
.\Lab02\.venv\Scripts\python.exe Lab02/tools/trial.py validate
```

O esperado é Python **3.11.16**, os quatro pacotes nas versões da tabela,
dependências compatíveis, suíte de testes com `OK` e validação do protocolo
com 3 participantes, 12 trials, 6 IA e 6 manuais. A opção `-b` oculta a saída
das simulações quando o teste passa, evitando confundir falhas esperadas de
stubs com falhas da suíte.

Os testes automatizados usam exercícios sintéticos e diretórios temporários.
Eles também verificam que os quatro stubs reais falham nos oito testes de
aceitação de cada kata. Isso não inicia trials oficiais nem preenche seu CSV.

Cada participante deve anexar à PR de preparação a saída dos comandos acima:

```text
Participante:
Sistema operacional:
Commit testado:
Python:
Pacotes:
Resultado de unittest:
Resultado de validate:
Data da conferência:
```

A confirmação no computador de Pedro não comprova os ambientes dos colegas.
O estado das confirmações fica no [README](../README.md#confirmações-para-a-baseline).

## 3. Editor e comandos dos trials

No VS Code, selecione **Python: Select Interpreter** e indique
`Lab02/.venv/Scripts/python.exe`. Os comandos abaixo usam o caminho completo
relativo à raiz e dispensam ativar o ambiente no PowerShell.

Os identificadores `PARTICIPANTE`, `KATA`, `NUMERO`, `TOTAL` e `HASH` são
marcadores: substitua-os pelos valores do trial. Não execute `start` apenas
para experimentar a instalação.

```text
.\Lab02\.venv\Scripts\python.exe Lab02/tools/trial.py start PARTICIPANTE KATA --issue NUMERO
.\Lab02\.venv\Scripts\python.exe Lab02/tools/trial.py check PARTICIPANTE KATA --prompts TOTAL
.\Lab02\.venv\Scripts\python.exe Lab02/tools/trial.py finish PARTICIPANTE KATA --prompts TOTAL
.\Lab02\.venv\Scripts\python.exe Lab02/tools/trial.py link-commit PARTICIPANTE KATA --commit HASH
```

Use `0` prompts no tratamento manual. No tratamento IA, informe o total
acumulado em cada `check`: ele pode finalizar o trial no primeiro verde.
O comando `finish` não encerra um trial vermelho antes de 35 minutos.
Não existem o subcomando público `conclude` nem as opções `--participant`
e `--kata`. A função interna `conclude` não é um comando de terminal.

Siga o [roteiro completo da Sprint 02](execucao_sprint02.md) para iniciar,
editar, encerrar e vincular o commit. Use alarme externo: a ferramenta
não fica executando em segundo plano.

Para inspecionar métricas de uma solução já encerrada:

```text
.\Lab02\.venv\Scripts\python.exe Lab02/tools/metrics.py CAMINHO_DA_SOLUCAO
```

## 4. Linux e macOS

Use também uv 0.12.15 e Python 3.11.16, com os mesmos pacotes. Na raiz do
repositório, com uv instalado:

```bash
export UV_PYTHON_INSTALL_DIR="$PWD/Lab02/.python"
uv python install 3.11.16 --no-bin --cache-dir Lab02/.uv-cache
uv venv --python 3.11.16 --managed-python --no-python-downloads --cache-dir Lab02/.uv-cache Lab02/.venv
uv pip sync --python Lab02/.venv/bin/python --cache-dir Lab02/.uv-cache Lab02/requirements.txt
Lab02/.venv/bin/python --version
uv pip freeze --python Lab02/.venv/bin/python --cache-dir Lab02/.uv-cache
uv pip check --python Lab02/.venv/bin/python --cache-dir Lab02/.uv-cache
Lab02/.venv/bin/python -m unittest discover -s Lab02/tests -v -b
Lab02/.venv/bin/python Lab02/tools/trial.py validate
```

Nos demais comandos, troque `.\Lab02\.venv\Scripts\python.exe` por
`Lab02/.venv/bin/python`. Esta preparação foi validada localmente em Windows;
participantes em outro sistema devem registrar sua própria verificação.

## 5. O que não vai para o Git

`Lab02/.venv`, `.tools`, `.python`, `.uv-cache`, caches Python e
`results/.state` são ignorados pelo Git. A versão do Python, as dependências,
os comandos e as evidências devem ser versionados. Nenhuma confirmação de
modelo ou de outra máquina deve ser preenchida por suposição.
