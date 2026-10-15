# Diogo — roteiro completo da parte A da Sprint 2

## 1. Sua responsabilidade e o estado atual

Você é o avaliador A. A coleta real de 300 repositórios, o sorteio definitivo de
60 projetos com cinco releases por projeto, o dicionário e a base da metodologia
já foram preparados. Não repita a mineração nem refaça o sorteio para começar.

Falta concluir sua avaliação independente, reunir as três avaliações legítimas,
calcular a concordância e o consenso e atualizar a metodologia de A com o que
realmente ocorreu. Lorran já entregou C no commit `ec590f8`, mas você não deve
consultar os votos dele antes de terminar os seus.

Os artefatos definitivos estão na branch `codex/lab03-s02-lorran-parte-c`, PR #162.
Ainda não estão integrados à main. O PR #153 de A foi integrado nessa branch,
preservando sua autoria, não diretamente na main.

## 2. Localizar o projeto e preparar o ambiente

No computador de Lorran, a pasta de trabalho é:

```text
C:\Users\BlueTape\Documents\lab-experimentacao-software\Lab03
```

No seu computador, substitua esse prefixo pela pasta onde clonou o projeto.
Todos os caminhos deste guia, a partir daqui, são relativos a `Lab03/`.
Repositório: https://github.com/PedroMaiaAlves/lab-experimentacao-software

Antes de atualizar, execute `git status --short` na raiz do repositório. Se houver
trabalho local, preserve-o antes de trocar de branch; não use reset, checkout
forçado ou push forçado. Faça `git fetch origin` para obter a branch de integração.

Uma opção para evitar pushes concorrentes é criar sua própria branch a partir
da integração atual. Nome sugerido, somente se ainda não existir:

```text
git switch -c codex/lab03-s02-diogo-a origin/codex/lab03-s02-lorran-parte-c
```

Se já tiver uma branch de A adequada, alinhe a integração com o grupo e preserve
suas alterações. Não trabalhe somente na main antiga, que não contém estes artefatos.
Não abra C/B durante a avaliação, mesmo que os arquivos estejam no checkout.

Para os comandos deste guia, entre em `Lab03/`. No Windows:

```powershell
Set-Location 'CAMINHO-DO-SEU-CHECKOUT\Lab03'
```

Com ambiente já instalado, use `python` associado a ele. No checkout de Lorran,
o executável é `.\.venv\Scripts\python.exe`. Para preparar um ambiente novo:

```text
python -m venv .venv
```

Windows: `.\.venv\Scripts\python.exe -m pip install -r requirements.txt`.
Linux: crie com `python3 -m venv .venv` e instale com
`./.venv/bin/python -m pip install -r requirements.txt`.
Substitua `python` nos comandos seguintes pelo executável do seu ambiente,
sem depender da ativação. Não precisa de token para preencher, validar ou calcular offline.

## 3. Arquivos para usar durante sua avaliação

| Caminho dentro de Lab03 | Uso |
|---|---|
| `data/amostra_ouro_s02/rotulos/rotulos_A.xlsx` | Sua planilha definitiva. |
| `data/amostra_ouro_s02/repos_sorteados.csv` | Os 60 projetos e seus links. Não modificar. |
| `data/amostra_ouro_s02/releases_sorteadas.csv` | As 300 releases e seus links/identificadores. Não modificar. |
| `data/amostra_ouro_s02/fontes_releases.json` | Notas e mensagens de commits preservadas, sem previsões. |
| `docs/guia_rotulagem.md` | Definições; os caminhos de cópia do modelo antigo são do piloto. |
| `docs/protocolo_rotulagem_B.md` | Critérios detalhados comuns a A/B/C; ignore os caminhos do piloto. |

Use sempre `amostra_ouro_s02`, não `amostra_ouro`. Não copie o modelo antigo sobre
a planilha definitiva. Não leia B/C, consensos, auditorias da heurística nem
`data/revisao_c_provisoria/` enquanto estiver decidindo seus votos.
Não peça a IA para fornecer os votos se for declarar a avaliação como humana.
Orientação sobre método não é uma classificação automática dos itens.

## 4. Preencher sua planilha, um projeto de cada vez

Abra o XLSX em Excel ou LibreOffice. Leia a aba `instrucoes`. Em `repositorios`,
preencha somente `tipo_projeto` e `releases_sao_entregas`; em `releases`, somente
`corretiva`. Preserve abas, cabeçalhos, IDs, URLs, tags, ordem e formato XLSX.
Não ordene uma única coluna isoladamente. Use as listas suspensas.

