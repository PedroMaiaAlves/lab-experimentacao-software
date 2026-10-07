"""Classificação DORA com os cortes fixos da disciplina (tabela de referência da RQ 07)."""
from enum import IntEnum
from math import floor
from statistics import median


class Categoria(IntEnum):
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    ELITE = 4


HORAS_DIA = 24
HORAS_SEMANA = 7 * 24
DIAS_MES = 30  # mesmo "mês" do corte de lead time (< 30 dias)
UM_POR_MES_EM_SEMANAS = 7 / DIAS_MES  # 1 deploy a cada 30 dias, em deploys/semana


def _validar(valor):
    if valor < 0:
        raise ValueError(f"valor negativo não faz sentido para a métrica: {valor}")


def classificar_deployment_frequency(releases_por_semana):
    if releases_por_semana is None:
        return None
    _validar(releases_por_semana)
    if releases_por_semana >= 7:
        return Categoria.ELITE
    if releases_por_semana >= 1:
        return Categoria.HIGH
    if releases_por_semana >= UM_POR_MES_EM_SEMANAS:
        return Categoria.MEDIUM
    return Categoria.LOW


def classificar_lead_time(horas):
    """Mediana do lead time, em horas."""
    if horas is None:
        return None
    _validar(horas)
    if horas < HORAS_DIA:
        return Categoria.ELITE
    if horas < HORAS_SEMANA:
        return Categoria.HIGH
    if horas < DIAS_MES * HORAS_DIA:
        return Categoria.MEDIUM
    return Categoria.LOW


def classificar_cfr(taxa):
    """Change failure rate como fração entre 0 e 1 (0,15 = 15%)."""
    if taxa is None:
        return None
    _validar(taxa)
    if taxa <= 0.15:
        return Categoria.ELITE
    if taxa <= 0.30:
        return Categoria.HIGH
    if taxa <= 0.45:
        return Categoria.MEDIUM
    return Categoria.LOW


def classificar_tempo_recuperacao(horas):
    """Mediana do tempo de recuperação, em horas."""
    if horas is None:
        return None
    _validar(horas)
    if horas < 1:
        return Categoria.ELITE
    if horas < HORAS_DIA:
        return Categoria.HIGH
    if horas < HORAS_SEMANA:
        return Categoria.MEDIUM
    return Categoria.LOW


def classificar_geral(categorias, minimo_metricas=3):
    """Mediana das notas (Elite=4 ... Low=1), arredondada para baixo.

    Métricas ausentes (None) são ignoradas; com menos de `minimo_metricas` notas
    disponíveis o repositório fica sem classificação geral (None).
    DECISÃO DO GRUPO: registrar esse mínimo na Metodologia.
    """
    notas = [int(c) for c in categorias if c is not None]
    if len(notas) < minimo_metricas:
        return None
    return Categoria(floor(median(notas)))


def classificar_repositorio(deployment_frequency, lead_time_horas, cfr, tempo_recuperacao_horas,
                            minimo_metricas=3):
    por_metrica = {
        "deployment_frequency": classificar_deployment_frequency(deployment_frequency),
        "lead_time": classificar_lead_time(lead_time_horas),
        "cfr": classificar_cfr(cfr),
        "tempo_recuperacao": classificar_tempo_recuperacao(tempo_recuperacao_horas),
    }
    por_metrica["geral"] = classificar_geral(list(por_metrica.values()), minimo_metricas)
    return por_metrica
