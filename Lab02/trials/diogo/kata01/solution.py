def consolidar_janelas(janelas, tolerancia=0):
    if tolerancia < 0:
        raise ValueError("tolerancia não pode ser negativa")

    if len(janelas) == 0:
        return []

    for inicio, fim in janelas:
        if inicio > fim:
            raise ValueError("o inicio não pode ser maior que o fim")

    ordenadas = sorted(janelas, key=lambda intervalo: intervalo[0])

    merged = [ordenadas[0]]

    for inicio, fim in ordenadas[1:]:
        inicio_anterior, fim_anterior = merged[-1]

        if inicio <= fim_anterior + tolerancia:
            merged[-1] = (
                inicio_anterior,
                max(fim_anterior, fim)
            )
        else:
            merged.append((inicio, fim))

    return merged
    
