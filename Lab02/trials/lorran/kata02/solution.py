def planejar_recargas(consumos, capacidade):
    if capacidade <= 0:
        raise ValueError("capacidade deve ser positiva")
    for c in consumos:
        if c < 0:
            raise ValueError("consumo negativo")
        if c > capacidade:
            raise ValueError("consumo excede capacidade")

    recargas = []
    nivel = capacidade
    for i, consumo in enumerate(consumos):
        if consumo > nivel:
            recargas.append(i)
            nivel = capacidade
        nivel -= consumo
    return recargas
