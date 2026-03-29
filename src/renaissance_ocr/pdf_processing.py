from __future__ import annotations

from pathlib import Path

import cv2
import fitz
import numpy as np
from PIL import Image


def render_pdf(pdf_path: Path, dpi: int) -> list[Image.Image]:
    document = fitz.open(pdf_path)
    zoom = dpi / 72
    matrix = fitz.Matrix(zoom, zoom)
    pages: list[Image.Image] = []
    for page in document:
        pixmap = page.get_pixmap(matrix=matrix, alpha=False)
        image = Image.frombytes("RGB", [pixmap.width, pixmap.height], pixmap.samples)
        pages.append(image)
    return pages


def detect_main_text_region(page_image: Image.Image) -> Image.Image:
    rgb = np.array(page_image)
    gray = cv2.cvtColor(rgb, cv2.COLOR_RGB2GRAY)
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)
    binary = cv2.threshold(
        blurred, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU
    )[1]
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (35, 9))
    merged = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, kernel, iterations=2)
    contours, _ = cv2.findContours(merged, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    if not contours:
        return page_image

    best_box = max(contours, key=cv2.contourArea)
    x, y, w, h = cv2.boundingRect(best_box)
    pad_x = max(int(w * 0.04), 18)
    pad_y = max(int(h * 0.03), 18)
    x0 = max(x - pad_x, 0)
    y0 = max(y - pad_y, 0)
    x1 = min(x + w + pad_x, rgb.shape[1])
    y1 = min(y + h + pad_y, rgb.shape[0])
    cropped = rgb[y0:y1, x0:x1]
    return Image.fromarray(cropped)


def make_clean_binary(text_region: Image.Image) -> np.ndarray:
    rgb = np.array(text_region)
    gray = cv2.cvtColor(rgb, cv2.COLOR_RGB2GRAY)
    denoised = cv2.fastNlMeansDenoising(gray, h=12)
    binary = cv2.threshold(
        denoised, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU
    )[1]

    num_labels, labels, stats, _ = cv2.connectedComponentsWithStats(binary, connectivity=8)
    areas = stats[1:, cv2.CC_STAT_AREA]
    heights = stats[1:, cv2.CC_STAT_HEIGHT]
    median_area = float(np.median(areas)) if len(areas) else 0.0
    median_height = float(np.median(heights)) if len(heights) else 0.0

    cleaned = binary.copy()
    for label in range(1, num_labels):
        x, y, w, h, area = stats[label]
        # Suppress very large blobs that usually correspond to stains, ornaments, or scans.
        if median_area and median_height and area > median_area * 18 and h > median_height * 2.2:
            cleaned[labels == label] = 0

    cleaned = cv2.morphologyEx(
        cleaned,
        cv2.MORPH_OPEN,
        cv2.getStructuringElement(cv2.MORPH_RECT, (2, 2)),
        iterations=1,
    )
    return cleaned


def split_lines(text_region: Image.Image, min_line_height: int) -> list[Image.Image]:
    rgb = np.array(text_region)
    binary = make_clean_binary(text_region)
    bridged = cv2.dilate(
        binary,
        cv2.getStructuringElement(cv2.MORPH_RECT, (9, 3)),
        iterations=1,
    )
    projection = (bridged > 0).sum(axis=1).astype(np.float32)
    if not np.any(projection):
        return [text_region]

    smooth_window = max(5, min_line_height // 2 * 2 + 1)
    kernel = np.ones(smooth_window, dtype=np.float32) / smooth_window
    smoothed = np.convolve(projection, kernel, mode="same")
    threshold = max(float(smoothed.max() * 0.18), 6.0)

    line_spans: list[tuple[int, int]] = []
    start: int | None = None
    quiet_rows = max(6, min_line_height // 3)
    quiet_count = 0
    for index, value in enumerate(smoothed):
        if value >= threshold:
            quiet_count = 0
            if start is None:
                start = index
        elif start is not None:
            quiet_count += 1
            if quiet_count >= quiet_rows:
                end = index - quiet_rows + 1
                if end - start >= min_line_height:
                    line_spans.append((start, end))
                start = None
                quiet_count = 0
    if start is not None and len(smoothed) - start >= min_line_height:
        line_spans.append((start, len(smoothed)))

    if not line_spans:
        return [text_region]

    line_images: list[Image.Image] = []
    for top, bottom in line_spans:
        pad = 6
        y0 = max(top - pad, 0)
        y1 = min(bottom + pad, rgb.shape[0])
        line_images.append(Image.fromarray(rgb[y0:y1, :]))
    return line_images
