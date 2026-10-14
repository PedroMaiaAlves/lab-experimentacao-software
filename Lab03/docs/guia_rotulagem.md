# Guia de rotulagem da amostra-ouro (S02)

Cada integrante rotula **sozinho**, sem consultar os outros e sem ver a saída da heurística.
Discussão só depois que os três arquivos estiverem commitados.

## Como fazer

1. Copie `data/amostra_ouro/modelo/rotulos_modelo.xlsx` para `data/amostra_ouro/rotulos/rotulos_<A|B|C>.xlsx` (a letra do seu avaliador).
2. Aba `repositorios` (60 linhas): preencha `tipo_projeto` e `releases_sao_entregas`.
3. Aba `releases` (até 300 linhas): preencha `corretiva`.
4. Use as listas suspensas. Nenhuma célula pode ficar em branco, e as colunas de identificação não podem ser alteradas.
5. Commite só o seu arquivo, citando a Issue.

## Definições (iguais para os três)

| Campo | Valor | Quando usar |
|---|---|---|
| `tipo_projeto` | biblioteca/framework | Código usado como dependência por outros programas (pacote, SDK, framework, plugin de biblioteca). |
| | aplicação/serviço | Programa ou serviço usado diretamente (app, servidor, jogo, extensão). |
| | ferramenta CLI | Programa cujo uso principal é pela linha de comando. |
| | outro | Documentação, listas, tutoriais, dados, configurações, GitHub Actions. |
| `releases_sao_entregas` | sim | As releases entregam versões a usuários (binários, pacotes, notas de versão). |
| | não | São marcações automáticas ou sem entrega real (ex.: nightly sem notas, atualização de dados). |
| | incerto | Não dá para decidir com as informações da página. |
| `corretiva` | sim | O objetivo principal da release é corrigir defeito recente (correções, hotfix, revert). |
| | não | Demais casos (funcionalidades, dependências, documentação, manutenção, mistas sem foco em correção). |

## Dicas

- Para `corretiva`, abra `release_url` (notas) e `compare_url` (lista de commits). Sem `compare_url`, a release não tem antecessora: use só as notas.
- Para `tipo_projeto`, o README do repositório costuma bastar.
- Caso ambíguo: escolha o melhor palpite. Não consulte os outros; a divergência é medida pelo kappa e discutida no consenso.
- São cerca de 360 linhas por pessoa: reserve blocos de tempo logo no início da sprint.