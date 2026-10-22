# Sprint 3 — entrega integrada A/B/C

## O que foi consolidado

- A: RQ01–04, censura, comparações pareadas e classificação C1, já na main `f6441c3`.
- B: RQ05/RQ06, bootstrap BCa, permutação, Holm, influência e documentação. Os
  quatro commits de Pedro até `f69b2ab` foram integrados por merge local, com autoria preservada.
- C: RQ07, combinações C1/C2/C3, kappa linear, mudanças de categoria e robustez;
  RQ08 bônus por rework rate, com ausências e sensibilidade de evidência completa.
- Artigo: `docs/artigo/artigo_final.pdf`, 9 páginas no template SBC, incluindo
  referências, resumo atualizado e RQ01–08. Fonte principal `docs/artigo/artigo.tex`.
- CI: testes, reprodução offline das três partes, seis notebooks e validação
  integrada. Uma execução local não é apresentada como execução remota no GitHub.

Não foram alterados dataset, amostra, planilhas humanas, heurística v3 ou parâmetros
da coleta. A estrutura completa dos resultados de A/B foi preservada; os manifestos
foram regenerados após a integração para registrar o ambiente/código atual.

## Executar e conferir

Dentro de `Lab03/`, após `python -m pip install -r requirements.txt`:

```bash
python -m validacao.entrega_s03 --reproduzir
python -m pytest --cov=metricas --cov-report=term-missing --cov-fail-under=80
python -m analises.notebooks_a
python -m analises.notebooks
python -m analises.notebooks_c
```

Não é necessário token, nova mineração ou extrair o ZIP. O primeiro comando confere
os hashes, dicionários, denominadores e PDF, recalcula A/B/C fora de `data/` e compara
as tabelas com as publicadas. O diagnóstico fica em
`cache/entrega_s03/validacao.json`; não substitui evidência de publicação/remoto.

Os comandos `python -m analises.sprint3_a`, `sprint3_b` e `sprint3_c` regeneram as
saídas publicadas. Depois de mudar código/entradas, regenere antes de validar:
um manifesto antigo deve falhar, não atestar resultados posteriores à sua geração.

## Resultados novos de C

| Comparação | Projetos | Mudaram de categoria | Kappa linear |
|---|---:|---:|---:|
| C1–C2 | 269 | 39,4% | 0,455 |
| C1–C3 | 269 | 40,1% | 0,437 |
| C2–C3 | 269 | 4,5% | 0,931 |

C2 usa frequência com pré-releases, lead time b e CFR b; C3 troca a frequência por
tags. Lead time/CFR por releases continuam baseados nas principais. Ausências não
são categoria. H7 é parcialmente sustentada: concordância moderada/alta, mas trocas
substanciais em relação a C1. Não isolamos causalmente a contribuição de cada proxy.

Rework mediano: 37,35%, em 289 projetos, com 11 ausentes. A sensibilidade de
evidência completa fica disponível em 201 projetos (mediana 40%); os limites
agregados 32,07–48,65% não são IC nem medianas por projeto.

RQ05 é robusta à fonte de frequência: CFR b mantém associação positiva; CI não
apresenta evidência após Holm. Na RQ06 exploratória ampliada, tipo–recuperação
deixa de atingir 5%; as outras cinco associações originais permanecem. A família
original de 18 testes de B não é substituída pela família exploratória de 24.

## Limite entre S03 e etapa FIN da disciplina

O planejamento `scripts/issues.csv` também prevê uma etapa **FIN**, distinta da
Sprint 3: executar o repositório sorteado de outro grupo em 30 projetos, comparar
com seu CSV original e tratar as Issues recebidas. Não há, neste repositório,
identificação do grupo sorteado, dados originais externos ou registros dessa execução.
As únicas Issues abertas identificadas nesta revisão eram B163–166 e uma issue
antiga de apresentação; não havia problema de replicador recebido para reproduzir.

Portanto, a implementação/integração S03 não certifica a etapa FIN inteira.
Não inventamos replicação, publicação na main, fechamento de Issues ou aprovação
docente. Para essa etapa externa, faltam o repositório sorteado e o CSV original;
o link específico do board Projects também não está registrado. O índice público
`https://github.com/PedroMaiaAlves/lab-experimentacao-software/projects` não é tratado
como link verificado de um board. A conta disponível não tem escopo `read:project`.

Os commits são locais nesta branch de integração. Nenhum push/merge na main foi
efetuado nesta revisão. A autorização desta execução foi usada para concluir o
código e os documentos; operações de publicação devem preservar o trabalho remoto.
