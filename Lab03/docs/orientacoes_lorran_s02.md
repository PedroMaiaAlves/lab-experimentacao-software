# Lorran — roteiro para finalizar a parte C da Sprint 2

## 1. O que está pronto e o que depende de você

A coleta dos 300 repositórios terminou. Não execute outra mineração para fazer
a rotulagem. Amostra, fontes e dataset estão na branch
`codex/lab03-s02-lorran-parte-c`, no PR #162. Ainda não estão integrados à main.

Sua tarefa imediata é a avaliação independente C: 60 projetos e as 300 releases
sorteadas, cinco por projeto. Não são 100 releases para cada integrante: os três
avaliam os mesmos itens separadamente. Depois vêm consenso, validação da
heurística, recálculo do dataset e revisão final do artigo.

Raiz local do projeto:

```text
C:\Users\BlueTape\Documents\lab-experimentacao-software
```

Todos os caminhos abaixo são relativos à pasta `Lab03` dessa raiz.

## 2. Arquivos que você deve usar agora

| Caminho dentro de Lab03 | Para que serve |
|---|---|
| `data/amostra_ouro_s02/rotulos/rotulos_C.xlsx` | Sua planilha definitiva. Preencher apenas os campos de avaliação. |
| `data/amostra_ouro_s02/repos_sorteados.csv` | Lista dos 60 projetos, com URLs e identificadores. Não editar. |
| `data/amostra_ouro_s02/releases_sorteadas.csv` | Lista das 300 releases, datas e links. Não editar. |
| `data/amostra_ouro_s02/fontes_releases.json` | Notas e mensagens de commits preservadas na coleta, sem previsões da heurística. |
| `docs/guia_rotulagem.md` | Definições das categorias. A instrução antiga de copiar o modelo do piloto não se aplica à amostra definitiva. |
| `docs/protocolo_rotulagem_B.md` | Critérios detalhados comuns aos avaliadores. Embora tenha B no nome, as definições são as mesmas para C. Os caminhos antigos desse documento são do piloto. |

Use sempre `data/amostra_ouro_s02/`. Não copie o modelo antigo sobre sua planilha
atual. `data/amostra_ouro/` é o piloto preservado, não a população definitiva.

### Não consultar durante sua avaliação independente

- `rotulos_A.xlsx` e `rotulos_B.xlsx`, inclusive os arquivos antigos preenchidos.
- Consensos, previsões, auditorias da heurística e resultados individuais de avaliação.
- `data/revisao_c_provisoria/`: material piloto provisório arquivado.
- O dataset ou código da heurística para obter a resposta de um item.

Estude as definições gerais, mas decida cada caso pelas fontes do projeto.
Se já tiver consultado respostas de um item, registre isso; não declare avaliação
cega que não ocorreu. Não tente reconstruir uma independência inexistente.

## 3. Preparar e preencher sua planilha

Abra `data/amostra_ouro_s02/rotulos/rotulos_C.xlsx` no Excel ou LibreOffice.
Ela contém três abas: `instrucoes`, `repositorios` e `releases`.

- Leia `instrucoes` antes de começar.
- Em `repositorios`, preencha somente `tipo_projeto` e `releases_sao_entregas`.
- Em `releases`, preencha somente `corretiva`.
- Use os valores das listas suspensas, sem criar outras categorias.
- Não altere nomes, IDs, tags, URLs, cabeçalhos ou abas. Não reordene apenas uma coluna.
- Salve no mesmo formato XLSX; não salve a planilha inteira como CSV.

Os links foram gravados como texto. Copie a URL da célula para o navegador.
Não é necessário clonar, instalar ou executar os projetos externos.

Trabalhe por projeto: leia o README, preencha sua linha de repositório e avalie
as cinco releases correspondentes. Depois avance ao próximo. Uma organização
possível são seis blocos de dez projetos, sem pressupor duração fixa por bloco.
Salve a cada bloco e anote onde parou.

## 4. Como analisar um repositório

Abra `repo_url`. Leia a descrição, o começo do README e a seção de instalação/uso.
Procure entender qual é o produto principal e quem o utiliza.

### Campo tipo_projeto

| Valor exato | Evidência que sustenta a escolha |
|---|---|
| `biblioteca/framework` | O uso principal é importar uma dependência, SDK, biblioteca ou framework para construir outro software. |
| `aplicação/serviço` | O produto é usado diretamente ou operado como aplicativo, servidor, serviço web, desktop ou mobile. |
| `ferramenta CLI` | O uso principal documentado acontece por comandos no terminal. |
| `outro` | A finalidade principal não cabe nas anteriores: documentação, listas, dados, configurações etc. |

