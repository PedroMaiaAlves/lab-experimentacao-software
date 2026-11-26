"""Valida a coleta oficial do Lab05 contra o protocolo congelado no G2."""

from __future__ import annotations

import argparse
import csv
import json
import math
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

RAIZ = Path(__file__).resolve().parent
sys.path.insert(0, str(RAIZ))

from experimento import plano  # noqa: E402
from experimento.coleta import carregar_plano_oficial, sha256_arquivo  # noqa: E402

PROTOCOLO = RAIZ / "data" / "plano" / "protocolo_oficial.json"
STATUS_VALIDOS = {"sucesso", "falha", "interrompida", "bloqueada"}


def _finito(linha: dict[str, str], campo: str) -> float | None:
    texto = linha.get(campo, "")
    if texto == "":
        return None
    valor = float(texto)
    if not math.isfinite(valor):
        raise ValueError(f"{campo} não é finito")
    return valor


def _hashes_brutos(diretorio: Path) -> dict[str, str]:
    return {
        str(caminho.relative_to(diretorio)).replace("\\", "/"): sha256_arquivo(caminho)
        for caminho in sorted((diretorio / "raw").glob("*.json"))
    }


def validar(
    diretorio: Path,
    fase: str = "completa",
    caminho_protocolo: Path = PROTOCOLO,
) -> dict[str, Any]:
    erros: list[str] = []
    avisos: list[str] = []
    protocolo = json.loads(caminho_protocolo.read_text(encoding="utf-8"))
    csv_resultados = diretorio / "resultados.csv"
    caminho_manifesto = diretorio / "manifesto.json"
    if not csv_resultados.exists() or not caminho_manifesto.exists():
        ausentes = [str(p.name) for p in (csv_resultados, caminho_manifesto) if not p.exists()]
        return {"valido": False, "erros": ["artefatos ausentes: " + ", ".join(ausentes)], "avisos": []}

    manifesto = json.loads(caminho_manifesto.read_text(encoding="utf-8"))
    with csv_resultados.open(encoding="utf-8") as arquivo:
        linhas = list(csv.DictReader(arquivo))

    execucoes = [e for exp in plano.EXPERIMENTOS for e in carregar_plano_oficial(exp)]
    por_id_plano = {e.id_execucao: e for e in execucoes}
    if len(por_id_plano) != len(execucoes):
        erros.append("o plano contém IDs duplicados")
    esperados = {
        e.id_execucao for e in execucoes
        if fase == "completa" or e.experimento == "E1"
    }

    por_id: dict[str, list[dict[str, str]]] = defaultdict(list)
    for numero, linha in enumerate(linhas, start=2):
        ident = linha.get("id_execucao", "")
        if ident not in por_id_plano:
            erros.append(f"linha {numero}: ID fora do plano: {ident or '<vazio>'}")
            continue
        por_id[ident].append(linha)
        esperado = por_id_plano[ident]
        campos_texto = {
            "bloco": esperado.bloco,
            "experimento": esperado.experimento,
            "broker": esperado.broker,
            "versao": esperado.versao,
        }
        campos_int = {
            "ordem": esperado.ordem,
            "ordem_no_bloco": esperado.ordem_no_bloco,
            "tamanho_bytes": esperado.tamanho_bytes,
            "repeticao": esperado.repeticao,
            "aquecimento_s": esperado.aquecimento_s,
            "medicao_s": esperado.medicao_s,
        }
        for campo, valor in campos_texto.items():
            if linha.get(campo) != str(valor):
                erros.append(f"{ident}: {campo} diverge do plano")
        for campo, valor in campos_int.items():
            try:
                obtido = int(linha.get(campo, ""))
            except ValueError:
                obtido = None
            if obtido != valor:
                erros.append(f"{ident}: {campo} diverge do plano")

        status = linha.get("status", "")
        if status not in STATUS_VALIDOS:
            erros.append(f"{ident}: status inválido: {status}")
        if status != "sucesso" and not linha.get("erro"):
            erros.append(f"{ident}: falha técnica sem causa registrada")

        try:
            tentativa = int(linha.get("tentativa", ""))
            if tentativa < 1:
                raise ValueError
        except ValueError:
            erros.append(f"{ident}: número de tentativa inválido")

        if status != "sucesso":
            continue
        try:
            throughput = _finito(linha, "throughput_msg_s")
            p50 = _finito(linha, "latencia_p50_ms")
            p99 = _finito(linha, "latencia_p99_ms")
            cpu = _finito(linha, "cpu_percent_medio")
            memoria = _finito(linha, "memoria_mib_media")
        except (TypeError, ValueError) as exc:
            erros.append(f"{ident}: {exc}")
            continue
        if throughput is None or throughput <= protocolo["faixas_integridade"]["throughput_msg_s_min_exclusivo"]:
            erros.append(f"{ident}: throughput deve ser positivo")
        if p50 is None or p99 is None or p50 < 0 or p99 < 0:
            erros.append(f"{ident}: latências devem ser finitas e não negativas")
        elif p99 < p50:
            erros.append(f"{ident}: p99 menor que p50")
        if cpu is None:
            avisos.append(f"{ident}: CPU não registrada")
        elif not protocolo["faixas_integridade"]["cpu_percent_min"] <= cpu <= protocolo["faixas_integridade"]["cpu_percent_max"]:
            erros.append(f"{ident}: CPU fora da faixa plausível")
        if memoria is None:
            avisos.append(f"{ident}: memória não registrada")
        elif not protocolo["faixas_integridade"]["memoria_mib_min"] <= memoria <= protocolo["faixas_integridade"]["memoria_mib_max"]:
            erros.append(f"{ident}: memória fora da faixa plausível")
        if p99 is not None and p99 > esperado.medicao_s * 1000:
            avisos.append(f"{ident}: p99 extremo, preservado para análise")

        bruto = linha.get("resultado_bruto", "").replace("\\", "/")
        if not bruto or not (diretorio / bruto).is_file():
            erros.append(f"{ident}: bruto de uma tentativa bem-sucedida ausente")

    for ident, tentativas in por_id.items():
        numeros = []
        for linha in tentativas:
            try:
                numeros.append(int(linha.get("tentativa", "")))
            except ValueError:
                pass
        if sorted(numeros) != list(range(1, len(tentativas) + 1)):
            erros.append(f"{ident}: sequência de tentativas inválida")

    sucessos_por_id = {
        ident: [r for r in por_id.get(ident, []) if r.get("status") == "sucesso"]
        for ident in esperados
    }
    faltantes = sorted(ident for ident, sucessos in sucessos_por_id.items() if not sucessos)
    duplicados = sorted(ident for ident, sucessos in sucessos_por_id.items() if len(sucessos) > 1)
    if faltantes:
        erros.append(f"{len(faltantes)} IDs planejados sem sucesso")
    if duplicados:
        erros.append("mais de um sucesso para os IDs: " + ", ".join(duplicados))

    contagens = Counter()
    for ident, sucessos in sucessos_por_id.items():
        if len(sucessos) == 1:
            e = por_id_plano[ident]
            contagens[(e.experimento, e.broker, e.tamanho_bytes)] += 1
    for exp in (("E1",) if fase == "E1" else plano.EXPERIMENTOS):
        for broker in plano.BROKERS:
            for tamanho in plano.TAMANHOS_BYTES:
                if contagens[(exp, broker, tamanho)] != protocolo["execucoes_por_celula"]:
                    erros.append(f"{exp}/{broker}/{tamanho}: n válido diferente de 20")

    ids_e1 = {e.id_execucao for e in execucoes if e.experimento == "E1"}
    ha_e2 = any(r.get("experimento") == "E2" for r in linhas)
    if ha_e2 and any(not [r for r in por_id.get(i, []) if r.get("status") == "sucesso"] for i in ids_e1):
        erros.append("há dados E2 antes de todos os IDs E1 terem sucesso")

    taxas_e2 = {int(k): int(v) for k, v in manifesto.get("taxas_e2", {}).items()}
    tolerancia = protocolo["faixas_integridade"]["tolerancia_taxa_e2_fracao"]
    for linha in linhas:
        if linha.get("status") != "sucesso" or linha.get("experimento") != "E2":
            continue
        tamanho = int(linha["tamanho_bytes"])
        alvo = taxas_e2.get(tamanho)
        if alvo is None:
            erros.append(f"{linha['id_execucao']}: taxa E2 não congelada no manifesto")
            continue
        try:
            registrado = int(linha.get("taxa_alvo_msg_s", ""))
            throughput = float(linha["throughput_msg_s"])
        except ValueError:
            continue
        if registrado != alvo:
            erros.append(f"{linha['id_execucao']}: taxa alvo diverge do manifesto")
        if abs(throughput - alvo) / alvo > tolerancia:
            erros.append(f"{linha['id_execucao']}: throughput E2 fora da tolerância de 10%")

    if manifesto.get("schema") != 2:
        erros.append("manifesto não usa schema 2")
    hashes = manifesto.get("hashes", {})
    if hashes.get("resultados.csv") != sha256_arquivo(csv_resultados):
        erros.append("SHA-256 de resultados.csv divergente")
    brutos_atuais = _hashes_brutos(diretorio)
    brutos_manifesto = hashes.get("brutos", {})
    if set(brutos_manifesto) != set(brutos_atuais):
        erros.append("lista de brutos do manifesto diverge dos arquivos existentes")
    for caminho, digest in brutos_atuais.items():
        if brutos_manifesto.get(caminho) != digest:
            erros.append(f"SHA-256 divergente: {caminho}")

    imagens_esperadas = {k: v["fingerprint"] for k, v in protocolo["imagens"].items()}
    for nome, esperado in imagens_esperadas.items():
        if manifesto.get("imagens", {}).get(nome) != esperado:
            erros.append(f"fingerprint da imagem {nome} diverge do protocolo")

    return {
        "valido": not erros,
        "fase": fase,
        "erros": erros,
        "avisos": avisos,
        "tentativas": len(linhas),
        "ids_validos": sum(len(sucessos) == 1 for sucessos in sucessos_por_id.values()),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Valida a coleta oficial do Lab05")
    parser.add_argument("coleta", type=Path)
    parser.add_argument("--fase", choices=("E1", "completa"), default="completa")
    args = parser.parse_args()
    relatorio = validar(args.coleta.resolve(), args.fase)
    print(json.dumps(relatorio, ensure_ascii=False, indent=2))
    return 0 if relatorio["valido"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
