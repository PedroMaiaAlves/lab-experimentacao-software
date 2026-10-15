# Guia de finalização da Sprint 2 — Diogo, Pedro e Lorran

Atualização: a classificação complementar e o importador já foram concluídos.
Este roteiro preserva as instruções usadas para executar a etapa, não uma lista
atual de pendências. Não recriem lotes nem repitam avaliações. O estado atual e a
separação de responsabilidades estão em `pendencias_manuais_s02.md`; o contrato
de reprodução está em `fechamento_s02.md`.

Estado conferido em 15/10/2026. Este guia parte do trabalho local já realizado.
Não refaçam as avaliações A/B/C nem iniciem uma nova coleta para seguir estes passos.

## 1. O que já está pronto e o que falta

Já temos coleta real de 300 repositórios, amostra congelada, três planilhas da
amostra-ouro preenchidas, consenso e validação da heurística v3 com F1 `0,743169`.
O último teste completo local teve 279 casos aprovados e 95,51% de cobertura em
`metricas`. O artigo parcial foi compilado e conferido.

Faltam, nesta ordem:

1. Classificar o tipo dos 240 projetos que estão fora da amostra-ouro.
2. Implementar a importação dessa classificação, com verificações e proveniência.
3. Recalcular dataset, estado e tabelas; testar e revisar os resultados.
4. Atualizar e recompilar o artigo com o estado final verdadeiro.
5. Publicar os arquivos revisados, conferir o CI do commit publicado e concluir
   revisão/merge/entrega conforme as regras do grupo e do professor.

O passo 1 exige julgamento dos integrantes. Os passos técnicos seguintes podem ser
automatizados. Hoje o importador do passo 2 ainda não existe: um CSV preenchido,
sozinho, não será incorporado pelo programa atual.

O checklist exato da plataforma do professor não está disponível aqui. Ao final,
confiram o enunciado completo: este roteiro cobre as pendências identificadas no
repositório e na divisão da Sprint 2, não garante requisitos externos desconhecidos.

### 1.1. O que vocês precisam fazer manualmente

1. Combinar a distribuição dos 240 projetos. Sugestão: 80 para Diogo, 80 para
   Pedro e 80 para Lorran, sem sobreposição.
2. Ler descrição, README e documentação de cada projeto do próprio lote e decidir
   seu tipo. O procedimento está nas seções 7 e 8; não é preciso analisar novas releases.
3. Registrar categoria, link de evidência, justificativa, nome de quem avaliou,
   origem verdadeira e data. Resolver os casos ambíguos com outro integrante.
4. Conferir no enunciado se essa classificação complementar individual atende à
   exigência, além dos arquivos/links e da forma de submissão ao professor.
5. Dar o aceite do grupo para a versão final, confirmar as decisões que dependem
   de vocês e efetuar a submissão na plataforma do professor, salvo se houver
   acesso disponível e autorização específica para eu realizá-la.

As três avaliações A/B/C já concluídas não precisam ser repetidas. Para manter
classificações declaradas humanas, a decisão precisa realmente ser de vocês.
Posso esclarecer critérios e revisar dúvidas; se a IA participar da decisão,
essa assistência deve ser declarada, não apresentada como trabalho humano independente.

### 1.2. O que eu posso fazer por vocês

- Preparar as listas e os lotes em branco, com identidades e links corretos.
- Implementar e testar o importador complementar; posso começar com fixtures
  antes de vocês terminarem, sem inventar rótulos para a entrega.
- Conferir preenchimento, categorias, duplicatas, cobertura, hashes e proveniência
  dos arquivos devolvidos. Isso não comprova, sozinho, a correção de cada julgamento humano.
- Importar os rótulos legítimos, recalcular dataset/manifestos/estado/tabelas e
  executar os testes. O fechamento real depende dos arquivos preenchidos por vocês.
- Atualizar o artigo e o dicionário, compilar e conferir o PDF, registrando o que
  realmente foi realizado e as limitações restantes.
- Preparar commit, descrição do PR e associação das issues efetivamente resolvidas;
  com acesso e autorização, fazer commit/push, atualizar o PR e acompanhar o CI.
  Merge também exige autorização e cumprimento das regras de revisão do grupo.

Vocês não precisam programar o importador nem executar todos os comandos deste
guia manualmente: as seções técnicas explicam o processo e permitem acompanhar ou
delegar sua execução. “Posso fazer” não significa que essas pendências já estejam feitas.

### 1.3. Ordem prática para dividir o trabalho

Eu preparo os lotes e o importador; vocês classificam os projetos; eu valido e
integro os arquivos, recalculo e testo, atualizo o artigo e preparo a publicação;
vocês conferem o aceite e os requisitos externos. Publicação/merge ocorrem com
acesso e autorização; a submissão ao professor precisa ser confirmada separadamente.

