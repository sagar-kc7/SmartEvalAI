# SmartEval AI

An AI-powered student answer evaluation platform that automatically grades handwritten and typed exam submissions using OCR, semantic similarity, and Large Language Models.

## Features

- **OCR Pipeline** — PaddleOCR (primary) + EasyOCR (fallback) with OpenCV preprocessing
- **Hybrid Scoring** — 40% semantic similarity (sentence-transformers) + 60% LLM evaluation (Google Gemini)
- **MCQ + Descriptive** — supports both question types with automatic grading
- **Personalized Feedback** — Gemini generates per-question feedback for each student
- **Reports** — CSV and PDF export of evaluation results per exam
- **Analytics** — average scores, similarity, AI scores, score distribution per exam
- **Frontend** — Jinja2 + TailwindCSS + HTMX dashboards for teachers and students
- **Auth** — JWT-based authentication with bcrypt passwords and role-based access

## Tech Stack

- **Backend:** Python 3.12, FastAPI, SQLModel, Alembic, SQLite
- **AI:** Google Gemini 2.5 Flash, sentence-transformers (all-MiniLM-L6-v2)
- **OCR:** PaddleOCR, EasyOCR, OpenCV, pdf2image
- **Frontend:** Jinja2, TailwindCSS, HTMX
- **Testing:** pytest (42 tests)
- **Package manager:** uv

## Setup

```bash
git clone https://github.com/sagar-kc7/SmartEvalAI.git
cd SmartEvalAI
cp .env.example .env        # add your GEMINI_API_KEY
uv sync --extra ai --extra ocr --extra dev
sudo apt install -y poppler-utils  # required for PDF conversion
uv run alembic upgrade head
uv run uvicorn smartevalai.main:app --reload
```

Open `http://localhost:8000` in your browser.

## Project Structure
src/smartevalai/
├── api/v1/          # FastAPI route handlers
├── core/            # Config, security, logging, dependencies
├── db/              # Database engine and session
├── models/          # SQLModel table definitions
├── schemas/         # Pydantic request/response schemas
├── services/
│   ├── ocr/         # OCR pipeline (detection, preprocessing, extraction)
│   ├── evaluation/  # Similarity scoring and hybrid grading
│   └── ai/          # Gemini client, prompts, evaluator
├── templates/       # Jinja2 HTML templates
└── utils/           # File storage helpers

## Running Tests

```bash
uv run pytest tests/ -v
```

## Environment Variables

| Variable | Description |
|---|---|
| `GEMINI_API_KEY` | Google Gemini API key (required) |
| `SECRET_KEY` | JWT signing secret (change in production) |
| `DATABASE_URL` | SQLAlchemy DB URL (default: SQLite) |
| `MAX_UPLOAD_SIZE_MB` | Max file upload size in MB (default: 15) |