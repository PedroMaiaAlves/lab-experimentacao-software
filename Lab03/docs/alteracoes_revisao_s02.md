# Sprint 2 — alterações e justificativas da revisão

Registro histórico da revisão anterior à classificação complementar. Os 240 tipos
e o importador foram entregues posteriormente; consulte `fechamento_s02.md` e
`pendencias_manuais_s02.md` para o estado atual, sem repetir as etapas concluídas.

Referência: estado local conferido em 15/10/2026, na branch
`codex/lab03-s02-lorran-parte-c`, baseada no commit `bf2288d`.
Este inventário distingue correções minhas de arquivos que já estavam preenchidos
ou implementados quando fiz a revisão. Não é uma lista de novos commits publicados.

## Resultado da revisão

A coleta dos 300 repositórios está concluída. As três avaliações da amostra-ouro
estão preenchidas, com origem humana declarada pelos integrantes e integridade
conferida. O consenso e a validação da heurística estão disponíveis localmente.
A entrega ainda não está completa: faltam classificar os outros 240 projetos e
integrar essa classificação ao dataset com proveniência.

Na última execução completa registrada, passaram 279 testes, com cobertura de
95,51% em `metricas`. Isso é teste local, não CI das alterações ainda não publicadas.

## 1. Correções que fiz no código

| Arquivo, a partir de `Lab03/` | O que alterei | Por quê |
| --- | --- | --- |
| `metricas/cfr.py` | Acrescentei a heurística v3, mantendo os caminhos v1/v2. Na v3, um commit conta no máximo uma vez como correção, mesmo contendo várias palavras-chave ou um termo crítico. | Na v2, um único commit podia ser contado várias vezes, distorcendo a proporção entre correções e funcionalidades. |
| `metricas/cfr.py` | Fiz a v3 respeitar `usar_palavras_commits: false`, sem consumir as mensagens nem deixar que influenciem o resultado; o critério de patch pode atuar sozinho se habilitado. | Desligar o texto precisa realmente desligar seu uso. Na v2, mensagens ainda influenciavam a decisão de patch. |
| `config_s02.yaml` | Ativei `versao: v3`. Não alterei a janela oficial, sementes ou filtros. | O dataset precisa usar a regra corrigida, sem apagar a versão anterior. |
| `validacao/fechamento_s02.py` | Vinculei a avaliação v3 ao SHA-256 da implementação de `metricas/cfr.py`, normalizando somente esse texto para UTF-8/LF. | Detecta troca de implementação sob o mesmo nome de versão sem gerar divergência artificial entre Windows e Linux por CRLF/LF. Os hashes dos dados continuam sobre os bytes originais. |
| `validacao/fechamento_s02.py` | Separei `validacao_concluida` de `entrega_completa`, explicitando tipos pendentes e CFR indisponíveis. Mantive o campo legado `concluido`. | A validação pode passar enquanto o dataset ainda tem tipos ausentes. O estado não deve esconder essa pendência. |

A v3 corrige os comportamentos acima; não é uma autorização para modificar os
rótulos humanos até a métrica melhorar. O resultado continua sendo medido na mesma
amostra usada no refinamento, não em uma amostra independente de teste.

## 2. Testes que acrescentei ou ampliei

| Arquivo | Verificação acrescentada |
| --- | --- |
| `tests/test_cfr.py` | Contagem única por commit; preservação da v2; controles de texto/patch; ausência de consumo do iterador quando o texto está desligado; limites da proporção; mensagens vazias, ruído, tags com namespace e configuração inválida. |
| `tests/test_dataset.py` | Integração da v3 ao cálculo do dataset, inclusive censura e texto desligado. |
| `tests/test_integracao_s02.py` | Execução integrada com fixtures de 300 projetos, tanto em v1 quanto em v3, e recálculo offline. Os 300 dessas fixtures são simulados, não a prova da coleta real. |
| `tests/test_fechamento_s02.py` | Vínculo da v3 com o hash do código e distinção entre validação aprovada e entrega ainda incompleta. |

O conjunto passou de 262 para 279 casos executados. A configuração do GitHub
Actions já existia; não a apresentei como uma alteração nova desta revisão.

## 3. Artefatos recalculados ou conferidos

| Arquivos | O que fiz e motivo |
| --- | --- |
| `data/amostra_ouro_s02/avaliacao_v3.csv` e `avaliacao_v3.manifest.json` | Registrei a avaliação da versão corrigida e seus vínculos de integridade. |
| `data/amostra_ouro_s02/heuristica_metricas.csv` e `heuristica_versoes.md` | Acrescentei o registro v3, preservando os resultados v1/v2 para reprodução. |
| `data/dataset.csv` e `dataset.manifest.json` | Recalculei os 300 projetos com v3 e o consenso válido dos 60. Mantive 240 tipos ausentes e 11 CFR (b) indisponíveis, sem inventar valores. |
| `data/amostra_ouro_s02/fechamento.json` | Atualizei o estado gerado: validação qualificada, entrega incompleta e pendência explícita dos 240 tipos. |
| `docs/artigo/tabelas/validacao_s02.tex` e `coleta_s02.tex` | Atualizei os números gerados para corresponderem aos resultados locais. |
| `docs/artigo/tabelas/kappa_s02.tex` | Conferi a regeneração; os kappas não mudaram. |
| Consensos de repositórios/releases e respectivos manifestos | Conferi integridade e reprodução. O recálculo preservou o conteúdo dos consensos; não fiz novos julgamentos humanos. |

