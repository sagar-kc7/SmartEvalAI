"""Utilities for detecting and validating uploaded answer sheet files."""

from pathlib import Path

SUPPORTED_IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png"}
SUPPORTED_PDF_EXTENSION = ".pdf"


class UnsupportedFileTypeError(Exception):
    """Raised when an uploaded file's extension isn't supported."""


def is_pdf(file_path: str | Path) -> bool:
    """Return True if the file is a PDF based on its extension."""
    return Path(file_path).suffix.lower() == SUPPORTED_PDF_EXTENSION


def is_image(file_path: str | Path) -> bool:
    """Return True if the file is a supported image type based on extension."""
    return Path(file_path).suffix.lower() in SUPPORTED_IMAGE_EXTENSIONS


def validate_file_type(file_path: str | Path) -> None:
    """Raise if the file extension isn't a supported PDF or image.

    Raises:
        UnsupportedFileTypeError: If the extension is neither PDF nor a
            supported image format.
    """
    if not (is_pdf(file_path) or is_image(file_path)):
        raise UnsupportedFileTypeError(
            f"Unsupported file type: '{Path(file_path).suffix}'. "
            f"Expected one of: .pdf, {', '.join(sorted(SUPPORTED_IMAGE_EXTENSIONS))}"
        )