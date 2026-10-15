# Pedro — roteiro completo da parte B da Sprint 2

## 1. Sua responsabilidade e o estado atual

Você é o avaliador B. A heurística v1, o CFR (b), os testes e o avaliador de
precisão/recall/F1 já existem. A coleta dos 300 e o sorteio definitivo 60×5
também terminaram. Não comece reescrevendo o que funciona ou minerando novamente.

Falta concluir sua avaliação independente na amostra definitiva, comparar a
heurística com o novo consenso, refinar se necessário até F1 >= 0,70 e registrar
cada versão e a metodologia efetiva. O resultado do piloto não certifica a S02.

Os artefatos estão na branch `codex/lab03-s02-lorran-parte-c`, PR #162, ainda fora
da main. Lorran entregou C em `ec590f8`; não consulte os votos dele antes de
terminar B. Mesmo tendo implementado a heurística, não use suas previsões para
preencher a referência manual.

## 2. Localizar o projeto e preparar o ambiente

No computador de Lorran, os comandos são executados em:

```text
C:\Users\BlueTape\Documents\lab-experimentacao-software\Lab03
```

No seu computador, substitua o prefixo pela pasta do seu checkout. Todos os
caminhos seguintes são relativos a `Lab03/`.
Repositório: https://github.com/PedroMaiaAlves/lab-experimentacao-software

Na raiz do repositório, confira `git status --short` e preserve trabalho local
antes de trocar de branch. Execute `git fetch origin`. Não use reset, checkout
forçado ou push forçado para atualizar.

Para evitar pushes concorrentes, uma opção é criar uma branch própria a partir
da integração atual. Nome sugerido, se ainda não existir:

```text
git switch -c codex/lab03-s02-pedro-b origin/codex/lab03-s02-lorran-parte-c
```

Se já houver branch B adequada, alinhe a integração com o grupo, preservando seus
commits. A main antiga não contém todos os artefatos definitivos.

Entre em `Lab03/` para todos os comandos Python. Use o executável do seu ambiente:
no Windows, `.\.venv\Scripts\python.exe`; no Linux, `./.venv/bin/python`.
Nos exemplos abaixo, `python` representa esse executável.

Se precisar preparar um ambiente novo, crie com `python -m venv .venv` no Windows
ou `python3 -m venv .venv` no Linux e instale:

```text
python -m pip install -r requirements.txt
```

Use o executável da venv também na instalação. A rotulagem, validação e o recálculo
offline não precisam de token da API.

## 3. Arquivos para sua avaliação independente

| Caminho dentro de Lab03 | Uso agora |
|---|---|
| `data/amostra_ouro_s02/rotulos/rotulos_B.xlsx` | Sua planilha definitiva. |
| `data/amostra_ouro_s02/repos_sorteados.csv` | Identificação dos 60 projetos e links. Não editar. |
| `data/amostra_ouro_s02/releases_sorteadas.csv` | Identificação das 300 releases e links. Não editar. |
| `data/amostra_ouro_s02/fontes_releases.json` | Notas e mensagens de commits preservadas, sem previsões. |
| `docs/protocolo_rotulagem_B.md` | Definições detalhadas; seus caminhos antigos são do piloto. |
| `docs/guia_rotulagem.md` | Categorias; não seguir a instrução antiga de copiar o modelo do piloto. |

Use `amostra_ouro_s02`, não `amostra_ouro`. Não copie seus votos antigos
automaticamente: só 50 releases coincidem entre piloto e sorteio definitivo.
Reaproveitamento exige mesma identidade/definição e origem confirmada, sem
consultar respostas dos outros ou previsões da heurística.

Até concluir B, não abra A/C, consensos, auditorias, previsões, resultados da
heurística ou `data/revisao_c_provisoria/`. Leia apenas esta fase de rotulagem e
as definições; deixe a fase técnica de refinamento abaixo para depois.
Se já houve exposição a respostas, registre o ocorrido em vez de atestar leitura
cega. Não use a regra automática como substituta da sua avaliação independente.

