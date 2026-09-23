import copy
import sys
import unittest
from pathlib import Path


TOOLS_DIR = Path(__file__).resolve().parents[1] / "tools"
if str(TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(TOOLS_DIR))

import analyze_rq1_rq2 as analysis


class AnalyzeRQ1RQ2Test(unittest.TestCase):
    def test_wilcoxon_exato_unilateral(self):
        result = analysis.wilcoxon_greater([1, 2, 3])
        self.assertEqual({"n": 3, "w_plus": 6.0, "p_one_sided": 0.125}, result)

    def test_wilcoxon_com_empates_e_diferencas_zero(self):
        result = analysis.wilcoxon_greater([1, 1, -2, 0])
        self.assertEqual({"n": 3, "w_plus": 3.0, "p_one_sided": 0.625}, result)
        self.assertIsNone(analysis.wilcoxon_greater([0, 0, 0]))

    def test_dados_reais_geram_tres_pares_e_nao_inventam_p_para_rq2(self):
        rows, protocol = analysis.read_trials()
        result = analysis.analyze(rows, protocol)
        self.assertEqual(12, result["trials"])
        self.assertEqual(3, result["participants"])
        self.assertEqual(0.125, result["rq1"]["wilcoxon"]["p_one_sided"])
        self.assertIsNone(result["rq2"]["wilcoxon"])

    def test_censura_exige_outro_metodo_para_tempo(self):
        rows, protocol = analysis.read_trials()
        censored = copy.deepcopy(rows)
        censored[0]["censored"] = True
        with self.assertRaisesRegex(ValueError, "censurados"):
            analysis.analyze(censored, protocol)


if __name__ == "__main__":
    unittest.main()
