"""Verifica o portão G1 (#209): o E1 está estável o bastante para a coleta oficial?

Critérios (planejamento_s02.md, constantes em experimento/plano.py):
  - em cada célula do E1, CV do throughput entre execuções <= G1_CV_MAXIMO (20%);
  - nenhuma execução com colapso (intervalo < 10% do maior intervalo da própria execução);
  - nenhuma execução da célula com throughput < 10% da mediana da célula;
  - ao menos 3 execuções com sucesso por célula.

A estabilidade é recalculada a partir dos JSON brutos do OMB, então o script
também roda sobre coletas antigas (linha de base do piloto de 19/11).

Uso: python Lab05/portao_g1.py Lab05/data/piloto_g1/<coleta>/resultados.csv
Saída: Lab05/data/analise/g1_<coleta>.json
"""

from __future__ import annotations

import argparse
import csv
import json
import statistics
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent
sys.path.insert(0, str(RAIZ))

from experimento import plano  # noqa: E402
from experimento.coleta import estabilidade_intervalos  # noqa: E402

MINIMO_EXECUCOES = 3


def carregar_e1(caminho_csv: Path) -> list[dict]:
    pasta = caminho_csv.parent
    linhas = []
    with caminho_csv.open(encoding="utf-8") as f:
        for r in csv.DictReader(f):
            if r["experimento"] != "E1":
                continue
            item = {
                "id_execucao": r["id_execucao"],
                "broker": r["broker"],
                "tamanho_bytes": int(r["tamanho_bytes"]),
                "status": r["status"],
                "taxa_alvo_msg_s": r.get("taxa_alvo_msg_s") or None,
            }
            bruto = r.get("resultado_bruto")
            if r["status"] == "sucesso" and bruto and (pasta / bruto).exists():
                dados = json.loads((pasta / bruto).read_text(encoding="utf-8"))
                taxas = [float(v) for v in dados.get("publishRate", [])]
                item["throughput_msg_s"] = statistics.fmean(taxas)
                item["taxas_intervalo"] = [round(t, 1) for t in taxas]
                item.update(estabilidade_intervalos(taxas))
            linhas.append(item)
    return linhas


def avaliar(linhas: list[dict]) -> dict:
    celulas = []
    for broker in plano.BROKERS:
        for tamanho in plano.TAMANHOS_BYTES:
            todas = [l for l in linhas if l["broker"] == broker and l["tamanho_bytes"] == tamanho]
            ok = [l for l in todas if "throughput_msg_s" in l]
            valores = [l["throughput_msg_s"] for l in ok]
            motivos = []
            cel = {
                "broker": broker,
                "tamanho_bytes": tamanho,
                "tentativas": len(todas),
                "sucessos": len(ok),
                "falhas": [l["id_execucao"] for l in todas if l["status"] != "sucesso"],
            }
            if len(ok) < MINIMO_EXECUCOES:
                motivos.append(f"menos de {MINIMO_EXECUCOES} execuções com sucesso")
            if valores:
                mediana = statistics.median(valores)
                cv = statistics.stdev(valores) / statistics.fmean(valores) if len(valores) > 1 else None
                paradas = [l["id_execucao"] for l in ok if mediana > 0 and l["throughput_msg_s"] < plano.G1_FRACAO_COLAPSO * mediana]
                colapsos = [l["id_execucao"] for l in ok if l.get("colapso")]
                cel.update(
                    mediana_msg_s=round(mediana, 1),
                    cv_entre_execucoes=round(cv, 4) if cv is not None else None,
                    execucoes_colapsadas=colapsos,
                    execucoes_abaixo_10pct_da_celula=paradas,
                    cv_intervalos_mediano=round(statistics.median(l["cv_intervalos"] for l in ok if l.get("cv_intervalos") is not None), 4)
                    if any(l.get("cv_intervalos") is not None for l in ok) else None,
                )
                if cv is None or cv > plano.G1_CV_MAXIMO:
                    motivos.append(f"CV entre execuções {cv:.0%} > {plano.G1_CV_MAXIMO:.0%}" if cv is not None else "CV indefinido")
                if colapsos:
                    motivos.append(f"{len(colapsos)} execução(ões) com colapso dentro da medição")
                if paradas:
                    motivos.append(f"{len(paradas)} execução(ões) abaixo de 10% da mediana da célula")
            cel["aprovada"] = not motivos
            cel["motivos"] = motivos
            celulas.append(cel)
    return {
        "criterios": {
            "cv_maximo": plano.G1_CV_MAXIMO,
            "fracao_colapso": plano.G1_FRACAO_COLAPSO,
            "minimo_execucoes": MINIMO_EXECUCOES,
        },
        "aprovado": all(c["aprovada"] for c in celulas),
        "celulas": celulas,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "resultados", type=Path, nargs="+",
        help="resultados.csv de uma coleta (e, opcionalmente, das repetições de falhas dela)",
    )
    args = parser.parse_args()
    caminhos = [c.resolve() for c in args.resultados]
    linhas = [linha for c in caminhos for linha in carregar_e1(c)]
    nome = caminhos[0].parent.name
    relatorio = {"coleta": nome, "arquivos": [c.parent.name for c in caminhos], **avaliar(linhas), "execucoes": linhas}

    destino = RAIZ / "data" / "analise" / f"g1_{nome}.json"
    destino.parent.mkdir(parents=True, exist_ok=True)
    destino.write_text(json.dumps(relatorio, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"Portão G1 — coleta {' + '.join(relatorio['arquivos'])}: {'APROVADO' if relatorio['aprovado'] else 'REPROVADO'}")
    for c in relatorio["celulas"]:
        cv = c.get("cv_entre_execucoes")
        print(
            f"  {c['broker']:8} {c['tamanho_bytes'] // 1024:>2} KiB  n={c['sucessos']}/{c['tentativas']}"
            f"  mediana={c.get('mediana_msg_s', '-'):>10}  CV={'-' if cv is None else f'{cv:.0%}':>5}"
            f"  {'ok' if c['aprovada'] else '; '.join(c['motivos'])}"
        )
    print(f"relatório -> {destino.relative_to(RAIZ)}")
    return 0 if relatorio["aprovado"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
