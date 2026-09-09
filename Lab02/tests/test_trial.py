from __future__ import annotations

import argparse
import csv
import copy
import json
import sys
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest import mock


LAB02_ROOT = Path(__file__).resolve().parents[1]
TOOLS_DIR = LAB02_ROOT / "tools"
if str(TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(TOOLS_DIR))

import trial  # noqa: E402


PROTOCOL_FIXTURE = {
    "timebox_seconds": 2100,
    "assistant": {
        "name": "ChatGPT",
        "plan": "Free",
        "model": "GPT-5.6 Luna",
        "model_verified_at": "2026-09-09",
    },
    "participants": [
        {"id": "pedro"},
        {"id": "diogo"},
        {"id": "lorran"},
    ],
    "katas": [
        {"id": "kata01", "expected_tests": 8},
        {"id": "kata02", "expected_tests": 8},
        {"id": "kata03", "expected_tests": 8},
        {"id": "kata04", "expected_tests": 8},
    ],
    "assignments": [
        {"participant": "pedro", "kata": "kata01", "treatment": "ia", "order": 1},
        {"participant": "pedro", "kata": "kata02", "treatment": "manual", "order": 2},
        {"participant": "pedro", "kata": "kata03", "treatment": "ia", "order": 3},
        {"participant": "pedro", "kata": "kata04", "treatment": "manual", "order": 4},
        {"participant": "diogo", "kata": "kata02", "treatment": "manual", "order": 1},
        {"participant": "diogo", "kata": "kata03", "treatment": "ia", "order": 2},
        {"participant": "diogo", "kata": "kata04", "treatment": "ia", "order": 3},
        {"participant": "diogo", "kata": "kata01", "treatment": "manual", "order": 4},
        {"participant": "lorran", "kata": "kata03", "treatment": "manual", "order": 1},
        {"participant": "lorran", "kata": "kata04", "treatment": "ia", "order": 2},
        {"participant": "lorran", "kata": "kata01", "treatment": "manual", "order": 3},
        {"participant": "lorran", "kata": "kata02", "treatment": "ia", "order": 4},
    ],
}

KATA_STUB = """\
def consolidar_janelas(janelas, tolerancia=0):
    raise NotImplementedError
"""

KATA_ACCEPTANCE = """\
import unittest
from solution import consolidar_janelas

class AcceptanceTest(unittest.TestCase):
    def test_01(self): self.assertEqual([], consolidar_janelas([]))
    def test_02(self): self.assertEqual([(1, 2)], consolidar_janelas([(1, 2)]))
    def test_03(self): self.assertEqual([(1, 4)], consolidar_janelas([(1, 3), (3, 4)]))
    def test_04(self): self.assertEqual([(1, 7)], consolidar_janelas([(1, 5), (3, 7)]))
    def test_05(self): self.assertEqual([(1, 6)], consolidar_janelas([(1, 2), (4, 6)], 2))
    def test_06(self): self.assertEqual([(5, 5)], consolidar_janelas([(5, 5)]))
    def test_07(self):
        with self.assertRaises(ValueError): consolidar_janelas([], -1)
    def test_08(self):
        with self.assertRaises(ValueError): consolidar_janelas([(4, 2)])
"""