## 2. Onde está cada coisa

Diretório principal do repositório no computador do Lorran:

```text
C:\Users\BlueTape\Documents\lab-experimentacao-software
```

Diretório do trabalho desta entrega:

```text
C:\Users\BlueTape\Documents\lab-experimentacao-software\Lab03
```

No computador dos colegas, o caminho inicial pode ser diferente. A estrutura
interna `Lab03/` é a mesma. Os caminhos abaixo são relativos a esse diretório.

| Caminho | Para que serve | O que fazer agora |
| --- | --- | --- |
| `data/amostra_final.csv` e `.manifest.json` | Identidades dos 300 projetos e vínculo com as fontes congeladas. | Consultar; não editar nem sortear novamente. |
| `data/dataset.csv` e `.manifest.json` | Métricas calculadas e quantidade de tipos ausentes. | Consultar; não preencher manualmente a saída gerada. |
| `data/amostra_ouro_s02/rotulos/rotulos_A.xlsx`, `rotulos_B.xlsx`, `rotulos_C.xlsx` | Avaliações dos 60 projetos e das 300 releases sorteadas. | Preservar as versões locais já conferidas e seus manifestos. |
| `data/amostra_ouro_s02/consenso_repos.csv` e `consenso_releases.csv` | Consenso dos três avaliadores, somente da amostra-ouro. | Não acrescentar os outros 240 projetos aqui. |
| `data/amostra_ouro_s02/avaliacao_v1.*`, `avaliacao_v2.*`, `avaliacao_v3.*` | Histórico de avaliação da heurística. | Preservar; não apagar versões para contornar erro de integridade. |
| `data/amostra_ouro_s02/fechamento.json` | Estado gerado da validação e das pendências. | Ler; não trocar os campos para `true` à mão. |
| `data/fontes_s02.zip` | Fontes para recalcular sem acessar a API. | Verificar/restaurar somente se necessário. |
| `data/s02/` | Fontes extraídas, checkpoint e informações locais de coleta. | Não editar; é ignorado pelo Git. |
| `pipeline/dataset.py` | Consolida o dataset; hoje lê somente o consenso. | É um dos pontos a ampliar para o importador complementar. |
| `validacao/fechamento_s02.py` | Orquestra validação, dataset e estado. | Integrar a nova entrada e seus critérios de aceite. |
| `docs/dicionario_dados.md` | Definições das colunas. | Atualizar se a importação alterar alguma definição ou coluna. |
| `docs/artigo/` | Fontes LaTeX e PDF parcial. | Atualizar depois do recálculo final. |
| `docs/alteracoes_revisao_s02.md` | Inventário das correções e justificativas. | Consultar para entender a revisão. |

## 3. Divisão sugerida para fechar sem sobreposição

Esta é uma proposta, não uma atribuição já combinada entre vocês.

| Integrante | Trabalho manual sugerido para o fechamento |
| --- | --- |
| Diogo (A) | Classificar 80 projetos complementares e revisar com o grupo dúvidas sobre categorias e a descrição da classificação. |
| Pedro (B) | Classificar 80 projetos complementares e conferir a descrição metodológica de sua parte. |
| Lorran (C) | Classificar 80 projetos complementares, reunir os arquivos e coordenar o aceite/publicação com o grupo. |

Eu posso cuidar da preparação dos lotes, implementação do importador, verificações,
recálculo, testes e atualização do artigo. A publicação segue as condições da seção 1.2.

A exigência de três avaliações independentes já foi atendida na amostra-ouro,
segundo as declarações recebidas. A classificação complementar proposta é de um
avaliador por projeto. Não a descrevam como consenso triplo dos 300 projetos.
Se o enunciado exigir outro desenho para os 240, ajustem essa etapa antes de começar.

## 4. Preparar o terminal sem complicação

Abra o PowerShell no VS Code ou no Windows e execute:

```powershell
Set-Location 'C:\Users\BlueTape\Documents\lab-experimentacao-software\Lab03'
Get-Location
Test-Path '.\.venv\Scripts\python.exe'
.\.venv\Scripts\python.exe --version
```

O teste deve mostrar `True`; a versão local conferida foi Python 3.12.14. Usar o
executável completo evita precisar ativar o ambiente ou alterar a política do Windows.

Se a pasta `.venv` não existir em outro computador, instale Python 3.12 e, dentro
de `Lab03/`, execute:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

Se `py` não for reconhecido, falta configurar a instalação do Python. Não é um
erro nos dados; resolva a instalação antes de continuar.

## 5. Conferir o ponto de partida

Ainda dentro de `Lab03/`:

