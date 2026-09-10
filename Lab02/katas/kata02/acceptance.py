import unittest

from solution import planejar_recargas


class PlanejarRecargasTest(unittest.TestCase):
    def test_lista_vazia(self):
        self.assertEqual([], planejar_recargas([], 5))

    def test_capacidade_cobre_todo_percurso(self):
        self.assertEqual([], planejar_recargas([1, 1, 1], 5))

    def test_identifica_indice_de_recarga_com_consumos_desiguais(self):
        self.assertEqual([2], planejar_recargas([3, 1, 3], 5))

    def test_consumo_zero_nao_exige_recarga(self):
        self.assertEqual([], planejar_recargas([0, 0, 0], 1))

    def test_nao_modifica_entrada(self):
        consumos = [2, 2, 2]
        original = list(consumos)
        planejar_recargas(consumos, 5)
        self.assertEqual(original, consumos)

    def test_rejeita_capacidade_nao_positiva(self):
        with self.assertRaises(ValueError):
            planejar_recargas([1, 1], 0)

    def test_rejeita_consumo_negativo(self):
        with self.assertRaises(ValueError):
            planejar_recargas([1, -1], 5)

    def test_rejeita_consumo_maior_que_capacidade(self):
        with self.assertRaises(ValueError):
            planejar_recargas([1, 6], 5)


if __name__ == "__main__":
    unittest.main()
