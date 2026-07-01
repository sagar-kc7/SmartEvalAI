"""Unit tests for semantic similarity scoring."""

import pytest

from smartevalai.services.evaluation.similarity import compute_similarity


class TestComputeSimilarity:
    def test_identical_texts_score_near_one(self):
        text = "Python is a high level programming language."
        score = compute_similarity(text, text)
        assert score > 0.99

    def test_similar_texts_score_high(self):
        a = "Python is a high level programming language."
        b = "Python is a high-level, general-purpose programming language."
        score = compute_similarity(a, b)
        assert score > 0.7

    def test_unrelated_texts_score_low(self):
        a = "Python is a programming language."
        b = "The mitochondria is the powerhouse of the cell."
        score = compute_similarity(a, b)
        assert score < 0.4

    def test_empty_student_answer_returns_zero(self):
        assert compute_similarity("", "Python is a programming language.") == 0.0

    def test_empty_official_answer_returns_zero(self):
        assert compute_similarity("Python is a programming language.", "") == 0.0

    def test_both_empty_returns_zero(self):
        assert compute_similarity("", "") == 0.0

    def test_score_in_valid_range(self):
        score = compute_similarity("hello world", "goodbye world")
        assert 0.0 <= score <= 1.0

    def test_whitespace_only_returns_zero(self):
        assert compute_similarity("   ", "Python is a language.") == 0.0