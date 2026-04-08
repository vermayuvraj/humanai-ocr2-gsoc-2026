from __future__ import annotations

import argparse
import csv
import json
from dataclasses import dataclass
from pathlib import Path
from statistics import mean

from .dataset import extract_reference_sections, read_ground_truth
from .evaluation import evaluate_prediction


@dataclass(slots=True)
class DocumentMetric:
    document_id: str
    page_count: int
    ocr_backend: str
    ocr_variant: str
    character_error_rate: float | None
    normalized_character_error_rate: float | None
    word_error_rate: float | None
    normalized_word_error_rate: float | None


@dataclass(slots=True)
class PageMetric:
    document_id: str
    page_index: int
    line_count: int
    cleanup_strategy: str
    character_error_rate: float
    normalized_character_error_rate: float
    word_error_rate: float
    normalized_word_error_rate: float
    cleaned_excerpt: str


def load_run_summary(path: Path) -> list[dict]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    documents = payload.get("documents")
    if not isinstance(documents, list):
        raise ValueError(f"{path} does not contain a valid run summary.")
    return documents


def build_document_metrics(documents: list[dict]) -> list[DocumentMetric]:
    metrics: list[DocumentMetric] = []
    for document in documents:
        evaluation = document.get("evaluation") or {}
        ocr_backend = document.get("ocr_backend") or "unknown"
        if ocr_backend == "tesseract":
            variant = f"{ocr_backend}:{document.get('tesseract_lang') or 'default'}"
        elif ocr_backend == "trocr":
            variant = document.get("ocr_model") or ocr_backend
        else:
            variant = ocr_backend
        metrics.append(
            DocumentMetric(
                document_id=document.get("document_id", "unknown"),
                page_count=len(document.get("pages", [])),
                ocr_backend=ocr_backend,
                ocr_variant=variant,
                character_error_rate=evaluation.get("character_error_rate"),
                normalized_character_error_rate=evaluation.get("normalized_character_error_rate"),
                word_error_rate=evaluation.get("word_error_rate"),
                normalized_word_error_rate=evaluation.get("normalized_word_error_rate"),
            )
        )
    return metrics


def build_page_metrics(documents: list[dict], project_root: Path) -> tuple[list[PageMetric], list[str]]:
    metrics: list[PageMetric] = []
    notes: list[str] = []
    for document in documents:
        ground_truth_path_str = document.get("ground_truth_path")
        if not ground_truth_path_str:
            notes.append(f"`{document.get('document_id', 'unknown')}` has no ground-truth path in the summary.")
            continue
        ground_truth_path = resolve_path(project_root, ground_truth_path_str)
        if not ground_truth_path.exists():
            notes.append(
                f"`{document.get('document_id', 'unknown')}` page-level evaluation was skipped because `{ground_truth_path}` was not found locally."
            )
            continue

        raw_reference = read_ground_truth(ground_truth_path)
        sections = extract_reference_sections(raw_reference)
        if not sections:
            notes.append(
                f"`{document.get('document_id', 'unknown')}` does not expose page markers in the available ground truth, so only document-level metrics are available."
            )
            continue

        for page_output in document.get("pages", []):
            page_number = int(page_output.get("page_index", 0)) + 1
            reference = sections.get(page_number)
            if not reference:
                continue
            cleaned_text = page_output.get("cleaned_text", "")
            evaluation = evaluate_prediction(reference, cleaned_text)
            if not evaluation:
                continue
            metrics.append(
                PageMetric(
                    document_id=document.get("document_id", "unknown"),
                    page_index=int(page_output.get("page_index", 0)),
                    line_count=int(page_output.get("line_count", 0)),
                    cleanup_strategy=str(page_output.get("cleanup_strategy", "unknown")),
                    character_error_rate=evaluation.character_error_rate,
                    normalized_character_error_rate=evaluation.normalized_character_error_rate,
                    word_error_rate=evaluation.word_error_rate,
                    normalized_word_error_rate=evaluation.normalized_word_error_rate,
                    cleaned_excerpt=build_excerpt(cleaned_text),
                )
            )
    return metrics, notes


