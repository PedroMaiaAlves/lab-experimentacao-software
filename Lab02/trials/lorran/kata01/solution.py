def consolidar_janelas(janelas, tolerancia=0):
    if tolerancia < 0:
        raise ValueError("tolerancia negativa")
    for j in janelas:
        if j[0] > j[1]:
            raise ValueError("inicio maior que fim")

    if len(janelas) == 0:
        return []

    ordenadas = sorted(janelas, key=lambda x: x[0])
    resultado = [ordenadas[0]]

    for i in range(1, len(ordenadas)):
        ultimo_inicio, ultimo_fim = resultado[-1]
        atual_inicio, atual_fim = ordenadas[i]
        if atual_inicio <= ultimo_fim + tolerancia:
            resultado[-1] = (ultimo_inicio, max(ultimo_fim, atual_fim))
        else:
            resultado.append(ordenadas[i])

    return resultado
