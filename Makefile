# platform-service — podman-compose dev workflow
# Everything runs in containers; `make sh` drops you into the app container.
COMPOSE := podman-compose

.DEFAULT_GOAL := help

.PHONY: help build up down restart ps logs sh shell psql \
        run worker beat flower migrate makemigrations test lint type check clean

help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) \
	  | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-14s\033[0m %s\n", $$1, $$2}'

build: ## Build the app image
	$(COMPOSE) build

up: ## Start all containers (infra + idle app) in the background
	$(COMPOSE) up -d

down: ## Stop and remove containers
	$(COMPOSE) down

restart: down up ## Recreate everything

ps: ## Show container status
	$(COMPOSE) ps

logs: ## Tail logs from all services
	$(COMPOSE) logs -f

sh: ## Open a shell inside the app container
	$(COMPOSE) exec app bash

shell: sh ## Alias for `sh`

psql: ## Open a psql session against the platform DB
	$(COMPOSE) exec postgres psql -U platform -d platform

# ---- app commands (run inside the app container) ----
run: ## Django dev server on :8000
	$(COMPOSE) exec app uv run python manage.py runserver 0.0.0.0:8000

worker: ## Celery worker
	$(COMPOSE) exec app uv run celery -A config worker -l info

beat: ## Celery beat scheduler
	$(COMPOSE) exec app uv run celery -A config beat -l info

flower: ## Flower task monitor on :5555
	$(COMPOSE) exec app uv run celery -A config flower --address=0.0.0.0 --port=5555

migrate: ## Apply migrations
	$(COMPOSE) exec app uv run python manage.py migrate

superuser: ## Create a Django admin superuser
	$(COMPOSE) exec app uv run python manage.py createsuperuser

makemigrations: ## Generate migrations
	$(COMPOSE) exec app uv run python manage.py makemigrations

test: ## Run the test suite
	$(COMPOSE) exec app uv run pytest -q

lint: ## Ruff lint + format check
	$(COMPOSE) exec app sh -c "uv run ruff check . && uv run ruff format --check ."

type: ## mypy
	$(COMPOSE) exec app uv run mypy .

check: lint type test ## All quality gates

clean: ## Stop containers and remove named volumes (DB + venv)
	$(COMPOSE) down -v