def write_metrics_csv(metrics: list[DocumentMetric], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(
            [
                "document_id",
                "page_count",
                "ocr_backend",
                "ocr_variant",
                "character_error_rate",
                "normalized_character_error_rate",
                "word_error_rate",
                "normalized_word_error_rate",
            ]
        )
        for metric in metrics:
            writer.writerow(
                [
                    metric.document_id,
                    metric.page_count,
                    metric.ocr_backend,
                    metric.ocr_variant,
                    format_metric(metric.character_error_rate),
                    format_metric(metric.normalized_character_error_rate),
                    format_metric(metric.word_error_rate),
                    format_metric(metric.normalized_word_error_rate),
                ]
            )


def write_page_metrics_csv(metrics: list[PageMetric], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(
            [
                "document_id",
                "page_number",
                "line_count",
                "cleanup_strategy",
                "character_error_rate",
                "normalized_character_error_rate",
                "word_error_rate",
                "normalized_word_error_rate",
                "cleaned_excerpt",
            ]
        )
        for metric in metrics:
            writer.writerow(
                [
                    metric.document_id,
                    metric.page_index + 1,
                    metric.line_count,
                    metric.cleanup_strategy,
                    format_metric(metric.character_error_rate),
                    format_metric(metric.normalized_character_error_rate),
                    format_metric(metric.word_error_rate),
                    format_metric(metric.normalized_word_error_rate),
                    metric.cleaned_excerpt,
                ]
            )


def build_markdown_report(
    metrics: list[DocumentMetric],
    page_metrics: list[PageMetric],
    notes: list[str],
    summary_path: Path,
) -> str:
    evaluated = [metric for metric in metrics if metric.normalized_character_error_rate is not None]
    unevaluated = [metric for metric in metrics if metric.normalized_character_error_rate is None]
    total_pages = sum(metric.page_count for metric in metrics)

    lines = [
        "# OCR Run Report",
        "",
        f"Generated from `{summary_path.name}`.",
        "",
        "## Run Overview",
        "",
        f"- Documents processed: {len(metrics)}",
        f"- Total pages processed: {total_pages}",
        f"- Documents with aligned evaluation: {len(evaluated)}",
        f"- Documents without aligned evaluation: {len(unevaluated)}",
    ]

    if evaluated:
        avg_ncer = mean(metric.normalized_character_error_rate for metric in evaluated if metric.normalized_character_error_rate is not None)
        avg_nwer = mean(metric.normalized_word_error_rate for metric in evaluated if metric.normalized_word_error_rate is not None)
        best_metric = min(evaluated, key=lambda metric: metric.normalized_character_error_rate or float("inf"))
        worst_metric = max(evaluated, key=lambda metric: metric.normalized_character_error_rate or float("-inf"))
        lines.extend(
            [
                f"- Mean normalized CER: {format_metric(avg_ncer)}",
                f"- Mean normalized WER: {format_metric(avg_nwer)}",
                f"- Best normalized CER: `{best_metric.document_id}` at {format_metric(best_metric.normalized_character_error_rate)}",
                f"- Worst normalized CER: `{worst_metric.document_id}` at {format_metric(worst_metric.normalized_character_error_rate)}",
            ]
        )
    if page_metrics:
        best_page = min(page_metrics, key=lambda metric: metric.normalized_character_error_rate)
        worst_page = max(page_metrics, key=lambda metric: metric.normalized_character_error_rate)
        lines.extend(
            [
                f"- Evaluated pages with page markers: {len(page_metrics)}",
                f"- Best page NCER: `{best_page.document_id}` page {best_page.page_index + 1} at {format_metric(best_page.normalized_character_error_rate)}",
                f"- Worst page NCER: `{worst_page.document_id}` page {worst_page.page_index + 1} at {format_metric(worst_page.normalized_character_error_rate)}",
            ]
        )

    lines.extend(
        [
            "",
            "## Document Metrics",
            "",
            "| Document | Pages | Backend | Variant | CER | NCER | WER | NWER |",
            "| --- | ---: | --- | --- | ---: | ---: | ---: | ---: |",
        ]
    )

    for metric in sorted(
        metrics,
        key=lambda item: (
            item.normalized_character_error_rate is None,
            item.normalized_character_error_rate if item.normalized_character_error_rate is not None else float("inf"),
            item.document_id.lower(),
        ),
    ):
        lines.append(
            "| {document_id} | {page_count} | {ocr_backend} | {ocr_variant} | {cer} | {ncer} | {wer} | {nwer} |".format(
                document_id=metric.document_id,
                page_count=metric.page_count,
                ocr_backend=metric.ocr_backend,
                ocr_variant=metric.ocr_variant,
                cer=format_metric(metric.character_error_rate),
                ncer=format_metric(metric.normalized_character_error_rate),
                wer=format_metric(metric.word_error_rate),
                nwer=format_metric(metric.normalized_word_error_rate),
            )
        )

    if page_metrics:
        lines.extend(
            [
                "",
                "## Worst Evaluated Pages",
                "",
                "| Document | Page | Lines | Cleanup | NCER | NWER | OCR Excerpt |",
                "| --- | ---: | ---: | --- | ---: | ---: | --- |",
            ]
        )
        for metric in sorted(
            page_metrics,
            key=lambda item: (-item.normalized_character_error_rate, -item.normalized_word_error_rate, item.document_id.lower(), item.page_index),
        )[:10]:
            lines.append(
                "| {document_id} | {page_number} | {line_count} | {cleanup_strategy} | {ncer} | {nwer} | {excerpt} |".format(
                    document_id=metric.document_id,
                    page_number=metric.page_index + 1,
                    line_count=metric.line_count,
                    cleanup_strategy=metric.cleanup_strategy,
                    ncer=format_metric(metric.normalized_character_error_rate),
                    nwer=format_metric(metric.normalized_word_error_rate),
                    excerpt=escape_markdown_cell(metric.cleaned_excerpt),
                )
            )

    if unevaluated or notes:
        lines.extend(
            [
                "",
                "## Notes",
                "",
            ]
        )
    if unevaluated:
        lines.append("The following documents were processed but do not currently have aligned evaluation slices in the summary:")
        for metric in unevaluated:
            lines.append(f"- `{metric.document_id}`")
    for note in notes:
        lines.append(f"- {note}")

    lines.extend(
        [
            "",
            "## Next Steps",
            "",
            "- Improve layout handling and segmentation before comparing additional OCR backends.",
            "- Re-run the report after cleanup changes to track normalized CER and WER shifts over time.",
            "- Add document-specific post-processing rules for the worst-performing print sources.",
            "",
        ]
    )

    return "\n".join(lines)


def format_metric(value: float | None) -> str:
    if value is None:
        return "n/a"
    return f"{value:.4f}"


def write_report_artifacts(
    summary_path: Path,
    report_path: Path | None = None,
    csv_path: Path | None = None,
    page_csv_path: Path | None = None,
) -> tuple[Path, Path, Path | None]:
    documents = load_run_summary(summary_path)
    metrics = build_document_metrics(documents)
    project_root = summary_path.parent.parent
    page_metrics, notes = build_page_metrics(documents, project_root)
    report_path = report_path or summary_path.with_name("run_report.md")
    csv_path = csv_path or summary_path.with_name("run_metrics.csv")
    page_csv_path = page_csv_path or summary_path.with_name("page_metrics.csv")
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(build_markdown_report(metrics, page_metrics, notes, summary_path), encoding="utf-8")
    write_metrics_csv(metrics, csv_path)
    if page_metrics:
        write_page_metrics_csv(page_metrics, page_csv_path)
    return report_path, csv_path, page_csv_path if page_metrics else None


def resolve_path(project_root: Path, path_str: str) -> Path:
    path = Path(path_str)
    if path.is_absolute():
        return path
    return project_root / path


def build_excerpt(text: str, limit: int = 90) -> str:
    collapsed = " ".join(part.strip() for part in text.splitlines() if part.strip())
    if len(collapsed) <= limit:
        return collapsed
    return collapsed[: limit - 1].rstrip() + "…"


def escape_markdown_cell(text: str) -> str:
    return text.replace("|", "\\|")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Generate markdown and CSV reports from an OCR run summary.")
    parser.add_argument(
        "--summary-path",
        type=Path,
        required=True,
        help="Path to outputs/run_summary.json.",
    )
    parser.add_argument(
        "--report-path",
        type=Path,
        default=None,
        help="Optional path for the markdown report.",
    )
    parser.add_argument(
        "--csv-path",
        type=Path,
        default=None,
        help="Optional path for the CSV metrics export.",
    )
    parser.add_argument(
        "--page-csv-path",
        type=Path,
        default=None,
        help="Optional path for the page-level metrics export.",
    )
    return parser


def main() -> None:
    args = build_parser().parse_args()
    report_path, csv_path, page_csv_path = write_report_artifacts(
        summary_path=args.summary_path,
        report_path=args.report_path,
        csv_path=args.csv_path,
        page_csv_path=args.page_csv_path,
    )
    print(f"Wrote report to {report_path}")
    print(f"Wrote metrics CSV to {csv_path}")
    if page_csv_path:
        print(f"Wrote page metrics CSV to {page_csv_path}")


if __name__ == "__main__":
    main()
