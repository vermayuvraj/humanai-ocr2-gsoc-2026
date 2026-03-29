# HumanAI GSoC 2026 - RenAIssance OCR2 Baseline

This repository is a baseline submission workspace for the HumanAI project **"Text recognition with transformer models and LLM or Vision-Language Model integration"**.

It targets **Test I** from the RenAIssance screening PDF:

- printed early modern sources
- transformer-based OCR
- late-stage LLM cleanup
- explicit evaluation metrics

## What this baseline does

1. Renders input PDFs into page images with PyMuPDF.
2. Detects the largest main-text block on each page to ignore margins and embellishments.
3. Splits the detected region into text lines.
4. Runs OCR with either:
   - default: `tesseract` using `spa_old`
   - optional: `microsoft/trocr-base-printed`
5. Applies a late-stage cleanup step:
   - default: heuristic cleanup
   - optional: `google/flan-t5-base` correction pass
6. Computes evaluation metrics when ground-truth transcripts are available:
   - Word Error Rate (WER)
   - Character Error Rate (CER)
7. Saves per-document JSON and TXT outputs.

## Recommended folder layout

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

## Run

Baseline OCR with heuristic cleanup:

```powershell
$env:PYTHONPATH="src"
python -m renaissance_ocr.cli
```

The default backend is currently `tesseract` with `spa_old`, because it performed better than the generic TrOCR checkpoints on the HumanAI historical-print samples tested so far.

Quick smoke test on the first document and first page:

```powershell
$env:PYTHONPATH="src"
python -m renaissance_ocr.cli --max-documents 1 --max-pages 1
```

Inspect a later page and save debug images:

```powershell
$env:PYTHONPATH="src"
python -m renaissance_ocr.cli --max-documents 1 --start-page 2 --max-pages 1 --save-debug-images
```

Try a different OCR backbone:

```powershell
$env:PYTHONPATH="src"
python -m renaissance_ocr.cli --ocr-model microsoft/trocr-large-printed --max-documents 1 --start-page 2 --max-pages 1
```

Force TrOCR instead of the default Tesseract backend:

```powershell
$env:PYTHONPATH="src"
python -m renaissance_ocr.cli --ocr-backend trocr --ocr-model microsoft/trocr-base-printed --max-documents 1 --start-page 2 --max-pages 1
```

Enable the late-stage language-model cleanup:

```powershell
$env:PYTHONPATH="src"
python -m renaissance_ocr.cli --use-cleanup-model
```

## Output files

- `outputs/<document_id>.txt`: final cleaned transcription
- `outputs/<document_id>.json`: page-by-page OCR details and metrics
- `outputs/run_summary.json`: all processed documents

## How this matches HumanAI's test

The HumanAI screening instructions ask applicants for:

- a model using convolutional-recurrent, transformer, or self-supervised architectures
- a late-stage LLM or VLM integration step
- a discussion of evaluation metrics

This repository now supports two OCR paths:

- a **historical-print baseline** using **Tesseract + `spa_old`**
- a **transformer OCR baseline** using **TrOCR**

The late-stage cleanup step can then be applied on top of either OCR backend.

## What to improve before submission

- Replace the heuristic page-region detector with a stronger layout detector if the source pages are complex.
- Experiment with `microsoft/trocr-large-printed` and compare CER/WER.
- Add Spanish historical lexicon constraints for post-processing.
- Benchmark with and without the cleanup model.
- Write a short report explaining:
  - why you chose a transformer OCR baseline
  - why the cleanup stage is late-stage rather than end-to-end
  - how CER/WER changed after cleanup

## Experiment notes

- `transformers` is pinned to `<5` because the 5.x line caused unstable `trocr-large-printed` behavior in local testing on this machine.
- A quick comparison on `Buendia - Instruccion`, page 2, showed that `trocr-large-printed` was not better than `trocr-base-printed` with the current preprocessing.
- A direct benchmark on the same page showed that `tesseract -l spa_old --psm 6` outperformed the generic TrOCR checkpoints for this dataset.
- The next quality bottleneck is now dataset-specific cleanup and stronger post-processing, not basic package setup.

## Submission checklist

- Add HumanAI test PDFs to `data/raw/`
- Add corresponding ground-truth transcript files to `data/ground_truth/`
- Ground-truth transcripts may be stored as `.txt` or `.docx`
- Run the pipeline and collect outputs
- Push code to GitHub
- Email `human-ai@cern.ch` with:
  - subject containing `Evaluation Test: RenAIssance`
  - your CV
  - GitHub repo link
  - notebook or PDF output if you prepare one