Em projetos híbridos, use a finalidade principal apresentada pela documentação.
Não classifique pela linguagem, pela existência de uma pasta ou por ter um comando
de instalação: uma biblioteca instalada pelo terminal não vira automaticamente CLI.
`outro` não significa simplesmente que você ainda não conseguiu entender o projeto.

### Campo releases_sao_entregas

Consulte a página de releases, a instalação e a distribuição oficial do projeto.

- `sim`: as versões correspondem a algo utilizável pelos consumidores, como
  pacote, imagem, binário, aplicação ou versão distribuída do código.
- `não`: são somente marcações internas/metadados sem entrega consumível identificável.
- `incerto`: as fontes não permitem decidir com segurança.

Não é necessário haver arquivo executável anexado ao GitHub: bibliotecas podem
ser distribuídas por gerenciadores de pacotes. Tampouco uma release prova que houve
deploy em produção. Uma publicação automática não é, por si só, uma entrega falsa.
O campo é uma decisão sobre o repositório, não uma nova resposta para cada release.

## 5. Como analisar cada release

Na aba `releases`, abra `release_url` e leia as notas. Pergunte:
**o objetivo principal desta versão é corrigir um defeito do software?**

Marque `sim` quando as evidências indicarem foco em corrigir defeito recente,
regressão, vulnerabilidade ou em reverter mudança defeituosa.
Marque `não` para novas funcionalidades, manutenção rotineira, documentação,
refatoração sem defeito declarado ou versão mista sem foco predominantemente corretivo.

Exemplos fictícios de aplicação dos critérios, não respostas da amostra:

- "Corrige travamento ao abrir arquivos" em uma versão focada nesse reparo: `sim`.
- "Novo painel e exportação de relatórios": `não`.
- "Correção ortográfica no README": `não`.
- "Atualiza dependências": não prova correção de defeito; procure a motivação.
  Se a atualização resolve explicitamente uma vulnerabilidade, analise esse contexto.

Se as notas forem vagas, abra `compare_url`: leia as mensagens e, quando necessário,
o PR ou a issue pública referenciada. Não examine cada linha de código se as
evidências já explicarem claramente o propósito. Amplie a leitura nos casos ambíguos.

Não transforme os seguintes sinais em respostas automáticas:

- Tag com incremento patch.
- Palavra `fix` isolada ou número de commits de correção.
- Release publicada poucos dias depois de outra.
- Tamanho pequeno da alteração.

Esses sinais fazem parte do problema que a heurística tenta aproximar; seu julgamento
é a referência independente. Uma versão com muitas funcionalidades não é corretiva
só porque inclui uma correção secundária.

O campo `corretiva` permite apenas `sim` ou `não`. Não escreva `incerto`, `talvez`
ou justificativas nessa célula. Se ainda não houver base para uma decisão, mantenha
o caso pendente em suas notas, busque contexto e não finja que a lacuna foi resolvida.
A entrega completa exige decisões justificáveis; casos realmente insolúveis devem
ter o tratamento metodológico acordado, sem consultar votos de colegas antes da hora.

### Quando o link estiver quebrado ou diferente

Use `data/amostra_ouro_s02/fontes_releases.json`. Abra em um editor, procure pelo
`release_id` exato e confirme também `full_name`. Cada caso contém:

- `name` e `body`: título e notas preservadas.
- `mensagens_commits`: mensagens coletadas.
- `release_url`, `compare_url`, `tag_name` e `published_at`: identificação e contexto.
- `origem_notas`: origem das notas preservadas.

Uma página live pode ter sido editada depois da coleta. Anote diferenças e as fontes
adicionais consultadas, sem mudar a amostra nem substituir a release por outra.
Se não houver comparação, use as notas e fontes oficiais disponíveis; ausência de
comparação não significa automaticamente que a versão não é corretiva.

### Suas anotações

Opcionalmente, mantenha `cache/anotacoes_C.md` para uso individual: projeto/ID,
decisão, uma frase de justificativa, URLs consultadas e pendências. A pasta `cache`
não entra no Git. Não acrescente colunas à planilha canônica para essas notas.
Depois das três avaliações independentes, as justificativas relevantes podem
acompanhar a discussão e o registro do consenso.

## 6. Validar sua planilha ao terminar

Feche o Excel após salvar. Abra o PowerShell e execute:

