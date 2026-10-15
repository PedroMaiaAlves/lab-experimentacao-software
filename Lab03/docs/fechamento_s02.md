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

A coleta real terminou em 15/10/2026, às 05:15 UTC (02:15 em Brasília).
Dos 53.143 candidatos do snapshot, 2.644 foram avaliados e 300 aceitos,
coletados e congelados. A validação estrutural conferiu os 11 CSVs agregados
e a completude das execuções dos 300 repositórios. Não há coleta em andamento.
O checkpoint e os logs originais permanecem localmente em `data/s02/` e `cache/s02/`.

As 311 fontes necessárias para reprodução (11 CSVs e 300 JSONs de runs) estão
publicadas em `data/fontes_s02.zip`, sem cache ou credenciais. O pacote ocupa
75.015.661 bytes e seus arquivos são conferidos contra o manifesto congelado.
Para reproduzir em um checkout novo, execute em `Lab03/`, sem token:

```bash
python -m scripts.fontes_s02 restaurar
python -m pipeline.dataset --config config_s02.yaml
```

A restauração recusa arquivos locais diferentes; não apague fontes para contornar
essa proteção. `python -m scripts.fontes_s02 verificar` confere o pacote sem extrair.
O teste real de restauração em diretório separado e recálculo offline produziu
um dataset idêntico byte a byte ao publicado.

- Amostra: SHA-256 `61468b19b001f71b10cd24d3323cdeb7bef915dac2b788ed65640194dac416fd`.
- Dataset: SHA-256 `6bf51ed7ce2587d1b36586c3912d4827b32ac9773e6640948b06deab745be0a8`.
- Fontes ZIP: SHA-256 `bf26c9a146a0823bd7cdf3e2fac882ef66de99b5c9b863982bee3ce2cd42db95`.

O sorteio definitivo e as três planilhas em branco estão publicados e conferidos.
Cada planilha contém 60 repositórios e 300 releases, URLs da amostra definitiva e
listas de valores permitidos, sem rótulos ou previsões. As URLs são texto para
copiar no navegador. `preparacao_planilhas.json` registra os hashes dos modelos,
não atesta avaliações concluídas. Há 10 repositórios e 50 releases em comum com
o piloto; as outras 250 releases exigem novas avaliações. Reaproveitamento dos
itens comuns depende de confirmação da origem e manutenção das definições.

### Aceite por tarefa

- C1 concluída: coleta real dos 300, filtros verificados e amostra congelada.
- C2 implementada e reproduzida, mas ainda não final: heurística v1 não revalidada
  na amostra definitiva; todos os 300 tipos ainda estão ausentes. Mesmo após o
  consenso dos 60, os demais 240 não ganham tipos automaticamente. Sete CFR (b)
  permanecem indisponíveis por evidência insuficiente, não iguais a zero.
- C3 pendente: Lorran e os colegas precisam realizar/confirmar suas avaliações
  independentes. Nenhuma avaliação substituta de IA foi gerada nesta etapa.
- C4 concluída quanto à coleta: metodologia e números reais incluídos no artigo;
  a versão final deve refletir o consenso e a heurística efetivamente validados.
- A1/A4/A5 integradas; A2/A3 e B2/B3/B4 dependem das avaliações definitivas,
  consenso, kappas e F1. O pipeline de fechamento já executa esses cálculos quando
  as entradas legítimas estiverem disponíveis.

`fechamento.json` continua com `concluido: false`, corretamente. Não usar o F1 do
piloto para certificar a nova amostra. A revisão C anterior é assistida por IA e
provisória sobre o piloto, com 19 decisões sem evidência suficiente; foi preservada,
não incorporada como avaliação humana. O PR permanece em rascunho, sem merge na main.
