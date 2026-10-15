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
sem decisão impedem o fechamento. O modo padrão de desempate é `reuniao`, com
`decisoes_reuniao.csv`.

`data/amostra_ouro_s02/fechamento.json` só recebe `concluido: true` depois de
três avaliações válidas, desempates resolvidos e F1 >= 0,70. Uma versão com F1
menor continua registrada, e uma regra/consenso diferente não sobrescreve a
avaliação já registrada sob o mesmo identificador de versão. O refinamento usa
a mesma amostra e não é evidência de desempenho em dados não vistos.
Com `--validar-avaliacoes`, pendências de desempate ou F1 abaixo da meta também
resultam em código de saída 1. A preparação inicial pode terminar com sucesso sem
declarar a validação concluída.

`concluido` e `validacao_concluida` qualificam esse fluxo computacional, não a
entrega inteira. `entrega_completa` também exige resolver `pendencias_entrega`,
incluindo os projetos sem tipo. Não confundir ausência conhecida de evidência de
CFR com valor zero. O CLI pode retornar 0 com validação aprovada e entrega parcial;
confira explicitamente os campos de estado. A v3 vincula a implementação pelo
SHA-256 de `metricas/cfr.py`, sem alterar os registros históricos de v1/v2.
Esse hash usa o texto UTF-8 com quebras LF (`implementacao_formato: utf-8-lf`),
para não mudar somente pela conversão CRLF/LF entre Windows e Linux. Os hashes
dos dados e XLSX continuam sobre seus bytes originais, sem normalização.

## Proveniência exigida

Cada planilha deve ter um arquivo ao lado, por exemplo `rotulos_A.manifest.json`:

```json
{
  "avaliador": "A",
  "origem": "humana",
  "id_avaliacao": "identificador-real-do-avaliador",
  "arquivo_sha256": "hash-da-planilha",
  "itens_sha256": "hash-de-releases_sorteadas.csv",
  "repos_sha256": "hash-de-repos_sorteados.csv",
  "avaliacao_concluida": true,
  "rotulos_outros_lidos": false,
  "saida_heuristica_lida": false
}
```

`origem` registra o processo efetivamente realizado: `humana` ou `assistida_por_IA`.
Os três identificadores precisam ser distintos. Os manifestos são declarações
auditáveis com hashes que vinculam cada arquivo à amostra sorteada, mas não
comprovam automaticamente independência cognitiva ou autoria humana.

## Preservação e critérios de aceite

- A amostra-ouro anterior em `data/amostra_ouro/` veio do piloto. Ela não é
  sobrescrita nem automaticamente promovida à população de 300.
- Sementes canônicas: 42 para os 60 repositórios e 42 para as cinco releases,
  preservando a implementação de `validacao.amostra_ouro`. O README antigo
  apontava outro módulo/layout com semente 43; essa ambiguidade foi corrigida.
- Faixas de estrelas do artigo vêm das consultas efetivas do snapshot, não de
  ampliações apenas previstas no config.
- Os 60 tipos consensuais não são extrapolados aos demais projetos. Os 240
  complementares têm revisão individual declarada e proveniência própria;
  ausências não são preenchidas com categorias ou métricas inventadas.
- `concluido` qualifica a coleta e a validação computacional com a proveniência
  declarada e integridade da amostra verificada.
- As três avaliações da amostra-ouro definitiva foram realizadas de forma independente
  pelos integrantes (Diogo = A, Pedro = B, Lorran = C), com declaração de origem humana
  e manifestos individuais conferidos.

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
- Dataset atual: SHA-256 `8c494ec09f475e7f44d512f72329257d5bb7c470b8a09e1cf75d5b273b995ee9`.
- Fontes ZIP: SHA-256 `bf26c9a146a0823bd7cdf3e2fac882ef66de99b5c9b863982bee3ce2cd42db95`.