```powershell
Set-Location 'C:\Users\BlueTape\Documents\lab-experimentacao-software\Lab03'
.\.venv\Scripts\python.exe -m scripts.validar_rotulos_b data/amostra_ouro_s02/rotulos/rotulos_C.xlsx
```

O nome B na mensagem do validador é legado: ele valida também a estrutura de C.
Ele precisa aceitar 60 projetos e 300 releases, cinco por projeto, sem avaliações
vazias ou inválidas. Se falhar, corrija a planilha, não o teste. Não use
`--exigir-revisao`: essa opção exige campos adicionais que não existem no modelo XLSX.
O contador de revisões confirmadas desse validador não substitui o manifesto abaixo.

Se `.venv` não existir em outro computador, prepare um ambiente Python e instale
`requirements.txt`. Neste checkout o ambiente já existe. A avaliação e o cálculo
offline não exigem token do GitHub.

Esse comando verifica estrutura, não comprova que você leu as fontes ou que
avaliou independentemente. A origem precisa ser registrada de forma verdadeira.

## 7. Registrar a origem da avaliação C

Somente após terminar e salvar a avaliação, obtenha os três hashes:

```powershell
(Get-FileHash '.\data\amostra_ouro_s02\rotulos\rotulos_C.xlsx' -Algorithm SHA256).Hash.ToLowerInvariant()
(Get-FileHash '.\data\amostra_ouro_s02\releases_sorteadas.csv' -Algorithm SHA256).Hash.ToLowerInvariant()
(Get-FileHash '.\data\amostra_ouro_s02\repos_sorteados.csv' -Algorithm SHA256).Hash.ToLowerInvariant()
```

No editor, crie `data/amostra_ouro_s02/rotulos/rotulos_C.manifest.json`, preenchendo
o modelo abaixo com os hashes reais e um identificador pessoal/data reais:

```json
{
  "avaliador": "C",
  "origem": "humana",
  "id_avaliacao": "Lorran-Avelar-S02-C-DATA-REAL",
  "arquivo_sha256": "PRIMEIRO-HASH",
  "itens_sha256": "SEGUNDO-HASH",
  "repos_sha256": "TERCEIRO-HASH",
  "avaliacao_concluida": true,
  "rotulos_outros_lidos": false,
  "saida_heuristica_lida": false
}
```

É um modelo, não uma declaração já feita. Use `humana` apenas se você realizou
os julgamentos. Se IA participou das decisões, registre `assistida_por_IA`.
Não declare leitura cega ou conclusão se não corresponder ao ocorrido.
Se alterar a planilha depois, atualize o hash; não altere as listas sorteadas.

Entregue ao responsável pela integração sua planilha e esse manifesto. Se for
commitar, inclua somente seus arquivos; não use `git add .` para misturar trabalho
dos colegas. A integração deve preservar os três arquivos independentes.

## 8. O que fazer depois que A e B terminarem

Não use esta etapa para descobrir respostas antes de concluir sua avaliação.

1. Diogo reúne os três arquivos e manifestos, calcula concordância e consenso.
2. Vocês resolvem os casos 1-1-1 efetivamente em conjunto e registram a decisão.
3. Pedro avalia a heurística contra o consenso, registra precisão/recall/F1 e,
   se necessário, refina e versiona a regra até atingir F1 >= 0,70.
4. Você confere a consolidação do dataset e a metodologia/números finais de C.

Com todas as entradas legítimas, o comando integrado é:

```powershell
.\.venv\Scripts\python.exe -m validacao.fechamento_s02 --config config_s02.yaml --validar-avaliacoes
```

Esse comando grava resultados: não é apenas uma consulta. Ele valida a origem,
calcula consenso/kappas/F1, recalcula o dataset e atualiza trechos do artigo.
Sem as avaliações/manifestos, ele falha. Casos sem desempate e F1 abaixo de 0,70
mantêm a entrega pendente. Não mude os critérios para apenas fazer o comando passar.

Se as fontes ainda não estiverem extraídas em um checkout novo:

```powershell
.\.venv\Scripts\python.exe -m scripts.fontes_s02 restaurar
```

O pacote verifica hashes e não sobrescreve fontes locais diferentes. Neste computador
as fontes já existem. Não rode `pipeline.sprint2` para refazer uma coleta concluída.

## 9. Arquivos para sua conferência técnica final

