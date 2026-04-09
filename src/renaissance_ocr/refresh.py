from __future__ import annotations

import argparse
import fnmatch
import json
from dataclasses import asdict
from pathlib import Path

from .cleanup import LanguageModelCleaner, heuristic_cleanup
from .dataset import extract_reference_for_pages, extract_reference_sections, read_ground_truth, write_json
from .evaluation import evaluate_prediction
from .reporting import write_report_artifacts


def refresh_outputs(
    output_dir: Path,
    use_cleanup_model: bool = False,
    cleanup_model_name: str = "google/flan-t5-base",
    document_glob: str | None = None,
) -> list[dict]:
    summary_path = output_dir / "run_summary.json"
    payload = json.loads(summary_path.read_text(encoding="utf-8"))
    documents = payload.get("documents")
    if not isinstance(documents, list):
        raise ValueError(f"{summary_path} does not contain a valid run summary.")

    cleaner = LanguageModelCleaner(cleanup_model_name) if use_cleanup_model else None
    project_root = output_dir.parent
    refreshed: list[dict] = []

    for document in documents:
        document_id = str(document.get("document_id", "unknown"))
        if document_glob and not fnmatch.fnmatch(document_id, document_glob):
            refreshed.append(document)
            continue

        full_text_parts: list[str] = []
        for page_output in document.get("pages", []):
            raw_text = str(page_output.get("raw_text", ""))
            cleanup_result = cleaner.clean(raw_text) if cleaner else heuristic_cleanup(raw_text)
            page_output["cleaned_text"] = cleanup_result.cleaned_text
            page_output["cleanup_strategy"] = cleanup_result.strategy
            if cleanup_result.cleaned_text:
                full_text_parts.append(cleanup_result.cleaned_text)

        full_text = "\n\n".join(full_text_parts)
        raw_reference = None
        reference = None
        evaluation_text = full_text
        ground_truth_path_str = document.get("ground_truth_path")
        if ground_truth_path_str:
            ground_truth_path = project_root / Path(str(ground_truth_path_str))
            raw_reference = read_ground_truth(ground_truth_path)
            reference_sections = extract_reference_sections(raw_reference)
            if reference_sections:
                matched_page_outputs = [
                    page_output
                    for page_output in document.get("pages", [])
                    if (int(page_output.get("page_index", 0)) + 1) in reference_sections
                ]
                matched_page_indexes = [int(page_output.get("page_index", 0)) for page_output in matched_page_outputs]
                reference = extract_reference_for_pages(raw_reference, matched_page_indexes)
                evaluation_text = "\n\n".join(
                    str(page_output.get("cleaned_text", ""))
                    for page_output in matched_page_outputs
                    if str(page_output.get("cleaned_text", ""))
                )
            else:
                reference = raw_reference

        evaluation = evaluate_prediction(reference, evaluation_text) if reference else None
        document["full_text"] = full_text
        document["reference_excerpt"] = reference
        document["evaluation_text"] = evaluation_text
        document["evaluation"] = asdict(evaluation) if evaluation else None

        write_json(output_dir / f"{document_id}.json", document)
        (output_dir / f"{document_id}.txt").write_text(full_text, encoding="utf-8")
        refreshed.append(document)

    write_json(summary_path, {"documents": refreshed})
    write_report_artifacts(summary_path)
    return refreshed


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Refresh cleaned OCR outputs from stored raw_text without rerunning OCR.")
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path(__file__).resolve().parents[2] / "outputs",
        help="Directory containing OCR JSON outputs and run_summary.json.",
    )
    parser.add_argument(
        "--use-cleanup-model",
        action="store_true",
        help="Use the configured language-model cleanup instead of the heuristic cleanup path.",
    )
    parser.add_argument(
        "--cleanup-model",
        type=str,
        default="google/flan-t5-base",
        help="Model name to use with --use-cleanup-model.",
    )
    parser.add_argument(
        "--document-glob",
        type=str,
        default=None,
        help="Refresh only matching documents, for example '*Buendia*'.",
    )
    return parser


def main() -> None:
    args = build_parser().parse_args()
    refreshed = refresh_outputs(
        output_dir=args.output_dir,
        use_cleanup_model=args.use_cleanup_model,
        cleanup_model_name=args.cleanup_model,
        document_glob=args.document_glob,
    )
    print(f"Refreshed {len(refreshed)} document(s) under {args.output_dir}.")


if __name__ == "__main__":
    main()
