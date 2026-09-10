import unittest

from solution import agrupar_alertas


class AgruparAlertasTest(unittest.TestCase):
    def test_lista_vazia(self):
        self.assertEqual([], agrupar_alertas([], 5))

    def test_cria_grupo_para_alerta_unico(self):
        alertas = [{"instante": 7, "categoria": "cpu"}]
        esperado = [{"categoria": "cpu", "inicio": 7, "fim": 7, "quantidade": 1}]
        self.assertEqual(esperado, agrupar_alertas(alertas, 2))

    def test_agrupa_por_diferenca_entre_eventos_consecutivos(self):
        alertas = [
            {"instante": 6, "categoria": "rede"},
            {"instante": 0, "categoria": "rede"},
            {"instante": 3, "categoria": "rede"},
        ]
        esperado = [{"categoria": "rede", "inicio": 0, "fim": 6, "quantidade": 3}]
        self.assertEqual(esperado, agrupar_alertas(alertas, 3))

    def test_separa_grupos_quando_intervalo_supera_janela(self):
        alertas = [
            {"instante": 1, "categoria": "cpu"},
            {"instante": 5, "categoria": "cpu"},
            {"instante": 10, "categoria": "cpu"},
        ]
        esperado = [
            {"categoria": "cpu", "inicio": 1, "fim": 5, "quantidade": 2},
            {"categoria": "cpu", "inicio": 10, "fim": 10, "quantidade": 1},
        ]
        self.assertEqual(esperado, agrupar_alertas(alertas, 4))

    def test_agrupa_categorias_independentemente_e_ordena_resultado(self):
        alertas = [
            {"instante": 4, "categoria": "rede"},
            {"instante": 3, "categoria": "cpu"},
            {"instante": 2, "categoria": "rede"},
            {"instante": 1, "categoria": "cpu"},
        ]
        esperado = [
            {"categoria": "cpu", "inicio": 1, "fim": 3, "quantidade": 2},
            {"categoria": "rede", "inicio": 2, "fim": 4, "quantidade": 2},
        ]
        self.assertEqual(esperado, agrupar_alertas(alertas, 2))

    def test_aceita_instantes_iguais_sem_modificar_entrada(self):
        alertas = [
            {"instante": 2, "categoria": "disco"},
            {"instante": 2, "categoria": "disco"},
        ]
        original = [dict(alerta) for alerta in alertas]
        esperado = [{"categoria": "disco", "inicio": 2, "fim": 2, "quantidade": 2}]
        self.assertEqual(esperado, agrupar_alertas(alertas, 0))
        self.assertEqual(original, alertas)

    def test_rejeita_janela_negativa(self):
        with self.assertRaises(ValueError):
            agrupar_alertas([], -1)

    def test_rejeita_alertas_invalidos(self):
        invalidos = [
            [{"categoria": "cpu"}],
            [{"instante": 1}],
            [{"instante": -1, "categoria": "cpu"}],
            [{"instante": True, "categoria": "cpu"}],
            [{"instante": 1, "categoria": ""}],
            [("cpu", 1)],
        ]
        for alertas in invalidos:
            with self.subTest(alertas=alertas):
                with self.assertRaises(ValueError):
                    agrupar_alertas(alertas, 1)


if __name__ == "__main__":
    unittest.main()
