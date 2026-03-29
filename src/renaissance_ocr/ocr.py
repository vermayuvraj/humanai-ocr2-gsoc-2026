from __future__ import annotations

import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path

import cv2
import numpy as np
import torch
from PIL import Image
from transformers import TrOCRProcessor, VisionEncoderDecoderModel


@dataclass(slots=True)
class OCRPrediction:
    line_index: int
    raw_text: str


class BaseOCREngine:
    def predict_region(
        self, text_region: Image.Image, line_images: list[Image.Image]
    ) -> list[OCRPrediction]:
        raise NotImplementedError


class TrOCREngine(BaseOCREngine):
    def __init__(self, model_name: str) -> None:
        try:
            self.processor = TrOCRProcessor.from_pretrained(
                model_name, local_files_only=True
            )
            self.model = VisionEncoderDecoderModel.from_pretrained(
                model_name, local_files_only=True
            )
        except OSError:
            self.processor = TrOCRProcessor.from_pretrained(model_name)
            self.model = VisionEncoderDecoderModel.from_pretrained(model_name)
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.model.to(self.device)
        self.model.eval()

    def predict_region(
        self, text_region: Image.Image, line_images: list[Image.Image]
    ) -> list[OCRPrediction]:
        predictions: list[OCRPrediction] = []
        for index, image in enumerate(line_images):
            prepared = prepare_line_image(image)
            pixel_values = self.processor(images=prepared, return_tensors="pt").pixel_values
            pixel_values = pixel_values.to(self.device)
            with torch.inference_mode():
                generated = self.model.generate(pixel_values, max_new_tokens=128)
            text = self.processor.batch_decode(generated, skip_special_tokens=True)[0]
            predictions.append(OCRPrediction(line_index=index, raw_text=text.strip()))
        return predictions


class TesseractEngine(BaseOCREngine):
    def __init__(self, language: str, psm: int) -> None:
        self.language = language
        self.psm = psm

    def predict_region(
        self, text_region: Image.Image, line_images: list[Image.Image]
    ) -> list[OCRPrediction]:
        prepared = prepare_region_for_tesseract(text_region)
        text = run_tesseract(prepared, language=self.language, psm=self.psm)
        lines = [line.strip() for line in text.splitlines() if line.strip()]
        return [
            OCRPrediction(line_index=index, raw_text=line)
            for index, line in enumerate(lines)
        ]


def build_ocr_engine(backend: str, model_name: str, language: str, psm: int) -> BaseOCREngine:
    normalized = backend.strip().casefold()
    if normalized == "tesseract":
        return TesseractEngine(language=language, psm=psm)
    return TrOCREngine(model_name=model_name)


def prepare_line_image(image: Image.Image) -> Image.Image:
    rgb = np.array(image.convert("RGB"))
    gray = cv2.cvtColor(rgb, cv2.COLOR_RGB2GRAY)
    filtered = cv2.bilateralFilter(gray, d=7, sigmaColor=50, sigmaSpace=50)
    binary = cv2.threshold(
        filtered, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU
    )[1]
    inverted = 255 - binary

    coords = cv2.findNonZero(inverted)
    if coords is not None:
        x, y, w, h = cv2.boundingRect(coords)
        pad = 10
        x0 = max(x - pad, 0)
        y0 = max(y - pad, 0)
        x1 = min(x + w + pad, gray.shape[1])
        y1 = min(y + h + pad, gray.shape[0])
        binary = binary[y0:y1, x0:x1]

    target_height = 96
    scale = max(target_height / max(binary.shape[0], 1), 1.0)
    resized = cv2.resize(
        binary,
        None,
        fx=scale,
        fy=scale,
        interpolation=cv2.INTER_CUBIC,
    )
    rgb_ready = cv2.cvtColor(resized, cv2.COLOR_GRAY2RGB)
    return Image.fromarray(rgb_ready)


def prepare_region_for_tesseract(image: Image.Image) -> Image.Image:
    rgb = np.array(image.convert("RGB"))
    gray = cv2.cvtColor(rgb, cv2.COLOR_RGB2GRAY)
    denoised = cv2.fastNlMeansDenoising(gray, h=10)
    binary = cv2.threshold(
        denoised, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU
    )[1]
    scaled = cv2.resize(
        binary,
        None,
        fx=1.6,
        fy=1.6,
        interpolation=cv2.INTER_CUBIC,
    )
    rgb_ready = cv2.cvtColor(scaled, cv2.COLOR_GRAY2RGB)
    return Image.fromarray(rgb_ready)


def run_tesseract(image: Image.Image, language: str, psm: int) -> str:
    with tempfile.TemporaryDirectory(prefix="renaissance-ocr-") as temp_dir_name:
        temp_dir = Path(temp_dir_name)
        input_path = temp_dir / "input.png"
        output_base = temp_dir / "ocr_output"
        image.save(input_path)
        subprocess.run(
            [
                "tesseract",
                str(input_path),
                str(output_base),
                "-l",
                language,
                "--psm",
                str(psm),
            ],
            capture_output=True,
            check=True,
        )
        output_path = output_base.with_suffix(".txt")
        try:
            return output_path.read_text(encoding="utf-8").strip()
        except UnicodeDecodeError:
            return output_path.read_text(encoding="latin-1").strip()