| Caminho dentro de Lab03 | O que conferir |
|---|---|
| `data/amostra_final.csv` | A população congelada tem 300 projetos; não modificar para acomodar rótulos. |
| `data/dataset.csv` | Uma linha por projeto; métricas, tipos, censura e ausentes conforme as fontes. |
| `data/dataset.manifest.json` | 300 projetos, heurística utilizada, consenso efetivamente usado, hashes e totais. |
| `data/amostra_ouro_s02/fechamento.json` | Pendências reais e resultado da validação integrada. |
| `data/amostra_ouro_s02/consenso_repos.csv` e `consenso_releases.csv` | Serão gerados depois das avaliações; atualmente ainda não existem. |
| `data/amostra_ouro_s02/kappa_fleiss.csv` e `heuristica_metricas.csv` | Resultados definitivos a gerar; não confundir com o piloto. |
| `docs/dicionario_dados.md` | Unidade e interpretação de cada coluna; vazio não é zero. |
| `docs/artigo/metodologia_coleta.tex` | Sua metodologia; atualizar para descrever a avaliação e consolidação efetivamente realizadas. |
| `docs/artigo/tabelas/coleta_s02.tex` | Totais de coleta gerados pelo dataset. |
| `docs/artigo/tabelas/validacao_s02.tex` e `kappa_s02.tex` | Serão gerados pelo fechamento; resultados da amostra definitiva. |
| `docs/artigo/artigo.tex` | Documento principal; conferir coerência depois das alterações dos três. |
| `docs/artigo/artigo_s02_parcial.pdf` | Versão atual, ainda parcial. Gerar e conferir novo PDF após os resultados finais. |
| `docs/fechamento_s02.md` e `docs/evidencias_s02_c.md` | Estado e evidências da entrega; atualizar quando as pendências forem realmente resolvidas. |

Para recalcular somente o dataset após o consenso/heurística final:

```powershell
.\.venv\Scripts\python.exe -m pipeline.dataset --config config_s02.yaml
```

Esse comando também grava saídas; sozinho não certifica independência ou F1.
Não altera a regra automaticamente: Pedro precisa atualizar a versão configurada
quando houver refinamento, mantendo o histórico.

Para rodar os testes:

```powershell
.\.venv\Scripts\python.exe -m pytest --cov=metricas --cov-report=term-missing --cov-fail-under=80
```

Última evidência publicada: 258 testes, 95,83% de cobertura em `metricas`.
Depois de qualquer alteração, vale o resultado da nova execução.

### Duas lacunas que não se resolvem apenas rodando o fechamento

**Tipos dos outros 240 projetos.** A amostra-ouro fornece consenso para 60.
Foi proposta uma divisão complementar de 80 dos demais para cada integrante,
mas isso não foi acordado nem uma lista de atribuição foi gerada. Combinem
explicitamente os responsáveis e o protocolo. Registrem projeto, tipo, fonte e
avaliador em material separado, sem apresentar avaliação única como consenso.
O importador atual aceita tipos do consenso; ainda será necessário implementar
e testar a importação dessa classificação complementar. Não basta anexar outro CSV.

**Sete CFR (b) indisponíveis.** Há evidência textual insuficiente em sete projetos
no dataset atual. Não são sete falhas nem necessariamente sete bugs corrigíveis
no código. Verifique se há fonte recuperável; se não houver, preserve e explique
o valor ausente. Não invente texto ou substitua a ausência por zero.

`concluido: true` no estado do fechamento qualifica aquela validação computacional.
Não comprova sozinho que os 300 tipos estão preenchidos nem que o professor
aceitou todas as decisões metodológicas. Confira também as condições acima.

## 10. Checklist pessoal

- [ ] Trabalhei na planilha C da pasta definitiva, não na do piloto.
- [ ] Avaliei sozinho os 60 projetos e 300 releases pelas fontes.
- [ ] Não consultei votos/previsões para decidir meus rótulos; registrei qualquer exposição real.
- [ ] Preenchi 60 tipos, 60 avaliações de entrega e 300 classificações corretivas.
- [ ] Preservei IDs, URLs, abas, colunas e formato XLSX.
- [ ] Resolvi ou documentei as lacunas de evidência sem inventar respostas.
- [ ] Passei no validador estrutural e registrei minha origem/hash corretamente.
- [ ] Entreguei somente minha avaliação independente para a integração.
- [ ] Depois do consenso e da heurística final, conferi dataset, artigo e testes.
- [ ] O grupo resolveu a classificação complementar dos 240, com importação testada.
- [ ] Revisei as limitações dos CFR (b) ausentes e o estado real antes da submissão.

Próxima ação imediata: abrir a planilha C, ler as instruções e começar pelo primeiro
projeto da aba `repositorios`, avaliando suas cinco releases em seguida.
