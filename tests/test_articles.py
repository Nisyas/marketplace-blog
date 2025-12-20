import pytest
from httpx import AsyncClient
from io import BytesIO

from sqlalchemy.ext.asyncio import AsyncSession


@pytest.mark.asyncio
async def test_create_category(client: AsyncClient, monkeypatch):
    from app.tasks import email_tasks

    def fake_delay(email: str) -> None:
        pass

    monkeypatch.setattr(email_tasks.send_registration_email_task, "delay", fake_delay)

    await client.post(
        "/api/v1/auth/register",
        data={"email": "catuser@example.com", "password": "password123"},
    )
    login_resp = await client.post(
        "/api/v1/auth/login",
        data={"email": "catuser@example.com", "password": "password123"},
    )
    cookies = login_resp.cookies

    response = await client.post(
        "/api/v1/categories",
        data={
            "name": "Technology",
            "slug": "technology",
            "description": "Tech articles",
        },
        cookies=cookies,
    )

    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Technology"
    assert data["slug"] == "technology"
    assert "id" in data


@pytest.mark.asyncio
async def test_list_categories(client: AsyncClient, monkeypatch):
    from app.tasks import email_tasks

    def fake_delay(email: str) -> None:
        pass

    monkeypatch.setattr(email_tasks.send_registration_email_task, "delay", fake_delay)

    await client.post(
        "/api/v1/auth/register",
        data={"email": "listcat@example.com", "password": "password123"},
    )
    login_resp = await client.post(
        "/api/v1/auth/login",
        data={"email": "listcat@example.com", "password": "password123"},
    )
    cookies = login_resp.cookies

    await client.post(
        "/api/v1/categories",
        data={"name": "Cat1", "slug": "cat1", "description": "Description 1"},
        cookies=cookies,
    )
    await client.post(
        "/api/v1/categories",
        data={"name": "Cat2", "slug": "cat2", "description": "Description 2"},
        cookies=cookies,
    )

    response = await client.get("/api/v1/categories")
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 2


@pytest.mark.asyncio
async def test_create_article_with_image(client: AsyncClient, monkeypatch):
    from app.tasks import email_tasks

    def fake_upload(file_obj, filename: str, content_type: str | None = None) -> str:
        return "http://test.local/fake-image.jpg"

    def fake_delay(email: str) -> None:
        pass

    from app.services import storage

    monkeypatch.setattr(storage, "upload_image_file", fake_upload)
    monkeypatch.setattr(email_tasks.send_registration_email_task, "delay", fake_delay)

    await client.post(
        "/api/v1/auth/register",
        data={"email": "articleauthor@example.com", "password": "password123"},
    )
    login_resp = await client.post(
        "/api/v1/auth/login",
        data={"email": "articleauthor@example.com", "password": "password123"},
    )
    cookies = login_resp.cookies

    cat_resp = await client.post(
        "/api/v1/categories",
        data={"name": "News", "slug": "news", "description": "News category"},
        cookies=cookies,
    )
    category_id = cat_resp.json()["id"]

    fake_image = BytesIO(b"fake image content")

    response = await client.post(
        "/api/v1/articles",
        files={"image": ("test.jpg", fake_image, "image/jpeg")},
        data={
            "title": "Breaking News",
            "content": "This is the content of the article.",
            "category_id": str(category_id),
        },
        cookies=cookies,
    )

    assert response.status_code == 201
    data = response.json()
    assert data["title"] == "Breaking News"
    assert data["content"] == "This is the content of the article."
    assert data["category_id"] == category_id
    assert "image_url" in data


@pytest.mark.asyncio
async def test_list_articles_with_pagination(client: AsyncClient, monkeypatch):
    from app.tasks import email_tasks

    def fake_upload(file_obj, filename: str, content_type: str | None = None) -> str:
        return "http://test.local/fake.jpg"

    def fake_delay(email: str) -> None:
        pass

    from app.services import storage

    monkeypatch.setattr(storage, "upload_image_file", fake_upload)
    monkeypatch.setattr(email_tasks.send_registration_email_task, "delay", fake_delay)

    await client.post(
        "/api/v1/auth/register",
        data={"email": "paguser@example.com", "password": "password123"},
    )
    login_resp = await client.post(
        "/api/v1/auth/login",
        data={"email": "paguser@example.com", "password": "password123"},
    )
    cookies = login_resp.cookies

    cat_resp = await client.post(
        "/api/v1/categories",
        data={"name": "Sports", "slug": "sports", "description": "Sports news"},
        cookies=cookies,
    )
    category_id = cat_resp.json()["id"]

    for i in range(5):
        fake_image = BytesIO(b"image")
        await client.post(
            "/api/v1/articles",
            files={"image": (f"img{i}.jpg", fake_image, "image/jpeg")},
            data={
                "title": f"Article {i}",
                "content": f"Content {i}",
                "category_id": str(category_id),
            },
            cookies=cookies,
        )

    response = await client.get("/api/v1/articles?page_number=1&page_size=3")
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert len(data["items"]) <= 3
    assert "total" in data
    assert data["total"] >= 5


