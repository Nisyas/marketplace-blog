import pytest
from httpx import AsyncClient
from app.services import storage
from app.tasks import email_tasks


@pytest.mark.asyncio
async def test_create_article_with_mocked_s3(client: AsyncClient, monkeypatch):
    def fake_upload_image_file(
        file_obj, filename: str, content_type: str | None = None
    ) -> str:
        return "http://test.local/fake-image.png"

    monkeypatch.setattr(storage, "upload_image_file", fake_upload_image_file)

    def fake_delay(email: str) -> None:
        pass

    monkeypatch.setattr(email_tasks.send_registration_email_task, "delay", fake_delay)

    resp = await client.post(
        "/api/v1/auth/register",
        data={"email": "author@example.com", "password": "password123"},
    )
    assert resp.status_code == 201

    login_resp = await client.post(
        "/api/v1/auth/login",
        data={"email": "author@example.com", "password": "password123"},
    )
    assert login_resp.status_code == 200

    cookies = login_resp.cookies
    assert "access_token" in cookies

    resp_cat = await client.post(
        "/api/v1/categories",
        data={
            "name": "Photos",
            "slug": "photos",
            "description": "Photos category",
        },
        cookies=cookies,
    )
    assert resp_cat.status_code == 201
    category = resp_cat.json()
    assert "id" in category

    files = {
        "title": (None, "My article"),
        "content": (None, "Some content"),
        "category_id": (None, str(category["id"])),
    }

    resp_article = await client.post(
        "/api/v1/articles",
        files=files,
        cookies=cookies,
    )
    assert resp_article.status_code == 201

    data = resp_article.json()
    assert data["title"] == "My article"
    assert data["category_id"] == category["id"]
    assert data["image_url"] == "http://test.local/fake-image.png"
