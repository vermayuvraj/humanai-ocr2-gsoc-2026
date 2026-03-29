from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from zipfile import ZipFile


@dataclass(slots=True)
class DocumentSample:
    document_id: str
    pdf_path: Path
    ground_truth_path: Path | None


def discover_documents(
    raw_dir: Path, ground_truth_dir: Path, document_glob: str | None = None
) -> list[DocumentSample]:
    transcript_index = build_ground_truth_index(ground_truth_dir)
    samples: list[DocumentSample] = []
    pattern = document_glob or "*.pdf"
    for pdf_path in sorted(raw_dir.glob(pattern)):
        ground_truth_path = transcript_index.get(normalize_stem(pdf_path.stem))
        samples.append(
            DocumentSample(
                document_id=pdf_path.stem,
                pdf_path=pdf_path,
                ground_truth_path=ground_truth_path,
            )
        )
    return samples


def read_ground_truth(path: Path | None) -> str | None:
    if path is None:
        return None
    if path.suffix.lower() == ".docx":
        return read_docx_text(path)
    return path.read_text(encoding="utf-8").strip()


def read_docx_text(path: Path) -> str:
    with ZipFile(path) as archive:
        document_xml = archive.read("word/document.xml").decode("utf-8")
    text = re.sub(r"</w:p>", "\n", document_xml)
    text = re.sub(r"<[^>]+>", "", text)
    text = text.replace("&amp;", "&")
    text = text.replace("&lt;", "<")
    text = text.replace("&gt;", ">")
    return re.sub(r"\n{3,}", "\n\n", text).strip()


def build_ground_truth_index(ground_truth_dir: Path) -> dict[str, Path]:
    index: dict[str, Path] = {}
    for path in sorted(ground_truth_dir.iterdir()):
        if not path.is_file() or path.suffix.lower() not in {".txt", ".docx"}:
            continue
        normalized = normalize_stem(path.stem)
        existing = index.get(normalized)
        if existing is None or existing.suffix.lower() != ".txt":
            index[normalized] = path
    return index


def normalize_stem(stem: str) -> str:
    normalized = stem.casefold()
    normalized = normalized.replace("\u2013", "-").replace("\u2014", "-")
    normalized = re.sub(r"\s+transcription$", "", normalized)
    normalized = re.sub(r"[_\s]+", " ", normalized)
    return normalized.strip()


def write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")


def extract_reference_for_pages(reference_text: str | None, page_indexes: list[int]) -> str | None:
    if not reference_text or not page_indexes:
        return reference_text

    sections = extract_reference_sections(reference_text)
    if not sections:
        return None

    extracted = [sections.get(page_index + 1, "") for page_index in page_indexes]
    combined = "\n".join(part for part in extracted if part)
    return combined.strip() or None


def extract_reference_sections(reference_text: str | None) -> dict[int, str]:
    if not reference_text:
        return {}
    marker_pattern = re.compile(r"PDF p(\d+)\n", re.IGNORECASE)
    matches = list(marker_pattern.finditer(reference_text))
    if not matches:
        return {}

    sections: dict[int, str] = {}
    for index, match in enumerate(matches):
        page_number = int(match.group(1))
        start = match.end()
        end = matches[index + 1].start() if index + 1 < len(matches) else len(reference_text)
        sections[page_number] = reference_text[start:end].strip()
    return sections