@pytest.mark.asyncio
async def test_search_articles(client: AsyncClient, db_session: AsyncSession):
    await client.post(
        "/api/v1/auth/register",
        data={"email": "searchuser@example.com", "password": "password123"},
    )
    login_resp = await client.post(
        "/api/v1/auth/login",
        data={"email": "searchuser@example.com", "password": "password123"},
    )
    cookies = login_resp.cookies

    cat_resp = await client.post(
        "/api/v1/categories",
        data={"name": "Science", "slug": "science", "description": "Science"},
        cookies=cookies,
    )
    category_id = cat_resp.json()["id"]

    fake_image = BytesIO(b"image")
    create_resp = await client.post(
        "/api/v1/articles",
        files={"image": ("img.jpg", fake_image, "image/jpeg")},
        data={
            "title": "Python Programming Guide",
            "content": "Learn Python basics",
            "category_id": str(category_id),
        },
        cookies=cookies,
    )

    assert create_resp.status_code == 201
    article_data = create_resp.json()
    assert article_data["title"] == "Python Programming Guide"

    response = await client.get("/api/v1/articles")
    assert response.status_code == 200
    data = response.json()

    assert "items" in data
    assert "total" in data
    assert data["total"] >= 1
    assert any("Python" in item.get("title", "") for item in data["items"])


@pytest.mark.asyncio
async def test_update_article(client: AsyncClient):
    await client.post(
        "/api/v1/auth/register",
        data={"email": "updateuser@example.com", "password": "password123"},
    )
    login_resp = await client.post(
        "/api/v1/auth/login",
        data={"email": "updateuser@example.com", "password": "password123"},
    )
    cookies = login_resp.cookies

    cat_resp = await client.post(
        "/api/v1/categories",
        data={"name": "Updates", "slug": "updates", "description": "Updates"},
        cookies=cookies,
    )
    category_id = cat_resp.json()["id"]

    fake_image = BytesIO(b"image")
    create_resp = await client.post(
        "/api/v1/articles",
        files={"image": ("img.jpg", fake_image, "image/jpeg")},
        data={
            "title": "Original Title",
            "content": "Original content",
            "category_id": str(category_id),
        },
        cookies=cookies,
    )
    article_id = create_resp.json()["id"]

    response = await client.put(
        f"/api/v1/articles/{article_id}",
        json={
            "title": "Updated Title",
            "content": "Updated content",
            "category_id": category_id,
        },
        cookies=cookies,
    )

    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "Updated Title"
    assert data["content"] == "Updated content"


@pytest.mark.asyncio
async def test_delete_article(client: AsyncClient, monkeypatch):
    from app.tasks import email_tasks

    def fake_upload(file_obj, filename: str, content_type: str | None = None) -> str:
        return "http://test.local/fake.jpg"

    def fake_delay(email: str) -> None:
        pass

    from app.services import storage

    monkeypatch.setattr(storage, "upload_image_file", fake_upload)
    monkeypatch.setattr(email_tasks.send_registration_email_task, "delay", fake_delay)

    await client.post(
        "/api/v1/auth/register",
        data={"email": "deleteuser@example.com", "password": "password123"},
    )
    login_resp = await client.post(
        "/api/v1/auth/login",
        data={"email": "deleteuser@example.com", "password": "password123"},
    )
    cookies = login_resp.cookies

    cat_resp = await client.post(
        "/api/v1/categories",
        data={"name": "ToDelete", "slug": "todelete", "description": "To delete"},
        cookies=cookies,
    )
    category_id = cat_resp.json()["id"]

    fake_image = BytesIO(b"image")
    create_resp = await client.post(
        "/api/v1/articles",
        files={"image": ("img.jpg", fake_image, "image/jpeg")},
        data={
            "title": "To be deleted",
            "content": "Will be deleted",
            "category_id": str(category_id),
        },
        cookies=cookies,
    )
    article_id = create_resp.json()["id"]

    response = await client.delete(f"/api/v1/articles/{article_id}", cookies=cookies)
    assert response.status_code == 204

    list_resp = await client.get("/api/v1/articles")
    articles = list_resp.json()["items"]
    assert not any(article["id"] == article_id for article in articles)
