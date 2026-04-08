# RenAIssance OCR Baseline

This repository contains my OCR baseline work for the HumanAI GSoC 2026 RenAIssance project on seventeenth-century Spanish printed sources.

The current codebase focuses on three practical goals:

1. building a reproducible OCR pipeline for difficult historical print
2. benchmarking different OCR backends on the same material
3. keeping the workflow usable on large source volumes

At the moment, the strongest baseline in this repository is a historical OCR path using `tesseract` with `spa_old`, supported by document preprocessing, line segmentation, cleanup, and structured output generation.

## Repository contents

- `src/renaissance_ocr/`: OCR pipeline code
- `outputs/`: generated OCR outputs for the processed print set
- `tools/`: helper scripts, including chunk merging for long volumes
- `EXPERIMENTS.md`: short notes on the main OCR comparisons run during development

## Local data layout

The source PDFs and transcript files used during development are not included in the public repository. If you want to rerun the pipeline locally, use the following structure:

```text
data/
  raw/
    source_01.pdf
  ground_truth/
    source_01.txt
    source_02.docx
outputs/
src/
  renaissance_ocr/
```

Ground-truth files can be either `.txt` or `.docx`. If both exist for the same document stem, the loader prefers `.txt`.

## Setup

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

## Lightweight tests

```powershell
$env:PYTHONPATH="src"
python -m pip install -r requirements-test.txt
python -m unittest discover -s tests -p "test_*.py" -v
```

The repository also includes a small GitHub Actions workflow that runs these checks on pushes and pull requests.

## Running the pipeline

Default run:

```powershell
$env:PYTHONPATH="src"
python -m renaissance_ocr.cli
```

The default backend is currently `tesseract` with `spa_old`, because it performed better than the generic TrOCR checkpoints tested on these historical print sources.

Quick smoke test:

```powershell
$env:PYTHONPATH="src"
python -m renaissance_ocr.cli --max-documents 1 --max-pages 1
```

Save debug crops for inspection:

```powershell
$env:PYTHONPATH="src"
python -m renaissance_ocr.cli --max-documents 1 --start-page 2 --max-pages 1 --save-debug-images
```

Try a different OCR backbone:

```powershell
$env:PYTHONPATH="src"
python -m renaissance_ocr.cli --ocr-model microsoft/trocr-large-printed --max-documents 1 --start-page 2 --max-pages 1
```

Use the transformer baseline instead of the default Tesseract path:

```powershell
$env:PYTHONPATH="src"
python -m renaissance_ocr.cli --ocr-backend trocr --ocr-model microsoft/trocr-base-printed --max-documents 1 --start-page 2 --max-pages 1
```

Enable the late-stage language-model cleanup:

```powershell
$env:PYTHONPATH="src"
python -m renaissance_ocr.cli --use-cleanup-model
```

## Outputs

- `outputs/<document_id>.txt`: final cleaned transcription
- `outputs/<document_id>.json`: page-by-page OCR details and metrics
- `outputs/run_summary.json`: all processed documents
- `outputs/run_report.md`: markdown summary of the latest run
- `outputs/run_metrics.csv`: compact metrics table for document-level comparisons
- `outputs/page_metrics.csv`: page-level metrics for slices with aligned page markers in the local ground truth

Regenerate the report from an existing run summary:

```powershell
$env:PYTHONPATH="src"
python -m renaissance_ocr.reporting --summary-path outputs/run_summary.json
```

## Current OCR paths

This repository currently supports two OCR paths:

- a **historical-print baseline** using **Tesseract + `spa_old`**
- a **transformer OCR baseline** using **TrOCR**

The cleanup step can be applied on top of either backend.

## Current limitations

- Replace the heuristic page-region detector with a stronger layout detector if the source pages are complex.
- Experiment with `microsoft/trocr-large-printed` and compare CER/WER.
- Add Spanish historical lexicon constraints for post-processing.
- Benchmark with and without the cleanup model.

## Experiment notes

- `transformers` is pinned to `<5` because the 5.x line caused unstable `trocr-large-printed` behavior in local testing on this machine.
- A quick comparison on `Buendia - Instruccion`, page 2, showed that `trocr-large-printed` was not better than `trocr-base-printed` with the current preprocessing.
- A direct benchmark on the same page showed that `tesseract -l spa_old --psm 6` outperformed the generic TrOCR checkpoints for this dataset.
- The next quality bottleneck is now dataset-specific cleanup and stronger post-processing, not basic package setup.
