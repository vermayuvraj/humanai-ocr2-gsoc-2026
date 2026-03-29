from __future__ import annotations

import argparse
from pathlib import Path

from .pipeline import make_default_config, run_pipeline


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run the HumanAI RenAIssance OCR2 screening baseline."
    )
    parser.add_argument(
        "--project-root",
        type=Path,
        default=Path(__file__).resolve().parents[2],
        help="Root directory of the OCR2 project.",
    )
    parser.add_argument(
        "--use-cleanup-model",
        action="store_true",
        help="Enable the late-stage language-model cleanup step.",
    )
    parser.add_argument(
        "--ocr-backend",
        type=str,
        default=None,
        help="OCR backend to use: trocr or tesseract.",
    )
    parser.add_argument(
        "--ocr-model",
        type=str,
        default=None,
        help="Override the default OCR model name.",
    )
    parser.add_argument(
        "--tesseract-lang",
        type=str,
        default=None,
        help="Tesseract language pack to use, for example spa_old.",
    )
    parser.add_argument(
        "--tesseract-psm",
        type=int,
        default=None,
        help="Tesseract page segmentation mode.",
    )
    parser.add_argument(
        "--cleanup-model",
        type=str,
        default=None,
        help="Override the default cleanup model name.",
    )
    parser.add_argument(
        "--max-documents",
        type=int,
        default=None,
        help="Process only the first N documents for quick iteration.",
    )
    parser.add_argument(
        "--max-pages",
        type=int,
        default=None,
        help="Process only the first N pages per document for quick iteration.",
    )
    parser.add_argument(
        "--start-page",
        type=int,
        default=0,
        help="Skip the first N pages before processing.",
    )
    parser.add_argument(
        "--save-debug-images",
        action="store_true",
        help="Save rendered pages, cropped text regions, and line images under data/processed.",
    )
    parser.add_argument(
        "--render-dpi",
        type=int,
        default=None,
        help="Override the PDF rendering DPI.",
    )
    parser.add_argument(
        "--document-glob",
        type=str,
        default=None,
        help="Process only documents matching this glob, for example '*Buendia*.pdf'.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=None,
        help="Override the output directory.",
    )
    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    config = make_default_config(args.project_root, use_cleanup_model=args.use_cleanup_model)
    if args.ocr_backend:
        config.ocr_backend = args.ocr_backend
    if args.ocr_model:
        config.trocr_model_name = args.ocr_model
    if args.tesseract_lang:
        config.tesseract_lang = args.tesseract_lang
    if args.tesseract_psm is not None:
        config.tesseract_psm = args.tesseract_psm
    if args.cleanup_model:
        config.cleanup_model_name = args.cleanup_model
    config.max_documents = args.max_documents
    config.max_pages = args.max_pages
    config.start_page = args.start_page
    config.save_debug_images = args.save_debug_images
    config.document_glob = args.document_glob
    if args.render_dpi:
        config.render_dpi = args.render_dpi
    if args.output_dir:
        config.output_dir = args.output_dir
    results = run_pipeline(config)
    print(f"Processed {len(results)} document(s). Outputs saved to {config.output_dir}.")


if __name__ == "__main__":
    main()
