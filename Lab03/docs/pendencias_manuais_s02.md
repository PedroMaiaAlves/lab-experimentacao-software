# Sprint 2 — responsabilidades restantes

## Estado atual em 15/10/2026

As avaliações A/B/C da amostra-ouro e os 240 tipos complementares estão
preenchidos e integrados. Lorran confirmou que cada integrante revisou todas
as 80 linhas de seu lote após sugestões automáticas, consultando os READMEs.
Não é preciso repetir classificações nem avaliar novas releases.

O fluxo computacional registra validação qualificada em v3, F1 `0,743169`,
300 projetos com tipo e `entrega_completa: true`. Esse campo não comprova
publicação, aprovação do professor ou submissão na plataforma.
Os 11 CFR (b) indisponíveis continuam ausentes, não iguais a zero.

**Vocês:** a conferência final foi confirmada por Lorran, com autorização para
publicar na branch. Não há nova análise manual pendente identificada. O merge
depende do CI do novo commit e das regras do grupo. Não foi identificada uma
exigência de submissão em outra plataforma; a menção anterior era genérica.

**Assistente:** corrigir/testar código, validar integridade e reprodução offline,
atualizar artigo/dicionário/documentação e compilar/conferir o PDF. Com acesso e
autorização, pode publicar e acompanhar o CI. Merge também depende de autorização.

Para reproduzir em `Lab03/`, o comando inclui a pasta complementar por padrão:

```bash
python -m validacao.fechamento_s02 --config config_s02.yaml --validar-avaliacoes
```

O contrato atual está em `fechamento_s02.md`. As instruções anteriores abaixo e
o guia de finalização ficam como histórico; não recriem lotes sobre arquivos
preenchidos. Resultados locais não comprovam publicação no GitHub.

## Histórico — antes da classificação complementar

As três avaliações da amostra-ouro já estão declaradas concluídas e com estrutura
e hashes conferidos. Não precisam ser refeitas por causa das correções da heurística.
v1/v2 foram preservadas; v3 corrigiu os dois comportamentos identificados na revisão.
O consenso dos 60 e os cálculos estão disponíveis localmente. O artigo foi atualizado.

## Separação de responsabilidades

**Vocês, manualmente:** combinar os lotes; ler e classificar os 240 projetos
com evidência, justificativa, avaliador, origem verdadeira e data; resolver dúvidas;
conferir o enunciado e dar o aceite do grupo; realizar/confirmar a submissão ao professor.
Não é preciso refazer a rotulagem da amostra-ouro nem avaliar novas releases.

**Eu posso executar:** preparar listas e lotes; implementar/testar o importador;
validar os arquivos preenchidos; recalcular dataset, manifestos, estado e tabelas;
rodar testes; atualizar o artigo/dicionário e compilar/conferir o PDF. Posso preparar
a publicação e, com acesso e autorização, fazer commit/push/atualização do PR e
acompanhar o CI. Merge depende de autorização e das regras de revisão do grupo.

O importador pode ser desenvolvido antes, com fixtures; a integração real depende
das classificações legítimas. Não posso declarar como humanas decisões feitas por IA.
O passo a passo detalhado e essa separação estão em `guia_finalizacao_s02.md`,
seções 1.1 a 1.3.

## Falta classificar os tipos dos outros 240 projetos

Ponto de partida: `data/dataset.csv`. Selecione os projetos com `tipo_projeto`
vazio e confira a identidade com `data/amostra_final.csv`. Não altere diretamente
o dataset nem a população congelada para preencher categorias.

Antes de começar, combinem responsáveis e uma lista sem sobreposição. Dividir em
80 projetos por integrante é uma possibilidade, não uma divisão já acordada.
Não há novas releases para avaliar nesta etapa complementar: o campo pendente é
o tipo de cada projeto fora da amostra-ouro.

Para cada projeto, leia descrição, README e instruções de uso na documentação
oficial. Registre `full_name`, `tipo_projeto`, URL da evidência, avaliador, origem
da avaliação e data em um arquivo separado que o grupo defina. Categorias:

- `biblioteca/framework`: dependência, SDK ou base para construir outro software.
- `aplicação/serviço`: aplicativo, servidor ou serviço utilizado/operado diretamente.
- `ferramenta CLI`: uso principal por comandos de terminal.
- `outro`: finalidade principal fora das categorias anteriores.

Não inferir o tipo pela linguagem ou copiar o tipo de outro projeto. Não preencher
ausência com `outro` apenas para fechar a contagem. Registrem casos sem evidência
ou ambíguos para revisão. Uma avaliação individual complementar não é consenso
de três avaliadores; mantenham sua proveniência separada do consenso da amostra-ouro.

## Depois da classificação

Será necessário integrar/importar a classificação complementar com verificações
de identidade, categorias, duplicação e proveniência, sem sobrescrever os 60 tipos
do consenso. O importador atual usa somente o consenso: não basta criar um CSV.
A implementação pode ser preparada antes; a importação efetiva fica para quando
as entradas manuais legítimas estiverem disponíveis. Em seguida, posso recalcular
dataset, manifesto e tabelas, recompilar artigo e rodar testes.

Os 11 CFR (b) indisponíveis por evidência insuficiente continuam documentados;
não são erros que possam ser resolvidos inventando mensagens ou trocando por zero.
Recuperação adicional de evidência, se possível, deve ser rastreável e não alterar
silenciosamente as fontes congeladas.

## Como identificar o estado real

`data/amostra_ouro_s02/fechamento.json` diferencia:

- `validacao_concluida: true`: avaliações/consenso e meta de F1 passaram pelo fluxo.
- `entrega_completa: false`: a classificação/importação complementar está pendente.
- `pendencias_entrega`: descreve os 240 projetos sem tipo.

`concluido` foi mantido como campo legado da validação; não representa sozinho
o aceite da sprint. Não refazer coleta nem alterar votos de referência para remover
essa pendência. A publicação no GitHub e revisão/merge devem refletir o estado parcial.
