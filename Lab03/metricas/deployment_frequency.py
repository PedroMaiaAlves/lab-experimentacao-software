from pipeline.config import semanas_da_janela
from pipeline.janela import na_janela


def deployment_frequency(datas_deploy, cfg):
    if cfg["janela_fim"] < cfg["janela_inicio"]:
        raise ValueError("janela_fim deve ser igual ou posterior a janela_inicio")
    total = sum(na_janela(str(data), cfg) for data in datas_deploy)
    return total / semanas_da_janela(cfg)
