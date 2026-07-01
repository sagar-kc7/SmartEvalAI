"""OCR text extraction, with PaddleOCR as primary and EasyOCR as fallback.

PaddleOCR generally performs better on mixed printed/handwritten text, but
it's a heavier, less universally-compatible dependency. If it fails to
initialize or errors at runtime (e.g. on a machine without proper GPU/CPU
support), we transparently fall back to EasyOCR so the pipeline doesn't
hard-fail.
"""

import numpy as np
from loguru import logger


class OCREngine:
    """Lazily-initialized OCR engine with automatic PaddleOCR -> EasyOCR fallback."""

    def __init__(self) -> None:
        self._paddle_ocr = None
        self._easy_ocr = None

    def _get_paddle_ocr(self):
        """Lazily construct the PaddleOCR instance (expensive to initialize)."""
        if self._paddle_ocr is None:
            from paddleocr import PaddleOCR

            self._paddle_ocr = PaddleOCR(use_angle_cls=True, lang="en")
        return self._paddle_ocr

    def _get_easy_ocr(self):
        """Lazily construct the EasyOCR reader (expensive to initialize)."""
        if self._easy_ocr is None:
            import easyocr

            self._easy_ocr = easyocr.Reader(["en"], gpu=False)
        return self._easy_ocr

    def extract_text(self, raw_image: np.ndarray, preprocessed_image: np.ndarray) -> str:
        """Run OCR on a page, trying PaddleOCR first then EasyOCR as fallback.

        Args:
            raw_image: The original color (RGB) page image. PaddleOCR's 3.x
                pipeline does its own internal document-orientation and
                unwarping preprocessing, which requires a 3-channel color
                image — feeding it our binarized output breaks that
                pipeline, so Paddle always gets the raw image.
            preprocessed_image: Our own OpenCV-cleaned (grayscale/binarized,
                deskewed) image, used only for the EasyOCR fallback, which
                benefits from this manual cleanup.

        Returns:
            The extracted text, with detected text lines joined by newlines.
        """
        try:
            return self._extract_with_paddle(raw_image)
        except Exception as exc:  # noqa: BLE001 — intentional broad fallback
            logger.warning(f"PaddleOCR failed ({exc}); falling back to EasyOCR")
            return self._extract_with_easyocr(preprocessed_image)

    def _extract_with_paddle(self, image: np.ndarray) -> str:
        """Extract text using PaddleOCR's 3.x `.predict()` API.

        PaddleOCR 3.x replaced the old `.ocr()` nested-list output with
        `.predict()`, which returns a list of result objects — one per
        input image — each exposing a `rec_texts` field containing the
        recognized text lines in reading order.
        """
        ocr = self._get_paddle_ocr()
        results = ocr.predict(image)
        lines: list[str] = []
        for result in results:
            lines.extend(result.get("rec_texts", []))
        return "\n".join(lines)

    def _extract_with_easyocr(self, image: np.ndarray) -> str:
        reader = self._get_easy_ocr()
        result = reader.readtext(image, detail=0)
        return "\n".join(result)


# Module-level singleton: OCR engines are expensive to initialize, so we
# reuse one instance across the app rather than constructing it per request.
ocr_engine = OCREngine()