Resultados para conferência:

| Versão | Precisão | Recall | F1 | VP | FP | FN | VN |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| v1 | 0,313725 | 0,919540 | 0,467836 | 80 | 175 | 7 | 38 |
| v2 | 0,701031 | 0,781609 | 0,739130 | 68 | 29 | 19 | 184 |
| v3 | 0,708333 | 0,781609 | 0,743169 | 68 | 28 | 19 | 185 |

Kappas preservados: tipo de projeto `0,966750`; releases como entregas `1,000000`;
release corretiva `0,961787`. Não houve caso 1-1-1 exigindo desempate.

## 4. Documentação e artigo

| Arquivo | Alteração e justificativa |
| --- | --- |
| `README.md` | Atualizei o estado local e retirei a indicação de que o piloto bastaria para validar a amostra definitiva. |
| `docs/fechamento_s02.md` | Documentei o fechamento parcial, a v3, sua integridade e a escolha da avaliação B local, preservando a rastreabilidade da versão remota diferente. Contém registros históricos; o bloco atual deve ser lido junto deles. |
| `docs/entrega_s02_c.md` | Acrescentei o estado atual, sem apagar o histórico da entrega C. |
| `docs/evidencias_s02_c.md` | Registrei os resultados atuais, testes, reprodução e limitações, distinguindo-os das evidências antigas. |
| `docs/artigo/artigo.tex` | Atualizei resumo/abstract para não anunciar fechamento integral enquanto os tipos complementares estão ausentes. |
| `docs/artigo/metodologia.tex` | Expliquei v1/v2/v3, correções, validação na mesma amostra e ausência de necessidade de desempate. |
| `docs/artigo/metodologia_coleta.tex` | Diferenciei a revisão assistida provisória das avaliações humanas declaradas da amostra definitiva e explicitei os 240 tipos pendentes. |
| `docs/artigo/README.md` | Expliquei a compilação e por que o PDF ainda é parcial. |
| `docs/artigo/artigo_s02_parcial.pdf` | Recompilei o artigo e conferi visualmente as sete páginas produzidas. O nome parcial foi mantido intencionalmente. |
| `docs/pendencias_manuais_s02.md` | Criei uma síntese das tarefas restantes, incluindo a ausência do importador complementar. |

Os três guias anteriores, `docs/orientacoes_diogo_s02.md`,
`docs/orientacoes_pedro_s02.md` e `docs/orientacoes_lorran_s02.md`, foram preparados
em etapas anteriores. Não significam que seja necessário repetir agora as três
avaliações concluídas. Nesta resposta, acrescentei este inventário e o guia
`docs/guia_finalizacao_s02.md`; não alterei novamente a heurística ou as planilhas.

## 5. Trabalho preexistente que preservei — não foi autoria minha nesta revisão

- As avaliações A/B/C e suas declarações de origem humana foram fornecidas pelos
  integrantes. Conferi estrutura, hashes e preservação dos identificadores;
  não produzi esses votos nem posso provar sua independência cognitiva por hash.
- Os arquivos `avaliacao_v1.*`, `avaliacao_v2.*`, `casos_divergentes.csv`,
  `consenso_repos.*`, `consenso_releases.*`, `kappa_fleiss.csv` e os manifestos A/B
  já integravam o trabalho local recebido, embora vários ainda não estejam no Git.
- A implementação v2, o consenso e o histórico anterior foram reaproveitados.
  O diff inteiro do diretório não corresponde apenas ao código que eu escrevi.
- A coleta real, o congelamento, o pacote `data/fontes_s02.zip` e o mecanismo de
  restauração offline vêm das etapas anteriores. Não repeti a mineração nesta revisão.

## 6. Integração Git que fiz e publicação que ainda não fiz

Integrei por fast-forward o commit remoto `bf2288d`. Antes disso, preservei o WIP
com backup e stash. Esse commit continha uma avaliação B diferente, declarada
assistida por IA. Você confirmou que a avaliação local B era a correta; mantive
esse arquivo local distinto e seu manifesto, sem mudar a origem do arquivo remoto
nem apagar o commit do Pedro.

Conferi os 43 arquivos do WIP anterior à integração: os conteúdos foram
preservados; diferenças de 12 textos eram apenas normalização de finais de linha.
Não restaram conflitos ou arquivos no staging. Mantive o stash de recuperação
`Preserva WIP S02 v3 antes de integrar bf2288d`. Não o reaplique sobre o estado atual.

Não fiz novo commit, push, edição do PR ou merge na main com essas correções.
O PR #162 permanece como referência da branch, mas seu conteúdo publicado não
deve ser confundido com tudo que está modificado localmente.

## 7. Limites e próxima ação

Os dados atuais têm 300 projetos, mas só os 60 da amostra-ouro possuem tipo.
Ainda não existe importador para a classificação complementar. A solução é
classificar os outros 240 com evidência e proveniência, implementar sua importação,
recalcular e validar tudo, atualizar o artigo e só então publicar o fechamento.

Não é necessário recolher novamente os 300, alterar votos, preencher ausência com
zero ou reabrir o sorteio. Os 11 CFR (b) indisponíveis devem continuar documentados
enquanto não existir evidência suficiente. Consulte o passo a passo em
`guia_finalizacao_s02.md`.
