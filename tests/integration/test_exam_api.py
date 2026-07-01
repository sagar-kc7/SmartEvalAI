"""Integration tests for exam and question API endpoints."""

import pytest
from fastapi.testclient import TestClient

from smartevalai.models.user import User


class TestSubjectEndpoint:
    def test_create_subject_as_teacher(self, teacher_client: TestClient):
        res = teacher_client.post("/api/v1/exams/subjects", json={"name": "Math"})
        assert res.status_code == 201
        assert res.json()["name"] == "Math"

    def test_create_subject_as_student_returns_403(self, student_client: TestClient):
        res = student_client.post("/api/v1/exams/subjects", json={"name": "Math"})
        assert res.status_code == 403

    def test_duplicate_subject_returns_existing(self, teacher_client: TestClient):
        teacher_client.post("/api/v1/exams/subjects", json={"name": "Physics"})
        res = teacher_client.post("/api/v1/exams/subjects", json={"name": "Physics"})
        assert res.status_code == 201
        assert res.json()["name"] == "Physics"


class TestExamEndpoint:
    def test_create_exam_as_teacher(self, teacher_client: TestClient, teacher_user: User):
        teacher_client.post("/api/v1/exams/subjects", json={"name": "CS"})
        res = teacher_client.post("/api/v1/exams", json={"title": "Midterm", "subject_id": 1})
        assert res.status_code == 201
        data = res.json()
        assert data["title"] == "Midterm"
        assert data["teacher_id"] == teacher_user.id

    def test_create_exam_invalid_subject_returns_404(self, teacher_client: TestClient):
        res = teacher_client.post("/api/v1/exams", json={"title": "Test", "subject_id": 999})
        assert res.status_code == 404

    def test_create_exam_as_student_returns_403(self, student_client: TestClient):
        res = student_client.post("/api/v1/exams", json={"title": "Test", "subject_id": 1})
        assert res.status_code == 403


class TestQuestionEndpoint:
    def _setup_exam(self, teacher_client: TestClient) -> int:
        teacher_client.post("/api/v1/exams/subjects", json={"name": "CS"})
        res = teacher_client.post("/api/v1/exams", json={"title": "Test Exam", "subject_id": 1})
        return res.json()["id"]

    def test_add_descriptive_question(self, teacher_client: TestClient):
        exam_id = self._setup_exam(teacher_client)
        res = teacher_client.post(f"/api/v1/exams/{exam_id}/questions", json={
            "question_number": "1",
            "question_text": "What is Python?",
            "question_type": "descriptive",
            "max_marks": 5.0,
            "official_answer": "Python is a high-level programming language.",
        })
        assert res.status_code == 201
        data = res.json()
        assert data["question_number"] == "1"
        assert "official_answer" not in data

    def test_add_mcq_question(self, teacher_client: TestClient):
        exam_id = self._setup_exam(teacher_client)
        res = teacher_client.post(f"/api/v1/exams/{exam_id}/questions", json={
            "question_number": "1",
            "question_text": "Which keyword defines a function?",
            "question_type": "mcq",
            "max_marks": 1.0,
            "options": ["def", "func", "function", "define"],
            "correct_option": "def",
        })
        assert res.status_code == 201

    def test_mcq_without_options_returns_400(self, teacher_client: TestClient):
        exam_id = self._setup_exam(teacher_client)
        res = teacher_client.post(f"/api/v1/exams/{exam_id}/questions", json={
            "question_number": "1",
            "question_text": "Which keyword?",
            "question_type": "mcq",
            "max_marks": 1.0,
        })
        assert res.status_code == 400

    def test_list_questions_hides_answer_key(self, teacher_client: TestClient):
        exam_id = self._setup_exam(teacher_client)
        teacher_client.post(f"/api/v1/exams/{exam_id}/questions", json={
            "question_number": "1",
            "question_text": "What is Python?",
            "question_type": "descriptive",
            "max_marks": 5.0,
            "official_answer": "Python is a programming language.",
        })
        res = teacher_client.get(f"/api/v1/exams/{exam_id}/questions")
        assert res.status_code == 200
        q = res.json()[0]
        assert "official_answer" not in q
        assert "correct_option" not in q