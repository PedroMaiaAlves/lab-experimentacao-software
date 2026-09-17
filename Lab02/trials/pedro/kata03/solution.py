def agrupar_alertas(alertas, janela):
    if janela < 0:
        raise ValueError("janela não pode ser negativa")

    por_categoria = {}

    for alerta in alertas:
        if not isinstance(alerta, dict):
            raise ValueError("cada alerta deve ser um dicionário")

        if "instante" not in alerta or "categoria" not in alerta:
            raise ValueError("alerta deve possuir instante e categoria")

        instante = alerta["instante"]
        categoria = alerta["categoria"]

        if isinstance(instante, bool) or not isinstance(instante, (int, float)):
            raise ValueError("instante deve ser um número não negativo")

        if instante < 0:
            raise ValueError("instante deve ser um número não negativo")

        if not isinstance(categoria, str) or not categoria:
            raise ValueError("categoria deve ser uma string não vazia")

        por_categoria.setdefault(categoria, []).append(instante)

    grupos = []

    for categoria, instantes in por_categoria.items():
        instantes.sort()

        inicio = instantes[0]
        fim = instantes[0]
        quantidade = 1

        for instante in instantes[1:]:
            # Regra encadeada: compara com o último instante
            # pertencente ao grupo atual.
            if instante - fim <= janela:
                fim = instante
                quantidade += 1
            else:
                grupos.append({
                    "categoria": categoria,
                    "inicio": inicio,
                    "fim": fim,
                    "quantidade": quantidade,
                })

                inicio = instante
                fim = instante
                quantidade = 1

        grupos.append({
            "categoria": categoria,
            "inicio": inicio,
            "fim": fim,
            "quantidade": quantidade,
        })

    grupos.sort(key=lambda grupo: (grupo["inicio"], grupo["categoria"]))

    return grupos