from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass

from jiwer import cer, wer


@dataclass(slots=True)
class EvaluationResult:
    word_error_rate: float
    character_error_rate: float
    normalized_word_error_rate: float
    normalized_character_error_rate: float


def evaluate_prediction(reference: str | None, hypothesis: str) -> EvaluationResult | None:
    if not reference:
        return None
    normalized_reference = normalize_for_historical_ocr(reference)
    normalized_hypothesis = normalize_for_historical_ocr(hypothesis)
    return EvaluationResult(
        word_error_rate=wer(reference, hypothesis),
        character_error_rate=cer(reference, hypothesis),
        normalized_word_error_rate=wer(normalized_reference, normalized_hypothesis),
        normalized_character_error_rate=cer(normalized_reference, normalized_hypothesis),
    )


def normalize_for_historical_ocr(text: str) -> str:
    text = text.replace("ſ", "s")
    text = text.replace("ç", "z").replace("Ç", "Z")
    protected = text.replace("ñ", "__enye__").replace("Ñ", "__ENYE__")
    stripped = unicodedata.normalize("NFKD", protected)
    stripped = "".join(ch for ch in stripped if not unicodedata.combining(ch))
    stripped = stripped.replace("__enye__", "ñ").replace("__ENYE__", "Ñ")
    stripped = stripped.casefold()
    stripped = stripped.replace("-", "")
    stripped = re.sub(r"\s+", " ", stripped)
    return stripped.strip()