```powershell
git branch --show-current
git status --short
Get-Content '.\data\amostra_ouro_s02\fechamento.json'
.\.venv\Scripts\python.exe -m scripts.fontes_s02 verificar
```

A branch esperada é `codex/lab03-s02-lorran-parte-c`. Os arquivos modificados e
novos são trabalho ainda não publicado; não os descarte para deixar o Git limpo.

O estado atual esperado é:

```text
coleta_congelada: 300
validacao_concluida: true
validacao.qualificada: true
validacao.versao: v3
entrega_completa: false
projetos_sem_tipo: 240
cfr_b_indisponiveis: 11
```

O campo legado `concluido: true` e uma saída de comando igual a zero não significam,
sozinhos, que a sprint está pronta. Os campos acima explicam a diferença.

Em um checkout novo, após verificar o pacote, restaure as fontes com:

```powershell
.\.venv\Scripts\python.exe -m scripts.fontes_s02 restaurar
```

Não precisa de token nem de nova mineração. Se o comando recusar uma fonte local
diferente, pare e investigue: não apague o arquivo nem edite seu hash para forçar a restauração.

## 6. Gerar a lista dos 240 projetos para classificar

Este passo cria uma pasta NOVA, proposta para organizar a etapa complementar:
`Lab03/data/classificacao_complementar/`. Ela não é uma entrada suportada pelo
pipeline atual até o passo 9 ser implementado.

O bloco abaixo é uma instrução para vocês executarem. Não foi executado para
inventar classificações nesta revisão. Ele cria somente listas em branco.

```powershell
$pendentes = @(Import-Csv '.\data\dataset.csv' | Where-Object {
    [string]::IsNullOrWhiteSpace($_.tipo_projeto)
} | Sort-Object full_name)
if ($pendentes.Count -ne 240) { throw "Esperados 240; encontrados $($pendentes.Count). Confira o estado antes de continuar." }
if (Test-Path '.\data\classificacao_complementar') { throw 'A pasta já existe. Não sobrescreva o trabalho de ninguém.' }
New-Item -ItemType Directory -Path '.\data\classificacao_complementar'
$itens = @($pendentes | Select-Object full_name,
    @{Name='repo_url'; Expression={'https://github.com/' + $_.full_name}},
    @{Name='tipo_projeto'; Expression={''}},
    @{Name='evidencia_url'; Expression={''}},
    @{Name='justificativa'; Expression={''}},
    @{Name='avaliador'; Expression={''}},
    @{Name='origem'; Expression={''}},
    @{Name='data_avaliacao'; Expression={''}})
$itens[0..79] | Export-Csv '.\data\classificacao_complementar\tipos_A.csv' -NoTypeInformation -Encoding UTF8
$itens[80..159] | Export-Csv '.\data\classificacao_complementar\tipos_B.csv' -NoTypeInformation -Encoding UTF8
$itens[160..239] | Export-Csv '.\data\classificacao_complementar\tipos_C.csv' -NoTypeInformation -Encoding UTF8
```

Cada arquivo terá 80 repositórios, sem sobreposição, em ordem alfabética. A
distribuição por letras só vale se o grupo aceitar a proposta do passo 3.
Se a contagem não for 240, não altere a condição apenas para o comando passar:
alguém pode ter atualizado o dataset depois deste guia.

## 7. Como abrir e preencher os arquivos sem estragar a estrutura

No Excel, use Dados → De Texto/CSV. Selecione o arquivo correspondente ao seu lote,
codificação UTF-8 e delimitador vírgula. Isso evita abrir tudo em uma coluna por
causa da configuração regional do Windows. Se as opções tiverem nomes diferentes,
procure a importação de texto/CSV equivalente.

Mantenha os nomes dos cabeçalhos e as colunas `full_name` e `repo_url` exatamente
como foram geradas. Não adicione linhas de totais, não una células e não altere IDs.
Não ordene só uma coluna, porque isso separa a classificação do repositório correto.

Pode trabalhar em uma cópia XLSX para facilitar, mas o arquivo de entrada que o
importador proposto receberá deve ser CSV UTF-8 com vírgula. Ao exportar, confira
no editor de texto se os cabeçalhos continuam separados por vírgulas e os acentos
aparecem corretamente. Não tente corrigir delimitadores substituindo todo `;` por
`,` às cegas: justificativas podem conter esses caracteres dentro do texto.

Preencha por linha:

| Campo | Como preencher |
| --- | --- |
| `tipo_projeto` | Uma das quatro categorias exatas do passo 8. |
| `evidencia_url` | Link específico do README, documentação ou página oficial que sustenta a decisão. |
| `justificativa` | Uma frase curta dizendo qual é o uso principal e por que corresponde à categoria. |
| `avaliador` | Nome real de quem examinou o projeto. |
| `origem` | `humana` se a classificação foi realmente feita por uma pessoa; se houve assistência de IA na decisão, declare `assistida_por_IA` e documente a assistência. Não mude para humana para satisfazer uma regra. |
| `data_avaliacao` | Data real no formato `AAAA-MM-DD`, por exemplo `2026-10-15` somente se foi nesse dia. |

