# Sprint 3 — entrega da parte B

## Execução

Dentro de `Lab03/`, em ambiente Python 3.12 ou superior com as dependências instaladas:

```bash
python -m analises.sprint3_b
python -m analises.notebooks
python -m validacao.dicionario --dicionario docs/dicionario_s03_b.md --dados results/s03_b
```

No PowerShell, se `python` abrir o atalho da Microsoft Store, use o executável
da instalação ou da venv. Neste ambiente:

```powershell
py -3.13 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m analises.sprint3_b
.\.venv\Scripts\python.exe -m analises.notebooks
```

Não é necessário token, cache de coleta ou restaurar o ZIP para estas análises.
O comando lê `data/dataset.csv`, seu manifesto, `data/amostra_final.csv` e seu
manifesto. Confere hashes, identidade, domínio, disponibilidade e contagens.
`--dataset`, `--amostra` e `--saida` permitem escolher caminhos; a saída precisa
ficar separada da árvore de dados. A análise não modifica suas entradas.

Parâmetros principais: `--semente 42 --reamostragens 9999`. Valores menores
(mínimo 99) servem para testes, não correspondem à configuração publicada.
O módulo de cada RQ pode ser importado separadamente; os notebooks chamam essas
funções, recalculam as tabelas e verificam a equivalência com os CSVs publicados.
`analises.notebooks` executa em kernels novos e salva cópias em
`cache/notebooks_s03/`. As versões apresentáveis estão em `notebooks/`.

## O que foi entregue

| Item local | Artefatos e comportamento |
|---|---|
| S03-B1 | RQ05: Spearman dos dois CFR, n por variante, dispersão, ausências e robustez |
| S03-B2 | RQ06: três fatores × seis medidas, 18 testes, Holm conjunto, efeitos e descritivas por grupo |
| S03-B3 | Resultados/discussão no artigo, confrontando H5/H6 com os achados e limitações |

Saídas numéricas, figuras PNG/PDF, tabelas LaTeX e manifesto estão em
`results/s03_b/`. O [dicionário específico](dicionario_s03_b.md) cobre todas as
colunas. A geração repetida usa nomes/ordem estáveis e não inclui horário variável
nos artefatos. O manifesto registra versões: reprodutibilidade numérica entre
versões/plataformas deve ser conferida com tolerância, sem prometer PDFs binários
idênticos entre ambientes diferentes.

## Resultados e interpretação

RQ05 usa 300 pares no CFR de CI e 289 no CFR de entrega. O rho de CI é 0,014740
(IC95% −0,094737 a 0,125500; p de permutação/Holm 0,8096). Para entrega, rho é
0,660229 (IC95% 0,585360 a 0,724381; p de permutação/Holm 0,0004). H5 não é
sustentada. Não encontrar associação em CI não demonstra igualdade ou ausência
de qualquer relação. A associação positiva em entrega não demonstra causalidade
e pode refletir a regra de encontrar corretivas em sete dias.

RQ06 usa tipo, contribuidores em quartis e linguagem, definidos na amostra
completa antes das exclusões. As seis comparações que sobrevivem a Holm são:

- Tipo × recuperação: ε²=0,0512; p ajustado=0,0347.
- Contribuidores × lead time (a)/(b): ε²=0,1235/0,1574.
- Contribuidores × recuperação: ε²=0,0624; p ajustado=0,0092.
- Linguagem × lead time (a)/(b): ε²=0,1240/0,0844.

As outras 12 comparações continuam na tabela completa. H6 recebe apoio parcial,
sem sustentar uma interpretação de que comunidades maiores necessariamente
entregam mais rápido. Testes globais não identificam pares específicos; não
foram executados testes post-hoc. Os 22 tempos ausentes são projetos sem episódios
observáveis, não recuperações com duração zero. Os 11 CFR(b) indisponíveis não
foram preenchidos. O grupo de tipos “outro” tem só seis recuperações disponíveis.

## Diferencial e limites

Além da reprodução offline e dos hashes já existentes, esta entrega acrescenta
IC95% BCa pareado, permutação e influência leave-one-out. Nenhuma remoção individual
muda o sinal dos rhos; as maiores variações são 0,0093 (CI) e 0,0076 (entrega).
Esse diagnóstico não elimina viés de seleção, dependências entre projetos,
ausência informativa, limitações dos proxies ou incerteza da heurística.

O refinamento e a avaliação da heurística usaram a mesma amostra-ouro. Os tipos
dos 60 projetos vêm de consenso triplo; os demais 240, de revisão individual
após sugestões automáticas. Essa distinção não é apagada pela análise.
O diferencial não substitui RQ07 e não equivale ao bônus RQ08.

## Validação e caminho até o fechamento

O CI executa testes, recalcula RQ05/RQ06, confere o dicionário e executa os dois
notebooks em kernels novos; publica os artefatos para inspeção. O validador de
dicionário antes vazio foi implementado e seus quatro testes passaram a ser
descobertos automaticamente pelo pytest. Evidências da execução desta entrega
estão em `evidencias_s03_b.md`.

A base da S02 permanece congelada. B entrega suas análises e sua discussão sem
esperar A ou C. Ainda faltam as análises descritivas e C1 de A, a sensibilidade
da RQ07 de C, a discussão consolidada e a entrega final de replicação cruzada,
respostas às Issues recebidas e revisão final do artigo. Cada integrante continua
responsável por contribuição de código atribuível e acompanhamento no Projects;
arquivos locais não comprovam, sozinhos, atualização do quadro ou avaliação docente.

Atualização de integração local (21/10/2026): os quatro commits de B, até `f69b2ab`,
foram incorporados por merge, preservando autoria. A já estava na main; C acrescentou
RQ07/RQ08 e a versão compacta do artigo, com 9 páginas. As análises originais e suas
famílias de testes não foram substituídas pelas sensibilidades ampliadas. As
pendências de A/C e do tamanho do artigo acima são históricas; a etapa FIN de
replicação cruzada continua distinta. Veja `entrega_s03_integrada.md`.
