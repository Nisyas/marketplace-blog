import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_register(client: AsyncClient):
    resp = await client.post(
        "/api/v1/auth/register",
        data={"email": "user@example.com", "password": "password123"},
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["email"] == "user@example.com"


@pytest.mark.asyncio
async def test_login(client: AsyncClient):
    await client.post(
        "/api/v1/auth/register",
        data={"email": "loginuser@example.com", "password": "password123"},
    )

    resp = await client.post(
        "/api/v1/auth/login",
        data={"email": "loginuser@example.com", "password": "password123"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert "access_token" in data