class TrialToolTest(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        self.protocol_path = self.root / "protocol.json"
        self.csv_path = self.root / "results" / "trials.csv"
        self.state_dir = self.root / "results" / ".state"
        self.protocol = copy.deepcopy(PROTOCOL_FIXTURE)
        self.protocol_path.write_text(
            json.dumps(self.protocol, ensure_ascii=False), encoding="utf-8"
        )
        self._globals = mock.patch.multiple(
            trial,
            ROOT=self.root,
            PROTOCOL_PATH=self.protocol_path,
            STATE_DIR=self.state_dir,
            CSV_PATH=self.csv_path,
        )
        self._globals.start()
        self.addCleanup(self._globals.stop)
        self.addCleanup(self.temporary.cleanup)
        self._create_kata01()

    def _create_kata01(self):
        target = self.root / "katas" / "kata01"
        target.mkdir(parents=True)
        (target / "README.md").write_text("# Kata de teste", encoding="utf-8")
        (target / "stub.py").write_text(KATA_STUB, encoding="utf-8")
        (target / "acceptance.py").write_text(KATA_ACCEPTANCE, encoding="utf-8")

    def _start(self, participant="pedro", kata="kata01", issue=101):
        trial.start(
            argparse.Namespace(
                participant=participant,
                kata=kata,
                issue=issue,
                force=False,
            )
        )

    def _state_time(self, participant="pedro", kata="kata01"):
        state = self.state_dir / f"{participant}-{kata}.json"
        return datetime.fromisoformat(json.loads(state.read_text())["started_at"])

    def test_protocol_has_balanced_unique_assignments(self):
        self.assertEqual([], trial._protocol_errors(self.protocol))

    def test_assignment_rejects_unknown_combination(self):
        with self.assertRaisesRegex(SystemExit, "Combinação não prevista"):
            trial.assignment(self.protocol, "desconhecido", "kata01")

    def test_start_creates_isolated_solution_and_prevents_second_active_trial(self):
        self._start()
        solution = self.root / "trials" / "pedro" / "kata01" / "solution.py"
        self.assertTrue(solution.exists())
        self.assertEqual(
            (self.root / "katas" / "kata01" / "stub.py").read_text(),
            solution.read_text(),
        )

        with self.assertRaisesRegex(SystemExit, "já possui um trial"):
            self._start(kata="kata03")

    def test_ia_requires_model_verification(self):
        self.protocol["assistant"]["model_verified_at"] = None
        self.protocol_path.write_text(json.dumps(self.protocol), encoding="utf-8")
        with self.assertRaisesRegex(SystemExit, "model_verified_at"):
            self._start()

    def test_stub_fails_all_eight_acceptance_tests(self):
        result = trial.run_tests(
            self.root / "katas" / "kata01" / "stub.py",
            self.root / "katas" / "kata01" / "acceptance.py",
        )
        self.assertEqual(8, result["total"])
        self.assertEqual(0, result["passed"])
        self.assertFalse(result["green"])

    def test_valid_temporary_solution_passes_all_tests(self):
        solution = self.root / "solution.py"
        solution.write_text(
            """
def consolidar_janelas(janelas, tolerancia=0):
    if tolerancia < 0:
        raise ValueError('tolerancia invalida')
    ordenadas = sorted(janelas)
    if any(inicio > fim for inicio, fim in ordenadas):
        raise ValueError('janela invalida')
    resultado = []
    for inicio, fim in ordenadas:
        if not resultado or inicio - resultado[-1][1] > tolerancia:
            resultado.append((inicio, fim))
        else:
            resultado[-1] = (resultado[-1][0], max(resultado[-1][1], fim))
    return resultado
""".strip(),
            encoding="utf-8",
        )
        result = trial.run_tests(
            solution, self.root / "katas" / "kata01" / "acceptance.py"
        )
        self.assertTrue(result["green"], result["output"])
        self.assertEqual(8, result["passed"])

    def test_red_trial_cannot_finish_before_timebox(self):
        started = datetime(2026, 9, 9, 12, 0, tzinfo=timezone.utc)
        with mock.patch.object(trial, "utc_now", return_value=started):
            self._start()
        args = argparse.Namespace(participant="pedro", kata="kata01", prompts=1)
        with mock.patch.object(trial, "utc_now", return_value=started + timedelta(minutes=5)):
            with self.assertRaisesRegex(SystemExit, "Trial ainda vermelho"):
                trial.conclude(args, explicit_finish=True)
        self.assertFalse(self.csv_path.exists())

    def test_red_trial_is_censored_at_timebox_and_kept(self):
        started = datetime(2026, 9, 9, 12, 0, tzinfo=timezone.utc)
        with mock.patch.object(trial, "utc_now", return_value=started):
            self._start()
        args = argparse.Namespace(participant="pedro", kata="kata01", prompts=2)
        with mock.patch.object(trial, "utc_now", return_value=started + timedelta(minutes=36)):
            trial.conclude(args, explicit_finish=True)

        row = trial.read_results()[0]
        self.assertEqual("2100", row["duration_seconds"])
        self.assertEqual("true", row["censored"])
        self.assertEqual("", row["time_to_green_seconds"])
        self.assertEqual("PENDING", row["commit_sha"])

    def test_green_trial_records_time_without_metrics_fabrication(self):
        started = datetime(2026, 9, 9, 12, 0, tzinfo=timezone.utc)
        with mock.patch.object(trial, "utc_now", return_value=started):
            self._start()
        solution = self.root / "trials" / "pedro" / "kata01" / "solution.py"
        solution.write_text(
            """
def consolidar_janelas(janelas, tolerancia=0):
    if tolerancia < 0:
        raise ValueError
    ordenadas = sorted(janelas)
    if any(a > b for a, b in ordenadas):
        raise ValueError
    saida = []
    for inicio, fim in ordenadas:
        if not saida or inicio - saida[-1][1] > tolerancia:
            saida.append((inicio, fim))
        else:
            saida[-1] = (saida[-1][0], max(saida[-1][1], fim))
    return saida
""".strip(),
            encoding="utf-8",
        )
        args = argparse.Namespace(participant="pedro", kata="kata01", prompts=3)
        with mock.patch.object(trial, "utc_now", return_value=started + timedelta(seconds=75)):
            trial.conclude(args, explicit_finish=False)

        row = trial.read_results()[0]
        self.assertEqual("75.0", row["duration_seconds"])
        self.assertEqual("false", row["censored"])
        self.assertEqual("100.0", row["success_rate"])
        self.assertEqual("", row["loc"])
        self.assertEqual("GPT-5.6 Luna", row["assistant_model"])

    def test_negative_prompt_count_is_rejected(self):
        args = argparse.Namespace(participant="pedro", kata="kata01", prompts=-1)
        with self.assertRaisesRegex(SystemExit, "não pode ser negativa"):
            trial.conclude(args, explicit_finish=True)

    def test_duplicate_result_is_rejected(self):
        row = {field: "" for field in trial.RESULT_FIELDS}
        row.update({"participant": "pedro", "kata": "kata01"})
        trial.append_result(row)
        with self.assertRaisesRegex(SystemExit, "já registrado"):
            trial.append_result(row)

    def test_link_commit_updates_only_matching_result(self):
        row = {field: "" for field in trial.RESULT_FIELDS}
        row.update(
            {"participant": "pedro", "kata": "kata01", "commit_sha": "PENDING"}
        )
        trial.append_result(row)
        args = argparse.Namespace(
            participant="pedro", kata="kata01", commit="HEAD", force=False
        )
        with mock.patch.object(trial, "git_sha", return_value="abc1234"):
            trial.link_commit(args)
        self.assertEqual("abc1234", trial.read_results()[0]["commit_sha"])

    def test_csv_header_matches_documented_contract(self):
        trial._ensure_csv()
        with self.csv_path.open(encoding="utf-8", newline="") as handle:
            header = next(csv.reader(handle))
        self.assertEqual(trial.RESULT_FIELDS, header)


if __name__ == "__main__":
    unittest.main()