## 4. Como fazer sua análise

Abra o XLSX no Excel ou LibreOffice e leia `instrucoes`. Cada avaliador faz os
mesmos 60 projetos e 300 releases, não um terço dos itens.

### 4.1. Aba repositorios

Abra `repo_url` no navegador. Leia descrição, README e instalação/uso. Preencha:

| Campo/valor exato | Critério |
|---|---|
| `tipo_projeto = biblioteca/framework` | Principalmente dependência, SDK, biblioteca ou base para outros programas. |
| `tipo_projeto = aplicação/serviço` | Principalmente aplicativo, servidor ou serviço usado diretamente/operado como produto. |
| `tipo_projeto = ferramenta CLI` | Principalmente ferramenta usada por comandos de terminal. |
| `tipo_projeto = outro` | Finalidade principal fora das anteriores, como documentação, dados ou configurações. |
| `releases_sao_entregas = sim` | Versões disponibilizam algo utilizável aos consumidores: pacote, imagem, aplicação, binário etc. |
| `releases_sao_entregas = não` | Somente marcações internas/metadados, sem entrega consumível identificável. |
| `releases_sao_entregas = incerto` | As fontes não permitem decidir. |

Julgue o uso principal, não a linguagem. Instalação por terminal não torna uma
biblioteca CLI. Ausência de executável no GitHub não invalida distribuição por
gerenciador de pacotes. Automação não significa entrega falsa; release não prova
deploy em produção. Esses dois rótulos são por projeto.

### 4.2. Aba releases

Abra `release_url` e leia as notas. Se necessário, abra `compare_url`, leia
mensagens e referências a PRs/issues públicas para entender o propósito.
Não é necessário clonar, instalar ou executar os projetos externos.

Preencha somente `corretiva`:

- `sim`: o objetivo principal é corrigir defeito recente, regressão, vulnerabilidade
  ou reverter mudança defeituosa.
- `não`: funcionalidades, manutenção, documentação, refatoração sem defeito
  declarado ou versão mista sem foco predominantemente corretivo.

Exemplos fictícios: versão focada em corrigir travamento é corretiva; versão de
novas funcionalidades sem esse foco não é; correção ortográfica não é defeito
do software. Atualização de dependência não prova correção: verifique a motivação,
como resolução explícita de vulnerabilidade.

Não decida por tag patch, presença isolada de `fix`, tamanho do diff ou intervalo
curto entre versões. O rótulo é semântico, não uma execução manual da heurística.
Se a evidência não sustentar decisão, registre a pendência e busque contexto.
Não invente conclusão nem crie categoria extra: o campo admite `sim`/`não`.
Casos insolúveis precisam de tratamento metodológico, sem pedir votos dos colegas
antes do encerramento das avaliações independentes.

Para link quebrado ou notas alteradas, procure `release_id` no JSON de fontes,
confirme `full_name` e leia `body` e `mensagens_commits`. Consulte `origem_notas`.
Não troque o item por outra release. Sem comparação, não presuma automaticamente `não`.

Trabalhe por projeto: sua linha e suas cinco releases, depois o próximo. Preserve
IDs, tags, URLs, cabeçalhos, ordem, abas e XLSX. Use listas suspensas, não CSV.
Anotações individuais podem ficar em `cache/anotacoes_B.md`, fora do Git, sem
modificar o esquema da planilha ou compartilhar votos antes da hora.

## 5. Validar B e registrar origem

Salve, feche o Excel e execute em `Lab03/`:

```text
python -m scripts.validar_rotulos_b data/amostra_ouro_s02/rotulos/rotulos_B.xlsx
```

Exige 60 projetos, 300 releases, cinco por projeto, sem campos de avaliação
vazios, duplicados ou categorias inválidas. Não use `--exigir-revisao`: essa opção
exige campos que não existem no XLSX canônico. Estrutura válida não prova autoria.

