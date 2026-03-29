from __future__ import annotations

from dataclasses import asdict
from pathlib import Path

from .cleanup import LanguageModelCleaner, heuristic_cleanup
from .config import PipelineConfig
from .dataset import (
    discover_documents,
    extract_reference_for_pages,
    extract_reference_sections,
    read_ground_truth,
    write_json,
)
from .evaluation import evaluate_prediction
from .ocr import build_ocr_engine
from .pdf_processing import detect_main_text_region, render_pdf, split_lines


def run_pipeline(config: PipelineConfig) -> list[dict]:
    documents = discover_documents(
        config.raw_dir,
        config.ground_truth_dir,
        document_glob=config.document_glob,
    )
    if not documents:
        raise FileNotFoundError(
            f"No PDF files found in {config.raw_dir}. Add the HumanAI test PDFs before running."
        )
    if config.max_documents is not None:
        documents = documents[: config.max_documents]

    ocr_engine = build_ocr_engine(
        backend=config.ocr_backend,
        model_name=config.trocr_model_name,
        language=config.tesseract_lang,
        psm=config.tesseract_psm,
    )
    cleaner = LanguageModelCleaner(config.cleanup_model_name) if config.use_cleanup_model else None

    run_summary: list[dict] = []
    for document in documents:
        pages = render_pdf(document.pdf_path, dpi=config.render_dpi)
        if config.start_page:
            pages = pages[config.start_page :]
        if config.max_pages is not None:
            pages = pages[: config.max_pages]
        page_outputs: list[dict] = []
        full_text_parts: list[str] = []

        for page_index, page in enumerate(pages):
            actual_page_index = page_index + config.start_page
            text_region = detect_main_text_region(page)
            if config.save_debug_images:
                debug_dir = config.processed_dir / document.document_id / f"page_{actual_page_index:03d}"
                debug_dir.mkdir(parents=True, exist_ok=True)
                page.save(debug_dir / "full_page.png")
                text_region.save(debug_dir / "text_region.png")
            line_images = split_lines(text_region, min_line_height=config.min_line_height)
            if config.save_debug_images:
                for line_number, line_image in enumerate(line_images):
                    line_image.save(debug_dir / f"line_{line_number:03d}.png")
            line_predictions = ocr_engine.predict_region(text_region, line_images)
            raw_text = "\n".join(prediction.raw_text for prediction in line_predictions if prediction.raw_text)

            cleanup_result = cleaner.clean(raw_text) if cleaner else heuristic_cleanup(raw_text)
            full_text_parts.append(cleanup_result.cleaned_text)
            page_outputs.append(
                {
                    "page_index": actual_page_index,
                    "line_count": len(line_predictions),
                    "raw_text": raw_text,
                    "cleaned_text": cleanup_result.cleaned_text,
                    "cleanup_strategy": cleanup_result.strategy,
                }
            )

        full_text = "\n\n".join(part for part in full_text_parts if part)
        processed_page_indexes = [page_output["page_index"] for page_output in page_outputs]
        raw_reference = read_ground_truth(document.ground_truth_path)
        reference_sections = extract_reference_sections(raw_reference)
        if reference_sections:
            matched_page_outputs = [
                page_output
                for page_output in page_outputs
                if (page_output["page_index"] + 1) in reference_sections
            ]
            matched_page_indexes = [page_output["page_index"] for page_output in matched_page_outputs]
            reference = extract_reference_for_pages(raw_reference, matched_page_indexes)
            evaluation_text = "\n\n".join(
                page_output["cleaned_text"] for page_output in matched_page_outputs if page_output["cleaned_text"]
            )
        else:
            reference = raw_reference
            evaluation_text = full_text
        partial_run = bool(config.start_page or config.max_pages is not None)
        evaluation = evaluate_prediction(reference, evaluation_text) if reference else None

        result = {
            "document_id": document.document_id,
            "pdf_path": str(document.pdf_path),
            "ground_truth_path": str(document.ground_truth_path) if document.ground_truth_path else None,
            "ocr_backend": config.ocr_backend,
            "ocr_model": config.trocr_model_name if config.ocr_backend == "trocr" else None,
            "tesseract_lang": config.tesseract_lang if config.ocr_backend == "tesseract" else None,
            "tesseract_psm": config.tesseract_psm if config.ocr_backend == "tesseract" else None,
            "partial_run": partial_run,
            "reference_excerpt": reference,
            "pages": page_outputs,
            "full_text": full_text,
            "evaluation_text": evaluation_text,
            "evaluation": asdict(evaluation) if evaluation else None,
        }
        run_summary.append(result)

        write_json(config.output_dir / f"{document.document_id}.json", result)
        (config.output_dir / f"{document.document_id}.txt").write_text(
            full_text, encoding="utf-8"
        )

    write_json(config.output_dir / "run_summary.json", {"documents": run_summary})
    return run_summary


def make_default_config(project_root: Path, use_cleanup_model: bool) -> PipelineConfig:
    return PipelineConfig(
        raw_dir=project_root / "data" / "raw",
        ground_truth_dir=project_root / "data" / "ground_truth",
        processed_dir=project_root / "data" / "processed",
        output_dir=project_root / "outputs",
        use_cleanup_model=use_cleanup_model,
    )
