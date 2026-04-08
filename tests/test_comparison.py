from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from renaissance_ocr.comparison import compare_run_summaries, write_comparison_report


def write_summary(path: Path, ncer: float, nwer: float, variant: str) -> None:
    payload = {
        "documents": [
            {
                "document_id": "sample",
                "ocr_backend": "tesseract",
                "tesseract_lang": variant,
                "pages": [{"page_index": 0, "line_count": 1}],
                "evaluation": {
                    "normalized_character_error_rate": ncer,
                    "normalized_word_error_rate": nwer,
                },
            }
        ]
    }
    path.write_text(json.dumps(payload), encoding="utf-8")


class ComparisonTests(unittest.TestCase):
    def test_compare_run_summaries_computes_metric_deltas(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            baseline = temp_path / "baseline.json"
            candidate = temp_path / "candidate.json"
            write_summary(baseline, ncer=0.40, nwer=0.60, variant="spa_old")
            write_summary(candidate, ncer=0.25, nwer=0.50, variant="spa")

            deltas = compare_run_summaries(baseline, candidate)

            self.assertEqual(len(deltas), 1)
            self.assertEqual(deltas[0].document_id, "sample")
            self.assertAlmostEqual(deltas[0].ncer_delta or 0.0, -0.15, places=4)
            self.assertAlmostEqual(deltas[0].nwer_delta or 0.0, -0.10, places=4)

    def test_write_comparison_report_creates_markdown_output(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            baseline = temp_path / "baseline.json"
            candidate = temp_path / "candidate.json"
            output = temp_path / "comparison.md"
            write_summary(baseline, ncer=0.40, nwer=0.60, variant="spa_old")
            write_summary(candidate, ncer=0.35, nwer=0.55, variant="spa_old")

            report_path = write_comparison_report(baseline, candidate, output)

            self.assertEqual(report_path, output)
            report_text = output.read_text(encoding="utf-8")
            self.assertIn("OCR Run Comparison", report_text)
            self.assertIn("sample", report_text)
            self.assertIn("-0.0500", report_text)


if __name__ == "__main__":
    unittest.main()
