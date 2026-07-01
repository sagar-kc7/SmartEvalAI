"""Integration tests for the authentication API endpoints."""

import pytest
from fastapi.testclient import TestClient


class TestRegisterEndpoint:
    def test_register_student_returns_201(self, client: TestClient):
        res = client.post("/api/v1/auth/register", json={
            "full_name": "Test Student",
            "email": "student@api.com",
            "password": "pass1234",
            "role": "student",
        })
        assert res.status_code == 201
        data = res.json()
        assert data["email"] == "student@api.com"
        assert data["role"] == "student"
        assert "hashed_password" not in data

    def test_register_teacher_returns_201(self, client: TestClient):
        res = client.post("/api/v1/auth/register", json={
            "full_name": "Test Teacher",
            "email": "teacher@api.com",
            "password": "pass1234",
            "role": "teacher",
        })
        assert res.status_code == 201
        assert res.json()["role"] == "teacher"

    def test_duplicate_email_returns_409(self, client: TestClient):
        payload = {
            "full_name": "Test",
            "email": "dup@api.com",
            "password": "pass",
            "role": "student",
        }
        client.post("/api/v1/auth/register", json=payload)
        res = client.post("/api/v1/auth/register", json=payload)
        assert res.status_code == 409

    def test_invalid_email_returns_422(self, client: TestClient):
        res = client.post("/api/v1/auth/register", json={
            "full_name": "Test",
            "email": "not-an-email",
            "password": "pass",
            "role": "student",
        })
        assert res.status_code == 422


class TestLoginEndpoint:
    def test_login_returns_token(self, client: TestClient):
        client.post("/api/v1/auth/register", json={
            "full_name": "Login Test",
            "email": "login@api.com",
            "password": "pass1234",
            "role": "student",
        })
        res = client.post("/api/v1/auth/login",
            data={"username": "login@api.com", "password": "pass1234"},
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        assert res.status_code == 200
        data = res.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"

    def test_wrong_password_returns_401(self, client: TestClient):
        client.post("/api/v1/auth/register", json={
            "full_name": "Login Test",
            "email": "fail@api.com",
            "password": "correctpass",
            "role": "student",
        })
        res = client.post("/api/v1/auth/login",
            data={"username": "fail@api.com", "password": "wrongpass"},
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        assert res.status_code == 401

    def test_nonexistent_user_returns_401(self, client: TestClient):
        res = client.post("/api/v1/auth/login",
            data={"username": "ghost@api.com", "password": "pass"},
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        assert res.status_code == 401