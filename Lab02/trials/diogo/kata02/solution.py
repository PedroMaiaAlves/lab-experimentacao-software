def planejar_recargas(consumos, capacidade):
    if capacidade <= 0:
        raise ValueError("A capacidade deve ser positiva")


    for consumo in consumos:
        if consumo < 0:
            raise ValueError("O consumo não pode ser negativo")

        if consumo > capacidade:
            raise ValueError("O consumo não pode ser maior que a capacidade")

    capacidade_atual = capacidade
    recargas = []

    for index, consumo in enumerate(consumos):
        if capacidade_atual < consumo:
            recargas.append(index)
            capacidade_atual = capacidade

        capacidade_atual -= consumo

    return recargas

