# RQ3 e integração do relatório

## Ambiente e reprodução

Execute na raiz do repositório, com a instalação da coleta já disponível.
Não substitua `Lab02/.venv` nem altere os requisitos usados nos trials.

```powershell
.\Lab02\.tools\bin\uv.exe venv --python Lab02/.venv/Scripts/python.exe --no-python-downloads Lab02/.venv-analysis
.\Lab02\.tools\bin\uv.exe pip sync --python Lab02/.venv-analysis/Scripts/python.exe --cache-dir Lab02/.uv-cache Lab02/requirements-analysis.txt
.\Lab02\.venv-analysis\Scripts\python.exe -B -m unittest discover -s Lab02/tests -v -b
.\Lab02\.venv-analysis\Scripts\python.exe -B Lab02/tools/analyze_rq3.py
```

Crie o ambiente apenas na primeira instalação; se já existir, confira sua
versão. É necessário ter o histórico Git das soluções disponível. Se necessário, obtenha
as referências com `git fetch origin` antes de executar.

O analisador aceita `--trials CAMINHO`, `--protocol CAMINHO` e `--output PASTA`.
O padrão é ler o CSV e protocolo do LAB02 e gravar em `Lab02/results/rq3/`.
Dados malformados interrompem a análise. Divergência entre métricas registradas
e recalculadas gera saídas com `release_status=needs_review` e retorno 2.
Ausências de métricas permanecem vazias/nulas. Um par inferencial só é usado
se seus dois trials em cada condição possuem a métrica. Nenhum resultado
original é atualizado e nenhuma solução é executada.

## Arquivos para Diogo

- `individual.csv`: um trial por linha, mantendo campos de identificação.
- `summary.csv`: n, mediana, Q1, Q3 e IQR por tratamento e métrica.
- `by_participant.csv` e `by_kata.csv`: resumos estratificados, sem presumir
  que linhas de participantes distintos sejam observações pareadas.
- `paired.csv`: duas medianas e diferença IA menos Manual por participante.
- `sensitivity.csv`: resumos excluindo um participante de cada vez.
- `outliers.csv`: valores além das cercas de 1,5 IQR, sempre mantidos.
- `analysis.json`: inferência, ajustes de Holm, auditoria e proveniência.
- `rq3_distribuicoes.png`, `rq3_pareados.png`, `rq3_loc.png`: figuras de RQ3.
- `interpretacao.md`: resultados e definições para revisão.

Os CSVs usam UTF-8, vírgula como separador e ponto decimal; percentuais estão
na escala 0–100. Quartis usam interpolação linear (type 7). A unidade pareada
é o participante, não cada trial. Os testes são bilaterais exatos por
enumeração de sinais, com postos médios nos empates. As diferenças são
arredondadas a oito casas apenas para o ranqueamento. A família de Holm
contém duas hipóteses: complexidade e duplicação, com alfa 0,05.

A média de complexidade registrada vem dos blocos retornados por `cc_visit`.
O campo `loc` usa SLOC do Radon, e não o total físico de linhas. A duplicação
é um detector próprio de janelas de três linhas normalizadas, sem vazias e
comentários de linha inteira, dentro do mesmo arquivo. Não é uma métrica do
Radon nem um detector de clones semânticos. A janela conta índices cobertos
uma única vez, mesmo quando há sobreposição.

## Relatório e responsabilidades

RQ1/RQ2 foram implementadas por Lorran na Issue #105, commit
`a1d6ca4b637245cd70bf1edfc62cdc74c3dd2ff8`. Os resultados foram reproduzidos
com o mesmo CSV para integração ao Word. As imagens do relatório não
substituem o dashboard geral de Diogo. Por decisão de Pedro, somente o DOCX
é versionado na entrega do relatório; seu motor de montagem e os insumos
intermediários permanecem locais e não são necessários para executar a RQ3.

O relatório mantém data de entrega, link e captura do Projects pendentes.
A integração do dashboard permanece pendente de entrega de Diogo. Não
interpretar o DOCX de revisão como documento liberado para submissão.

Issues cadastradas, responsável PedroMaiaAlves:

1. **#107 — Análise da RQ3 (Métricas e Estatísticas)** — script,
   testes, auditoria e gráficos. Aceite: entradas intactas, resultados
   reproduzíveis e revisão por outro integrante.
2. **#108 — Relatório Final - (Lab02)(Sprint 3)** — Word
   no modelo, resultados das três RQs, referências e evidências do Projects.
   Aceite: pendências preenchidas, números conferidos e páginas revisadas.

Nenhuma Issue ou evidência de participação é criada automaticamente. Os
commits futuros devem mencionar os números reais das Issues cadastradas.
