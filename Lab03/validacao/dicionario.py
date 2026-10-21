"""Confere colunas documentadas nos CSVs de um diretório, sem alterar arquivos."""
import argparse
import csv
from pathlib import Path
import re


def colunas_documentadas(texto):
    secoes, atual = {}, None
    for linha in texto.splitlines():
        if re.match(r"^#{1,6}\s", linha):
            nomes = re.findall(r"`([^`]+\.csv)`", linha)
            atual = nomes[0] if nomes else None
            if atual:
                secoes.setdefault(atual, [])
        elif atual:
            campo = re.match(r"\|\s*`([^`]+)`\s*\|", linha)
            if campo:
                secoes[atual].append(campo[1])
    return secoes


def inferir_tipos(caminho):
    with Path(caminho).open(encoding="utf-8-sig", newline="") as arquivo:
        leitor = csv.DictReader(arquivo)
        campos = leitor.fieldnames or []
        linhas = list(leitor)
    tipos = {}
    for campo in campos:
        valores = [r[campo] for r in linhas if r.get(campo)]
        if valores and all(re.fullmatch(r"[+-]?\d+", v) for v in valores):
            tipos[campo] = "inteiro"
        elif valores:
            try:
                for v in valores:
                    float(v)
                tipos[campo] = "real"
            except ValueError:
                tipos[campo] = "texto"
        else:
            tipos[campo] = "texto"
    return tipos


def verificar(dicionario, dados):
    docs = colunas_documentadas(Path(dicionario).read_text(encoding="utf-8"))
    sem_secao, faltando, obsoletas = [], {}, {}
    for caminho in sorted(Path(dados).rglob("*.csv")):
        nome = caminho.relative_to(dados).as_posix()
        documentadas = docs.get(nome, docs.get(caminho.name))
        if documentadas is None:
            sem_secao.append(caminho)
            continue
        with caminho.open(encoding="utf-8-sig", newline="") as arquivo:
            campos = next(csv.reader(arquivo), [])
        novas = [c for c in campos if c not in documentadas]
        antigas = [c for c in documentadas if c not in campos]
        if novas:
            faltando[caminho] = novas
        if antigas:
            obsoletas[caminho] = antigas
    return sem_secao, faltando, obsoletas


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dicionario", default="docs/dicionario_dados.md")
    parser.add_argument("--dados", default="data")
    parser.add_argument("--esqueleto", action="store_true", help="imprime sugestões; não escreve no dicionário")
    args = parser.parse_args(argv)
    if not Path(args.dados).is_dir():
        parser.error("diretório de dados inexistente")
    sem_secao, faltando, obsoletas = verificar(args.dicionario, args.dados)
    for p in sem_secao:
        print(f"SEM SEÇÃO: {p.name}")
    for p, campos in faltando.items():
        print(f"COLUNAS SEM DOCUMENTAÇÃO: {p.name}: {', '.join(campos)}")
    for p, campos in obsoletas.items():
        print(f"COLUNAS OBSOLETAS: {p.name}: {', '.join(campos)}")
    if args.esqueleto:
        for p in sorted(set(sem_secao) | set(faltando)):
            print(f"\n### `{p.name}`\n\n| Coluna | Tipo | Unidade/definição |\n|---|---|---|")
            for campo, tipo in inferir_tipos(p).items():
                if p in sem_secao or campo in faltando[p]:
                    print(f"| `{campo}` | {tipo} | PREENCHER |")
    return int(bool(sem_secao or faltando or obsoletas))


if __name__ == "__main__":
    raise SystemExit(main())
