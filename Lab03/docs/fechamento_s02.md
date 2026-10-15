# Fechamento integrado da Sprint 2

Lorran autorizou complementar A, B e C. O PR #153 de A foi integrado nesta branch,
preservando sua implementação e autoria. Não foi mesclado diretamente na main.
As planilhas antigas, o consenso e o histórico da heurística continuam intactos.

## Fluxo canônico

1. `pipeline.sprint2 --config config_s02.yaml --candidatos data/candidatos.csv` retoma
   a execução real existente. Não execute uma segunda coleta no mesmo diretório.
2. Após validar os 300, o pipeline congela a amostra e chama
   `validacao.fechamento_s02`: prepara os 60 projetos/300 releases da população
   definitiva, o dataset e os números de coleta do artigo.
3. As três avaliações independentes usam esse novo sorteio, sem previsões da
   heurística nem rótulos dos demais. As planilhas são
   `data/amostra_ouro_s02/rotulos/rotulos_A.xlsx`, `rotulos_B.xlsx`, `rotulos_C.xlsx`,
   no modelo canônico de três abas. Fontes e identificadores do sorteio são imutáveis.
4. Com as avaliações concluídas, execute:

```bash
python -m validacao.fechamento_s02 --config config_s02.yaml --validar-avaliacoes
```

O comando confere cobertura e proveniência, calcula kappa e consenso, registra
precisão/recall/F1 da versão configurada e recalcula o dataset. Casos 1-1-1 ainda
sem decisão impedem o fechamento. Para adjudicação efetivamente realizada por IA,
use `--tipo-desempate adjudicacao_IA` e registre `decisoes_adjudicacao.csv` com
`dimensao,chave,rotulo`; isso não é descrito como reunião humana. O modo `reuniao`
mantém o protocolo original, com `decisoes_reuniao.csv`.

`data/amostra_ouro_s02/fechamento.json` só recebe `concluido: true` depois de
três avaliações válidas, desempates resolvidos e F1 >= 0,70. Uma versão com F1
menor continua registrada, e uma regra/consenso diferente não sobrescreve a
avaliação já registrada sob o mesmo identificador de versão. O refinamento usa
a mesma amostra e não é evidência de desempenho em dados não vistos.
Com `--validar-avaliacoes`, pendências de desempate ou F1 abaixo da meta também
resultam em código de saída 1. A preparação inicial pode terminar com sucesso sem
declarar a validação concluída.

## Proveniência exigida

Cada planilha deve ter um arquivo ao lado, por exemplo `rotulos_A.manifest.json`:

```json
{
  "avaliador": "A",
  "origem": "assistida_por_IA",
  "id_avaliacao": "identificador-real-da-execucao-ou-avaliador",
  "arquivo_sha256": "hash-da-planilha",
  "itens_sha256": "hash-de-releases_sorteadas.csv",
  "repos_sha256": "hash-de-repos_sorteados.csv",
  "avaliacao_concluida": true,
  "rotulos_outros_lidos": false,
  "saida_heuristica_lida": false
}
```

`origem` também pode ser `humana`, somente se isso corresponder ao ocorrido.
Os três identificadores precisam ser distintos. Os manifestos são declarações
auditáveis, não prova automática de cognição independente. Não atribua três
avaliações humanas a uma análise única de IA. Execuções cegas separadas de IA
também precisam ser declaradas e podem compartilhar vieses do modelo.

## Preservação e critérios de aceite

- A amostra-ouro anterior em `data/amostra_ouro/` veio do piloto. Ela não é
  sobrescrita nem automaticamente promovida à população de 300.
- Sementes canônicas: 42 para os 60 repositórios e 42 para as cinco releases,
  preservando a implementação de `validacao.amostra_ouro`. O README antigo
  apontava outro módulo/layout com semente 43; essa ambiguidade foi corrigida.
- Faixas de estrelas do artigo vêm das consultas efetivas do snapshot, não de
  ampliações apenas previstas no config.
- Nenhum tipo é imputado fora do consenso: valores ausentes e sua quantidade
  permanecem explícitos. Os tipos da amostra-ouro não se generalizam aos 300.
- `concluido` qualifica a coleta e a validação computacional com a proveniência
  declarada; não equivale a aceite do professor de avaliadores de IA, aprovação
  pelos colegas ou compilação/publicação do artigo.
- Lorran decidiu manter as avaliações dos integrantes. Não serão geradas três
  avaliações substitutas por agentes de IA. As avaliações anteriores podem ser
  reaproveitadas nos mesmos itens e definições, com origem confirmada; os itens
  novos da amostra definitiva ainda precisam das avaliações independentes.
- O C legado não é automaticamente atribuído a Lorran: ele informou não o ter
  preenchido. A revisão assistida provisória continua separada e não substitui
  a avaliação humana C sem uma revisão efetivamente realizada e registrada.

## Situação desta execução

A coleta real segue com checkpoint, cache e logs em `data/s02/` e `cache/s02/`.
Consulte o checkpoint para o progresso; valores de andamento não são resultados
finais. A validação integrada com 300 fixtures comprova o fluxo offline, não a
mineração real de 300. A revisão C anterior é assistida por IA e provisória sobre
a amostra do piloto, com 19 decisões ainda sem evidência suficiente.
