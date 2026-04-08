from __future__ import annotations

import argparse
import csv
import json
from dataclasses import dataclass
from pathlib import Path
from statistics import mean


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


def build_markdown_report(metrics: list[DocumentMetric], summary_path: Path) -> str:
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

    if unevaluated:
        lines.extend(
            [
                "",
                "## Notes",
                "",
                "The following documents were processed but do not currently have aligned evaluation slices in the summary:",
            ]
        )
        for metric in unevaluated:
            lines.append(f"- `{metric.document_id}`")

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


def write_report_artifacts(summary_path: Path, report_path: Path | None = None, csv_path: Path | None = None) -> tuple[Path, Path]:
    metrics = build_document_metrics(load_run_summary(summary_path))
    report_path = report_path or summary_path.with_name("run_report.md")
    csv_path = csv_path or summary_path.with_name("run_metrics.csv")
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(build_markdown_report(metrics, summary_path), encoding="utf-8")
    write_metrics_csv(metrics, csv_path)
    return report_path, csv_path


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
    return parser


def main() -> None:
    args = build_parser().parse_args()
    report_path, csv_path = write_report_artifacts(
        summary_path=args.summary_path,
        report_path=args.report_path,
        csv_path=args.csv_path,
    )
    print(f"Wrote report to {report_path}")
    print(f"Wrote metrics CSV to {csv_path}")


if __name__ == "__main__":
    main()
