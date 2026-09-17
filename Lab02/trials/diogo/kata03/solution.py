def agrupar_alertas(alertas, janela):
    """Agrupa alertas próximos da mesma categoria sem modificar a entrada."""

    if janela < 0:
        raise ValueError("janela não pode ser negativa")

    if not isinstance(alertas, list):
        raise ValueError("alertas deve ser uma lista")

    grupos = []

    # Validação + cópia para não modificar a entrada
    alertas_ordenados = []

    for alerta in alertas:
        if not isinstance(alerta, dict):
            raise ValueError("cada alerta deve ser um dicionário")

        if "instante" not in alerta or "categoria" not in alerta:
            raise ValueError("cada alerta deve possuir instante e categoria")

        instante = alerta["instante"]
        categoria = alerta["categoria"]

        if isinstance(instante, bool) or not isinstance(instante, (int, float)):
            raise ValueError("instante deve ser um número não negativo")

        if instante < 0:
            raise ValueError("instante deve ser um número não negativo")

        if not isinstance(categoria, str) or categoria == "":
            raise ValueError("categoria deve ser uma string não vazia")

        alertas_ordenados.append({
            "instante": instante,
            "categoria": categoria
        })

    # Ordena sem alterar a lista original
    alertas_ordenados.sort(key=lambda alerta: (alerta["categoria"], alerta["instante"]))

    # Agrupa por categoria
    categoria_atual = None
    inicio = None
    fim = None
    quantidade = 0

    for alerta in alertas_ordenados:
        instante = alerta["instante"]
        categoria = alerta["categoria"]

        # Primeira categoria ou mudança de categoria
        if categoria_atual != categoria:
            if categoria_atual is not None:
                grupos.append({
                    "categoria": categoria_atual,
                    "inicio": inicio,
                    "fim": fim,
                    "quantidade": quantidade
                })

            categoria_atual = categoria
            inicio = instante
            fim = instante
            quantidade = 1

        # Mesmo grupo
        elif instante - fim <= janela:
            fim = instante
            quantidade += 1

        # Novo grupo
        else:
            grupos.append({
                "categoria": categoria_atual,
                "inicio": inicio,
                "fim": fim,
                "quantidade": quantidade
            })

            inicio = instante
            fim = instante
            quantidade = 1

    # Adiciona o último grupo
    if categoria_atual is not None:
        grupos.append({
            "categoria": categoria_atual,
            "inicio": inicio,
            "fim": fim,
            "quantidade": quantidade
        })

    # Ordenação final: inicio e, em empate, categoria
    grupos.sort(key=lambda grupo: (grupo["inicio"], grupo["categoria"]))

    return grupos