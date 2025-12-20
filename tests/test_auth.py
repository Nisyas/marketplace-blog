import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_register_and_login(client: AsyncClient, monkeypatch):
    from app.tasks import email_tasks

    def fake_delay(email: str) -> None:
        pass

    monkeypatch.setattr(email_tasks.send_registration_email_task, "delay", fake_delay)

    resp = await client.post(
        "/api/v1/auth/register",
        data={"email": "test@example.com", "password": "password123"},
    )
    assert resp.status_code == 201

    resp = await client.post(
        "/api/v1/auth/login",
        data={"email": "test@example.com", "password": "password123"},
    )
    assert resp.status_code == 200
    assert "access_token" in resp.cookies


@pytest.mark.asyncio
async def test_register_sends_email_task(client: AsyncClient, monkeypatch):
    from app.tasks import email_tasks

    called_args: dict = {}

    def fake_delay(email: str) -> None:
        called_args["email"] = email

    monkeypatch.setattr(email_tasks.send_registration_email_task, "delay", fake_delay)

    resp = await client.post(
        "/api/v1/auth/register",
        data={"email": "mail@example.com", "password": "password123"},
    )
    assert resp.status_code == 201
    assert called_args["email"] == "mail@example.com"