Cada avaliador faz os mesmos 60 projetos e 300 releases. Não divida as 300 releases
em três lotes de 100: precisamos de três julgamentos para cada item.

### 4.1. Tipo do projeto

Abra `repo_url`, leia a descrição, o README e instalação/uso. Escolha a finalidade principal:

| Valor exato | Como reconhecer |
|---|---|
| `biblioteca/framework` | É usado como dependência, SDK ou base para construir outro software. |
| `aplicação/serviço` | É aplicativo, servidor ou serviço utilizado diretamente ou operado como produto. |
| `ferramenta CLI` | O uso principal documentado é por comandos no terminal. |
| `outro` | A finalidade principal não cabe nas anteriores, como documentação, dados ou configurações. |

Não classifique pela linguagem. Um pacote instalado pelo terminal não é
automaticamente CLI. Em um projeto híbrido, use o propósito principal descrito
na documentação. `outro` não é sinônimo de falta de investigação.

### 4.2. Releases representam entregas reais?

Consulte a distribuição do produto e as releases:

- `sim`: há versão utilizável distribuída a consumidores, como pacote, imagem,
  aplicação, binário ou versão do código efetivamente disponibilizada para uso.
- `não`: são somente marcações internas/metadados, sem entrega consumível identificável.
- `incerto`: não há evidência suficiente para decidir.

Não exigir executável anexado ao GitHub: bibliotecas podem ser publicadas em
gerenciadores de pacotes. Automação não torna uma entrega falsa. Uma release
também não comprova implantação em produção. Esta classificação é por projeto.

### 4.3. Cada release é corretiva?

Abra `release_url` e leia as notas. Se forem vagas, abra `compare_url`, leia
mensagens de commits e, quando necessário, PRs/issues públicas referenciadas.
Não é necessário clonar ou executar código dos projetos.

- `sim`: o objetivo principal é corrigir defeito recente, regressão, vulnerabilidade
  ou reverter uma mudança defeituosa.
- `não`: funcionalidades, documentação, manutenção rotineira ou versão mista sem
  foco predominantemente corretivo.

Exemplos fictícios: uma versão focada em corrigir travamento é corretiva; uma
versão focada em novas telas não é; uma correção ortográfica no README não conta
como correção de defeito do software. Atualizar uma dependência só por rotina
difere de atualizar para resolver vulnerabilidade explicitamente identificada.

Não decida automaticamente por tag patch, palavra `fix` ou poucos dias entre
versões. Considere o significado e o objetivo principal, não só a contagem de commits.
O campo `corretiva` admite somente `sim`/`não`. Se não houver base, registre o
caso pendente nas suas notas e amplie a leitura, sem inventar uma conclusão.
Uma lacuna insolúvel exige tratamento metodológico, não uma resposta fabricada.

Se um link quebrar ou tiver sido editado, procure o `release_id` exato em
`fontes_releases.json` e confirme `full_name`. Leia `body` e `mensagens_commits`;
`origem_notas` identifica a origem. Não substitua o item por outra release.
Sem comparação disponível, use as notas e fontes oficiais; não marque `não`
automaticamente pela falta de uma comparação.

Faça a linha do projeto e suas cinco releases antes de avançar. Salve por blocos.
Pode manter justificativas/URLs individuais em `cache/anotacoes_A.md`, fora do Git,
sem adicionar colunas à planilha nem compartilhar votos antes do término dos três.

## 5. Validar A e registrar sua origem

Salve e feche o Excel. A partir de `Lab03/`:

```text
python -m scripts.validar_rotulos_b data/amostra_ouro_s02/rotulos/rotulos_A.xlsx
```

O nome B é legado; o comando também verifica A. Exige 60 projetos, 300 releases,
cinco por projeto, sem campos de avaliação vazios, duplicados ou categorias inválidas.
Não use `--exigir-revisao`: exige campos adicionais ausentes do modelo XLSX.
O resultado verifica estrutura, não prova autoria ou independência.

No PowerShell, obtenha os hashes:

```powershell
(Get-FileHash '.\data\amostra_ouro_s02\rotulos\rotulos_A.xlsx' -Algorithm SHA256).Hash.ToLowerInvariant()
(Get-FileHash '.\data\amostra_ouro_s02\releases_sorteadas.csv' -Algorithm SHA256).Hash.ToLowerInvariant()
(Get-FileHash '.\data\amostra_ouro_s02\repos_sorteados.csv' -Algorithm SHA256).Hash.ToLowerInvariant()
```

