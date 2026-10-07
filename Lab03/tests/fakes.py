"""Cliente falso para testar as coletas sem chamar a API."""


class ClienteFalso:
    """Simula GitHubClient. `rotas` mapeia caminho -> resposta, onde a resposta pode ser:
    dados | (dados, headers) | função(params) devolvendo um dos dois."""

    def __init__(self, rotas):
        self.rotas = rotas
        self.chamadas = []

    def get_json(self, caminho, params=None):
        self.chamadas.append((caminho, params))
        resposta = self.rotas[caminho]
        if callable(resposta):
            resposta = resposta(params or {})
        if isinstance(resposta, tuple):
            return resposta
        return resposta, {}

    def paginate(self, caminho, params=None, chave=None):
        dados, _ = self.get_json(caminho, params)
        yield from (dados[chave] if chave else dados)
