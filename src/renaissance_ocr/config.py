from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(slots=True)
class PipelineConfig:
    raw_dir: Path
    ground_truth_dir: Path
    processed_dir: Path
    output_dir: Path
    trocr_model_name: str = "microsoft/trocr-base-printed"
    cleanup_model_name: str = "google/flan-t5-base"
    ocr_backend: str = "tesseract"
    tesseract_lang: str = "spa_old"
    tesseract_psm: int = 6
    render_dpi: int = 220
    min_line_height: int = 18
    use_cleanup_model: bool = False
    max_documents: int | None = None
    max_pages: int | None = None
    start_page: int = 0
    save_debug_images: bool = False
    document_glob: str | None = None