No PowerShell:

```powershell
(Get-FileHash '.\data\amostra_ouro_s02\rotulos\rotulos_B.xlsx' -Algorithm SHA256).Hash.ToLowerInvariant()
(Get-FileHash '.\data\amostra_ouro_s02\releases_sorteadas.csv' -Algorithm SHA256).Hash.ToLowerInvariant()
(Get-FileHash '.\data\amostra_ouro_s02\repos_sorteados.csv' -Algorithm SHA256).Hash.ToLowerInvariant()
```

No Linux, use `sha256sum` nos mesmos três arquivos. Depois de concluir, crie pelo
editor `data/amostra_ouro_s02/rotulos/rotulos_B.manifest.json`:

```json
{
  "avaliador": "B",
  "origem": "humana",
  "id_avaliacao": "Pedro-S02-B-DATA-REAL",
  "arquivo_sha256": "PRIMEIRO-HASH-REAL",
  "itens_sha256": "SEGUNDO-HASH-REAL",
  "repos_sha256": "TERCEIRO-HASH-REAL",
  "avaliacao_concluida": true,
  "rotulos_outros_lidos": false,
  "saida_heuristica_lida": false
}
```

Preencha hashes/data reais e somente declarações verdadeiras. Se IA participou
dos julgamentos, declare `assistida_por_IA`. Não ateste leitura cega se consultou
votos/previsões. Alterou o XLSX depois? Recalcule o hash, sem alterar o sorteio.
Entregue ao Diogo sua planilha e manifesto antes de olhar as outras avaliações.
Publique com sua identidade/conta, incluindo apenas seus arquivos; não use
`git add .`, force push ou alterações nos votos de A/C. Sua branch precisa ser
integrada ao checkout comum antes do consenso, sem sobrescrever o trabalho de C.

## 6. Depois de B concluída: aguardar o consenso definitivo de A

Diogo reúne A/B/C e manifestos, calcula kappa e consenso, com reunião real para
casos 1-1-1. Não altere seus votos depois de ver o resultado só para aumentar
concordância ou F1. O consenso não é apenas sua própria avaliação B.

Arquivos a receber/conferir em `data/amostra_ouro_s02/`:

- `consenso_releases.csv`: 300 IDs únicos, `corretiva` completa e categorias válidas.
- `consenso_repos.csv`: 60 projetos, tipos e avaliações de entrega.
- `consenso_releases.manifest.json` e `consenso_repos.manifest.json`: gerados pelo
  fechamento integrado depois da validação, vinculados à amostra/avaliações.
- `kappa_fleiss.csv` e registro dos desempates realizados.

Os comandos antigos da CLI de avaliação usam defaults do piloto e podem carregar
CSV de commits inteiro na memória. Para o fechamento definitivo, prefira o
orquestrador abaixo, que seleciona as fontes correspondentes à amostra-ouro.

## 7. Avaliar v1 contra o consenso correto

Somente após todos concluírem as avaliações, leia a implementação:

| Caminho | O que entender |
|---|---|
| `config_s02.yaml` | Versão ativa, regras e janela oficial. Não confundir com `config.yaml` do piloto. |
| `metricas/cfr.py` | `explicar_release_corretiva` e `calcular_cfr_b`; heurística e censura. |
| `scripts/avaliar_heuristica.py` | Junção por projeto/ID, matriz de confusão e precisão/recall/F1. |
| `validacao/fechamento_s02.py` | Proveniência, seleção das 300 releases, registro por versão e qualificação. |
| `pipeline/dataset.py` | Aplicação da regra em todos os projetos, ausentes e evidências insuficientes. |
| `tests/test_cfr.py` e `tests/test_avaliar_heuristica.py` | Comportamentos esperados e cálculos controlados. |

