def distribuir_cotas(demandas, estoque):
    if type(demandas) is not dict:
        raise ValueError

    if type(estoque) is not int or estoque < 0:
        raise ValueError

    total = 0

    for nome in demandas:
        if type(nome) is not str or nome.strip() == "":
            raise ValueError

        quantidade = demandas[nome]

        if type(quantidade) is not int or quantidade < 0:
            raise ValueError

        total += quantidade

    nomes = sorted(demandas)
    resultado = {}
    restos = {}

    for nome in nomes:
        resultado[nome] = 0

    if total == 0:
        return resultado

    disponivel = estoque
    if disponivel > total:
        disponivel = total

    distribuidos = 0

    for nome in nomes:
        valor = demandas[nome] * disponivel

        resultado[nome] = valor // total
        restos[nome] = valor % total

        distribuidos += resultado[nome]

    faltam = disponivel - distribuidos

    while faltam > 0:
        escolhido = ""
        maior_resto = -1

        for nome in nomes:
            if restos[nome] > maior_resto:
                maior_resto = restos[nome]
                escolhido = nome

        resultado[escolhido] += 1
        restos[escolhido] = -1
        faltam -= 1

    return resultado