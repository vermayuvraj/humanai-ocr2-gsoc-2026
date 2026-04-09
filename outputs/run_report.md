# OCR Run Report

Generated from `run_summary.json`.

## Run Overview

- Documents processed: 6
- Total pages processed: 1395
- Documents with aligned evaluation: 6
- Documents without aligned evaluation: 0
- Mean normalized CER: 0.6782
- Mean normalized WER: 0.8412
- Best normalized CER: `Covarrubias - Tesoro lengua` at 0.1749
- Worst normalized CER: `PORCONES.23.5 - 1628` at 0.9850
- Evaluated pages with page markers: 19
- Best page NCER: `Guardiola - Tratado nobleza` page 13 at 0.0801
- Worst page NCER: `PORCONES.23.5 - 1628` page 1 at 0.9850
- Low-signal evaluated pages: 4

## Document Metrics

| Document | Pages | Backend | Variant | CER | NCER | WER | NWER |
| --- | ---: | --- | --- | ---: | ---: | ---: | ---: |
| Covarrubias - Tesoro lengua | 990 | tesseract | tesseract:spa_old | 0.2045 | 0.1749 | 0.6042 | 0.5338 |
| Guardiola - Tratado nobleza | 311 | tesseract | tesseract:spa_old | 0.3325 | 0.3020 | 0.6959 | 0.6580 |
| PORCONES.748.6 – 1650 | 26 | tesseract | tesseract:spa_old | 0.8588 | 0.8387 | 0.9651 | 0.9530 |
| PORCONES.228.38 – 1646 | 23 | tesseract | tesseract:spa_old | 0.8908 | 0.8766 | 0.9734 | 0.9642 |
| Buendia - Instruccion | 33 | tesseract | tesseract:spa_old | 0.9025 | 0.8922 | 0.9466 | 0.9432 |
| PORCONES.23.5 - 1628 | 12 | tesseract | tesseract:spa_old | 0.9881 | 0.9850 | 0.9977 | 0.9952 |

## Worst Evaluated Pages

| Document | Page | Lines | Cleanup | NCER | NWER | OCR Excerpt |
| --- | ---: | ---: | --- | ---: | ---: | --- |
| PORCONES.23.5 - 1628 | 1 | 12 | heuristic | 0.9850 | 0.9952 | +: $ ooo E, E ' OA y (©) : L . Y} AA >». N \| \|: UA 2 GN “al ° E treo) ASA '} 23 6 LO Er \|… |
| PORCONES.228.38 – 1646 | 4 | 1 | heuristic | 0.9789 | 0.9862 | - ha de auerpor ſu legitima materna, |
| PORCONES.228.38 – 1646 | 5 | 1 | heuristic | 0.9770 | 0.9879 | r cuenta de ſu legirimasnooo.reales por |
| PORCONES.228.38 – 1646 | 3 | 1 | heuristic | 0.9753 | 0.9895 | \| capital,que auia llcuado al matrimonio |
| PORCONES.228.38 – 1646 | 2 | 2 | heuristic | 0.9740 | 0.9899 | Lajultarcon certeza, yciaridad © Y MES a VEO |
| Buendia - Instruccion | 3 | 4 | heuristic | 0.9267 | 0.9545 | curo difſeño Y: edad : la Religion para con Dios en la devora aſsiſtécia a los Templos;la… |
| Buendia - Instruccion | 4 | 3 | heuristic | 0.8903 | 0.9398 | ambos Drechos, Canonigo, y Sacriſtán] Dignidad de la Santa Igleſia de Gerona, y Vicario G… |
| PORCONES.748.6 – 1650 | 2 | 5 | heuristic | 0.8775 | 0.9457 | RR rg rar 5 a ai \| ETIDA nani in equentta: Querido mio portas fenas que me ha miſte ajerp… |
| PORCONES.748.6 – 1650 | 1 | 60 | heuristic | 0.8695 | 0.9942 | } j A d a y, E (7 á ) (4 es \|). ' ) SP, e / ¡Í, / 7 %, _ ”, ) d ho \| \| » \| ed \| Y) \| q L… |
| Buendia - Instruccion | 2 | 5 | heuristic | 0.8176 | 0.9184 | SAT ==] Vos, Dulciſsimo Niño SEAN, ] JEsus, que no ſolo 08 Exrſaj.zz: 5’ ==) \| dignaſteis… |

## Low-Signal Pages

| Document | Page | Lines | Text Length | Alpha Ratio | Noise Ratio | OCR Excerpt |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| PORCONES.748.6 – 1650 | 1 | 60 | 119 | 0.3782 | 0.2353 | } j A d a y, E (7 á ) (4 es \|). ' ) SP, e / ¡Í, / 7 %, _ ”, ) d ho \| \| » \| ed \| Y) \| q L… |
| PORCONES.23.5 - 1628 | 1 | 12 | 118 | 0.5932 | 0.1525 | +: $ ooo E, E ' OA y (©) : L . Y} AA >». N \| \|: UA 2 GN “al ° E treo) ASA '} 23 6 LO Er \|… |
| Buendia - Instruccion | 2 | 5 | 122 | 0.7459 | 0.0902 | SAT ==] Vos, Dulciſsimo Niño SEAN, ] JEsus, que no ſolo 08 Exrſaj.zz: 5’ ==) \| dignaſteis… |
| PORCONES.748.6 – 1650 | 4 | 6 | 213 | 0.7042 | 0.0610 | o ESPESO CIDO a CS _ Joannes T anger. de tortur.cab.3:num.76.Farinac.da : deliA.carjas, q… |

## Next Steps

- Improve layout handling and segmentation before comparing additional OCR backends.
- Re-run the report after cleanup changes to track normalized CER and WER shifts over time.
- Add document-specific post-processing rules for the worst-performing print sources.
