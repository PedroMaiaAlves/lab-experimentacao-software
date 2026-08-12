"""Pacote responsável pela coleta de dados via API GraphQL do GitHub."""
from .client import coletar_repositorios

__all__ = ["coletar_repositorios"]
