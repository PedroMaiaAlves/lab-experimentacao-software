"""Testes da análise com dados temporários; nunca escrevem nos trials reais."""
import copy
import csv
import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from Lab02.tools import analyze_rq3 as rq3


class StatisticsTest(unittest.TestCase):
    def test_linear_quartiles(self):
        self.assertEqual(rq3.describe([1, 2, 3, 4, 5, 6]),
                         dict(n=6, median=3.5, q1=2.25, q3=4.75, iqr=2.5))

    def test_missing_is_not_zero(self):
        self.assertEqual(rq3.describe([None, 4])["median"], 4)
        self.assertIsNone(rq3.describe([None])["median"])
        self.assertEqual(rq3.describe([None])["n"], 0)

    def test_exact_all_positive_three_pairs(self):
        result = rq3.wilcoxon_two_sided([1, 2, 3])
        self.assertEqual(result["statistic"], 0)
        self.assertEqual(result["p_value"], .25)

    def test_balanced_ranks(self):
        result = rq3.wilcoxon_two_sided([-2, 11, -.5])
        self.assertEqual(result["statistic"], 3)
        self.assertEqual(result["p_value"], 1)

    def test_ties_receive_average_ranks(self):
        result = rq3.wilcoxon_two_sided([1, 1, -2])
        self.assertEqual(result["w_plus"], 3)
        self.assertEqual(result["w_minus"], 3)
        self.assertEqual(result["p_value"], 1)

    def test_zero_pairs_excluded(self):
        result = rq3.wilcoxon_two_sided([0, 1, 2])
        self.assertEqual(result["n_effective"], 2)
        self.assertEqual(result["p_value"], .5)

    def test_all_zero_has_no_fabricated_p(self):
        result = rq3.wilcoxon_two_sided([0, 0, 0])
        self.assertIsNone(result["p_value"])
        self.assertIsNone(result["statistic"])

    def test_unavailable_pairs(self):
        result = rq3.wilcoxon_two_sided([None, 0, 2])
        self.assertEqual(result["n_pairs"], 2)
        self.assertEqual(result["n_effective"], 1)

    def test_holm_family_and_monotonicity(self):
        self.assertEqual(rq3.holm(dict(a=.04, b=.03)), dict(a=.06, b=.06))
        self.assertEqual(rq3.holm(dict(a=.5, b=1)), dict(a=1, b=1))
        self.assertEqual(rq3.holm(dict(a=.03, b=None)), dict(a=.06, b=None))


class DataAndAuditTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.csv_path = Path(self.temp.name) / "trials.csv"
        self.protocol_path = Path(self.temp.name) / "protocol.json"
        self.protocol = json.loads((rq3.ROOT / "protocol.json").read_text(encoding="utf-8"))
        self.protocol_path.write_text(json.dumps(self.protocol), encoding="utf-8")
        self.rows = []
        for assignment in self.protocol["assignments"]:
            self.rows.append(dict(**assignment, commit_sha="1234567", issue_number=1,
                                 duration_seconds=20, time_to_green_seconds=20,
                                 censored="false", total_tests=8, passed_tests=8, failed_tests=0,
                                 success_rate=100, loc=10, mean_complexity=2,
                                 duplication_percent=0, maintainability_index=80))

    def save(self):
        with self.csv_path.open("w", encoding="utf-8", newline="") as stream:
            writer = csv.DictWriter(stream, fieldnames=list(self.rows[0]))
            writer.writeheader()
            writer.writerows(self.rows)

    def load(self):
        self.save()
        return rq3.read_trials(self.csv_path, self.protocol_path)

    def test_complete_data_and_leave_one_out(self):
        rows, protocol = self.load()
        analysis = rq3.analyze(rows, protocol)
        self.assertEqual(len(rows), 12)
        self.assertEqual(len(analysis["paired"]), 12)
        self.assertEqual(len(analysis["sensitivity"]), 3)
        for scenario in analysis["sensitivity"]:
            self.assertTrue(all(s["n"] == 4 for s in scenario["summaries"]))

    def test_duplicates_rejected(self):
        self.rows[-1] = self.rows[0].copy()
        with self.assertRaisesRegex(ValueError, "duplicada"):
            self.load()

    def test_missing_trial_rejected(self):
        self.rows.pop()
        with self.assertRaisesRegex(ValueError, "12 atribuições"):
            self.load()

    def test_treatment_mismatch_rejected(self):
        self.rows[0]["treatment"] = "manual"
        with self.assertRaisesRegex(ValueError, "Tratamento"):
            self.load()

    def test_missing_metric_preserved_and_pair_excluded(self):
        self.rows[0]["mean_complexity"] = ""
        rows, protocol = self.load()
        result = rq3.analyze(rows, protocol)
        self.assertIsNone(rows[0]["mean_complexity"])
        self.assertEqual(result["tests"]["mean_complexity"]["n_pairs"], 2)

    def test_nonfinite_metric_rejected(self):
        for value in ("nan", "inf", -1):
            with self.subTest(value=value):
                self.rows[0]["loc"] = value
                with self.assertRaises(ValueError):
                    self.load()

    def test_invalid_percent_rejected(self):
        self.rows[0]["duplication_percent"] = 120
        with self.assertRaisesRegex(ValueError, "escala"):
            self.load()

    def test_issue_zero_is_preserved(self):
        self.rows[0]["issue_number"] = 0
        self.assertEqual(self.load()[0][0]["issue_number"], 0)

    def test_censored_trial_not_discarded(self):
        self.rows[0].update(censored="true", duration_seconds=2100, time_to_green_seconds="",
                            passed_tests=4, failed_tests=4, success_rate=50)
        rows, protocol = self.load()
        self.assertEqual(len(rows), 12)
        self.assertEqual(sum(s["n"] for s in rq3.analyze(rows, protocol)["summary_by_treatment"]), 48)

    def test_read_and_analysis_do_not_modify_source(self):
        rows, protocol = self.load()
        before = self.csv_path.read_bytes()
        original = copy.deepcopy(rows)
        rq3.analyze(rows, protocol)
        self.assertEqual(rows, original)
        self.assertEqual(self.csv_path.read_bytes(), before)

    def test_outlier_retained(self):
        self.rows[0]["mean_complexity"] = 999
        rows, protocol = self.load()
        result = rq3.analyze(rows, protocol)
        self.assertTrue(any(r["value"] == 999 and r["retained"] for r in result["outliers"]))
        self.assertEqual(result["summary_by_treatment"][0]["n"], 6)

    def test_audit_reads_committed_source_without_execution(self):
        rows, _ = self.load()
        code = b'def dobro(numero):\n    return numero * 2\n'
        measured = dict(loc=2, mean_complexity=1, duplication_percent=None, maintainability_index=90)
        rows[0].update(measured)
        with patch.object(rq3, "git", side_effect=[b'a' * 40 + b'\n', code]), \
                patch('Lab02.tools.metrics.collect', return_value=measured):
            audit = rq3.audit_sources(rows[:1], Path(self.temp.name))
        self.assertEqual(audit[0]["status"], "ok")
        self.assertEqual(audit[0]["source_sha256"], hashlib.sha256(code).hexdigest())

    def test_audit_reports_missing_and_different_sources(self):
        rows, _ = self.load()
        with patch.object(rq3, "git", side_effect=ValueError('missing commit')):
            self.assertEqual(rq3.audit_sources(rows[:1], Path(self.temp.name))[0]["status"], "unavailable")
        with patch.object(rq3, "git", side_effect=[b'a' * 40, b'x = 1']), \
                patch('Lab02.tools.metrics.collect', return_value=dict(loc=1, mean_complexity=None, duplication_percent=None, maintainability_index=100)):
            self.assertEqual(rq3.audit_sources(rows[:1], Path(self.temp.name))[0]["status"], "divergent")


if __name__ == "__main__":
    unittest.main()