Não pré-preencha declaração de revisão concluída. Origem, nome e data devem
descrever o que ocorreu, não o que seria conveniente para o relatório.

## 8. Como analisar o tipo de cada projeto, na prática

Faça o seguinte para cada uma das suas 80 linhas:

1. Copie a `repo_url` e abra no navegador.
2. Leia a descrição no topo do GitHub e o início do README.
3. Procure as seções de uso, instalação e exemplos. Se ainda não estiver claro,
   abra a documentação oficial indicada pelo próprio projeto.
4. Responda: a pessoa normalmente usa isso como dependência de outro programa,
   como aplicativo/serviço, como comando de terminal ou para outra finalidade?
5. Registre a categoria, o link que leu e uma justificativa de uma frase.
6. Preencha seu nome, a origem verdadeira e a data. Salve e passe ao próximo.

Use estas categorias, com a mesma escrita:

| Categoria | Quando usar | Cuidado para não confundir |
| --- | --- | --- |
| `biblioteca/framework` | O produto principal é uma dependência, SDK ou estrutura para desenvolver outro software. | Ter um comando auxiliar não transforma uma biblioteca em CLI. |
| `aplicação/serviço` | O produto principal é um aplicativo, servidor ou serviço que o usuário utiliza ou opera diretamente. | Uma aplicação pode ser instalada pelo terminal e continuar sendo uma aplicação. |
| `ferramenta CLI` | O uso principal é executar comandos no terminal para realizar uma tarefa. | Não classifique como CLI apenas porque a instalação usa `pip`, `npm` ou shell. |
| `outro` | A finalidade identificada realmente não cabe nas três anteriores. | Não significa “não li”, “não sei” ou “quero acabar logo”. |

Exemplos fictícios: um SDK de pagamentos importado pelo código é biblioteca;
um servidor de chat auto-hospedado é aplicação/serviço; um programa cujo produto
principal é converter arquivos por comando é CLI. Baseie a decisão no projeto
real, não só no nome, na linguagem ou nesses exemplos.

Se for híbrido, identifique a finalidade principal anunciada e demonstrada na
documentação. Se duas categorias continuarem igualmente defensáveis, anote a
dúvida em um arquivo separado e peça revisão de outro integrante. Não invente
evidência e não use `outro` para esconder incerteza.

Se a página não abrir, verifique o link, procure a documentação oficial e registre
eventual redirecionamento/renomeação, preservando o `full_name` congelado. Se ainda
não houver evidência suficiente, deixe a classificação pendente e registre o motivo.

Não é necessário instalar, executar ou clonar nenhum dos 240 programas. Leia as
páginas; não execute comandos de READMEs desconhecidos. As páginas podem ter
mudado desde a janela do estudo: registre a data real da inspeção e explique essa
limitação no método, em vez de alegar uma inspeção histórica que não ocorreu.

### Revisão do próprio lote

Antes de enviar ao grupo, confira:

- Há exatamente 80 linhas de dados, com as mesmas identidades da lista recebida.
- Todas têm categoria válida, link de evidência, justificativa, nome, origem e data.
- Nenhum nome de repositório foi trocado, repetido ou apagado.
- O CSV final está em UTF-8 e usa vírgula como delimitador.
- Dúvidas foram resolvidas com evidência ou continuam explicitamente pendentes.

Não edite as planilhas `rotulos_A/B/C.xlsx` para acrescentar os 240 projetos.
Elas pertencem ao experimento independente da amostra-ouro, que já terminou.

## 9. Implementar a importação — pendência técnica real

Responsável sugerido: Lorran, com assistência técnica. Entradas: os três CSVs
complementares legítimos. Saída: o mesmo dataset de 300, preservando os 60 tipos
do consenso e incorporando os outros 240 com proveniência separada.

Hoje `pipeline.dataset.carregar_rotulos` só usa o consenso atestado. Não existe
uma opção pronta para importar os CSVs novos. Não passe esses arquivos em
`--consenso`, não acrescente linhas ao consenso nem preencha diretamente
`dataset.csv`: isso quebra a distinção entre avaliação individual e consenso.

Para quem não programa, a maneira segura de concluir esta etapa é solicitar a
implementação depois de preencher os lotes. Você pode usar este pedido completo:

