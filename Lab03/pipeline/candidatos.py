"""S01-A2: seleção de repositórios candidatos via Search API.

A busca devolve no máximo 1.000 resultados por consulta; por isso fatiamos
recursivamente por faixas de estrelas até cada consulta ficar abaixo do teto.
Se uma faixa unitária ainda estiver saturada, usamos as linguagens configuradas
como última dimensão de partição e recusamos qualquer partição ainda saturada.
"""
import csv
import logging
import random
from pathlib import Path

log = logging.getLogger(__name__)

LIMITE_BUSCA = 1000
CAMPOS = ["full_name", "stars", "language", "default_branch", "created_at", "html_url", "consulta"]


def _consulta(faixa, linguagem=None):
    # archived/fork fora: não têm 12 meses de atividade comparável (decisão a citar na Metodologia)
    q = f"stars:{faixa} archived:false fork:false"
    if linguagem:
        q += f' language:"{linguagem}"'
    return q


def _buscar(client, q, max_itens=LIMITE_BUSCA):
    params = {"q": q, "sort": "stars", "order": "desc", "per_page": 100}
    primeira, _ = client.get_json("/search/repositories", params)
    itens = []
    for item in client.paginate("/search/repositories", params, chave="items"):
        itens.append(item)
        if len(itens) >= max_itens:
            break
    return primeira["total_count"], itens


def _normalizar(item, consulta):
    return {
        "full_name": item["full_name"],
        "stars": item["stargazers_count"],
        "language": item.get("language") or "",
        "default_branch": item.get("default_branch") or "",
        "created_at": item["created_at"],
        "html_url": item["html_url"],
        "consulta": consulta,
    }


def _limites_faixa(faixa, itens):
    if ".." in faixa:
        inicio, fim = faixa.split("..", 1)
        return int(inicio), int(fim)
    if faixa.startswith(">") and itens:
        return int(faixa[1:]) + 1, max(int(item["stargazers_count"]) for item in itens)
    return None


def _buscar_por_linguagens(client, faixa, linguagens):
    if not linguagens:
        raise RuntimeError(
            "consulta saturada não pode ser subdividida por estrelas e "
            f"não há linguagens de fallback configuradas: {_consulta(faixa)}"
        )

    particoes = []
    for linguagem in linguagens:
        q = _consulta(faixa, linguagem)
        total, itens = _buscar(client, q)
        log.info(
            "faixa %s, linguagem %s: %d repositórios no total, %d obtidos",
            faixa, linguagem, total, len(itens),
        )
        if total >= LIMITE_BUSCA:
            raise RuntimeError(
                "consulta saturada mesmo após subdivisão por estrelas e linguagem: "
                f"{q} ({total} resultados)"
            )
        particoes.append((q, itens))
    return particoes


def _buscar_faixa_completa(client, faixa, linguagens):
    q = _consulta(faixa)
    total, itens = _buscar(client, q)
    log.info("faixa %s: %d repositórios no total, %d obtidos", faixa, total, len(itens))
    if total < LIMITE_BUSCA:
        return [(q, itens)]

    limites = _limites_faixa(faixa, itens)
    if limites is None or limites[0] >= limites[1]:
        log.warning(
            "faixa %s continua saturada com %d resultados: subdividindo por linguagem",
            faixa, total,
        )
        return _buscar_por_linguagens(client, faixa, linguagens)
    inicio, fim = limites
    meio = (inicio + fim) // 2
    log.warning("faixa %s tem %d resultados: subdividindo em %d..%d e %d..%d",
                faixa, total, inicio, meio, meio + 1, fim)
    return (
        _buscar_faixa_completa(client, f"{inicio}..{meio}", linguagens)
        + _buscar_faixa_completa(client, f"{meio + 1}..{fim}", linguagens)
    )


def selecionar_candidatos(client, cfg):
    """Devolve candidatos únicos, embaralhados com a semente do config."""
    sel = cfg["selecao"]
    vistos = {}
    for faixa in sel["faixas_estrelas"]:
        for consulta, lista in _buscar_faixa_completa(client, faixa, sel["linguagens"]):
            for item in lista:
                # setdefault: o primeiro que aparece vence; nome em minúsculas evita duplicata por caixa
                vistos.setdefault(item["full_name"].lower(), _normalizar(item, consulta))
    candidatos = list(vistos.values())
    # embaralhar com semente fixa evita viés de "só os mais famosos" e é reprodutível
    random.Random(cfg["semente"]).shuffle(candidatos)
    log.info("%d candidatos únicos", len(candidatos))
    return candidatos


def salvar_candidatos(candidatos, caminho):
    caminho = Path(caminho)
    caminho.parent.mkdir(parents=True, exist_ok=True)
    with open(caminho, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=CAMPOS)
        w.writeheader()
        w.writerows(candidatos)


def carregar_candidatos(caminho):
    with open(caminho, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))
