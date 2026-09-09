import unittest

from solution import consolidar_janelas


class ConsolidarJanelasTest(unittest.TestCase):
    def test_lista_vazia(self):
        self.assertEqual([], consolidar_janelas([], 0))

    def test_ordena_sem_modificar_entrada(self):
        janelas = [(8, 9), (1, 2)]
        original = list(janelas)

        self.assertEqual([(1, 2), (8, 9)], consolidar_janelas(janelas, 0))
        self.assertEqual(original, janelas)

    def test_consolida_sobreposicao(self):
        resultado = consolidar_janelas([(1, 5), (3, 7), (10, 11)], 0)
        self.assertEqual([(1, 7), (10, 11)], resultado)

    def test_consolida_adjacencia(self):
        self.assertEqual([(1, 4)], consolidar_janelas([(1, 3), (3, 4)], 0))

    def test_aplica_tolerancia_ao_espaco_entre_janelas(self):
        resultado = consolidar_janelas([(1, 2), (4, 6), (9, 10)], 2)
        self.assertEqual([(1, 6), (9, 10)], resultado)

    def test_aceita_intervalos_pontuais(self):
        self.assertEqual([(5, 5)], consolidar_janelas([(5, 5)], 0))

    def test_rejeita_tolerancia_negativa(self):
        with self.assertRaises(ValueError):
            consolidar_janelas([(1, 2)], -1)

    def test_rejeita_janela_com_inicio_maior_que_fim(self):
        with self.assertRaises(ValueError):
            consolidar_janelas([(4, 2)], 0)


if __name__ == "__main__":
    unittest.main()
