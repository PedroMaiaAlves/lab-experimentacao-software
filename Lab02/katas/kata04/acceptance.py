import unittest

from solution import distribuir_cotas


class DistribuirCotasTest(unittest.TestCase):
    def test_demandas_vazias(self):
        self.assertEqual({}, distribuir_cotas({}, 10))

    def test_estoque_zero_retorna_cotas_zero_em_ordem_alfabetica(self):
        resultado = distribuir_cotas({"sul": 3, "norte": 2}, 0)
        self.assertEqual({"norte": 0, "sul": 0}, resultado)
        self.assertEqual(["norte", "sul"], list(resultado))

    def test_distribui_proporcao_exata(self):
        self.assertEqual(
            {"norte": 1, "sul": 3},
            distribuir_cotas({"norte": 2, "sul": 6}, 4),
        )

    def test_distribui_unidades_pelos_maiores_restos(self):
        demandas = {"alta": 5, "media": 3, "baixa": 2}
        esperado = {"alta": 1, "baixa": 1, "media": 1}
        self.assertEqual(esperado, distribuir_cotas(demandas, 3))

    def test_desempata_restos_alfabeticamente(self):
        demandas = {"caio": 1, "bia": 1, "ana": 1}
        esperado = {"ana": 1, "bia": 1, "caio": 0}
        self.assertEqual(esperado, distribuir_cotas(demandas, 2))

    def test_limita_cotas_e_preserva_demanda_zero_e_entrada(self):
        demandas = {"sul": 0, "norte": 2}
        original = dict(demandas)
        resultado = distribuir_cotas(demandas, 5)
        self.assertEqual({"norte": 2, "sul": 0}, resultado)
        self.assertEqual(original, demandas)

    def test_rejeita_estoque_ou_demanda_negativa(self):
        with self.subTest(campo="estoque"):
            with self.assertRaises(ValueError):
                distribuir_cotas({"norte": 1}, -1)
        with self.subTest(campo="demanda"):
            with self.assertRaises(ValueError):
                distribuir_cotas({"norte": -1}, 1)

    def test_rejeita_identificadores_e_tipos_invalidos(self):
        casos = [
            ([], 1),
            ({"": 1}, 1),
            ({"   ": 1}, 1),
            ({1: 1}, 1),
            ({"norte": 1.5}, 1),
            ({"norte": True}, 1),
            ({"norte": 1}, True),
        ]
        for demandas, estoque in casos:
            with self.subTest(demandas=demandas, estoque=estoque):
                with self.assertRaises(ValueError):
                    distribuir_cotas(demandas, estoque)


if __name__ == "__main__":
    unittest.main()
