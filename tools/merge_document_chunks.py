from __future__ import annotations

import argparse
import json
from pathlib import Path


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Merge chunked OCR JSON outputs for one document.")
    parser.add_argument("--chunks-dir", type=Path, required=True, help="Directory containing chunk subdirectories.")
    parser.add_argument("--document-name", type=str, required=True, help="Document stem, without .pdf.")
    parser.add_argument("--output-dir", type=Path, required=True, help="Final merged output directory.")
    return parser


def main() -> None:
    args = build_parser().parse_args()
    chunk_dirs = sorted(path for path in args.chunks_dir.iterdir() if path.is_dir())

    page_records: list[dict] = []
    full_text_parts: list[str] = []
    base_document: dict | None = None

    for chunk_dir in chunk_dirs:
        json_path = chunk_dir / f"{args.document_name}.json"
        txt_path = chunk_dir / f"{args.document_name}.txt"
        if not json_path.exists():
            continue
        payload = json.loads(json_path.read_text(encoding="utf-8"))
        if base_document is None:
            base_document = payload.copy()
            base_document["pages"] = []
        page_records.extend(payload.get("pages", []))
        if txt_path.exists():
            text = txt_path.read_text(encoding="utf-8").strip()
            if text:
                full_text_parts.append(text)

    if base_document is None:
        raise FileNotFoundError("No chunk JSON files were found for the requested document.")

    page_records.sort(key=lambda item: item["page_index"])
    base_document["pages"] = page_records
    base_document["full_text"] = "\n\n".join(full_text_parts)
    base_document["evaluation_text"] = None
    base_document["evaluation"] = None
    base_document["partial_run"] = False

    args.output_dir.mkdir(parents=True, exist_ok=True)
    (args.output_dir / f"{args.document_name}.json").write_text(
        json.dumps(base_document, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    (args.output_dir / f"{args.document_name}.txt").write_text(
        base_document["full_text"],
        encoding="utf-8",
    )
    (args.output_dir / "run_summary.json").write_text(
        json.dumps({"documents": [base_document]}, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    print(f"Merged {len(page_records)} pages for {args.document_name}.")


if __name__ == "__main__":
    main()
