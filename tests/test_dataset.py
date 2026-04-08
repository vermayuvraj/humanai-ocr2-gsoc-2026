from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from renaissance_ocr.dataset import (
    build_ground_truth_index,
    extract_reference_sections,
    normalize_stem,
)


class DatasetTests(unittest.TestCase):
    def test_normalize_stem_handles_transcription_suffix_and_dash_variants(self) -> None:
        self.assertEqual(
            normalize_stem("PORCONES.228.38 – 1646 transcription"),
            "porcones.228.38 - 1646",
        )

    def test_build_ground_truth_index_prefers_txt_over_docx(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            ground_truth_dir = Path(temp_dir)
            txt_path = ground_truth_dir / "Sample transcription.txt"
            docx_path = ground_truth_dir / "Sample transcription.docx"
            txt_path.write_text("plain text", encoding="utf-8")
            docx_path.write_text("not a real docx, but path discovery only uses the name", encoding="utf-8")

            index = build_ground_truth_index(ground_truth_dir)

            self.assertEqual(index["sample"], txt_path)

    def test_extract_reference_sections_reads_page_markers(self) -> None:
        reference = "PDF p1\nfirst page\nPDF p2\nsecond page"
        sections = extract_reference_sections(reference)
        self.assertEqual(sections, {1: "first page", 2: "second page"})


if __name__ == "__main__":
    unittest.main()
