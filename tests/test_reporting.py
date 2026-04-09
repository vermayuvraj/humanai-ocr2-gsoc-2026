from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from renaissance_ocr.reporting import write_report_artifacts


class ReportingTests(unittest.TestCase):
    def test_write_report_artifacts_generates_document_and_page_reports(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            project_root = Path(temp_dir)
            outputs_dir = project_root / "outputs"
            ground_truth_dir = project_root / "data" / "ground_truth"
            outputs_dir.mkdir(parents=True)
            ground_truth_dir.mkdir(parents=True)

            ground_truth_path = ground_truth_dir / "sample.txt"
            ground_truth_path.write_text(
                "PDF p1\nHola mundo\nPDF p2\nAdios mundo\n",
                encoding="utf-8",
            )

            summary_path = outputs_dir / "run_summary.json"
            summary_payload = {
                "documents": [
                    {
                        "document_id": "sample",
                        "ground_truth_path": "data/ground_truth/sample.txt",
                        "ocr_backend": "tesseract",
                        "tesseract_lang": "spa_old",
                        "pages": [
                            {
                                "page_index": 0,
                                "line_count": 1,
                                "cleaned_text": "Hola mundo",
                                "cleanup_strategy": "heuristic",
                            },
                            {
                                "page_index": 1,
                                "line_count": 1,
                                "cleaned_text": "Adios mund0",
                                "cleanup_strategy": "heuristic",
                            },
                        ],
                        "evaluation": {
                            "character_error_rate": 0.05,
                            "normalized_character_error_rate": 0.04,
                            "word_error_rate": 0.10,
                            "normalized_word_error_rate": 0.08,
                        },
                    }
                ]
            }
            summary_path.write_text(json.dumps(summary_payload), encoding="utf-8")

            report_path, csv_path, page_csv_path = write_report_artifacts(summary_path)

            self.assertTrue(report_path.exists())
            self.assertTrue(csv_path.exists())
            self.assertIsNotNone(page_csv_path)
            assert page_csv_path is not None
            self.assertTrue(page_csv_path.exists())

            report_text = report_path.read_text(encoding="utf-8")
            page_csv_text = page_csv_path.read_text(encoding="utf-8")

            self.assertIn("Worst Evaluated Pages", report_text)
            self.assertIn("Low-Signal Pages", report_text)
            self.assertIn("sample", report_text)
            self.assertIn("page_number", page_csv_text)
            self.assertIn("signal_band", page_csv_text)
            self.assertIn("Adios mund0", page_csv_text)


if __name__ == "__main__":
    unittest.main()
