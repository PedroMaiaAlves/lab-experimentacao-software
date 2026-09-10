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


CLEAN_CODE = """\
def soma(a, b):
    return a + b


def subtrai(a, b):
    return a - b
"""

DUPLICATED_CODE = """\
def calcula_a(x, y):
    total = x + y
    total = total * 2
    return total


def calcula_b(x, y):
    total = x + y
    total = total * 2
    return total
"""

COMPLEX_CODE = """\
def classifica(n):
    if n < 0:
        return "negativo"
    elif n == 0:
        return "zero"
    elif n < 10:
        return "pequeno"
    elif n < 100:
        return "medio"
    else:
        return "grande"
"""

INVALID_CODE = "def isso nao e python válido(:"


class MetricsCollectTest(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp_dir.cleanup)

    def _write(self, content: str, name: str = "source.py") -> str:
        path = Path(self.temp_dir.name) / name
        path.write_text(content, encoding="utf-8")
        return str(path)

    def test_collect_returns_all_expected_keys(self):
        path = self._write(CLEAN_CODE)
        result = metrics.collect(path)
        self.assertEqual(
            {"loc", "mean_complexity", "maintainability_index", "duplication_percent"},
            set(result.keys()),
        )

    def test_loc_ignores_blank_lines_and_comments(self):
        code = "# comentario\n\n\ndef f():\n    # outro comentario\n    return 1\n"
        path = self._write(code)
        result = metrics.collect(path)
        self.assertEqual(2, result["loc"])

    def test_empty_file_returns_zero_loc_and_none_for_the_rest(self):
        path = self._write("")
        result = metrics.collect(path)
        self.assertEqual(0, result["loc"])
        self.assertIsNone(result["maintainability_index"])
        self.assertIsNone(result["mean_complexity"])
        self.assertIsNone(result["duplication_percent"])

    def test_invalid_syntax_does_not_fabricate_zero(self):
        path = self._write(INVALID_CODE)
        result = metrics.collect(path)
        self.assertIsNone(result["loc"])
        self.assertIsNone(result["mean_complexity"])
        self.assertIsNone(result["maintainability_index"])

    def test_mean_complexity_reflects_branching(self):
        simple_path = self._write(CLEAN_CODE, "simples.py")
        complex_path = self._write(COMPLEX_CODE, "complexo.py")
        simple_result = metrics.collect(simple_path)
        complex_result = metrics.collect(complex_path)
        self.assertLess(
            simple_result["mean_complexity"], complex_result["mean_complexity"]
        )

    def test_maintainability_index_is_between_zero_and_hundred(self):
        path = self._write(CLEAN_CODE)
        result = metrics.collect(path)
        self.assertGreaterEqual(result["maintainability_index"], 0)
        self.assertLessEqual(result["maintainability_index"], 100)

    def test_duplication_percent_is_zero_without_repeated_blocks(self):
        path = self._write(CLEAN_CODE)
        result = metrics.collect(path)
        self.assertEqual(0.0, result["duplication_percent"])

    def test_duplication_percent_detects_repeated_block(self):
        path = self._write(DUPLICATED_CODE)
        result = metrics.collect(path)
        self.assertGreater(result["duplication_percent"], 0.0)

    def test_duplication_percent_is_none_below_minimum_block_size(self):
        path = self._write("x = 1\ny = 2\n")
        result = metrics.collect(path)
        self.assertIsNone(result["duplication_percent"])

    def test_collect_raises_for_missing_file(self):
        with self.assertRaises(FileNotFoundError):
            metrics.collect(str(Path(self.temp_dir.name) / "nao_existe.py"))


if __name__ == "__main__":
    unittest.main()
