def agrupar_alertas(alertas, janela):
    if janela < 0:
        raise ValueError("janela negativa")

    for alerta in alertas:
        if not isinstance(alerta, dict):
            raise ValueError("alerta invalido")
        if "instante" not in alerta or "categoria" not in alerta:
            raise ValueError("campo faltando")
        if isinstance(alerta["instante"], bool) or not isinstance(alerta["instante"], (int, float)):
            raise ValueError("instante invalido")
        if alerta["instante"] < 0:
            raise ValueError("instante negativo")
        if not isinstance(alerta["categoria"], str) or alerta["categoria"] == "":
            raise ValueError("categoria invalida")

    categorias = {}
    for alerta in alertas:
        cat = alerta["categoria"]
        if cat not in categorias:
            categorias[cat] = []
        categorias[cat].append(alerta["instante"])

    for cat in categorias:
        categorias[cat].sort()

    grupos = []
    for cat in categorias:
        instantes = categorias[cat]
        inicio = instantes[0]
        fim = instantes[0]
        qtd = 1
        for i in range(1, len(instantes)):
            if instantes[i] - fim <= janela:
                fim = instantes[i]
                qtd += 1
            else:
                grupos.append({"categoria": cat, "inicio": inicio, "fim": fim, "quantidade": qtd})
                inicio = instantes[i]
                fim = instantes[i]
                qtd = 1
        grupos.append({"categoria": cat, "inicio": inicio, "fim": fim, "quantidade": qtd})

    grupos.sort(key=lambda g: (g["inicio"], g["categoria"]))
    return grupos
