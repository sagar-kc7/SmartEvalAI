"""Semantic similarity scoring using sentence-transformer embeddings."""

import numpy as np
from sentence_transformers import SentenceTransformer

# all-MiniLM-L6-v2 is a small (~80MB), fast model that performs well on
# semantic textual similarity tasks — a good fit for scoring short-to-medium
# length student answers without requiring a GPU.
_MODEL_NAME = "all-MiniLM-L6-v2"

_model: SentenceTransformer | None = None


def _get_model() -> SentenceTransformer:
    """Lazily load the embedding model (expensive — load once, reuse)."""
    global _model
    if _model is None:
        _model = SentenceTransformer(_MODEL_NAME)
    return _model


def compute_similarity(student_answer: str, official_answer: str) -> float:
    """Compute cosine similarity between a student answer and the official answer.

    Args:
        student_answer: The student's extracted answer text.
        official_answer: The teacher-provided model answer.

    Returns:
        A similarity score in [0, 1], where 1.0 means semantically identical.
        Returns 0.0 if either input is empty/whitespace-only, since an
        empty answer should never be treated as similar to anything.
    """
    if not student_answer.strip() or not official_answer.strip():
        return 0.0

    model = _get_model()
    embeddings = model.encode([student_answer, official_answer])

    a, b = embeddings[0], embeddings[1]
    cosine = float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b)))

    # Cosine similarity can technically be slightly negative for unrelated
    # text; clamp to [0, 1] since negative "similarity" isn't meaningful
    # for scoring purposes.
    return max(0.0, min(1.0, cosine))