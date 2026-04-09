from __future__ import annotations

import unittest

from renaissance_ocr.cleanup import heuristic_cleanup, repair_mojibake


class CleanupTests(unittest.TestCase):
    def test_repair_mojibake_restores_common_utf8_sequences(self) -> None:
        text = "DulciÅ¿simo NiÃ±o"
        self.assertEqual(repair_mojibake(text), "Dulciſsimo Niño")

    def test_heuristic_cleanup_repairs_mojibake_before_other_rules(self) -> None:
        result = heuristic_cleanup("Vos , DulciÅ¿simo NiÃ±o")
        self.assertEqual(result.cleaned_text, "Vos, Dulciſsimo Niño")


if __name__ == "__main__":
    unittest.main()