O sorteio definitivo e os modelos foram publicados e conferidos. As avaliações
locais agora estão preenchidas, com 60 repositórios e 300 releases por integrante,
manifestos individuais de origem humana declarada e hashes válidos. Os julgamentos
não foram alterados pelas correções técnicas da heurística. As URLs são texto para
copiar no navegador. `preparacao_planilhas.json` registra os hashes dos modelos,
não atesta avaliações concluídas. Há 10 repositórios e 50 releases em comum com
o piloto; as outras 250 releases foram cobertas pelas avaliações definitivas.
O reaproveitamento dos itens comuns mantém as definições e a origem declarada.

### Classificação complementar e sua ferramenta de preparação

Os arquivos `data/classificacao_complementar/tipos_A.csv`, `tipos_B.csv` e
`tipos_C.csv` contêm 80 projetos cada, fora dos 60 do consenso. Lorran confirmou
que Diogo, Pedro e ele revisaram pessoalmente todas as linhas após a geração de
sugestões automáticas, consultando os READMEs antes do manifesto final. Esse
processo é revisão humana de pré-classificação, não consenso triplo dos 300.

`pipeline.dataset.carregar_complementar` confere cobertura exata, estrutura,
categorias, URLs HTTP(S), datas e proveniência. Um manifesto existente deve
coincidir em amostra, hashes, origem e contagem; na reutilização, não é regravado.
A criação inicial do manifesto ocorre somente após validar todas as entradas.
O diretório está protegido com `-text` em `.gitattributes`, preservando os bytes
atestados entre Windows e Linux.

O gerador é opcional e não participa do recálculo do dataset. Para preparar uma
nova rodada de sugestões, use uma entrada JSON explícita contendo `full_name`,
`description`, `topics` e `homepage` para 240 projetos distintos:

```bash
python -m scripts.gerar_classificacao_complementar --entrada caminho/snapshot.json --saida cache/sugestoes_novas
```

A entrada histórica local foi `cache/pendentes_raw.json`; ela não é necessária
para reproduzir os resultados finais, que usam os CSVs revisados e atestados.
A saída tem `tipo_sugerido` e `justificativa_sugerida`, mantendo os campos de
avaliação vazios. O programa recusa pasta existente e qualquer destino dentro
de `data/classificacao_complementar/`. Não o execute para refazer os rótulos atuais.

### Aceite por tarefa

- C1 concluída: coleta real dos 300, filtros verificados e amostra congelada.
- C2 concluída: dataset consolidado com v3 qualificada e todos os 300 tipos de
  projetos classificados e integrados (60 do consenso da amostra-ouro e 240 da
  classificação complementar particionada com links de evidência pública). Onze CFR (b)
  permanecem indisponíveis por ausência de evidência textual, mantidos como vazios.
- C3 concluída: avaliação independente do integrante C (Lorran) realizada e validada,
  com manifesto de origem humana e integridade conferida.
- C4 concluída: metodologia e números reais da coleta e validação incluídos no artigo.
- A1–A5 e B1–B4 concluídas: kappas de 0,96675, 1 e 0,96179; sem casos 1-1-1. v1/v2
  preservadas; v3 qualificada com precisão 0,708333, recall 0,781609 e F1 0,743169.

`fechamento.json` atesta `validacao_concluida: true`, `concluido: true` e
`entrega_completa: true`, com 0 projetos sem tipo e nenhuma pendência impeditiva.

A avaliação B confirmada para este consenso é a versão com SHA-256
`9a0c24b99b425ce38a269b019be8918a58870ab0a6d05d8ca09ec1ef9966f1a9`, com manifesto
de origem humana declarada, conforme confirmação recebida. O commit `bf2288d`
preserva outra avaliação B, assistida por IA, com 122 células diferentes. O par
local confirmado é uma avaliação distinta; não foi alterada a origem do arquivo remoto.

Antes da integração, todo o WIP foi preservado em stash identificado como
`Preserva WIP S02 v3 antes de integrar bf2288d`, mantido para recuperação.
A reaplicação teve conflito somente no XLSX B e no manifesto B já existente;
o par local confirmado foi restaurado e os 43 arquivos de trabalho foram
conferidos. Não houve push destas correções nem alteração da main.
