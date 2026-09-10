"""Validações adicionais do pacote experimental do LAB02.

Este módulo complementa (sem substituir) as validações já existentes em
``tools/trial.py`` — protocolo, censura e esquema do CSV. Aqui verificamos:

1. que ``requirements.txt`` existe e declara as dependências usadas por
   ``tools/metrics.py`` (Radon);
2. que ``tools/metrics.py`` expõe a interface ``collect(path)`` com o
   contrato de retorno esperado (chaves obrigatórias, sem fabricar zero
   para métricas não calculáveis).

Nenhuma verificação de protocolo, censura ou CSV é removida ou substituída
por este arquivo.
"""

from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

LAB02_ROOT = Path(__file__).resolve().parents[1]
TOOLS_DIR = LAB02_ROOT / "tools"
if str(TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(TOOLS_DIR))

import metrics  # noqa: E402


EXPECTED_METRIC_KEYS = {
    "loc",
    "mean_complexity",
    "maintainability_index",
    "duplication_percent",
}


class RequirementsValidationTest(unittest.TestCase):
    def test_requirements_file_exists(self):
        requirements_path = LAB02_ROOT / "requirements.txt"
        self.assertTrue(
            requirements_path.exists(),
            "Lab02/requirements.txt não encontrado",
        )

    def test_requirements_declares_radon(self):
        requirements_path = LAB02_ROOT / "requirements.txt"
        content = requirements_path.read_text(encoding="utf-8").lower()
        self.assertIn(
            "radon",
            content,
            "requirements.txt deve declarar a dependência 'radon', usada em metrics.py",
        )


class MetricsContractValidationTest(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp_dir.cleanup)

    def _write(self, content: str) -> str:
        path = Path(self.temp_dir.name) / "solution.py"
        path.write_text(content, encoding="utf-8")
        return str(path)

    def test_collect_exposes_all_expected_keys(self):
        path = self._write("def f():\n    return 1\n")
        result = metrics.collect(path)
        self.assertEqual(EXPECTED_METRIC_KEYS, set(result.keys()))

    def test_collect_does_not_fabricate_zero_for_uncomputable_metrics(self):
        # Código sintaticamente inválido: nenhuma métrica derivada de AST
        # deve ser fabricada como zero.
        path = self._write("def f(:\n    isso nao compila\n")
        result = metrics.collect(path)
        for key in ("mean_complexity", "maintainability_index", "loc"):
            self.assertIsNone(
                result[key],
                f"'{key}' não deveria ser fabricado quando não pôde ser calculado",
            )

    def test_collect_raises_for_missing_file_instead_of_returning_defaults(self):
        missing_path = str(Path(self.temp_dir.name) / "nao_existe.py")
        with self.assertRaises(FileNotFoundError):
            metrics.collect(missing_path)


if __name__ == "__main__":
    unittest.main()
