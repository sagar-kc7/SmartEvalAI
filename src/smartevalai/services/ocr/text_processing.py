"""Cleans raw OCR output and splits it into per-question answers."""

import re


def clean_text(raw_text: str) -> str:
    """Normalize whitespace and strip common OCR noise artifacts.

    Args:
        raw_text: Unprocessed text straight out of the OCR engine.

    Returns:
        Cleaned text with collapsed whitespace and stripped stray symbols.
    """
    # Collapse multiple spaces/tabs into one, but preserve line breaks.
    text = re.sub(r"[ \t]+", " ", raw_text)
    # Remove stray OCR noise characters that aren't real punctuation.
    text = re.sub(r"[^\w\s.,;:!?()\-'\"/]", "", text)
    # Collapse 3+ blank lines down to a single blank line.
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def split_answers_by_question(cleaned_text: str) -> dict[str, str]:
    """Split cleaned OCR text into a dict keyed by question number.

    Looks for lines that start a new answer, in the common student-written
    formats: "1.", "1)", "Q1.", "Q1)", "Question 1:". Everything between
    one such marker and the next is treated as that question's answer.

    Args:
        cleaned_text: Output of `clean_text`.

    Returns:
        A dict mapping question number (as a string, e.g. "1") to the
        extracted answer text for that question. If no question markers
        are found at all, returns {"1": cleaned_text} as a fallback so
        downstream code always has something to work with.
    """
    # The separator after the question number is intentionally lenient:
    # OCR frequently misreads "." as "_", ":", "-", or drops it entirely,
    # especially on handwritten or lower-quality scanned answer sheets.
    pattern = re.compile(
        r"^(?:Q(?:uestion)?\s*)?(\d+)[.)_:\-]?\s*",
        re.MULTILINE | re.IGNORECASE,
    )

    matches = list(pattern.finditer(cleaned_text))
    if not matches:
        return {"1": cleaned_text}

    answers: dict[str, str] = {}
    for i, match in enumerate(matches):
        question_number = match.group(1)
        start = match.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(cleaned_text)
        answers[question_number] = cleaned_text[start:end].strip()

    return answers