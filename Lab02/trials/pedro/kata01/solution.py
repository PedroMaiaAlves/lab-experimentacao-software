def consolidar_janelas(janelas, tolerancia=0):
    """Consolida janelas sobrepostas ou próximas sem modificar a entrada."""
    
    if tolerancia < 0:
        raise ValueError("tolerancia não pode ser negativa")

    # Valida as janelas sem modificar a entrada.
    for inicio, fim in janelas:
        if inicio > fim:
            raise ValueError("inicio não pode ser maior que fim")

    if not janelas:
        return []

    # Ordena uma cópia da entrada pelo início.
    ordenadas = sorted(janelas, key=lambda janela: janela[0])

    resultado = []
    inicio_atual, fim_atual = ordenadas[0]

    for inicio, fim in ordenadas[1:]:
        # Consolida se houver sobreposição, adjacência
        # ou distância menor/igual à tolerância.
        if inicio <= fim_atual + tolerancia:
            fim_atual = max(fim_atual, fim)
        else:
            resultado.append((inicio_atual, fim_atual))
            inicio_atual, fim_atual = inicio, fim

    resultado.append((inicio_atual, fim_atual))

    return resultado