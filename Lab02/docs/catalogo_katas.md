# Catálogo e calibração dos katas

Os quatro katas foram selecionados para exercitar transformação de coleções,
ordenação, validação de entradas e tratamento de casos-limite em uma única
função Python. Eles usam contextos menos recorrentes que os enunciados
clássicos dos quais foram adaptados e não dependem de bibliotecas externas.

| Kata | Origem e adaptação | Autor | Revisor designado |
| --- | --- | --- | --- |
| 01 — Consolidar Janelas | Adaptação autoral do problema de união de intervalos. Acrescenta tolerância entre janelas, adjacência, intervalos pontuais e preservação da entrada. | Pedro (`PedroMaiaAlves`) | Lorran (`LorranX`) |
| 02 — Planejar Recargas | Adaptação autoral de problemas de consumo de recurso. Em vez de apenas contar paradas, exige os índices exatos das recargas, capacidade restaurada e validação de consumos inviáveis. | Diogo (`DiogoBrunoro`) | Lorran (`LorranX`) |
| 03 — Agrupar Alertas | Adaptação autoral da divisão de eventos em sessões por intervalo de inatividade. A separação por categoria, o encadeamento por eventos consecutivos e a ordenação dos grupos substituem o cenário clássico de logs de acesso. | Lorran (`LorranX`) | Pedro (`PedroMaiaAlves`) |
| 04 — Distribuir Cotas | Adaptação autoral do método de Hamilton, ou maiores restos, para distribuir estoque entre demandas identificadas. Acrescenta limite por demanda, estoque excedente e desempate alfabético determinístico. | Lorran (`LorranX`) | Diogo (`DiogoBrunoro`) |

## Equivalência de dificuldade

Todos os katas têm uma interface pequena, recebem uma coleção e produzem uma
nova coleção. A solução esperada combina uma passagem principal com, no
máximo, uma ordenação. Nenhum exercício exige estado persistente, entrada e
saída de arquivos, recursão, concorrência ou conhecimento de domínio.

Cada kata concentra uma decisão algorítmica central:

- consolidar intervalos que se conectam;
- recarregar antes de esgotar uma capacidade;
- separar sequências temporais por categoria e distância;
- repartir inteiros por quocientes e maiores restos.

As diferenças de contexto são compensadas pelos mesmos tipos de exigência:
ordem determinística, preservação da entrada, casos vazios ou nulos e rejeição
de dados inválidos. Cada especificação possui exatamente oito testes de
aceitação, cobrindo caminho básico, fronteiras, imutabilidade e validação.

## Adequação ao limite de 35 minutos

Uma solução direta cabe em uma função curta e pode ser construída apenas com
recursos da biblioteca padrão. A leitura do enunciado, a implementação e a
execução dos oito testes cabem no time-box de 35 minutos para um estudante que
domine listas, dicionários, laços e ordenação em Python. O limite ainda permite
uma correção após o primeiro resultado dos testes, mas desestimula arquitetura
ou otimizações que não fazem parte do objetivo experimental.

## Risco de memorização pela IA

Os padrões de união de intervalos, agrupamento temporal e maiores restos são
conhecidos, portanto o risco de a IA reconhecer parte da estratégia não é
nulo. O experimento reduz esse risco usando nomes e contextos próprios,
combinando restrições que não costumam aparecer juntas e exigindo formatos de
entrada e saída específicos. As soluções de referência não são versionadas,
e cada trial com IA parte de uma conversa nova ou temporária.

Essas medidas reduzem respostas copiadas por associação direta, mas não
eliminam conhecimento prévio do modelo. Por isso, o risco residual deve ser
considerado ao interpretar os resultados, principalmente nos katas baseados em
técnicas algorítmicas conhecidas.
