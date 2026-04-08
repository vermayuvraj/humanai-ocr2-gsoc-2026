# OCR Run Report

Generated from `run_summary.json`.

## Run Overview

- Documents processed: 6
- Total pages processed: 1395
- Documents with aligned evaluation: 5
- Documents without aligned evaluation: 1
- Mean normalized CER: 0.7789
- Mean normalized WER: 0.9027
- Best normalized CER: `Guardiola - Tratado nobleza` at 0.3020
- Worst normalized CER: `PORCONES.23.5 - 1628` at 0.9850

## Document Metrics

| Document | Pages | Backend | Variant | CER | NCER | WER | NWER |
| --- | ---: | --- | --- | ---: | ---: | ---: | ---: |
| Guardiola - Tratado nobleza | 311 | tesseract | tesseract:spa_old | 0.3325 | 0.3020 | 0.6959 | 0.6580 |
| PORCONES.748.6 – 1650 | 26 | tesseract | tesseract:spa_old | 0.8588 | 0.8387 | 0.9651 | 0.9530 |
| PORCONES.228.38 – 1646 | 23 | tesseract | tesseract:spa_old | 0.8908 | 0.8766 | 0.9734 | 0.9642 |
| Buendia - Instruccion | 33 | tesseract | tesseract:spa_old | 0.9025 | 0.8922 | 0.9466 | 0.9432 |
| PORCONES.23.5 - 1628 | 12 | tesseract | tesseract:spa_old | 0.9881 | 0.9850 | 0.9977 | 0.9952 |
| Covarrubias - Tesoro lengua | 990 | tesseract | tesseract:spa_old | n/a | n/a | n/a | n/a |

## Notes

The following documents were processed but do not currently have aligned evaluation slices in the summary:
- `Covarrubias - Tesoro lengua`

## Next Steps

- Improve layout handling and segmentation before comparing additional OCR backends.
- Re-run the report after cleanup changes to track normalized CER and WER shifts over time.
- Add document-specific post-processing rules for the worst-performing print sources.
