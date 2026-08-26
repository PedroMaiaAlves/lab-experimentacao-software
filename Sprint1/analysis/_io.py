"""Utilitário comum de exportação dos resultados das RQs para JSON."""
import json


def salvar_json(resultado: dict, caminho: str) -> None:
    """Salva o resultado como JSON estrito, recusando NaN e infinito."""
    with open(caminho, "w", encoding="utf-8") as f:
        json.dump(
            resultado,
            f,
            ensure_ascii=False,
            indent=2,
            allow_nan=False,
            default=str,
        )
        f.write("\n")
