# Protocolo de rotulagem independente — integrante B

Este documento deve ser lido e acordado por A, B e C **antes** do início da
rotulagem. Pode-se discutir a definição das categorias, mas não repositórios ou
releases concretas. Depois do início, cada avaliador trabalha sem consultar os
rótulos dos demais e sem executar ou visualizar a heurística automática.

## Arquivo e valores canônicos

`data/amostra_ouro/rotulos/rotulos_B.xlsx` deve preservar todas as abas, colunas e links entregues por
A1 e conter, no mínimo, estas colunas preenchidas:

| Coluna | Valores permitidos |
|---|---|
| `full_name` | `owner/repo` da planilha original |
| `release_id` | identificador da release na planilha original |
| `tipo_projeto` | `biblioteca/framework`, `aplicação/serviço`, `ferramenta CLI`, `outro` |
| `releases_sao_entregas` | `sim`, `não`, `incerto` |
| `corretiva` | `sim`, `não` |

Os rótulos de `tipo_projeto` e `releases_sao_entregas` se referem ao repositório e,
portanto, devem ser repetidos de forma idêntica nas cinco releases desse projeto.

## Ordem de trabalho

1. Use `data/amostra_ouro/rotulos/rotulos_B.xlsx`.
2. Para cada repositório, consulte a documentação oficial e preencha os rótulos do
   projeto sem consultar A ou C.
3. Para cada release, abra as notas e, quando necessário, a comparação de commits.
4. Registre o rótulo sustentado pelas evidências consultadas.
5. Não use a forma da tag, a diferença entre números de versão ou palavras isoladas
   como decisão automática. O rótulo final considera o significado das evidências.
6. Ao terminar, execute o validador estrutural.

## Tipo do projeto

- `biblioteca/framework`: o uso principal é como dependência, SDK, API reutilizável
  ou base para construir outros programas.
- `aplicação/serviço`: o produto principal é utilizado diretamente por usuários ou
  operado como aplicação, servidor, serviço web, desktop ou mobile.
- `ferramenta CLI`: a interface principal documentada é um comando de terminal.
- `outro`: nenhuma das categorias anteriores representa adequadamente o uso principal.

Em projetos híbridos, escolha a finalidade apresentada como principal na documentação,
não a linguagem ou a estrutura interna do código.

## Releases como entregas reais

- `sim`: as releases publicam artefato, pacote, imagem, binário, versão utilizável ou
  implantação destinada a consumidores do projeto.
- `não`: os registros são apenas marcos internos, snapshots automáticos ou metadados sem
  uma entrega consumível identificável.
- `incerto`: a documentação e os links não oferecem evidência suficiente para decidir.

## Release corretiva

Marque `sim` quando o **objetivo principal** indicado pelas notas ou pelos commits for
corrigir defeito recente, regressão, vulnerabilidade ou reverter mudança defeituosa.
Uma release mista sem foco predominantemente corretivo deve ser marcada como `não`.

Marque `não` quando houver somente funcionalidades, refatoração sem defeito declarado,
atualização rotineira de dependências, documentação, formatação, testes ou tarefas
internas. Correções apenas tipográficas/documentais não contam como defeito do software.

Quando a evidência for curta, procure o contexto nos links fornecidos, mas não consulte
issues, arquivos ou pessoas que revelem os rótulos de A/C ou a previsão automática. O
campo de release não admite `incerto`: registre a melhor decisão sustentada pela evidência.

## Validação

A partir de `Lab03/`, execute:

```bash
python scripts/validar_rotulos_b.py data/amostra_ouro/rotulos/rotulos_B.xlsx
```

O aceite exige 300 linhas únicas, 60 repositórios, cinco releases por repositório,
campos completos, valores canônicos e rótulos de repositório consistentes.