No Linux, use `sha256sum` nesses mesmos três arquivos, na mesma ordem.
Crie pelo editor `data/amostra_ouro_s02/rotulos/rotulos_A.manifest.json`:

```json
{
  "avaliador": "A",
  "origem": "humana",
  "id_avaliacao": "Diogo-S02-A-DATA-REAL",
  "arquivo_sha256": "PRIMEIRO-HASH-REAL",
  "itens_sha256": "SEGUNDO-HASH-REAL",
  "repos_sha256": "TERCEIRO-HASH-REAL",
  "avaliacao_concluida": true,
  "rotulos_outros_lidos": false,
  "saida_heuristica_lida": false
}
```

Preencha somente depois de concluir e somente com declarações verdadeiras.
Se IA decidiu rótulos, use `assistida_por_IA`, não `humana`. Se houve exposição
a outros votos/previsões, registre e alinhe o tratamento, sem atestar leitura cega.
Se alterar a planilha depois, recalcule seu hash. Não altere a amostra sorteada.
Entregue sua planilha e manifesto antes de começar o consenso.

Para publicar sua avaliação, use sua conta e identidade Git. Confira `git diff`
e inclua somente seus dois arquivos, sem `git add .`, force push ou alterações em B/C.
Se usar sua branch própria, envie-a e alinhe o merge com a branch de integração
do PR #162; não suponha que já foi incorporada só porque fez push em outra branch.

## 6. Só depois das três avaliações: conferir entradas e calcular kappa

Reúna A, B e C e seus manifestos na mesma versão do checkout. As avaliações e
manifestos individuais devem ser preservados. Agora pode consultar divergências.

Primeiro, execute esta validação sem gerar consenso:

```text
python -c "from validacao.fechamento_s02 import validar_avaliacoes; validar_avaliacoes('data/amostra_ouro_s02'); print('Tres avaliacoes validas para a amostra definitiva')"
```

Se faltar arquivo/hash/origem ou houver itens diferentes, resolva a entrada correta.
Não remova a verificação para continuar. O arquivo de preparação das planilhas
registra hashes dos modelos vazios, não substitui os manifestos das avaliações.

Com as entradas conferidas, calcule a concordância e o consenso inicial:

```text
python -m validacao.concordancia --pasta data/amostra_ouro_s02 --tex docs/artigo/tabelas/kappa_s02.tex
```

O comando grava arquivos; não é uma consulta. Usar os argumentos explícitos evita
os defaults legados do piloto. Confira em `data/amostra_ouro_s02/`:

- `kappa_fleiss.csv`: três dimensões, com 60, 60 e 300 itens, respectivamente.
- `casos_divergentes.csv`: votos distintos, maiorias e eventuais desempates pendentes.
- `consenso_repos.csv`: tipos e entregas por projeto.
- `consenso_releases.csv`: corretiva por release.

Kappa mede concordância descontando o acaso, não a porcentagem de acertos.
Relate o valor calculado, interpretação e concordância unânime. Não mude votos
para aumentar kappa. Se não houver variação e ficar indefinido, relate isso;
não substitua por 1. O kappa usa os votos independentes, antes da adjudicação.

## 7. Resolver consenso sem apagar as avaliações

- Três votos iguais: unanimidade.
- Dois iguais: maioria simples; não precisa inventar uma reunião por item.
- Três categorias diferentes: reunião real dos três para decidir e justificar.

Na dimensão binária `corretiva`, com três votos válidos, não existe empate 1-1-1.
Os empates podem ocorrer nas dimensões com três ou quatro categorias.

Para os casos pendentes indicados como `reuniao`, registre as decisões em
`data/amostra_ouro_s02/decisoes_reuniao.csv`, com cabeçalho:

```text
dimensao,chave,rotulo
```

Copie dimensão e chave exatamente de `casos_divergentes.csv`; para projeto a chave
é `full_name`. Se a dimensão de release for usada em registros, a chave é
`full_name|release_id`. Use rótulos permitidos e não duplique a mesma dimensão/chave.
Documente participantes, data, evidências e justificativa em registro de reunião
separado. Não declare reunião que não ocorreu nem modifique o XLSX individual
para fazê-lo coincidir com a decisão coletiva.

Rode a concordância novamente com os mesmos argumentos. O comando pode escrever
CSVs parciais mesmo quando retorna pendência: existência de arquivo não significa
consenso final. Só entregue consenso sem rótulos vazios e com 60 projetos/300 releases.

