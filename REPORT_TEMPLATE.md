# RenAIssance OCR2 Test Report

## 1. Project goal

This submission targets the HumanAI GSoC 2026 project **"Text recognition with transformer models and LLM or Vision-Language Model integration"**. The objective is to build a printed-text OCR pipeline for early modern Spanish sources and improve transcription quality with a late-stage language-model cleanup step.

## 2. Dataset choice

- Dataset used:
- Number of PDF sources:
- Number of pages processed:
- Ground-truth transcripts available for:

## 3. Pipeline overview

### 3.1 Page rendering and preprocessing

- PDF rendering method:
- Resolution:
- Main-text detection strategy:
- Line segmentation strategy:

### 3.2 OCR model

- Model:
- Why this model:
- Inference setup:

### 3.3 Late-stage LLM or VLM integration

- Model:
- Why late-stage integration was chosen:
- Prompting or correction strategy:

## 4. Evaluation metrics

The HumanAI task asks applicants to discuss evaluation metrics. I report:

- **Character Error Rate (CER)**: useful for OCR because even small character mistakes matter.
- **Word Error Rate (WER)**: useful for estimating readability and downstream usability.

## 5. Results

| Document | CER | WER | Notes |
| --- | --- | --- | --- |
| source_01 |  |  |  |
| source_02 |  |  |  |

## 6. Error analysis

- Common OCR failures:
- Historical spelling challenges:
- Layout or ornament issues:
- What improved after cleanup:

## 7. Next improvements

- Stronger layout detection for non-standard pages
- Compare more OCR backbones
- Fine-tune on project-specific scanned material
- Add historical Spanish lexicon constraints
- Evaluate VLM-based cleanup

## 8. Conclusion

This baseline demonstrates a working transformer-based OCR pipeline with a late-stage language-model correction step, directly aligned with the HumanAI RenAIssance screening requirements.
