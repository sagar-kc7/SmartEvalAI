"""Prompt templates for Gemini-based evaluation and feedback generation.

Every prompt explicitly instructs Gemini to return ONLY raw JSON (no
markdown, no commentary) so `gemini_client.generate_json` can parse the
response directly.
"""


def build_descriptive_evaluation_prompt(
    question_text: str, official_answer: str, student_answer: str, max_marks: float
) -> str:
    """Build the prompt for evaluating a descriptive answer."""
    return f"""You are an expert teacher evaluating a student's exam answer.

Question:
{question_text}

Official model answer (out of {max_marks} marks):
{official_answer}

Student's answer:
{student_answer}

Evaluate the student's answer against the official answer. Consider:
- Concept correctness
- Missing points compared to the official answer
- Wrong or incorrect concepts present
- Completeness of the answer
- Clarity of expression

Return ONLY a JSON object with this exact structure, no markdown fences, no extra text:
{{
  "llm_score": <float between 0 and {max_marks}>,
  "explanation": "<2-3 sentence explanation of the score>",
  "missing_points": ["<concept the student missed>", ...],
  "strong_points": ["<concept the student got right>", ...]
}}"""


def build_mcq_evaluation_prompt(
    question_text: str, correct_option: str, student_selected_option: str, max_marks: float
) -> str:
    """Build the prompt for evaluating an MCQ answer."""
    return f"""You are an expert teacher evaluating a student's multiple-choice answer.

Question:
{question_text}

Correct option:
{correct_option}

Student selected:
{student_selected_option}

Determine if the student's selected option is correct, and provide a short
conceptual explanation suitable for learning purposes — explain briefly why
the correct option is right, regardless of what the student chose.

Return ONLY a JSON object with this exact structure, no markdown fences, no extra text:
{{
  "is_correct": <true or false>,
  "marks_awarded": <{max_marks} if correct, otherwise 0>,
  "explanation": "<brief explanation of why the correct option is correct>"
}}"""


def build_feedback_prompt(
    question_text: str, student_answer: str, missing_points: list[str], strong_points: list[str]
) -> str:
    """Build the prompt for generating personalized student feedback."""
    missing_str = ", ".join(missing_points) if missing_points else "none"
    strong_str = ", ".join(strong_points) if strong_points else "none"

    return f"""You are an encouraging but honest teacher writing personalized
feedback for a student.

Question:
{question_text}

Student's answer:
{student_answer}

Strong points identified: {strong_str}
Missing points identified: {missing_str}

Write 2-4 sentences of personalized, constructive feedback. Acknowledge what
the student did well, point out what to review, and suggest one concrete
way to improve next time.

Return ONLY a JSON object with this exact structure, no markdown fences, no extra text:
{{
  "feedback": "<the personalized feedback text>"
}}"""