> Na branch `codex/lab03-s02-lorran-parte-c`, implemente a importação complementar
> dos tipos dos projetos fora da amostra-ouro. Leia o estado atual antes de editar
> e preserve todo o WIP. As entradas estão em
> `Lab03/data/classificacao_complementar/tipos_A.csv`, `tipos_B.csv` e `tipos_C.csv`,
> com os campos descritos em `Lab03/docs/guia_finalizacao_s02.md`.
> Não invente classificações nem altere os votos A/B/C, consensos, fontes, amostra,
> janela ou heurística v3. Amplie `pipeline/dataset.py` e o fluxo
> `validacao/fechamento_s02.py`, acrescentando uma interface explícita/documentada
> para a nova entrada, sem fingir que ela é consenso. Aceite CSV UTF-8 com ou sem
> BOM. Valide a identidade contra a amostra congelada; rejeite nomes desconhecidos,
> duplicatas, sobreposição com os 60 do consenso, categoria inválida, falta de
> evidência/justificativa/avaliador/origem/data e datas inválidas. Não aceite 240
> linhas apenas pela contagem: confira exatamente o conjunto de projetos faltantes.
> Preserve a origem declarada, sem converter assistência de IA em humana.
> Registre hashes dos arquivos complementares e vínculo à amostra em manifesto;
> confira qualquer manifesto registrado na reutilização. Mantenha separada a
> proveniência dos 60 consensuais e dos 240 individuais. Não crie valores para
> `releases_sao_entregas` nos 240: a tarefa complementar é apenas tipo de projeto.
> Documente o significado de `rotulo_disponivel` se passar a cobrir ambos os grupos.
> Adicione testes de todas as recusas, integridade, integração, recálculo offline
> e estado parcial/completo. Atualize o dicionário se mudar o esquema. O estado
> só pode declarar entrega completa com os tipos preenchidos e a validação válida;
> não esconda os 11 CFR (b) indisponíveis. Recalcule dataset, manifesto e tabelas
> pelas fontes congeladas, rode toda a suíte, confira invariância dos consensos,
> kappas e F1, documente o comando realmente implementado e não publique sem a
> revisão final solicitada pelo grupo.

Isso não depende de uma nova coleta. O trabalho pode ser preparado com fixtures
antes de os CSVs estarem prontos, mas o fechamento real depende das entradas reais.

Caso vocês mesmos implementem, confiram especialmente os pontos acima. Código
que simplesmente atribui uma categoria para cada nome sem validação/proveniência
não conclui esta pendência de forma adequada.

## 10. Recalcular e conferir o fechamento integrado

Faça este passo DEPOIS de o importador estar implementado e testado. Primeiro
confira a interface real, sem adivinhar opções novas:

```powershell
.\.venv\Scripts\python.exe -m pipeline.dataset --help
.\.venv\Scripts\python.exe -m validacao.fechamento_s02 --help
```

Use o comando documentado por quem implementou a importação. O comando existente
abaixo valida a amostra-ouro, mas, no código atual, NÃO importa os 240 CSVs:

```powershell
.\.venv\Scripts\python.exe -m validacao.fechamento_s02 --config config_s02.yaml --validar-avaliacoes
if ($LASTEXITCODE -ne 0) { throw 'A validação falhou. Leia o erro antes de continuar.' }
```

Se a implementação nova exigir uma opção para a classificação complementar,
essa opção precisará estar no comando final. Rodar só o comando antigo e continuar
com 240 tipos vazios não fecha a sprint.

Depois do fluxo com a nova entrada, leia:

```powershell
Get-Content '.\data\dataset.manifest.json'
Get-Content '.\data\amostra_ouro_s02\fechamento.json'
$final = @(Import-Csv '.\data\dataset.csv')
$final.Count
@($final | Where-Object { [string]::IsNullOrWhiteSpace($_.tipo_projeto) }).Count
```

Esperado para resolver a pendência conhecida: `300` linhas e `0` tipos vazios;
validação qualificada em v3; manifesto com a nova proveniência; estado sem
pendência de classificação. A implantação do importador deve atualizar os campos
de estado automaticamente. Não edite JSONs para forçar o resultado.

Se apenas os tipos complementares mudaram, devem continuar iguais:

- A amostra congelada e suas fontes.
- Os votos, consensos e kappas da amostra-ouro.
- F1 da v3: `0,7431693989071039`; VP=68, FP=28, FN=19 e VN=185.
- As métricas de tempo, frequência e falha já calculadas para cada projeto.

O SHA-256 do dataset mudará legitimamente quando os tipos forem preenchidos.
Não reutilize o hash antigo no manifesto novo. Também não aceite mudança no F1
como efeito normal da classificação de tipos: isso indica outra alteração a revisar.

### E os 11 CFR (b) indisponíveis?

No estado atual são 11 projetos sem evidência textual suficiente para esse cálculo.
Isso é diferente de uma taxa de falha igual a zero. Para localizar:

