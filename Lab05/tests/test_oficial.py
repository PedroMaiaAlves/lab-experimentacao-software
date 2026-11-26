import csv
import json
import sys
from dataclasses import asdict
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import validar as validador  # noqa: E402
from experimento import plano  # noqa: E402
from experimento.coleta import (  # noqa: E402
    ColetorOficial,
    Resultado,
    carregar_plano_oficial,
    criar_diretorio_coleta,
    sha256_arquivo,
)

RAIZ = Path(__file__).resolve().parents[1]
PROTOCOLO = json.loads((RAIZ / "data" / "plano" / "protocolo_oficial.json").read_text(encoding="utf-8"))


class ExecutorOficialFake:
    def __init__(self, falhar_uma_vez=None):
        self.falhar_uma_vez = set(falhar_uma_vez or [])
        self.executadas = []
        self.limpezas = 0

    def limpar(self):
        self.limpezas += 1

    def metadados(self):
        return {
            "ambiente": {
                "so": "teste", "cpu": "cpu-teste", "processadores_logicos": 8,
                "memoria_total_bytes": 16 * 1024**3, "python": "teste",
            },
            "imagens": {nome: dados["fingerprint"] for nome, dados in PROTOCOLO["imagens"].items()},
        }

    def executar(self, execucao, workload, bruto, stdout, stderr):
        self.executadas.append(execucao.id_execucao)
        stdout.write_text("stdout", encoding="utf-8")
        stderr.write_text("stderr", encoding="utf-8")
        if execucao.id_execucao in self.falhar_uma_vez:
            self.falhar_uma_vez.remove(execucao.id_execucao)
            return 7, [10.0], [100.0], ["omb", execucao.id_execucao]
        taxa = 1_000.0 if execucao.broker == "kafka" else 800.0
        bruto.write_text(
            json.dumps(
                {
                    "publishRate": [taxa, taxa + 100],
                    "consumeRate": [taxa, taxa + 100],
                    "aggregatedEndToEndLatency50pct": 2.0,
                    "aggregatedEndToEndLatency99pct": 9.0,
                }
            ),
            encoding="utf-8",
        )
        return 0, [10.0], [100.0], ["omb", execucao.id_execucao]


def _diretorio_oficial(tmp_path):
    diretorio = criar_diretorio_coleta(tmp_path)
    documento = tmp_path / "protocolo.md"
    documento.write_text("| coleta | bloco | horário | máquina | energia | desvio |\n", encoding="utf-8")
    return diretorio, documento


def test_coleta_oficial_retoma_repete_e_congela_taxas_e2(tmp_path):
    diretorio, documento = _diretorio_oficial(tmp_path)
    primeiro_id = next(e.id_execucao for e in carregar_plano_oficial("E1") if e.bloco == "E1-B1")
    executor = ExecutorOficialFake({primeiro_id})
    coletor = ColetorOficial(diretorio, executor, documento_protocolo=documento)
    primeira = coletor.executar_bloco("E1-B1", "nenhum")
    assert len(primeira) == 40
    assert sum(r.status == "falha" for r in primeira) == 1

    retomado = ColetorOficial(diretorio, ExecutorOficialFake(), documento_protocolo=documento)
    assert retomado.executar_bloco("E1-B1", "nenhum") == []
    repetida = retomado.executar_bloco("E1-B1", "falha técnica registrada", repetir_falhas=True)
    assert len(repetida) == 1 and repetida[0].tentativa == 2 and repetida[0].status == "sucesso"
    assert (diretorio / "raw" / f"{primeiro_id}-t02.json").exists()

    retomado.executar_bloco("E1-B2", "nenhum")
    retomado.executar_bloco("E2-B1", "nenhum")
    manifesto = json.loads((diretorio / "manifesto.json").read_text(encoding="utf-8"))
    assert manifesto["schema"] == 2
    assert manifesto["taxas_e2"] == {"1024": 425, "16384": 425}
    assert manifesto["hashes"]["resultados.csv"] == sha256_arquivo(diretorio / "resultados.csv")
    assert len(manifesto["hashes"]["brutos"]) == 120
    assert "E2-B1" in documento.read_text(encoding="utf-8")


