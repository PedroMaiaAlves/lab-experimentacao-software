# Entrega de Pedro — Lab04S01, P1 + P2

## Escopo

Esta parte contém estrutura, coleta real, cenário, calibração e simulação.
Diogo implementará os testes estatísticos e G2 (D1/D2); Lorran implementará
Streamlit, G1 e integração (L1/L2). Não há dashboard pronto nesta entrega.

A coleta está vinculada à issue #173 e ao commit `8c5cc12`; a simulação está
vinculada à issue #174, na branch correspondente. A branch da #174 inclui a
coleta da #173. As PRs devem ser revisadas e integradas nessa ordem; revisão,
merge e atualização do Projects ainda precisam ser concluídos pelo grupo.
Os títulos duplicados das issues foram preservados; a divisão de escopo está
em `docs/issues_s01.md`.

## Evidências técnicas

O cenário foi registrado antes da coleta, com seu hash no manifesto inicial.
O coletor foi verificado por 31 testes antes de iniciar a sessão oficial,
incluindo compilação real de uma fonte pequena, estados do cache, exclusão do
preenchimento da cronometragem e repetição integral de pares com falhas.

O objeto de medição contém 883 arquivos Python do Django 5.2.8. O SHA-256 do
arquivo oficial foi conferido. Cada arquivo compilado tem seu próprio hash
registrado em `data/real/arquivos_fonte.csv`.

**Estado final:** P1/P2 implementadas e validadas localmente. Coleta concluída em
02/11/2026, entre 02:41:59 e 02:54:43 (America/Sao_Paulo, UTC−03). O período inclui
preparação e aquecimento, além das medições oficiais.

- 30 pares reais completos (60 medições oficiais), com 15 pares de cada ordem.
- Três pares de aquecimento separados (seis medições adicionais).
- Nenhuma falha técnica; todos os pares foram válidos na primeira tentativa.
- 30 pares simulados, calibrados pelos dados reais, com semente 42.
- Validação offline aprovada: hashes, origem, ordem, logs, estado do cache e
  reprodução exata da amostra simulada.
- **33 testes automatizados passaram** na verificação final. Incluem regeneração
  completa em diretório temporário, com acesso à rede bloqueado no teste, e
  comparação byte a byte dos três arquivos simulados com os artefatos preservados.

Saída de `validar.py`:

```json
{
  "status": "ok",
  "pares_reais": 30,
  "pares_simulados": 30,
  "aquecimento_separado": 3,
  "reproducao_exata": true
}
```

## Descrição da amostra real

| Medida | Sem cache | Com cache |
| --- | ---: | ---: |
| Média (s) | 5,791318 | 1,463384 |
| Mediana (s) | 5,837706 | 1,448520 |
| Mínimo (s) | 4,043622 | 1,237033 |
| Máximo (s) | 7,233402 | 2,059666 |

A razão geométrica observada sem/com cache é **3,944398**. Esse é um resumo
descritivo desta sessão, não um resultado dos testes de hipótese nem uma
estimativa da vantagem universal do cache em outros projetos.

Calibração, na ordem `[sem_cache, com_cache]`, usando log natural:

```text
mu = [1.748562089288608, 0.3762657828471741]
Sigma = [[ 0.01682414153489459, -0.003923782386226294],
         [-0.003923782386226294, 0.00885089832872303]]
delta observado = 1.372296306441434
```

A covariância estimada é negativa nesta amostra e foi preservada, sem trocar
seu sinal ou gerar condições independentes. A amostra simulada não precisa ter
momentos amostrais exatamente iguais aos da coleta: eles são os parâmetros
populacionais do modelo gerador. O G1 deverá mostrar o ajuste e suas limitações.

SHA-256 do CSV real:

```text
205af2f581924402fb23a4ce60744de3199324a79fc2e52c04acc76d76c46586
```

Os valores completos, a versão do NumPy e os vínculos de proveniência estão em
`data/simulado/parametros.json`. O cenário prévio permaneceu inalterado; sua
expectativa ainda será confrontada com as simulações da sprint 2.

## Como conferir

Na raiz do repositório, com o ambiente instalado:

```powershell
.\Lab04\.venv\Scripts\python.exe Lab04/validar.py
.\Lab04\.venv\Scripts\python.exe -m pytest -c Lab04/pytest.ini Lab04/tests -q
```

Para regenerar os parâmetros e o CSV simulado sem acessar a rede:

```powershell
.\Lab04\.venv\Scripts\python.exe Lab04/simular.py
```

Não rodar `coletar.py` para apenas conferir a entrega: uma nova coleta mede
outros tempos e precisa de outro diretório. A sessão original é preservada.

## Entrega aos colegas

- Compartilhar a divisão de `docs/issues_s01.md`; P1 e P2 correspondem às issues #173 e #174.
- Diogo utiliza os pares simulados e a transformação definida em `docs/contratos.md`.
- Lorran utiliza os dois CSVs e os parâmetros para G1, cenário e integração.
- Cada colega implementa e testa seu próprio código nas issues correspondentes.
- O link correto do Projects será preenchido quando Pedro criar os cartões.

A coleta não demonstra poder ou controle de erro tipo I dos testes. Esses
resultados exigem as simulações da S02. Estatísticas descritivas da coleta
não devem ser apresentadas como conclusões dos testes ainda não implementados.