```powershell
Import-Csv '.\data\dataset.csv' | Where-Object {
    $_.cfr_b_disponivel -ieq 'False'
} | Select-Object full_name, releases_sem_evidencia_textual, releases_erro_404
```

Preserve os ausentes e explique a limitação. A classificação do tipo não resolve
essa falta de evidência. Recuperar fontes adicionais exigiria uma alteração
rastreável, não edição silenciosa do congelamento. Não é motivo para repetir toda
a coleta nem para inventar mensagens de commits. Confiram se o professor exige
tratamento adicional além de contabilizar/documentar os ausentes.

## 11. Executar os testes

Dentro de `Lab03/`, com o Excel fechado nos arquivos avaliados:

```powershell
.\.venv\Scripts\python.exe -m scripts.validar_rotulos_b data/amostra_ouro_s02/rotulos/rotulos_A.xlsx
.\.venv\Scripts\python.exe -m scripts.validar_rotulos_b data/amostra_ouro_s02/rotulos/rotulos_B.xlsx
.\.venv\Scripts\python.exe -m scripts.validar_rotulos_b data/amostra_ouro_s02/rotulos/rotulos_C.xlsx
.\.venv\Scripts\python.exe -m pytest --cov=metricas --cov-report=term-missing --cov-fail-under=80
if ($LASTEXITCODE -ne 0) { throw 'Os testes falharam. Não publique como entrega aprovada.' }
```

O validador se chama `validar_rotulos_b` e imprime “B”, mas aceita o formato
canônico das três planilhas. Esperado: 60 repositórios e 300 releases em cada uma.
Essa checagem é estrutural; a conferência de manifestos/proveniência pertence ao
fluxo de fechamento. Uma não substitui a outra.

Referência anterior à implementação do importador: 279 testes aprovados,
95,51% de cobertura. Com novos testes, a quantidade pode aumentar. A regra do CI
exige pelo menos 80% de cobertura de `metricas`, não “exatamente 279 testes”.
Se houver falha, leia a primeira mensagem, corrija a causa e execute novamente;
não apague o teste ou diminua a meta para ficar verde.

## 12. Atualizar o artigo e os documentos de entrega

Arquivos em `Lab03/docs/artigo/`:

1. `artigo.tex`: resumo e abstract devem dizer o que ficou efetivamente completo.
2. `metodologia.tex`: manter a validação dos 60/300, histórico v1/v2/v3 e a
   limitação de refinar e avaliar na mesma amostra.
3. `metodologia_coleta.tex`: explicar os números reais da coleta e como os 240 tipos
   complementares foram atribuídos, por quem, quando e com qual origem.
4. `tabelas/validacao_s02.tex`, `kappa_s02.tex` e `coleta_s02.tex`: conferir contra
   as saídas geradas. Corrigir o gerador se necessário, não inventar números na tabela.
5. `README.md`: atualizar o link/estado do PDF e a forma de reproduzir.

Fora da pasta do artigo, atualizar os blocos de estado atual em `Lab03/README.md`,
`docs/fechamento_s02.md`, `docs/entrega_s02_c.md`, `docs/evidencias_s02_c.md` e
`docs/pendencias_manuais_s02.md`. Atualizar `docs/dicionario_dados.md` se a importação
mudou o significado dos campos ou acrescentou colunas.

Não precisa apagar o histórico antigo: marque claramente o que ele descreve e
qual estado atual o substitui. Este guia também é um retrato datado, não prova de
que os passos futuros já ocorreram.

Texto metodológico deve distinguir:

- 300 repositórios coletados e congelados.
- 60 repositórios e 300 releases avaliados por três integrantes para consenso/kappa/F1.
- 240 projetos classificados complementarmente quanto ao tipo, com protocolo e
  proveniência próprios; não avaliados três vezes só porque o dataset tem 300 linhas.
- Ausências/censuras reais, inclusive os 11 CFR (b), se a situação permanecer igual.
- Refinamento na mesma amostra, sem alegação de teste em dados não vistos.

Números já registrados: 53.143 candidatos no snapshot, 2.644 avaliados e 300 aceitos;
11.453 releases principais; 314.276 runs totais, 291.405 válidos e 22.871 ignorados;
274 releases censuradas no CFR (b); 90 episódios de recuperação censurados;
9 comparações 404; 561 relações release/commit com datas inválidas. Confira os
manifestos finais antes de copiar esses números.

Repositório: https://github.com/PedroMaiaAlves/lab-experimentacao-software
Se houver campo para GitHub Projects, obtenham o link real na aba Projects do grupo.
Não inventem número de projeto nem usem o link do repositório como se fosse o board.

### Compilar no computador do Lorran

O compilador usado na revisão está no cache local. Dentro de `Lab03/`:

