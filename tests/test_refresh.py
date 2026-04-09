from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from renaissance_ocr.refresh import refresh_outputs


class RefreshTests(unittest.TestCase):
    def test_refresh_outputs_updates_cleaned_text_and_summary(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            project_root = Path(temp_dir)
            outputs_dir = project_root / "outputs"
            ground_truth_dir = project_root / "data" / "ground_truth"
            outputs_dir.mkdir(parents=True)
            ground_truth_dir.mkdir(parents=True)

            (ground_truth_dir / "sample.txt").write_text("PDF p1\nDulciſsimo Niño\n", encoding="utf-8")
            summary_payload = {
                "documents": [
                    {
                        "document_id": "sample",
                        "ground_truth_path": "data/ground_truth/sample.txt",
                        "pages": [
                            {
                                "page_index": 0,
                                "raw_text": "DulciÅ¿simo NiÃ±o",
                                "cleaned_text": "stale",
                                "cleanup_strategy": "heuristic",
                                "line_count": 1,
                            }
                        ],
                        "evaluation": None,
                    }
                ]
            }
            (outputs_dir / "run_summary.json").write_text(json.dumps(summary_payload), encoding="utf-8")

            refreshed = refresh_outputs(outputs_dir)

            self.assertEqual(len(refreshed), 1)
            self.assertEqual(refreshed[0]["pages"][0]["cleaned_text"], "Dulciſsimo Niño")
            self.assertTrue((outputs_dir / "sample.txt").exists())
            self.assertTrue((outputs_dir / "run_report.md").exists())


if __name__ == "__main__":
    unittest.main()
