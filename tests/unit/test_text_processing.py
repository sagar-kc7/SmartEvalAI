"""Unit tests for OCR text cleaning and question splitting."""

import pytest

from smartevalai.services.ocr.text_processing import clean_text, split_answers_by_question


class TestCleanText:
    def test_collapses_multiple_spaces(self):
        assert clean_text("hello    world") == "hello world"

    def test_collapses_multiple_blank_lines(self):
        result = clean_text("line1\n\n\n\nline2")
        assert "\n\n\n" not in result

    def test_strips_leading_trailing_whitespace(self):
        assert clean_text("  hello  ") == "hello"

    def test_preserves_normal_punctuation(self):
        text = "Hello, world. How are you? I'm fine!"
        result = clean_text(text)
        assert "," in result
        assert "." in result
        assert "?" in result

    def test_empty_string(self):
        assert clean_text("") == ""


class TestSplitAnswersByQuestion:
    def test_splits_dot_format(self):
        text = "1. First answer\n2. Second answer"
        result = split_answers_by_question(text)
        assert result["1"] == "First answer"
        assert result["2"] == "Second answer"

    def test_splits_paren_format(self):
        text = "1) Answer one\n2) Answer two"
        result = split_answers_by_question(text)
        assert "1" in result
        assert "2" in result

    def test_splits_underscore_ocr_artifact(self):
        """OCR sometimes misreads '.' as '_' — must still split correctly."""
        text = "1_ def\n2. Polymorphism is about multiple forms."
        result = split_answers_by_question(text)
        assert result["1"] == "def"
        assert "Polymorphism" in result["2"]

    def test_fallback_no_markers(self):
        """If no question markers found, entire text goes under key '1'."""
        text = "This is just a paragraph with no question numbers."
        result = split_answers_by_question(text)
        assert result == {"1": text}

    def test_question_prefix_format(self):
        text = "Q1. First answer\nQ2. Second answer"
        result = split_answers_by_question(text)
        assert "1" in result
        assert "2" in result

    def test_multiline_answer(self):
        text = "1. First line\nstill first answer\n2. Second answer"
        result = split_answers_by_question(text)
        assert "still first answer" in result["1"]