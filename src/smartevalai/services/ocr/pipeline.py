"""End-to-end OCR pipeline: file -> images -> preprocessing -> OCR -> cleaned, split text.

This module implements the 6-step process from the spec:
1. Detect whether the file is PDF or image.
2. Convert PDF pages into images.
3. Perform OCR.
4. Clean extracted text.
5. Split answers by question number.
6. (Storing in the DB happens in the calling service, not here — this
   module is pure processing logic and stays easily unit-testable.)
"""

from pathlib import Path

import numpy as np
from PIL import Image

from smartevalai.services.ocr.engine import ocr_engine
from smartevalai.services.ocr.file_utils import is_pdf, validate_file_type
from smartevalai.services.ocr.pdf_converter import pdf_to_images
from smartevalai.services.ocr.preprocessing import preprocess_for_ocr
from smartevalai.services.ocr.text_processing import clean_text, split_answers_by_question


class OCRPipelineResult:
    """Container for the full output of running the OCR pipeline once.

    Attributes:
        raw_text: Concatenated raw OCR output across all pages.
        cleaned_text: Raw text after `clean_text`.
        answers_by_question: Dict mapping question number to answer text.
    """

    def __init__(self, raw_text: str, cleaned_text: str, answers_by_question: dict[str, str]):
        self.raw_text = raw_text
        self.cleaned_text = cleaned_text
        self.answers_by_question = answers_by_question


def _load_pages(file_path: str | Path) -> list[np.ndarray]:
    """Load a file as a list of page images, handling both PDF and image inputs."""
    if is_pdf(file_path):
        return pdf_to_images(file_path)
    # Single image file -> treat as a one-page "document".
    return [np.array(Image.open(file_path).convert("RGB"))]


def run_ocr_pipeline(file_path: str | Path) -> OCRPipelineResult:
    """Run the full OCR pipeline on an uploaded answer sheet.

    Args:
        file_path: Path to the uploaded PDF or image file.

    Returns:
        An OCRPipelineResult with raw text, cleaned text, and per-question
        answers.

    Raises:
        UnsupportedFileTypeError: If the file extension isn't supported.
    """
    validate_file_type(file_path)

    pages = _load_pages(file_path)

    page_texts = []
    for page_image in pages:
        preprocessed = preprocess_for_ocr(page_image)
        page_texts.append(ocr_engine.extract_text(page_image, preprocessed))

    raw_text = "\n".join(page_texts)
    cleaned = clean_text(raw_text)
    answers = split_answers_by_question(cleaned)

    return OCRPipelineResult(
        raw_text=raw_text,
        cleaned_text=cleaned,
        answers_by_question=answers,
    )