def distribuir_cotas(demandas, estoque):
    """Distribui o estoque proporcionalmente sem modificar as demandas."""

    # Validação do estoque
    if isinstance(estoque, bool) or not isinstance(estoque, int) or estoque < 0:
        raise ValueError("estoque deve ser um inteiro não negativo")

    # Validação das demandas
    if not isinstance(demandas, dict):
        raise ValueError("demandas deve ser um dicionário")

    for identificador, demanda in demandas.items():
        if (
            not isinstance(identificador, str)
            or identificador.strip() == ""
            or isinstance(demanda, bool)
            or not isinstance(demanda, int)
            or demanda < 0
         ):
            raise ValueError("dados de demanda inválidos")

    if not demandas:
        return {}

    total_demanda = sum(demandas.values())

    if total_demanda == 0 or estoque == 0:
        return {identificador: 0 for identificador in sorted(demandas)}

    quantidade = min(estoque, total_demanda)

    cotas = {}
    restos = []

    # Parte inteira da cota ideal
    for identificador in sorted(demandas):
        demanda = demandas[identificador]

        numerador = demanda * quantidade
        parte_inteira = numerador // total_demanda
        resto = numerador % total_demanda

        cotas[identificador] = parte_inteira
        restos.append((resto, identificador))

    # Quantidade ainda não distribuída
    restantes = quantidade - sum(cotas.values())

    # Maiores restos; empate pela ordem alfabética
    restos.sort(key=lambda item: (-item[0], item[1]))

    for _, identificador in restos[:restantes]:
        # A parte inteira já não ultrapassa a demanda.
        # Como a quantidade total distribuída não excede a demanda total,
        # o maior-resto mantém as cotas dentro dos limites.
        if cotas[identificador] < demandas[identificador]:
            cotas[identificador] += 1

    # Garante a ordem alfabética no dicionário retornado
    return {identificador: cotas[identificador] for identificador in sorted(cotas)}