# Correções finais da Sprint 2 — 15/10/2026

## Escopo e preservação

Correções dos cinco achados da revisão final, sem nova coleta ou reclassificação.
As três avaliações da amostra-ouro e os 240 tipos complementares foram mantidos.
Lorran confirmou a revisão humana individual de todas as linhas após as sugestões
automáticas. O artigo registra esse processo e suas limitações, sem atribuir
consenso triplo aos 240 projetos nem tratar hash como prova de análise humana.

Foram comparados antes/depois os hashes de 17 entradas/artefatos protegidos:
amostra e manifesto, pacote de fontes, dataset, consensos, planilhas/manifestos,
complementares/manifesto e implementação da heurística v3. Todos permaneceram
idênticos. O dataset continua com 300 tipos, 11 CFR (b) indisponíveis e SHA-256
`8c494ec09f475e7f44d512f72329257d5bb7c470b8a09e1cf75d5b273b995ee9`.

## O que foi corrigido e por quê

| Arquivo | Correção | Motivo |
| --- | --- | --- |
| `.gitattributes` | `-text` para `Lab03/data/classificacao_complementar/**`. | Evita conversão CRLF/LF dos bytes atestados por SHA-256. |
| `pipeline/dataset.py` | Cabeçalhos obrigatórios e sem duplicação; linhas com a quantidade correta de campos; campos obrigatórios não vazios. | Não aceitar campos ausentes transformados no texto `None`. |
| `pipeline/dataset.py` | Validação offline de URLs HTTP(S) com host, sem credenciais/espaços e com porta válida; datas em `AAAA-MM-DD`. | Exigir formatos coerentes sem depender da rede. Isso não verifica a disponibilidade da página. |
| `pipeline/dataset.py` | Conferência de todos os campos canônicos do manifesto; recusa de divergência e reutilização sem regravação. | Não apagar inconsistências de origem/contagem silenciosamente. A primeira criação ocorre após validar as entradas. |
| `scripts/gerar_classificacao_complementar.py` | Entrada explícita, sugestões separadas por padrão em cache, campos de revisão vazios e recusa de sobrescrita/destino final. | Preservar revisões humanas e não declarar nomes, origem ou datas de avaliações inexistentes. |
| `tests/test_dataset.py` | Cenários independentes para valores/campos/estrutura/chaves/cobertura/manifestos, além de BOM e origem mista. | Testar a recusa exata, sem um erro de duplicação esconder o teste de categoria. |
| `tests/test_classificacao_complementar.py` | Proteções do gerador e preservação de bytes pelo Git com autocrlf ligado. | Cobrir os dois riscos operacionais identificados. |
| `tests/test_artigo.py` | Coerência dos resumos com a etapa complementar concluída. | Evitar regressão da contradição entre resumo e corpo do artigo. |
| `docs/artigo/artigo.tex`, `metodologia.tex`, `metodologia_coleta.tex` | Resumos coerentes, pré-classificação/revisão humana e ameaças específicas documentadas. | Descrever o processo confirmado, sem exagerar a evidência. |
| `README.md`, dicionário, fechamento, evidências e pendências | Estado atual reconciliado, hash correto, instruções seguras e históricos identificados. | Não orientar repetição de tarefas concluídas nem confundir cálculo local com publicação. |
| `docs/artigo/artigo_s02_parcial.pdf` | PDF recompilado e sete páginas conferidas visualmente. | Sincronizar o documento entregue com os fontes corrigidos; nome mantido por compatibilidade. |

As linhas em branco adicionais ao fim dos três arquivos apontados na revisão
foram removidas. `git diff --check` não aponta erros de whitespace.

## Validação e limites

Os 62 testes focais de dataset, gerador e fechamento passaram. A validação completa
foi executada em uma cópia exportada pelo Git com finais LF, usando um índice
temporário, sem selecionar arquivos no staging real ou criar um commit.
Nessa cópia, a restauração verificou as 311 fontes, e o fechamento reproduziu
dataset e cinco tabelas byte a byte, com `entrega_completa: true`, zero tipos
ausentes e a mesma v3: F1 `0,7431693989071039`, VP=68, FP=28, FN=19, VN=185.
A suíte completa da cópia exportada passou com **321 testes em 145,65 segundos**
e **95,51% de cobertura em `metricas`**. Esse percentual não representa a
cobertura de todo o importador, que fica em outro pacote.

A execução usou Python 3.12.14 no Windows. Exportar com LF verifica os bytes do
Git; não equivale a executar em um runner Linux ou ao CI de um novo commit.
O PDF foi compilado com Tectonic 0.17.0, com saída de sucesso e avisos de fonte/
espaçamento não impeditivos; todas as páginas foram inspecionadas após a compilação.

As validações acima foram realizadas antes do commit/push. A publicação no PR
#162, o CI do commit publicado e o merge na main são etapas separadas; seus
estados devem ser conferidos no GitHub, não inferidos deste registro local.

## Responsabilidades restantes

Não há nova rotulagem manual identificada. Lorran confirmou a conferência final
do grupo e autorizou a publicação na branch da entrega. O próximo passo é
commit/push, atualização do PR e CI do novo commit; merge é uma etapa separada.
Não foi identificada uma exigência de envio em outra plataforma. A menção
anterior a uma submissão separada era uma possibilidade genérica, não um
requisito confirmado do enunciado.