v1 combina patch SemVer crescente com mesmo major/minor OU tokens completos
`fix`, `hotfix`, `revert` nas mensagens dos commits, conforme configuração.
Tags não-SemVer dependem do critério textual. Isso é a regra automática existente,
não a definição a impor aos votos humanos.

Se as fontes não estiverem extraídas, restaure sem API:

```text
python -m scripts.fontes_s02 restaurar
```

O ZIP verifica hashes; arquivos locais diferentes não são sobrescritos.
Não execute nova mineração para recalcular a heurística.

Com o Diogo, em um único checkout de integração, execute:

```text
python -m validacao.fechamento_s02 --config config_s02.yaml --validar-avaliacoes
```

O comando grava consenso, proveniência, avaliação, dataset e trechos do artigo.
Não rode simultaneamente com outro integrante nem antes de receber as três
avaliações. Se houver desempate pendente, devolva para consenso. Se o F1 ficar
abaixo da meta, o código de saída 1 é uma pendência científica registrada, não
permissão para mascarar resultado ou alterar os rótulos de referência.

Confira as saídas na pasta definitiva:

| Arquivo | Como analisar |
|---|---|
| `avaliacao_v1.csv` | Cada release, consenso, previsão, critério acionado e `tipo_resultado`. |
| `avaliacao_v1.manifest.json` | Configuração avaliada e hash do consenso; não reutilizar v1 com conteúdo diferente. |
| `heuristica_metricas.csv` | Precisão, recall, F1, positivos e matriz de confusão por versão. |
| `heuristica_versoes.md` | Histórico e regras registradas, incluindo resultados abaixo da meta. |
| `fechamento.json` | Qualificação e pendências reais da execução. |

O campo `suporte` representa o número de corretivas no consenso, não o total de
300 itens. Confira também o total das quatro células da matriz e as 300 linhas
de auditoria. Use o valor não arredondado de F1 para conferir a meta de 0,70.

## 8. Entender e melhorar a heurística, se necessário

A classe positiva é release corretiva:

| Consenso | Previsão | Resultado |
|---|---|---|
| sim | sim | VP: correção detectada corretamente. |
| não | sim | FP: classificou como corretiva sem ser no consenso. |
| sim | não | FN: deixou passar uma corretiva do consenso. |
| não | não | VN: negativo identificado corretamente. |

Precisão = VP/(VP+FP); recall = VP/(VP+FN); F1 é a média harmônica entre ambos.
O avaliador usa zero nos casos de divisão sem definição, conforme a implementação;
isso não significa desempenho perfeito nem deve ser trocado por 1.

Para refinar:

1. Separe FP e FN de `avaliacao_v1.csv` e examine as fontes correspondentes.
2. Identifique padrões gerais: palavra com contexto não corretivo, versão mista,
   tag enganosa, correção sem os termos atuais etc. Não invente a causa antes de ler.
3. Proponha uma mudança que trate o padrão, sem exceções decoradas por ID/repositório.
4. Registre a motivação e exemplos de erro no histórico fora do bloco gerado.
5. Incremente a versão em `config_s02.yaml`, por exemplo v2. Se mudar código,
   também registre o commit que identifica a implementação daquela versão.
6. Acrescente testes focais e rode novamente o fechamento integrado com a mesma
   amostra/consenso. Preserve a avaliação v1 e seus resultados.

Não use a CLI legada para sobrescrever a versão anterior; o orquestrador protege
regras/consenso de uma versão já registrada. Se houver correção legítima do consenso,
preserve o histórico e registre nova avaliação/versionamento.
Não introduza outra semente, amostra ou janela para atingir a meta.

Se F1 já for >= 0,70, não há obrigação de modificar uma regra que atende ao critério.
Se continuar abaixo, relate o resultado e continue uma revisão justificável;
não prometa que atingir o limiar é garantido.
Refinar e medir na mesma amostra não comprova generalização: essa limitação deve
aparecer no artigo. Uma nova regra não pode transformar ausências de fonte em evidência.

