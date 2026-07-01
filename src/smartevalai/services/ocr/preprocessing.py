"""OpenCV-based image preprocessing to improve OCR accuracy.

Typical pipeline for a photographed/scanned answer sheet:
1. Convert to grayscale (OCR engines work on intensity, not color).
2. Denoise (phone photos in particular have sensor noise).
3. Adaptive thresholding (handles uneven lighting better than a flat threshold).
4. Deskew (photos are rarely perfectly aligned).
"""

import cv2
import numpy as np


def to_grayscale(image: np.ndarray) -> np.ndarray:
    """Convert an RGB/BGR image to single-channel grayscale."""
    if len(image.shape) == 2:
        return image  # already grayscale
    return cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)


def denoise(image: np.ndarray) -> np.ndarray:
    """Remove sensor/compression noise while preserving text edges."""
    return cv2.fastNlMeansDenoising(image, h=10)


def adaptive_threshold(image: np.ndarray) -> np.ndarray:
    """Binarize the image, adapting to uneven local lighting.

    This handles shadows or uneven phone-camera lighting far better than
    a single global threshold value would.
    """
    return cv2.adaptiveThreshold(
        image,
        255,
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY,
        blockSize=31,
        C=15,
    )


def deskew(image: np.ndarray) -> np.ndarray:
    """Correct slight rotation so text lines are horizontal.

    OpenCV's `minAreaRect` angle convention is ambiguous for boxes that are
    already close to axis-aligned (it can report 90 degrees for a box that
    needs *no* rotation at all). To avoid that trap, we compute the skew
    angle ourselves from the longest edge of the bounding box's corner
    points, which is unambiguous regardless of orientation.
    """
    foreground = np.column_stack(np.where(image == 0))  # black text pixels
    if foreground.shape[0] < 50:
        return image  # too little text to estimate a reliable angle

    # Merge each line of text into one solid horizontal blob.
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (25, 5))
    dilated = cv2.dilate(255 - image, kernel, iterations=1)

    contours, _ = cv2.findContours(dilated, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if not contours:
        return image

    largest_contour = max(contours, key=cv2.contourArea)
    rect = cv2.minAreaRect(largest_contour)
    box_points = cv2.boxPoints(rect)

    # Find the longest edge of the box and measure its angle from horizontal.
    edges = [
        (box_points[i], box_points[(i + 1) % 4]) for i in range(4)
    ]
    longest_edge = max(edges, key=lambda e: np.linalg.norm(e[0] - e[1]))
    dx = longest_edge[1][0] - longest_edge[0][0]
    dy = longest_edge[1][1] - longest_edge[0][1]
    angle = np.degrees(np.arctan2(dy, dx))

    # Normalize to the smallest equivalent rotation in [-45, 45].
    if angle > 45:
        angle -= 90
    elif angle < -45:
        angle += 90

    if abs(angle) < 0.5:
        return image  # negligible skew, don't introduce rotation artifacts

    (h, w) = image.shape[:2]
    center = (w // 2, h // 2)
    rotation_matrix = cv2.getRotationMatrix2D(center, angle, 1.0)
    return cv2.warpAffine(
        image,
        rotation_matrix,
        (w, h),
        flags=cv2.INTER_CUBIC,
        borderMode=cv2.BORDER_REPLICATE,
    )


def preprocess_for_ocr(image: np.ndarray) -> np.ndarray:
    """Run the full preprocessing pipeline on a raw page image.

    Args:
        image: Raw RGB image as a NumPy array (e.g. from `pdf_to_images`
            or a loaded photo).

    Returns:
        A cleaned, binarized, deskewed grayscale image ready for OCR.
    """
    gray = to_grayscale(image)
    denoised = denoise(gray)
    thresholded = adaptive_threshold(denoised)
    return deskew(thresholded)