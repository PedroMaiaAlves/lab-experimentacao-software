def distribuir_cotas(demandas, estoque):
    if not isinstance(demandas, dict):
        raise ValueError("demandas deve ser dict")
    if isinstance(estoque, bool) or not isinstance(estoque, int):
        raise ValueError("estoque invalido")
    if estoque < 0:
        raise ValueError("estoque negativo")
    for k, v in demandas.items():
        if not isinstance(k, str) or not k.strip():
            raise ValueError("identificador invalido")
        if isinstance(v, bool) or not isinstance(v, int):
            raise ValueError("demanda invalida")
        if v < 0:
            raise ValueError("demanda negativa")

    if not demandas:
        return {}

    total = sum(demandas.values())
    a_distribuir = min(estoque, total)
    resultado = {}
    sobras = []
    dado = 0

    for nome in sorted(demandas):
        if total == 0:
            resultado[nome] = 0
        else:
            ideal = demandas[nome] * a_distribuir / total
            inteiro = min(int(ideal), demandas[nome])
            resultado[nome] = inteiro
            dado += inteiro
            sobras.append((nome, ideal - int(ideal)))

    restante = a_distribuir - dado
    sobras.sort(key=lambda x: (-x[1], x[0]))
    for i in range(restante):
        nome = sobras[i][0]
        if resultado[nome] < demandas[nome]:
            resultado[nome] += 1

    return dict(sorted(resultado.items()))