## 9. Conferir CFR (b) e censura

Não confunda duas coisas: a heurística identifica a release corretiva; o CFR (b)
marca uma release anterior como falha quando uma corretiva posterior aparece em
até sete dias. O denominador exclui as sete últimas datas da janela.

Na janela oficial de 01/10/2025 a 30/09/2026, as datas censuradas são 24 a 30 de
setembro de 2026. Uma corretiva publicada nesse trecho ainda pode ser evidência
de falha de uma release anterior elegível. Não a exclua de toda a observação.

Confira testes de limite exato de sete dias, mais de sete dias, censura,
draft/prerelease e falta de denominador. Os sete CFR (b) indisponíveis atuais
por evidência textual insuficiente não viram zero nem falha observada.
Definir corretiva e calcular CFR são etapas distintas; F1 avalia a primeira.

## 10. Testar, documentar e entregar para C

Testes focais e depois suite completa, sem depender da API:

```text
python -m pytest tests/test_cfr.py tests/test_avaliar_heuristica.py tests/test_fechamento_s02.py -q
python -m pytest --cov=metricas --cov-report=term-missing --cov-fail-under=80
```

No artigo, coordene alterações com Diogo em `docs/artigo/metodologia.tex`:
regra final, fontes usadas, versão, protocolo manual, critérios de refinamento,
precisão/recall/F1, matriz e limitação de avaliação na mesma amostra.
Os arquivos `docs/artigo/tabelas/validacao_s02.tex` e `kappa_s02.tex` são gerados
pelo fechamento. Não digite números diferentes para forçar coerência.
Preserve a metodologia de coleta de C e use resultados da amostra definitiva.

Entregue ao Lorran a configuração/código final versionados, os registros de todas
as versões, consenso vinculado e resultados dos testes. O fechamento já recalcula
`data/dataset.csv` e seu manifesto; Lorran precisa conferir a integração e o artigo.
Um PDF antigo não se atualiza só porque os arquivos TEX mudaram: recompilar e
conferir o novo PDF faz parte da revisão final.

Não inclua tokens, `.venv`, cache, notas privadas ou alterações dos colegas em um
commit amplo. Publique só suas mudanças revisadas e integre com o grupo. A main
não deve ser mesclada automaticamente só porque um comando retornou sucesso.

## 11. Pendência compartilhada dos outros 240 tipos

O consenso cobre apenas os 60 projetos da amostra-ouro. Foi sugerida uma divisão
complementar de 80 dos outros 240 para cada integrante, mas não há atribuição
acordada/gerada. Combine primeiro os responsáveis e o protocolo. Essa etapa é
classificar o tipo do projeto, não repetir a rotulagem de releases fora do sorteio.
Registre fonte e avaliador, sem apresentar avaliação única como consenso de três.
A importação complementar ainda precisa ser implementada e testada com C;
ter F1 suficiente não preenche automaticamente os outros 240 tipos.

## 12. Checklist de conclusão de B

- [ ] Preenchi B individualmente: 60 projetos e 300 releases, sem previsões ou votos de A/C.
- [ ] Validador passou e o manifesto tem origem verdadeira e hashes atuais.
- [ ] O consenso usado é o definitivo e está completo/vinculado às três avaliações.
- [ ] Avaliei v1 antes de refinar e preservei os resultados anteriores.
- [ ] Analisei FP/FN e registrei mudanças gerais, versões e commits correspondentes.
- [ ] F1 atingiu a meta sem arredondamento enganoso, ou a pendência permanece explícita.
- [ ] CFR (b), censura e valores ausentes continuam coerentes e testados.
- [ ] Artigo e histórico descrevem a validação efetivamente realizada e suas limitações.
- [ ] Entreguei a regra final e evidências a C, sem declarar o dataset inteiro concluído só pelo F1.

Próxima ação: concluir sua avaliação B sem consultar C/A; refinamento somente após o consenso.
