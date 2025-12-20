.PHONY: help install dev lint test fmt alembic-revision alembic-upgrade docker-up docker-down

PYTHON=python
POETRY=poetry

help:
	@echo "Доступные команды:"
	@echo "  make install           - установить зависимости через poetry"
	@echo "  make dev               - запустить dev-сервер (uvicorn)"
	@echo "  make lint              - запустить ruff"
	@echo "  make fmt               - (опционально) автоформатирование ruff"
	@echo "  make test              - запустить pytest"
	@echo "  make alembic-revision  - создать ревизию alembic (AUTOGENERATE)"
	@echo "  make alembic-upgrade   - применить миграции alembic до head"
	@echo "  make docker-up         - поднять все сервисы через docker compose"
	@echo "  make docker-down       - остановить и удалить контейнеры"

install:
	$(POETRY) install

dev:
	$(POETRY) run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

lint:
	$(POETRY) run ruff check .

fmt:
	$(POETRY) run ruff check . --fix

test:
	$(POETRY) run pytest

alembic-revision:
	$(POETRY) run alembic revision --autogenerate -m "$(m)"

alembic-upgrade:
	$(POETRY) run alembic upgrade head

docker-up:
	docker compose up --build

docker-down:
	docker compose down
