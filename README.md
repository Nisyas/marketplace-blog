# Marketplace Blog API

API блога маркетплейса, разработанное на FastAPI с полнотекстовым поиском, JWT аутентификацией и асинхронной отправкой email через Celery.

## 📋 Описание

Backend API для блога маркетплейса, реализующий все требования дизайн-макета (Figma). Проект предоставляет REST API для управления статьями, категориями и пользователями с поддержкой пагинации, полнотекстового поиска и загрузки изображений в S3.

## ✨ Функциональность

### Аутентификация и авторизация
- Регистрация пользователей с email-уведомлением.
- JWT токены в HTTP-only cookies.
- Middleware для проверки токенов при каждом запросе.
- Асинхронная отправка email через Celery и RabbitMQ.

### Управление статьями
- **Список статей** – пагинация, полнотекстовый поиск (PostgreSQL), фильтрация по категориям.
- **Создание статьи** – заголовок, текст, категория, изображение (S3/MinIO).
- **Редактирование статьи** – обновление полей с автоматической датой изменения.
- **Удаление статьи** – soft delete с переносом в отдельную таблицу.

### Управление категориями
- Создание категорий.
- Получение списка категорий.
- Привязка статей к категориям.

## 🛠 Технологический стек

- **Backend**: Python 3.12, FastAPI
- **База данных**: PostgreSQL (полнотекстовый поиск)
- **ORM**: SQLAlchemy 2.x (async)
- **Миграции**: Alembic
- **Очереди**: RabbitMQ + Celery
- **Хранилище файлов**: MinIO (S3-compatible)
- **Конфигурация**: Pydantic, pydantic-settings
- **Тестирование**: pytest, httpx, pytest-asyncio
- **Качество кода**: ruff, pre-commit
- **Контейнеризация**: Docker, Docker Compose
- **Управление зависимостями**: Poetry

## 🚀 Быстрый старт

### Предварительные требования

- Установлены Docker и Docker Compose.
- (Опционально) Poetry для локальной разработки без Docker.

### Установка и запуск

1. Клонировать репозиторий:
git clone https://github.com/Nisyas/marketplace-blog.git
cd marketplace-blog
git checkout develop


2. Создать файл `.env` (если есть `.env.example`, скопировать на его основе):
cp .env.example .env



3. Настроить переменные окружения в `.env`, например:
Database
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
POSTGRES_DB=marketplace_blog
POSTGRES_HOST=db
POSTGRES_PORT=5432
DATABASE_URL=postgresql+asyncpg://postgres:postgres@db:5432/marketplace_blog

JWT
SECRET_KEY=your-secret-key-here
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

RabbitMQ / Celery
RABBITMQ_DEFAULT_USER=guest
RABBITMQ_DEFAULT_PASS=guest
CELERY_BROKER_URL=amqp://guest:guest@rabbitmq:5672//
CELERY_RESULT_BACKEND=rpc://

MinIO (S3)
MINIO_ROOT_USER=minioadmin
MINIO_ROOT_PASSWORD=minioadmin
MINIO_ENDPOINT=minio:9000
MINIO_BUCKET=blog-images
MINIO_USE_SSL=false

Email
SMTP_HOST=smtp.example.com
SMTP_PORT=587
SMTP_USER=your-email@example.com
SMTP_PASSWORD=your-password
SMTP_USE_TLS=true
FROM_EMAIL=your-email@example.com


4. Запустить проект через Docker Compose:
docker-compose up -d --build


5. Применить миграции:
docker-compose exec app alembic upgrade head


6. Открыть API:

- Приложение: `http://localhost:8000`
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

### Makefile (если используется)
make up # Запуск всех сервисов
make down # Остановка всех сервисов
make logs # Логи приложения
make migrate # Применить миграции
make test # Запуск тестов
make lint # Проверка кода ruff
make format # Форматирование кода



## 📚 API Endpoints (общее описание)

### Аутентификация

- `POST /api/auth/register` – регистрация пользователя.
- `POST /api/auth/login` – логин, выдача JWT в cookie.
- `POST /api/auth/logout` – выход, очистка cookie.

### Категории

- `GET /api/categories` – список категорий.
- `POST /api/categories` – создание категории (для авторизованных).

### Статьи

- `GET /api/articles` – список статей с фильтрами и пагинацией:
  - `page_number` – номер страницы.
  - `page_size` – количество элементов на странице (с ограничением максимального размера).
  - `search` – полнотекстовый поиск по заголовку/контенту.
  - `category_id` – фильтрация по категории.
- `GET /api/articles/{id}` – получение статьи по ID.
- `POST /api/articles` – создание статьи (заголовок, текст, категория, изображение).
- `PUT /api/articles/{id}` – обновление статьи.
- `DELETE /api/articles/{id}` – soft delete статьи (перенос в отдельную таблицу).

## 🧪 Тестирование

### Запуск тестов в Docker

docker-compose exec app pytest


### Локальный запуск тестов

poetry install
poetry run pytest


## 📁 Структура проекта

marketplace-blog/
├── app/
│ ├── api/ # Роуты и зависимости FastAPI
│ ├── core/ # Настройки и конфигурация (settings, security)
│ ├── db/ # Подключение к БД, сессии
│ ├── models/ # SQLAlchemy модели
│ ├── schemas/ # Pydantic-схемы
│ ├── services/ # Бизнес-логика, работа с БД
│ ├── tasks/ # Celery задачи (email и др.)
│ └── main.py # Точка входа FastAPI приложения
├── alembic/ # Миграции БД
├── tests/ # Тесты (auth, articles, categories и пр.)
├── docker-compose.yml # Описание контейнеров
├── Dockerfile # Образ приложения
├── pyproject.toml # Зависимости Poetry
├── Makefile # Утилитарные команды
└── README.md


## 💡 Особенности реализации

- Полнотекстовый поиск реализован средствами PostgreSQL (tsvector/tsquery).
- Soft delete: статьи при удалении переносятся в отдельную таблицу, а не удаляются физически.
- Email-рассылка на регистрацию выполняется через Celery worker и RabbitMQ, чтобы не блокировать HTTP-запрос.
- JWT токен хранится в HTTP-only cookie и проверяется на каждом запросе через middleware.

## 🤝 Contributing

1. Форкнуть репозиторий.
2. Создать ветку фичи: `git checkout -b feature/my-feature`.
3. Внести изменения и пройти линтеры/тесты.
4. Открыть Pull Request.

## 👤 Автор

**Valerii Tkachenko**

- GitHub: [@Nisyas](https://github.com/Nisyas)

---
