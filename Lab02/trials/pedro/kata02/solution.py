def planejar_recargas(consumos, capacidade):
    if len(consumos) == 0:
        return []

    if capacidade <= 0:
        raise ValueError

    if any(x < 0 for x in consumos):
        raise ValueError

    if any(x > capacidade for x in consumos):
        raise ValueError

    consumos = tuple(consumos)
    recargas = []
    indice = 0

    for consumo in consumos:
        if (capacidade - consumo) < 0:
            recargas.append(indice)
            capacidade = 5

        capacidade = capacidade - consumo
        indice += 1
    return recargas

    #"""Retorna os índices em que uma recarga é necessária antes do consumo."""
    #raise NotImplementedError("Implemente planejar_recargas")
