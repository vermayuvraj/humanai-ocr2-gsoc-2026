# Submission Notes

## Current best OCR path

The strongest baseline currently implemented in this workspace is:

- OCR backend: `tesseract`
- Language pack: `spa_old`
- PSM: `6`

This outperformed the generic TrOCR checkpoints tested earlier on the HumanAI historical-print pages.

## Final print-set outputs

The completed print-document outputs are stored in `outputs/`:

- `Buendia - Instruccion`
- `Covarrubias - Tesoro lengua`
- `Guardiola - Tratado nobleza`
- `PORCONES.228.38 – 1646`
- `PORCONES.23.5 - 1628`
- `PORCONES.748.6 – 1650`

For each document there is:

- `<document>.txt`
- `<document>.json`

The consolidated print-set summary is:

- `outputs/run_summary.json`

## Why Covarrubias was chunked

`Covarrubias - Tesoro lengua.pdf` contains 990 pages, so it was processed in 50-page chunks to avoid long-run failures on the laptop. The chunk outputs were stored under `outputs_chunks/` and merged back into the final files in `outputs/`.

## Recommended explanation for the HumanAI test write-up

Use this framing:

- start with a transformer-based OCR baseline as an experimental reference
- explain that historical-print benchmarking on the provided sources showed better practical performance with `tesseract + spa_old`
- describe preprocessing, segmentation, and cleanup as the main quality levers
- position a future transformer/VLM stage as the next research step rather than pretending the generic transformer baseline already wins

## Honest current status

This is now a **submission-level working baseline**, not a finished research-quality OCR system. The strongest parts are:

- reproducible pipeline
- real outputs on the full print set
- chunk-safe handling for very large sources
- experiment history showing why the current backend was chosen

The next improvements with the highest payoff would be:

- stronger historical post-processing
- page-aware evaluation cleanup
- targeted transformer fine-tuning on RenAIssance-style material
