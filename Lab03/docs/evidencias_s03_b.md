# Evidências da Sprint 3 — parte B

Validação local em 18/10/2026, Windows, Python 3.13.5.

## Testes e execução

- Suíte completa: **350 testes aprovados**, em 123,77 segundos.
- Cobertura: **95,51% de `metricas`**, **85,42% de `analises`** e **90,45% no conjunto**.
- O executor de notebooks foi validado por execução real em kernels novos,
  separadamente do pytest; sua cobertura não está incluída na execução dos testes.
- RQ05/RQ06 executadas com 9.999 reamostragens, semente 42 e os hashes de entrada
  registrados no manifesto. Repetição em outro diretório produziu todos os
  artefatos, inclusive o manifesto e as figuras, idênticos byte a byte neste ambiente.
- Dois notebooks executados do início ao fim; tabelas recalculadas conferidas
  com os CSVs, com tolerâncias de 1e-12 relativa e 1e-14 absoluta. Figuras PNG
  incorporadas às saídas dos notebooks.
- Verificador do dicionário das análises concluiu sem colunas faltantes/obsoletas.
- PDF compilado com Tectonic 0.17.0: **dez páginas**, referências resolvidas,
  páginas inspecionadas e tabelas ajustadas para legibilidade. Houve avisos de
  fonte/espaçamento não impeditivos. O PDF anterior da S02 permanece preservado.

Comandos principais usados:

```bash
python -m pytest --cov=metricas --cov=analises --cov-report=term-missing --cov-fail-under=80
python -m analises.sprint3_b
python -m analises.sprint3_b --saida cache/s03_reproducao
python -m analises.notebooks --saida notebooks
python -m validacao.dicionario --dicionario docs/dicionario_s03_b.md --dados results/s03_b
```

O workflow do GitHub Actions também instala dependências, executa a suíte com o
limite de 80% em métricas, recalcula as análises, verifica o dicionário, executa
os notebooks e publica os artefatos. Seu estado remoto deve ser consultado nas
[execuções da branch](https://github.com/PedroMaiaAlves/lab-experimentacao-software/actions/workflows/testes.yml?query=branch%3A166-lab03-s03---b4-validar-a-entrega),
separadamente das evidências locais acima.

## Preservação

Os **233 arquivos de dados versionados** tiveram seus SHA-256 comparados antes e
depois: nenhum foi alterado. Isso inclui o pacote com 311 fontes congeladas,
dataset, manifestos e avaliações. Não houve nova coleta nem nova rotulagem.

- Dataset: `8c494ec09f475e7f44d512f72329257d5bb7c470b8a09e1cf75d5b273b995ee9`.
- Amostra: `61468b19b001f71b10cd24d3323cdeb7bef915dac2b788ed65640194dac416fd`.
- 300 projetos; 11 CFR(b) ausentes; 22 recuperações ausentes; 300 tipos disponíveis.

## Limites da conclusão

A entrega cobre S03-B1/B2/B3. O diferencial escolhido foi robustez estatística;
RQ08 não foi implementada. A e C continuam necessárias para fechar a Sprint 3,
e a replicação cruzada depende do grupo atribuído pelo professor.
O artigo atual atinge o limite de dez páginas: a integração dos resultados
restantes exigirá condensar a metodologia e evitar repetir tabelas disponíveis
no repositório. Não é possível inferir nota, contribuição individual dos colegas
ou atualização do GitHub Projects a partir dos testes automatizados.
