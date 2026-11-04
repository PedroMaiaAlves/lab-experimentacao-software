# Protocolo da coleta real — P1

## Configuração congelada

`protocolo.json` define Django 5.2.8, CPython 3.13.5, 30 pares oficiais,
três pares de aquecimento, semente 42, alpha 0,05 e alternativas bicaudais.
O hash do cenário e uma cópia do protocolo são registrados no manifesto antes
de medir. Trata-se de registro local; não é uma pré-inscrição pública do estudo.

O arquivo oficial baixado é `django-5.2.8.tar.gz`, SHA-256:

```text
23254866a5bb9a2cfa6004e8b809ec6246eba4b58a7589bc2772f1bcc8456c7f
```

O valor foi conferido no [arquivo oficial de checksums](https://media.djangoproject.com/pgp/Django-5.2.8.checksum.txt).
O coletor compara o SHA-256; não declara ter verificado a assinatura PGP.
Somente arquivos da árvore `django/` são usados, sem importar ou executar Django.

## Procedimento

1. Extrair uma cópia nova dos fontes na área local ignorada `.cache/`.
2. Inventariar todos os `.py`, com caminho relativo e SHA-256.
3. Montar 15 ordens sem/com e 15 com/sem e embaralhá-las com
   `random.Random(42).shuffle`, independentemente da semente do gerador NumPy.
4. Executar três pares de aquecimento, em ordens sem/com, com/sem e sem/com.
5. Para cada condição de cada par oficial, limpar os `__pycache__` da cópia
   isolada. Para a condição com cache, preencher os bytecodes com uma execução
   não cronometrada do mesmo comando.
6. Conferir estado inicial, iniciar o relógio monotônico, executar o subprocesso
   e parar o relógio. Download, extração, limpeza, preenchimento e verificações
   ficam fora desse intervalo. Captura de saída e inicialização do processo
   fazem parte do tempo medido.
7. Conferir que todos os `.pyc` correspondem ao Python, timestamp e tamanho dos
   fontes. Na condição com cache, conferir que tamanho e mtime dos `.pyc` não
   mudaram. Registrar contagens e evidências no log.
8. Salvar cada par completo imediatamente. Conferir novamente os hashes dos
   fontes ao terminar e finalizar o manifesto com hashes dos artefatos.

Comando idêntico nas duas condições, com caminho absoluto para a fonte:

```text
<python-do-ambiente> -I -m compileall -q -j 1 --invalidation-mode timestamp -o 0 <fonte-django>
```

`-I` isola a execução de variáveis Python e pacotes do usuário. `-j 1` usa um
processo de trabalho. A compilação normal permite reutilizar bytecode válido;
não usamos `-f`, que forçaria recompilação nas duas condições.

## Dados, falhas e integridade

- A unidade experimental é o bloco pareado; nunca analisar as condições como
  dois grupos independentes.
- `pares_reais.csv` contém somente pares oficiais completos. Aquecimento fica
  em outro CSV e não calibra o modelo.
- Se uma das condições falhar, toda a tentativa do par é descartada do CSV,
  mas suas medições ficam no log. Repete-se o par inteiro na mesma ordem.
- No máximo três tentativas por par; depois disso, a sessão fica incompleta e
  não pode alimentar a simulação. Não há retomada que misture sessões distintas.
- Não há corte por tempo, winsorização nem exclusão de outliers. O timeout de
  120 segundos é uma falha operacional documentada, não uma medição válida.
- O CSV salva precisão suficiente para reconstruir os valores de ponto flutuante.
  `duracao_ns` no log preserva a leitura original do relógio.
- Datas dos logs são UTC do relógio da máquina. O dashboard poderá convertê-las
  para `America/Sao_Paulo`; não se deve alterar os instantes brutos.
- A validação offline verifica hashes, tamanho, ordem, logs, estados do cache e
  vínculo entre coleta, parâmetros e simulação.

## Ameaças à validade

O cache do sistema operacional não é limpo. Preencher o cache de bytecode também
lê os fontes, portanto pode influenciar o estado de disco. Aquecimento e ordem
balanceada não eliminam esse fator. Não foi desligado antivírus nem monitorada
a carga do sistema continuamente. O manifesto registra sistema e processador,
mas não pretende comprovar isolamento de CPU.

Os 30 pares são repetições temporais na mesma máquina e projeto, não 30 projetos
independentes. Autocorrelação pode afetar a inferência. O modelo bivariado supõe
pares independentes na simulação; essa simplificação deve aparecer no dashboard.
Uma redução grande do tempo com cache não demonstra qual teste possui melhor
controle de erro tipo I ou poder; essa comparação pertence à S02.