```powershell
Test-Path '.\cache\latex\tectonic\tectonic.exe'
Push-Location '.\docs\artigo'
try {
    & '..\..\cache\latex\tectonic\tectonic.exe' artigo.tex --outdir ../../cache/latex --keep-logs
    if ($LASTEXITCODE -ne 0) { throw 'Falha na compilação; confira o log.' }
} finally {
    Pop-Location
}
```

Se o teste do executável mostrar `False`, não rode o bloco seguinte: o compilador
não está disponível naquele computador. Use uma instalação LaTeX ou importe a
pasta inteira `docs/artigo/` para o Overleaf, mantendo os arquivos `.sty`, `.bst`,
`.bib` e a subpasta `tabelas/`. Defina `artigo.tex` como principal e compile.

A compilação local acima gera `Lab03/cache/latex/artigo.pdf`. Abra e confira todas
as páginas: tabelas sem corte, acentos, referências, ausência de `??`, títulos,
autores, números coerentes e nenhum texto de “pendente” contradizendo o fechamento.
O PDF anterior tinha sete páginas; a versão final pode ter outra quantidade.

Após aprovação real, uma opção é publicar o PDF final como
`Lab03/docs/artigo/artigo_s02.pdf` e atualizar o README para apontar a ele.
Esse nome é uma proposta nova, não um arquivo final já existente. Copie o PDF
aprovado para lá, preservando o parcial como histórico se o grupo quiser. Nunca
renomeie o parcial para “final” sem atualizar conteúdo e conferir a compilação.

## 13. Preparar a publicação sem perder trabalho

Agora os comandos Git usam a raiz do repositório, não `Lab03/`:

```powershell
Set-Location 'C:\Users\BlueTape\Documents\lab-experimentacao-software'
git branch --show-current
git status --short
git fetch origin
git rev-list --left-right --count HEAD...origin/codex/lab03-s02-lorran-parte-c
```

O último comando mostra commits só locais e só remotos, nessa ordem. Se o segundo
número não for zero, alguém publicou depois da integração: não use push forçado,
não execute `reset --hard` e não dê `pull` às cegas sobre arquivos modificados.
Peça uma integração que preserve o WIP antes de continuar. A referência desta
revisão é `bf2288d`, não uma garantia de que o remoto ficará parado.

Há um stash antigo chamado `Preserva WIP S02 v3 antes de integrar bf2288d`.
Ele é recuperação da integração anterior, não uma instrução para dar `stash pop`.
Não o aplique sobre o trabalho atual. Antes de uma integração complicada, preservem
também os arquivos novos e o trabalho mais recente; `git diff` sozinho não contém
os arquivos ainda não rastreados.

### Conferir identidade

```powershell
gh auth status
gh api user --jq .login
git config user.name
git config user.email
```

O autor do commit e a conta autenticada para publicar são coisas diferentes.
A identidade usada anteriormente para Lorran foi `lorranpuc`, nome `Lorran Avelar`
e e-mail `229218484+lorranpuc@users.noreply.github.com`. Confirme a conta que você
quer usar; não presuma que a conta ativa da CLI tem permissão de escrita.

Se quiser usar uma conta sua já salva na CLI, `gh auth switch --user lorranpuc`
troca a conta ativa e deve ser uma decisão sua. Se ela não estiver salva, faça login
interativo com `gh auth login`. Nunca copie tokens para o chat, CSV, arquivo do projeto
ou comando de commit. Se o push usar outra credencial do Windows e falhar, corrija
a autenticação em vez de forçar ou apagar o trabalho dos outros.

### Escolher exatamente os arquivos a publicar

Use `git status --short` para ver a lista. Confira os arquivos contra o inventário
`Lab03/docs/alteracoes_revisao_s02.md` e os arquivos da nova classificação/importação.
Inclua as avaliações e artefatos legítimos ainda não rastreados, não só a correção v3.

Não inclua `.env`, tokens, `.venv/`, `cache/`, `__pycache__/`, arquivos `~$` do Excel,
logs de inspeção ou cópias temporárias. Não use `git add .` sem revisar. Exemplos
de seleção explícita, a partir da raiz:

```powershell
git add -- Lab03/metricas/cfr.py Lab03/config_s02.yaml Lab03/validacao/fechamento_s02.py
git add -- Lab03/tests/test_cfr.py Lab03/tests/test_dataset.py Lab03/tests/test_fechamento_s02.py Lab03/tests/test_integracao_s02.py
git add -- Lab03/data/dataset.csv Lab03/data/dataset.manifest.json
```

