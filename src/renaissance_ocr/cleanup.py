from __future__ import annotations

import re
from dataclasses import dataclass

from transformers import pipeline


@dataclass(slots=True)
class CleanupResult:
    cleaned_text: str
    strategy: str


def heuristic_cleanup(text: str) -> CleanupResult:
    text = repair_mojibake(text)
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    rebuilt: list[str] = []
    index = 0
    while index < len(lines):
        current = lines[index]
        if current.endswith("-") and index + 1 < len(lines):
            current = current[:-1] + lines[index + 1].lstrip()
            index += 1
        rebuilt.append(current)
        index += 1

    cleaned = "\n".join(rebuilt)
    cleaned = re.sub(r"(?<=\b)IA(?=\b)", "LA", cleaned)
    cleaned = re.sub(r"([;:,])IA\b", r"\1 LA", cleaned)
    cleaned = cleaned.replace(" EN IA ", " EN LA ")
    cleaned = cleaned.replace(" CON IA ", " CON LA ")
    cleaned = cleaned.replace("RELI-TION", "RELI-GION")
    cleaned = cleaned.replace(" IA ", " LA ")
    cleaned = re.sub(r"[ \t]+", " ", cleaned).strip()
    cleaned = cleaned.replace(" ,", ",").replace(" .", ".").replace(" ;", ";")
    return CleanupResult(cleaned_text=cleaned, strategy="heuristic")


def repair_mojibake(text: str) -> str:
    if not likely_mojibake(text):
        return text
    try:
        repaired = text.encode("cp1252").decode("utf-8")
    except UnicodeError:
        return apply_common_replacements(text)
    if mojibake_score(repaired) < mojibake_score(text):
        return repaired
    return apply_common_replacements(text)


def likely_mojibake(text: str) -> bool:
    return any(marker in text for marker in ("Ã", "Å", "â", "Â"))


def mojibake_score(text: str) -> int:
    return sum(text.count(marker) for marker in ("Ã", "Å", "â", "Â"))


def apply_common_replacements(text: str) -> str:
    replacements = {
        "Å¿": "ſ",
        "Ã±": "ñ",
        "Ã‘": "Ñ",
        "Ã¡": "á",
        "Ã©": "é",
        "Ã­": "í",
        "Ã³": "ó",
        "Ãº": "ú",
        "Ã": "Á",
        "Ã‰": "É",
        "Ã": "Í",
        "Ã“": "Ó",
        "Ãš": "Ú",
        "Ã¼": "ü",
        "Ãœ": "Ü",
        "Ã§": "ç",
        "Ã‡": "Ç",
        "â€™": "’",
        "â€˜": "‘",
        "â€œ": "“",
        "â€": "”",
        "â€”": "—",
        "â€“": "–",
        "Â¡": "¡",
        "Â¿": "¿",
        "Âº": "º",
        "Âª": "ª",
    }
    repaired = text
    for source, target in replacements.items():
        repaired = repaired.replace(source, target)
    return repaired


class LanguageModelCleaner:
    def __init__(self, model_name: str) -> None:
        try:
            self.generator = pipeline(
                "text2text-generation",
                model=model_name,
                tokenizer=model_name,
                local_files_only=True,
            )
        except OSError:
            self.generator = pipeline(
                "text2text-generation",
                model=model_name,
                tokenizer=model_name,
            )
        self.model_name = model_name

    def clean(self, text: str) -> CleanupResult:
        prompt = (
            "You are correcting OCR output from seventeenth-century Spanish printed text. "
            "Fix obvious OCR mistakes, preserve historical spelling when possible, and do not "
            "invent content.\nOCR text:\n"
            f"{text}"
        )
        response = self.generator(
            prompt,
            max_new_tokens=180,
            do_sample=False,
        )[0]["generated_text"].strip()
        return CleanupResult(
            cleaned_text=response if response else text,
            strategy=f"llm:{self.model_name}",
        )
