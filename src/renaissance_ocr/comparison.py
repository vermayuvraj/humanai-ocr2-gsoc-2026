from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path

from .reporting import DocumentMetric, build_document_metrics, format_metric, load_run_summary


@dataclass(slots=True)
class MetricDelta:
    document_id: str
    baseline_variant: str
    candidate_variant: str
    baseline_ncer: float | None
    candidate_ncer: float | None
    ncer_delta: float | None
    baseline_nwer: float | None
    candidate_nwer: float | None
    nwer_delta: float | None


def compare_run_summaries(baseline_path: Path, candidate_path: Path) -> list[MetricDelta]:
    baseline_metrics = index_metrics(build_document_metrics(load_run_summary(baseline_path)))
    candidate_metrics = index_metrics(build_document_metrics(load_run_summary(candidate_path)))

    deltas: list[MetricDelta] = []
    for document_id in sorted(set(baseline_metrics) | set(candidate_metrics)):
        baseline = baseline_metrics.get(document_id)
        candidate = candidate_metrics.get(document_id)
        deltas.append(
            MetricDelta(
                document_id=document_id,
                baseline_variant=baseline.ocr_variant if baseline else "n/a",
                candidate_variant=candidate.ocr_variant if candidate else "n/a",
                baseline_ncer=baseline.normalized_character_error_rate if baseline else None,
                candidate_ncer=candidate.normalized_character_error_rate if candidate else None,
                ncer_delta=compute_delta(
                    baseline.normalized_character_error_rate if baseline else None,
                    candidate.normalized_character_error_rate if candidate else None,
                ),
                baseline_nwer=baseline.normalized_word_error_rate if baseline else None,
                candidate_nwer=candidate.normalized_word_error_rate if candidate else None,
                nwer_delta=compute_delta(
                    baseline.normalized_word_error_rate if baseline else None,
                    candidate.normalized_word_error_rate if candidate else None,
                ),
            )
        )
    return deltas


def index_metrics(metrics: list[DocumentMetric]) -> dict[str, DocumentMetric]:
    return {metric.document_id: metric for metric in metrics}


def compute_delta(baseline: float | None, candidate: float | None) -> float | None:
    if baseline is None or candidate is None:
        return None
    return candidate - baseline


def build_comparison_report(deltas: list[MetricDelta], baseline_path: Path, candidate_path: Path) -> str:
    comparable = [delta for delta in deltas if delta.ncer_delta is not None]
    improved = [delta for delta in comparable if delta.ncer_delta is not None and delta.ncer_delta < 0]
    regressed = [delta for delta in comparable if delta.ncer_delta is not None and delta.ncer_delta > 0]

    lines = [
        "# OCR Run Comparison",
        "",
        f"- Baseline: `{baseline_path}`",
        f"- Candidate: `{candidate_path}`",
        f"- Comparable documents: {len(comparable)}",
        f"- Improved documents by NCER: {len(improved)}",
        f"- Regressed documents by NCER: {len(regressed)}",
        "",
        "## Document Deltas",
        "",
        "| Document | Baseline | Candidate | Baseline NCER | Candidate NCER | Delta NCER | Baseline NWER | Candidate NWER | Delta NWER |",
        "| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]

    for delta in sorted(
        deltas,
        key=lambda item: (
            item.ncer_delta is None,
            abs(item.ncer_delta) if item.ncer_delta is not None else -1,
        ),
        reverse=True,
    ):
        lines.append(
            "| {document_id} | {baseline_variant} | {candidate_variant} | {baseline_ncer} | {candidate_ncer} | {ncer_delta} | {baseline_nwer} | {candidate_nwer} | {nwer_delta} |".format(
                document_id=delta.document_id,
                baseline_variant=delta.baseline_variant,
                candidate_variant=delta.candidate_variant,
                baseline_ncer=format_metric(delta.baseline_ncer),
                candidate_ncer=format_metric(delta.candidate_ncer),
                ncer_delta=format_delta(delta.ncer_delta),
                baseline_nwer=format_metric(delta.baseline_nwer),
                candidate_nwer=format_metric(delta.candidate_nwer),
                nwer_delta=format_delta(delta.nwer_delta),
            )
        )

    return "\n".join(lines) + "\n"


def format_delta(value: float | None) -> str:
    if value is None:
        return "n/a"
    sign = "+" if value > 0 else ""
    return f"{sign}{value:.4f}"


def write_comparison_report(
    baseline_path: Path,
    candidate_path: Path,
    output_path: Path | None = None,
) -> Path:
    output_path = output_path or candidate_path.with_name("comparison_report.md")
    output_path.write_text(
        build_comparison_report(compare_run_summaries(baseline_path, candidate_path), baseline_path, candidate_path),
        encoding="utf-8",
    )
    return output_path


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Compare two OCR run summaries and generate a markdown diff report.")
    parser.add_argument("--baseline", type=Path, required=True, help="Path to the baseline run_summary.json file.")
    parser.add_argument("--candidate", type=Path, required=True, help="Path to the candidate run_summary.json file.")
    parser.add_argument("--output", type=Path, default=None, help="Optional path for the comparison markdown report.")
    return parser


def main() -> None:
    args = build_parser().parse_args()
    output_path = write_comparison_report(
        baseline_path=args.baseline,
        candidate_path=args.candidate,
        output_path=args.output,
    )
    print(f"Wrote comparison report to {output_path}")


if __name__ == "__main__":
    main()