Esses exemplos NÃO são a lista completa do commit. Acrescente explicitamente os
arquivos revisados de `data/amostra_ouro_s02/`, `data/classificacao_complementar/`,
`pipeline/dataset.py`, testes novos, documentos e PDF final. Um arquivo só entra
no commit quando estiver no staging. A escolha deve acompanhar a implementação
final, não uma lista fixa escrita antes de ela existir.

Depois de selecionar tudo:

```powershell
git diff --cached --stat
git diff --cached --name-only
git -c core.whitespace=cr-at-eol diff --cached --check
git status --short
```

No status, a coluna da esquerda representa staging; a da direita representa
modificação que ainda não entrou no staging. Se um arquivo tiver mudanças nas duas,
o commit não conterá necessariamente sua última versão: confira novamente.

Revise o diff textual, os hashes das planilhas e o PDF. Não transforme a B remota
assistida em humana: o arquivo local B aceito é outro, com histórico preservado.
Se alguém editar uma planilha após o consenso, manifestos e resultados precisarão
ser legitimamente regenerados e revisados; não mude só o hash para esconder a edição.

### Commit e push, somente depois da revisão

Com todos os arquivos corretos selecionados, testes e artigo aprovados:

```powershell
git -c user.name='Lorran Avelar' -c user.email='229218484+lorranpuc@users.noreply.github.com' commit -m 'Conclui classificacao complementar e validacao integrada da S02'
if ($LASTEXITCODE -ne 0) { throw 'O commit não foi criado. Confira o erro.' }
git push origin codex/lab03-s02-lorran-parte-c
if ($LASTEXITCODE -ne 0) { throw 'O push falhou. Não use force; confira autenticação ou avanço do remoto.' }
git status --short
```

Use essa mensagem de conclusão somente quando ela for verdadeira. Um checkpoint
parcial pode ser publicado se o grupo quiser, mas deve estar claramente identificado
como parcial, sem fechar a entrega ou suas issues prematuramente.

## 14. Conferir PR, CI, merge e entrega

PR existente: https://github.com/PedroMaiaAlves/lab-experimentacao-software/pull/162

1. Abra o PR e confira se os commits novos e todos os arquivos necessários apareceram.
2. Atualize a descrição com v3, F1 atual, tipos completos somente se realmente
   completos, testes do commit publicado e limitações mantidas.
3. Registre a escolha da avaliação B local e a preservação do commit remoto;
   não esconda a diferença entre os arquivos.
4. Confira os checks do novo commit, não o check verde de um commit antigo:

```powershell
gh pr checks 162 --watch --interval 15
```

5. Se o CI falhar, abra o log e corrija antes de anunciar aprovação. A suíte local
   aprovada não garante que o CI do commit publicado já passou.
6. Peça revisão dos colegas. A integração de código de A na branch não significa
   que todos os PRs de A já estejam mesclados na main; coordenem PRs sobrepostos.
7. Associe issues corretas com `Closes #NUMERO` na descrição do PR somente para
   tarefas realmente resolvidas. Confira título e checklist de cada issue no GitHub;
   não use um número de exemplo literalmente nem feche tarefas ainda pendentes.
8. Tire o PR de rascunho e faça/solicite merge apenas quando a revisão e os checks
   estiverem aprovados e vocês tiverem combinado a integração. Não dê push direto
   na main para contornar a revisão.
9. Confira a main no GitHub depois do merge, o CI correspondente, os arquivos e
   o PDF acessível. Registre o commit final para saber exatamente o que foi entregue.
10. Envie na plataforma do professor os links/arquivos efetivamente solicitados.
    Um merge no GitHub não equivale automaticamente a submissão no portal.

## 15. Checklist final — o que significa “acabou”

- [ ] 300 repositórios e fontes congeladas preservados, sem nova coleta desnecessária.
- [ ] A/B/C da amostra-ouro preservadas, manifestos íntegros e origem verdadeira.
- [ ] Consenso, kappas e F1 reproduzidos, com v1/v2/v3 rastreáveis.
- [ ] Os 240 tipos complementares realmente analisados e documentados.
- [ ] Importador implementado, testado, com validação de identidade e proveniência.
- [ ] Dataset com 300 linhas e nenhum tipo ausente; manifestos/estado atualizados.
- [ ] CFR indisponível mantido ausente e suas limitações explicitadas, não zerado.
- [ ] Testes locais e CI do commit publicado aprovados.
- [ ] Artigo coerente com os resultados e PDF final visualmente conferido.
- [ ] Commit/push feitos na branch correta, sem segredos ou perda de trabalho alheio.
- [ ] PR revisado/integrado, issues corretas e submissão realizada conforme enunciado.

Se qualquer item ainda não estiver verdadeiro, anotem exatamente qual falta.
Não há necessidade de refazer o que já está validado para parecer que o projeto
avançou: o próximo avanço útil é a classificação complementar com sua integração.
