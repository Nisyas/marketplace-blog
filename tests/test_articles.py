import pytest
from io import BytesIO

from httpx import AsyncClient


async def create_category(
    client: AsyncClient,
    cookies: dict,
    name: str = "Category",
    slug: str = "category",
    description: str = "Description",
) -> dict:
    resp = await client.post(
        "/api/v1/categories",
        data={
            "name": name,
            "slug": slug,
            "description": description,
        },
        cookies=cookies,
    )
    assert resp.status_code == 201
    return resp.json()


@pytest.mark.asyncio
async def test_create_category(client: AsyncClient, auth_cookies: dict):
    resp = await client.post(
        "/api/v1/categories",
        data={
            "name": "Technology",
            "slug": "technology",
            "description": "Tech articles",
        },
        cookies=auth_cookies,
    )

    assert resp.status_code == 201
    data = resp.json()
    assert data["name"] == "Technology"
    assert data["slug"] == "technology"
    assert "id" in data


@pytest.mark.asyncio
async def test_list_categories(client: AsyncClient, auth_cookies: dict):
    await create_category(
        client, auth_cookies, name="Cat1", slug="cat1", description="Description 1"
    )
    await create_category(
        client, auth_cookies, name="Cat2", slug="cat2", description="Description 2"
    )

    resp = await client.get("/api/v1/categories")

    assert resp.status_code == 200
    data = resp.json()
    assert len(data) >= 2


@pytest.mark.asyncio
async def test_create_article_with_image(client: AsyncClient, auth_cookies: dict):
    category = await create_category(
        client,
        auth_cookies,
        name="News",
        slug="news",
        description="News category",
    )
    category_id = category["id"]

    fake_image = BytesIO(b"fake image content")

    resp = await client.post(
        "/api/v1/articles",
        files={"image": ("test.jpg", fake_image, "image/jpeg")},
        data={
            "title": "Breaking News",
            "content": "This is the content of the article.",
            "category_id": str(category_id),
        },
        cookies=auth_cookies,
    )

    assert resp.status_code == 201
    data = resp.json()
    assert data["title"] == "Breaking News"
    assert data["content"] == "This is the content of the article."
    assert data["category_id"] == category_id
    assert "image_url" in data


@pytest.mark.asyncio
async def test_list_articles_with_pagination(client: AsyncClient, auth_cookies: dict):
    category = await create_category(
        client,
        auth_cookies,
        name="Sports",
        slug="sports",
        description="Sports news",
    )
    category_id = category["id"]

    for i in range(15):
        resp = await client.post(
            "/api/v1/articles",
            data={
                "title": f"Article {i}",
                "content": f"Content {i}",
                "category_id": str(category_id),
            },
            cookies=auth_cookies,
        )
        assert resp.status_code == 201

    resp = await client.get(
        "/api/v1/articles", params={"page_number": 1, "page_size": 10}
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["page_number"] == 1
    assert data["page_size"] == 10
    assert len(data["items"]) == 10
    assert data["total"] >= 15
