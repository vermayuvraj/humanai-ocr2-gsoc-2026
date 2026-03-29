---
noteId: "3037f630293711f18604996533becafa"
tags: []

---

# Experiment Log

## 2026-03-26

### Environment

- Created Python venv and installed the OCR stack.
- Pinned `transformers` to `<5` after a `trocr-large-printed` failure under `5.3.0`.

### Dataset handling

- Added support for `.docx` ground-truth files.
- Added tolerant filename matching for:
  - trailing `transcription`
  - dash variants
  - capitalization differences

### Smoke tests

#### `microsoft/trocr-base-printed`

- Command:

```powershell
$env:PYTHONPATH="src"
python -m renaissance_ocr.cli --max-documents 1 --start-page 2 --max-pages 1 --save-debug-images
```

- Outcome:
  - pipeline completed
  - debug images saved
  - initial transcription quality was poor on historical print
  - after improving segmentation and line preprocessing, the page output became structurally much closer to the source

#### `microsoft/trocr-large-printed`

- Command:

```powershell
$env:PYTHONPATH="src"
python -m renaissance_ocr.cli --ocr-model microsoft/trocr-large-printed --max-documents 1 --start-page 2 --max-pages 1
```

- Outcome:
  - ran successfully under `transformers 4.57.6`
  - output was not better than the base model on the tested page

#### Higher render DPI

- Command:

```powershell
$env:PYTHONPATH="src"
python -m renaissance_ocr.cli --max-documents 1 --start-page 2 --max-pages 1 --render-dpi 300
```

- Outcome:
  - `300 DPI` performed worse than the default `220 DPI` on the same page
  - higher resolution amplified noise and reduced line stability

### Current conclusion

The best next improvement is not a larger generic TrOCR checkpoint or a higher DPI by itself. The strongest gains so far came from better page preprocessing and line segmentation. The next serious jump likely requires either:

- a historical-text-specific OCR backbone, or
- light fine-tuning on RenAIssance-style material, or
- stronger layout handling before OCR
