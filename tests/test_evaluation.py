from __future__ import annotations

import unittest

from renaissance_ocr.evaluation import evaluate_prediction, normalize_for_historical_ocr


class EvaluationTests(unittest.TestCase):
    def test_normalize_for_historical_ocr_collapses_spacing_and_long_s(self) -> None:
        text = "A\u017fsi   mi\u017fmo"
        self.assertEqual(normalize_for_historical_ocr(text), "assi mismo")

    def test_evaluate_prediction_returns_zero_for_exact_match(self) -> None:
        result = evaluate_prediction("texto igual", "texto igual")
        self.assertIsNotNone(result)
        assert result is not None
        self.assertEqual(result.character_error_rate, 0.0)
        self.assertEqual(result.word_error_rate, 0.0)
        self.assertEqual(result.normalized_character_error_rate, 0.0)
        self.assertEqual(result.normalized_word_error_rate, 0.0)


if __name__ == "__main__":
    unittest.main()
