# Sprint 02 — roteiro passo a passo

Este roteiro é para as **12 execuções reais**, depois da preparação. Não use
`start` para testar a instalação. A validação técnica usa `validate` e
`unittest`, conforme [ambiente.md](ambiente.md).

## 1. Antes de qualquer medição

- Conferir o [estado da liberação](../README.md#confirmações-para-a-baseline):
  os três ambientes e as três contas devem estar confirmados.
- Confirmar que a preparação foi integrada e que a tag
  `lab02-s02-baseline` foi publicada. A tag é uma versão inicial salva,
  igual para todos.
- Criar as 12 Issues manualmente. O gerador abaixo apenas mostra títulos,
  responsáveis e corpos; não publica nada:

```powershell
.\Lab02\.venv\Scripts\python.exe Lab02/tools/create_issues.py
```

Usar milestone `LAB02 — Sprint 02`, iteration `Sprint 02`, labels
`lab02`, `sprint-02` e `ia` ou `manual`, com o participante como responsável.
Cada pessoa mantém somente uma Issue em andamento. Exemplo de título:

```text
[Lab02S02][Pedro][01] Consolidar Janelas — IA
```

Cada participante escolhe seus horários e segue a ordem abaixo. Reservar até
35 minutos por trial, mais o registro dos commits, e pelo menos 10 minutos
de pausa entre trials feitos no mesmo dia.

| Ordem | Pedro (`pedro`) | Diogo (`diogo`) | Lorran (`lorran`) |
| --- | --- | --- | --- |
| 1 | kata01 — IA | kata02 — Manual | kata03 — Manual |
| 2 | kata02 — Manual | kata03 — IA | kata04 — IA |
| 3 | kata03 — IA | kata04 — IA | kata01 — Manual |
| 4 | kata04 — Manual | kata01 — Manual | kata02 — IA |

Há quatro exercícios, e cada pessoa resolve os quatro uma única vez. A
condição vem do protocolo, não do nome da branch nem de uma escolha no dia.

## 2. Abrir o terminal e preparar a branch

Abra o repositório no VS Code, selecione **Terminal → Novo Terminal** e use
PowerShell. Todos os comandos deste roteiro partem da raiz do repositório.

Depois da liberação da baseline:

```powershell
git switch main
git pull --ff-only
git fetch origin --tags
git status --short
git rev-parse 'lab02-s02-baseline^{commit}'
.\Lab02\.venv\Scripts\python.exe --version
```

Pare se houver erro. `git status --short` deve ficar sem saída, a tag deve
mostrar um hash e o Python deve ser `3.11.16`. Não descarte alterações
pendentes para continuar. Se a tag não existir, a preparação ainda não foi liberada.

O exemplo a seguir é **Pedro / Kata 01 / IA**. Nos próximos trials, altere os
três valores conforme a matriz; mantenha o mesmo terminal até terminar:

```powershell
$trialParticipant = 'pedro'
$trialKata = 'kata01'
$trialTreatment = 'ia'
$trialIssue = [int](Read-Host 'Numero real da Issue deste trial, sem #')
$trialBranch = "lab02-s02/$trialParticipant-$trialKata-$trialTreatment"
git switch -c $trialBranch lab02-s02-baseline
```

Digite o número fornecido pelo GitHub, e não um número de exemplo. Cada branch
nasce diretamente da baseline; não use a branch da solução anterior. Não use
`--force` para repetir um trial ou sobrescrever uma solução existente.

Mova a Issue para **In Progress**.

## 3. Preparar os recursos antes de iniciar o relógio

- **IA:** abrir uma conversa nova ou temporária no ChatGPT previsto no protocolo,
  com memória e instruções personalizadas desativadas. Desabilitar outros
  assistentes. Não usar esta conversa de preparação como conversa do trial.
- **Manual:** fechar chats de IA e desabilitar Copilot, Codex e outros assistentes
  ou sugestões de IA no editor e navegador.
- Deixar terminal, editor e alarme externo preparados. O ambiente e os pacotes
  já devem estar instalados.
- Não consultar soluções dos colegas, referências antigas ou commits que
  contenham respostas. Não começar a resolver ou enviar o enunciado à IA
  antes de iniciar a medição.

Pesquisa convencional na web é permitida nas duas condições. Anotar as URLs;
não usar respostas geradas por outras IAs. A leitura para resolução, a
programação, as mensagens ao assistente e os testes contam no tempo.

## 4. Iniciar a execução

```powershell
.\Lab02\.venv\Scripts\python.exe Lab02/tools/trial.py start $trialParticipant $trialKata --issue $trialIssue
```

Só quando aparecer **TRIAL INICIADO**, ativar imediatamente o alarme de
35 minutos. O terminal mostra o início e o prazo final em UTC.

O programa cria um arquivo de trabalho a partir do stub. Para Pedro/Kata 01:

- Enunciado: [`../katas/kata01/README.md`](../katas/kata01/README.md).
- Arquivo que será editado: `Lab02/trials/pedro/kata01/solution.py`.

Para outra combinação, siga os caminhos **Especificação** e **Solução** que o
comando imprimir. Os outros enunciados são [Kata 02](../katas/kata02/README.md),
[Kata 03](../katas/kata03/README.md) e [Kata 04](../katas/kata04/README.md).

Edite somente o `solution.py` do seu trial. Preserve assinatura da função,
enunciado, stub original, testes, ferramentas e protocolo. Salve com **Ctrl+S**
antes de verificar.

## 5. Programar na condição indicada

### Se o trial for com IA

Você pode enviar o enunciado completo ao assistente. Exemplo de pedido,
a ser usado somente depois do início da medição:

```text
Implemente a função Python descrita neste enunciado.
Respeite a assinatura, as regras, as validações e o formato de retorno.

[cole aqui o enunciado completo]
```

A primeira mensagem conta como um prompt. Cada nova mensagem enviada,
inclusive pedidos de explicação ou correção, acrescenta um. Registre as
mensagens da conversa para conferir a contagem ao final.

Copie ou adapte a resposta no seu `solution.py`. A solução que vale é a salva
nesse arquivo, não a que ficou apenas na conversa.

### Se o trial for manual

Escreva a solução por conta própria, sem consultas a assistentes de IA.
A contagem de prompts é zero. Use os mesmos testes e o mesmo limite de tempo.

## 6. Verificar os testes durante o trabalho

No tratamento IA, antes de cada verificação, informe o total acumulado:

```powershell
$trialPrompts = [int](Read-Host 'Total de mensagens ja enviadas a IA neste trial')
.\Lab02\.venv\Scripts\python.exe Lab02/tools/trial.py check $trialParticipant $trialKata --prompts $trialPrompts
```

No tratamento manual:

```powershell
$trialPrompts = 0
.\Lab02\.venv\Scripts\python.exe Lab02/tools/trial.py check $trialParticipant $trialKata --prompts $trialPrompts
```

- Se aparecer **Trial ainda vermelho**, leia as falhas, continue trabalhando,
  salve e repita a verificação. A saída com falhas é esperada nesse caso.
- Se aparecer **TRIAL FINALIZADO: verde**, todos os testes passaram e o CSV
  já foi gravado. Pare de editar e vá ao registro do commit.
- Se aparecer **TRIAL FINALIZADO: censurado**, o prazo acabou. Pare de editar
  e vá ao registro do commit.

Informe a contagem correta em **todo** `check`, pois ele pode encerrar a
medição. Não execute os testes de aceitação por outro comando durante o trial:
use `check` para que o primeiro verde seja registrado pela ferramenta.

## 7. Encerrar quando o alarme tocar

Se o trial ainda estiver ativo, pare de editar ao atingir 35 minutos.
Use o último código salvo, informe a contagem final de prompts (zero no
manual) e execute imediatamente:

```powershell
$trialPrompts = [int](Read-Host 'Total final de prompts; use 0 no manual')
.\Lab02\.venv\Scripts\python.exe Lab02/tools/trial.py finish $trialParticipant $trialKata --prompts $trialPrompts
```

A ferramenta não tem processo de contagem em segundo plano. Ela só verifica
o prazo quando você chama `check` ou `finish`; o alarme externo é necessário.
Um trial vermelho antes do prazo permanece ativo mesmo ao chamar `finish`.

Se `check` já finalizou, não chame `finish` novamente. O resultado censurado
é válido: dura 2.100 segundos, fica sem Time-to-Green e preserva a solução
incompleta. Não continue corrigindo nem refazendo a tentativa.

Interrupções, limites da IA ou falhas técnicas devem ser registrados na
Issue; o relógio não é pausado. Não repita silenciosamente uma execução para
melhorar o resultado. Se uma falha técnica impedir o encerramento, preserve
arquivos e estado e solicite suporte registrando a ocorrência.

## 8. Fazer o primeiro commit: solução e resultado

Somente depois de aparecer **TRIAL FINALIZADO**, executar:

```powershell
git add -- "Lab02/trials/$trialParticipant/$trialKata/solution.py" Lab02/results/trials.csv
git commit -m "feat(lab02): registra trial $trialParticipant $trialKata $trialTreatment #$trialIssue"
```

O primeiro commit contém a solução medida e a primeira versão do resultado,
ainda com `commit_sha=PENDING`. O tempo de Git fica fora da medição.

## 9. Vincular o commit e fazer o segundo commit

```powershell
.\Lab02\.venv\Scripts\python.exe Lab02/tools/trial.py link-commit $trialParticipant $trialKata --commit HEAD
```

Copie o hash informado: ele identifica o commit que contém a solução.
Depois salve a atualização do CSV:

```powershell
git add -- Lab02/results/trials.csv
git commit -m "docs(lab02): vincula commit do trial $trialParticipant $trialKata #$trialIssue"
git status --short
```

O último comando deve ficar sem saída. São dois commits porque o hash do
primeiro só existe depois de criá-lo. Não tente alterar o primeiro commit
para incluir seu próprio hash.

## 10. Preencher a Issue e seguir para o próximo trial

Registrar na Issue:

```text
Branch:
Commit da solução (informado por link-commit):
Início UTC:
Fim UTC:
Resultado: verde ou censurado
Total de prompts:
URLs consultadas:
Problemas ou interrupções:
```

Anexar a saída final dos testes e guardar as mensagens usadas no tratamento
IA. Mover o cartão para **In Review**. Não preencher tempos de memória nem
inventar métricas ausentes.

Manter os commits locais até os três concluírem seus quatro trials. Cada
próximo trial começa da baseline, em uma nova branch, seguindo a matriz.
O anterior deve estar encerrado e commitado antes da troca.

Se fechar o terminal, redefina as variáveis para a combinação correta antes
de executar comandos. Não use novamente `start` em um trial já iniciado.
O estado local não vai para o Git: conclua cada trial na mesma máquina e pasta.

## 11. Publicar e revisar depois das 12 execuções

Quando todos tiverem terminado, cada participante publica suas quatro branches.
Para Pedro:

```powershell
git push -u origin lab02-s02/pedro-kata01-ia
git push -u origin lab02-s02/pedro-kata02-manual
git push -u origin lab02-s02/pedro-kata03-ia
git push -u origin lab02-s02/pedro-kata04-manual
```

Criar PRs com as evidências. Pedro revisa Diogo; Diogo revisa Lorran; Lorran
revisa Pedro. A revisão confere protocolo e evidências, sem corrigir o código
medido ou trocar resultados incompletos por soluções melhores.

Pedro reúne as branches numa branch de consolidação. Como todas saem da
baseline, podem ocorrer conflitos no CSV: preservar cada linha, identificada
por **participante + kata**, em vez de escolher um arquivo inteiro e perder
as linhas dos outros. Os hashes devem continuar apontando para os commits
originais das soluções.

Diogo confere métricas e tempos; Lorran confere Issues e vínculos. A entrega
deve ter 12 combinações únicas, quatro por pessoa, seis IA e seis manuais,
sem `PENDING` e com os censurados preservados. A análise estatística será
realizada na Sprint 03.
