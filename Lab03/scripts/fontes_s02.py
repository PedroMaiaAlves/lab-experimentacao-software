"""Publica e restaura as fontes congeladas sem cache, tokens ou arquivos intermediários."""
import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath
import shutil
import tempfile
from zipfile import ZIP_DEFLATED, ZipFile

from pipeline.sprint2 import sha256


def fontes_esperadas(manifesto):
    fontes = dict(manifesto["fontes_sha256"])
    for arquivos in manifesto["fontes_repos_sha256"].values():
        fontes.update({n: h for n, h in arquivos.items() if n.startswith("workflow_runs/")})
    for nome in fontes:
        caminho = PurePosixPath(nome)
        if caminho.is_absolute() or ".." in caminho.parts or "\\" in nome or ":" in nome:
            raise ValueError(f"caminho de fonte inseguro: {nome}")
    return fontes


def empacotar(manifesto, dados, destino):
    dados, destino = Path(dados), Path(destino)
    fontes = fontes_esperadas(manifesto)
    for nome, esperado in fontes.items():
        if sha256(dados / nome) != esperado:
            raise ValueError(f"fonte alterada: {nome}")
    destino.parent.mkdir(parents=True, exist_ok=True)
    if destino.exists():
        verificar(manifesto, destino)
        return
    with tempfile.NamedTemporaryFile(dir=destino.parent, suffix=".zip", delete=False) as arquivo:
        temporario = Path(arquivo.name)
    try:
        with ZipFile(temporario, "w", ZIP_DEFLATED, compresslevel=9) as pacote:
            for nome in sorted(fontes):
                pacote.write(dados / nome, nome)
        verificar(manifesto, temporario)
        temporario.replace(destino)
    finally:
        temporario.unlink(missing_ok=True)


def verificar(manifesto, pacote):
    fontes = fontes_esperadas(manifesto)
    with ZipFile(pacote) as arquivo:
        if len(arquivo.namelist()) != len(fontes) or set(arquivo.namelist()) != set(fontes):
            raise ValueError("o pacote não contém exatamente as fontes congeladas")
        for nome, esperado in fontes.items():
            with arquivo.open(nome) as item:
                if hashlib.file_digest(item, "sha256").hexdigest() != esperado:
                    raise ValueError(f"hash inválido no pacote: {nome}")
    return len(fontes)


def restaurar(manifesto, pacote, destino):
    verificar(manifesto, pacote)
    destino = Path(destino).resolve()
    fontes = fontes_esperadas(manifesto)
    for nome, esperado in fontes.items():
        caminho = (destino / nome).resolve()
        if not caminho.is_relative_to(destino):
            raise ValueError("extração fora do destino")
        if caminho.exists() and sha256(caminho) != esperado:
            raise ValueError(f"não sobrescreva fonte local diferente: {nome}")
    with ZipFile(pacote) as arquivo:
        for nome in fontes:
            caminho = destino / nome
            if caminho.exists():
                continue
            caminho.parent.mkdir(parents=True, exist_ok=True)
            with tempfile.NamedTemporaryFile(dir=caminho.parent, delete=False) as item:
                temporario = Path(item.name)
                with arquivo.open(nome) as origem:
                    shutil.copyfileobj(origem, item)
            temporario.replace(caminho)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("acao", choices=["empacotar", "verificar", "restaurar"])
    ap.add_argument("--manifesto", default="data/amostra_final.manifest.json")
    ap.add_argument("--pacote", default="data/fontes_s02.zip")
    ap.add_argument("--dados", default="data/s02")
    a = ap.parse_args(argv)
    manifesto = json.loads(Path(a.manifesto).read_text(encoding="utf-8"))
    if a.acao == "empacotar":
        empacotar(manifesto, a.dados, a.pacote)
    elif a.acao == "restaurar":
        restaurar(manifesto, a.pacote, a.dados)
    total = verificar(manifesto, a.pacote)
    print(f"{total} fontes verificadas; SHA-256 do pacote: {sha256(a.pacote)}")


if __name__ == "__main__":
    main()
