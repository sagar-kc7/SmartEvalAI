"""Converts PDF answer sheets into per-page images for OCR."""

from pathlib import Path

import numpy as np
from pdf2image import convert_from_path


def pdf_to_images(pdf_path: str | Path, dpi: int = 300) -> list[np.ndarray]:
    """Convert every page of a PDF into a NumPy image array (RGB).

    Args:
        pdf_path: Path to the PDF file.
        dpi: Render resolution. 300 is a good balance of OCR accuracy vs
            processing time for handwritten/printed answer sheets.

    Returns:
        A list of NumPy arrays, one per page, in RGB order (height, width, 3).
    """
    pil_pages = convert_from_path(str(pdf_path), dpi=dpi)
    return [np.array(page) for page in pil_pages]