## 8. Integrar com Pedro e atualizar o artigo

A execução direta de concordância não gera os manifestos de consenso exigidos
pelo dataset. Depois de resolver os desempates, coordene com Pedro esta execução:

```text
python -m scripts.fontes_s02 restaurar
python -m validacao.fechamento_s02 --config config_s02.yaml --validar-avaliacoes
```

Restaure fontes somente se necessário; o comando verifica o pacote e recusa
sobrescrever fontes locais diferentes. Não refaça a coleta.
O fechamento integrado gera proveniência do consenso, avalia a heurística,
recalcula o dataset e atualiza trechos do artigo. Se F1 < 0,70, retorna código 1
e registra a pendência: isso é trabalho de refinamento de B, não motivo para
alterar rótulos independentes. Não execute simultaneamente com outra integração.

Sua revisão de A inclui:

| Caminho | O que revisar |
|---|---|
| `docs/artigo/metodologia.tex` | Funil, janela oficial, seleção, definições, variantes, sorteio, kappa e consenso reais. |
| `docs/artigo/tabelas/funil.tex` e `numeros.tex` | Tabelas/números gerados das fontes; não editar para ajustar resultados. |
| `docs/artigo/tabelas/kappa_s02.tex` | Três dimensões e resultados definitivos, sem misturar piloto. |
| `docs/dicionario_dados.md` | Nomes, tipos, unidades e fórmulas coerentes com o dataset final. |
| `docs/protocolo_consenso.md` | Protocolo efetivo; usar a pasta definitiva nos comandos. |
| `data/amostra_ouro_s02/consenso_repos.manifest.json` e `consenso_releases.manifest.json` | Manifestos gerados pelo fechamento e vinculados às avaliações corretas. |

Na metodologia, confira explicitamente a janela de 01/10/2025 a 30/09/2026,
semente 42 tanto para repositórios quanto para releases, 60 projetos com cinco
releases cada e população definitiva de 300 após os filtros. O snapshot real
tem 53.143 candidatos; foram avaliados 2.644 até aceitar os 300. As consultas
efetivamente usadas abrangem 1.000 a 8.000 estrelas: faixas adicionais previstas
no config não são consultas realizadas. Os números gerados devem continuar
vinculados às fontes congeladas, não a uma busca nova ou ao piloto.

Para conferir a implementação de A sem executar a coleta ou gerar votos:

```text
python -m pytest tests/test_amostra_ouro.py tests/test_concordancia.py tests/test_artefatos_artigo.py -q
python -m pytest --cov=metricas --cov-report=term-missing --cov-fail-under=80
```

Preserve a parte de coleta de Lorran e coordene com Pedro alterações na mesma
metodologia. Não descreva refinamento/avaliação na mesma amostra como validação
em dados não vistos. Não declare sprint pronta só por ter consenso: F1 e dataset
final ainda precisam da integração B/C.

## 9. Pendência compartilhada dos outros 240 tipos

O consenso cobre apenas os 60 projetos da amostra-ouro. Foi sugerida uma divisão
complementar de 80 dos outros 240 para cada integrante, mas não há atribuição
acordada/gerada. Combinem responsáveis e critérios antes de começar.
Não são outras 400 releases para avaliar: a pendência complementar é a classificação
do tipo do projeto, com fonte e avaliador identificados. Não apresente avaliação
única como consenso de três. A importação dessa classificação ainda precisa ser
implementada e testada com C; apenas criar um CSV não completa o dataset.

## 10. Checklist de conclusão de A

- [ ] Avaliei independentemente a planilha A definitiva: 60 projetos e 300 releases.
- [ ] Estrutura passou no validador; manifesto de A está verdadeiro e com hashes atuais.
- [ ] As três avaliações/manifestos estão integrados e foram validados.
- [ ] Kappa calculado para 60 tipos, 60 avaliações de entrega e 300 corretivas.
- [ ] Maiorias e desempates foram registrados sem sobrescrever votos individuais.
- [ ] Consenso completo, com manifestos vinculados à amostra correta.
- [ ] Artigo e dicionário estão coerentes; resultados do piloto não viraram definitivos.
- [ ] Entreguei ao Pedro/Lorran os artefatos reais e pendências, sem declarar F1 ou tipos ainda inexistentes.

Próxima ação: preencher sua planilha A; consenso só depois das três avaliações.