def _criar_coleta_sintetica(tmp_path):
    diretorio, _ = _diretorio_oficial(tmp_path)
    linhas = []
    taxas_e2 = {1024: 400, 16384: 300}
    for exp in plano.EXPERIMENTOS:
        for e in carregar_plano_oficial(exp):
            bruto = diretorio / "raw" / f"{e.id_execucao}-t01.json"
            bruto.write_text(json.dumps({"publishRate": [800, 800]}), encoding="utf-8")
            taxa = plano.TAXA_E1_ABERTA if exp == "E1" else taxas_e2[e.tamanho_bytes]
            throughput = 800.0 if exp == "E1" else float(taxa)
            linhas.append(
                Resultado(
                    colecao_id=diretorio.name, ordem=e.ordem, id_execucao=e.id_execucao,
                    experimento=e.experimento, broker=e.broker, versao=e.versao,
                    tamanho_bytes=e.tamanho_bytes, repeticao=e.repeticao, bloco=e.bloco,
                    ordem_no_bloco=e.ordem_no_bloco, tentativa=1, status="sucesso",
                    inicio_utc="2026-11-26T00:00:00.000Z", fim_utc="2026-11-26T00:03:00.000Z",
                    duracao_s=180.0, aquecimento_s=e.aquecimento_s, medicao_s=e.medicao_s,
                    taxa_alvo_msg_s=taxa, throughput_msg_s=throughput,
                    throughput_mib_s=throughput * e.tamanho_bytes / 1024**2,
                    latencia_p50_ms=2.0, latencia_p99_ms=9.0,
                    throughput_consumo_msg_s=throughput, cv_intervalos=0.01,
                    intervalo_min_rel=0.98, colapso=False, cpu_percent_medio=10.0,
                    memoria_mib_media=100.0, codigo_saida=0,
                    resultado_bruto=str(bruto.relative_to(diretorio)),
                )
            )
    with (diretorio / "resultados.csv").open("w", newline="", encoding="utf-8") as arquivo:
        escritor = csv.DictWriter(arquivo, fieldnames=list(Resultado.__dataclass_fields__))
        escritor.writeheader()
        escritor.writerows(asdict(r) for r in linhas)
    manifesto = {
        "schema": 2,
        "colecao_id": diretorio.name,
        "status": "concluida",
        "taxas_e2": {str(k): v for k, v in taxas_e2.items()},
        "imagens": {nome: dados["fingerprint"] for nome, dados in PROTOCOLO["imagens"].items()},
        "hashes": {},
    }
    _atualizar_hashes(diretorio, manifesto)
    return diretorio


def _atualizar_hashes(diretorio, manifesto=None):
    caminho = diretorio / "manifesto.json"
    if manifesto is None:
        manifesto = json.loads(caminho.read_text(encoding="utf-8"))
    manifesto["hashes"] = {
        "resultados.csv": sha256_arquivo(diretorio / "resultados.csv"),
        "brutos": {
            str(p.relative_to(diretorio)).replace("\\", "/"): sha256_arquivo(p)
            for p in sorted((diretorio / "raw").glob("*.json"))
        },
    }
    caminho.write_text(json.dumps(manifesto), encoding="utf-8")


def _alterar_csv(diretorio, alteracao):
    caminho = diretorio / "resultados.csv"
    with caminho.open(encoding="utf-8") as arquivo:
        linhas = list(csv.DictReader(arquivo))
        campos = list(linhas[0])
    alteracao(linhas)
    with caminho.open("w", newline="", encoding="utf-8") as arquivo:
        escritor = csv.DictWriter(arquivo, fieldnames=campos)
        escritor.writeheader()
        escritor.writerows(linhas)
    _atualizar_hashes(diretorio)


def test_validador_aprova_coleta_sintetica_completa(tmp_path):
    relatorio = validador.validar(_criar_coleta_sintetica(tmp_path))
    assert relatorio["valido"], relatorio["erros"]
    assert relatorio["ids_validos"] == 160


@pytest.mark.parametrize(
    ("caso", "trecho"),
    [
        ("contagem", "IDs planejados sem sucesso"),
        ("id", "ID fora do plano"),
        ("duplicado", "mais de um sucesso"),
        ("faixa", "CPU fora da faixa"),
        ("p99", "p99 menor que p50"),
    ],
)
def test_validador_reprova_inconsistencias_de_resultado(tmp_path, caso, trecho):
    diretorio = _criar_coleta_sintetica(tmp_path)

    def alterar(linhas):
        if caso == "contagem":
            linhas.pop()
        elif caso == "id":
            linhas[0]["id_execucao"] = "E1-id-inexistente"
        elif caso == "duplicado":
            copia = dict(linhas[0])
            copia["tentativa"] = "2"
            linhas.append(copia)
        elif caso == "faixa":
            linhas[0]["cpu_percent_medio"] = "401"
        elif caso == "p99":
            linhas[0]["latencia_p50_ms"] = "10"
            linhas[0]["latencia_p99_ms"] = "9"

    _alterar_csv(diretorio, alterar)
    relatorio = validador.validar(diretorio)
    assert not relatorio["valido"]
    assert any(trecho in erro for erro in relatorio["erros"]), relatorio["erros"]


def test_validador_reprova_hash_e_imagem(tmp_path):
    diretorio = _criar_coleta_sintetica(tmp_path)
    bruto = next((diretorio / "raw").glob("*.json"))
    bruto.write_text("adulterado", encoding="utf-8")
    relatorio = validador.validar(diretorio)
    assert any("SHA-256 divergente" in erro for erro in relatorio["erros"])

    _atualizar_hashes(diretorio)
    manifesto = json.loads((diretorio / "manifesto.json").read_text(encoding="utf-8"))
    manifesto["imagens"]["kafka"] = "sha256:outra"
    (diretorio / "manifesto.json").write_text(json.dumps(manifesto), encoding="utf-8")
    relatorio = validador.validar(diretorio)
    assert any("imagem kafka" in erro for erro in relatorio["erros"])
