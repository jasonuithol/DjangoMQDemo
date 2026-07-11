# Claude Code Setup Guide — Python/Django Platform Stack (2026)

> **Purpose:** Instructions for Claude Code to bootstrap a Python development
> environment and a working demo project ("platform-service") using the stack from
> a Core Platform job ad: **Django, PostgreSQL, RabbitMQ** — REST APIs, background
> jobs, and "real tests". The developer comes from C#/.NET and Java/Spring, so the
> demo should deliberately showcase the idioms that differ (no DI container,
> Active Record ORM, Celery for anything slow, pytest fixtures, DB-backed tests).
> Follow the phases in order and verify each before continuing.

---

## 1. Stack decisions (context for every choice you make)

| Concern | Choice | Rationale / Java–.NET analog |
|---|---|---|
| Python | **Python 3.12+** (managed by uv) | Latest stable; type hints used pervasively |
| Framework | **Django 5.x** | Spring Boot/ASP.NET Core role, but batteries *included* (ORM, migrations, admin, auth) |
| API layer | **Django REST Framework (DRF)** | Serializers ≈ records + validation; ViewSets/routers ≈ convention controllers |
| ORM | **Django ORM** (built in) | Active Record, not Data Mapper; watch N+1 → `select_related`/`prefetch_related` |
| Migrations | **Django migrations** (built in) | Auto-diffed from models; ≈ EF Migrations, replaces Flyway |
| Database | **PostgreSQL 16** (Docker) | JSONB for third-party payloads; Django's Postgres support is first-class |
| Background jobs | **Celery 5.x** + **RabbitMQ** broker, **Redis** result backend | Hangfire/MassTransit role; the integration engine — slow paths never run in-request |
| Scheduling | **Celery Beat** | Quartz/cron analog |
| Dependency mgmt | **uv** + `pyproject.toml` + `uv.lock` | NuGet/Maven role; lockfile ≈ packages.lock.json; per-project `.venv` |
| Lint/format | **Ruff** (lint + format) | Replaces Black/flake8/isort; ≈ analyzers + dotnet format |
| Type checking | **mypy** (strict-ish) with `django-stubs`, `djangorestframework-stubs` | Type hints everywhere; CI-enforced |
| Testing | **pytest** + **pytest-django** | xUnit/JUnit role; bare `assert` with rewriting — no assertion library |
| Test data | **factory_boy** | Instancio/AutoFixture analog |
| HTTP stubbing | **responses** | WireMock analog for the `requests` library |
| Time control | **freezegun** | — |
| DI container | **None — deliberately** | Python idiom: plain modules/functions, mock at boundaries, pytest fixtures |
| Config | `settings.py` split + environment variables via **django-environ** | appsettings/application.yml analog; 12-factor |
| Admin UI | **Django admin** (built in) | The free internal CRUD tool — register every model |
| Task monitoring | **Flower** (dev) | — |

**Conventions to enforce throughout:**
- Type hints on all function signatures; `mypy` must pass.
- Business logic lives in `services.py` modules of plain functions per app — thin DRF views, no logic in serializers, models for data behavior only.
- Celery tasks receive **IDs, never ORM objects**; every task idempotent; `acks_late=True` and explicit retry policy on integration tasks.
- Tests hit the real (test) database — do not mock the ORM. Mock only boundaries: external HTTP, time, task dispatch.
- `pytest.ini`/`pyproject` marks: unit-ish tests run by default; anything needing RabbitMQ runs Celery **eagerly** in tests instead.
- No `requirements.txt` — `pyproject.toml` + `uv.lock` only.

---

## 2. Phase 1 — Development environment

### 2.1 uv (installs Python too)
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh     # Windows: powershell irm https://astral.sh/uv/install.ps1 | iex
uv --version
uv python install 3.12
```

### 2.2 Docker
Verify `docker info` works — required for Postgres, RabbitMQ, Redis. If unavailable, stop and report; this stack's demo depends on it.

### 2.3 VS Code extensions
```
code --install-extension ms-python.python            # core Python support
code --install-extension ms-python.vscode-pylance    # language server (type-aware)
code --install-extension charliermarsh.ruff          # lint + format on save
code --install-extension ms-python.debugpy           # debugger
code --install-extension batisteo.vscode-django      # Django template/nav support
code --install-extension humao.rest-client           # .http files
code --install-extension ms-azuretools.vscode-docker
```
Workspace `.vscode/settings.json`:
```json
{
  "python.defaultInterpreterPath": ".venv/bin/python",
  "[python]": {
    "editor.defaultFormatter": "charliermarsh.ruff",
    "editor.formatOnSave": true,
    "editor.codeActionsOnSave": { "source.organizeImports": "explicit" }
  },
  "python.testing.pytestEnabled": true
}
```

---

## 3. Phase 2 — Project scaffold

### 3.1 Initialize
```bash
mkdir platform-service && cd platform-service
uv init --python 3.12
uv add django djangorestframework celery[amqp] redis django-environ psycopg[binary] requests
uv add --dev pytest pytest-django factory-boy responses freezegun ruff mypy django-stubs djangorestframework-stubs flower
uv run django-admin startproject config .        # settings live in config/, manage.py at root
uv run python manage.py startapp orders
uv run python manage.py startapp integrations
```
(Check latest stable versions at run time; uv resolves and locks them in `uv.lock`.)

### 3.2 Local infrastructure — `compose.yaml`
```yaml
services:
  postgres:
    image: postgres:16
    environment:
      POSTGRES_DB: platform
      POSTGRES_USER: platform
      POSTGRES_PASSWORD: platform
    ports: ["5432:5432"]
  rabbitmq:
    image: rabbitmq:3-management
    ports: ["5672:5672", "15672:15672"]   # 15672 = management UI (guest/guest)
  redis:
    image: redis:7
    ports: ["6379:6379"]
```

### 3.3 Configuration
- Split settings: `config/settings/base.py`, `local.py`, `test.py`; select via `DJANGO_SETTINGS_MODULE`.
- Use `django-environ`: `DATABASES` from `DATABASE_URL=postgres://platform:platform@localhost:5432/platform`; `CELERY_BROKER_URL=amqp://guest:guest@localhost:5672//`; `CELERY_RESULT_BACKEND=redis://localhost:6379/0`. Provide `.env.example`, never commit `.env`.
- `config/celery.py` with the standard app bootstrap (`app.config_from_object("django.conf:settings", namespace="CELERY")`, `app.autodiscover_tasks()`), imported in `config/__init__.py`.
- In `test.py`: `CELERY_TASK_ALWAYS_EAGER = True`, `CELERY_TASK_EAGER_PROPAGATES = True` (tasks run inline in tests — no broker needed).
- `pyproject.toml` sections for Ruff (line length, rule set incl. `DJ` Django rules), mypy (plugins: `mypy_django_plugin`, `mypy_drf_plugin`), and pytest (`DJANGO_SETTINGS_MODULE = "config.settings.test"`, `--reuse-db`).

---

## 4. Phase 3 — Demo domain

Theme: a small "platform" slice proving the ad's three claims — REST APIs, background jobs, third-party integration.

```
orders/
  models.py          # Order model: UUID pk, customer_name, total_amount (Decimal),
                     # status (TextChoices), created_at; Meta.indexes on status
  serializers.py     # OrderSerializer (+ validation: total_amount > 0)
  views.py           # DRF ViewSet (list/retrieve/create), status filter via query param
  services.py        # create_order(...): creates row, enqueues sync task — the logic seam
  factories.py       # factory_boy OrderFactory
  admin.py           # register Order with list_display/list_filter — show off the admin
integrations/
  client.py          # PartnerClient: requests-based client for a fake partner API,
                     # timeout + raise_for_status + typed response dataclass
  tasks.py           # @shared_task(bind=True, acks_late=True, max_retries=5,
                     #   retry_backoff=True) sync_order_to_partner(self, order_id: str)
                     # loads Order by id, calls PartnerClient, marks synced; idempotent
  webhooks.py        # POST /webhooks/partner/ view: verify shared-secret header,
                     # store raw JSONB payload, enqueue processing task, return 202 fast
  models.py          # WebhookEvent: payload = models.JSONField(), processed flag
config/
  urls.py            # /api/orders/ router, /webhooks/partner/, /admin/, /health/
  health.py          # trivial JSON health view (DB check via one cheap query)
```

Implementation notes:
- Views stay thin: `perform_create` delegates to `orders.services.create_order`.
- `sync_order_to_partner` demonstrates the Celery contract from §1 (ID-passing, idempotency check before external call, retry with backoff on `requests.RequestException`).
- Webhook flow demonstrates "plugs into third-party ecosystems": accept fast → persist raw payload (JSONB) → process async.
- List endpoint uses `select_related`/`prefetch_related` where applicable and orders by `-created_at` with DRF pagination — the N+1 discipline, visible.
- Run `uv run python manage.py makemigrations && uv run python manage.py migrate` and commit the generated migrations.
- Create a superuser instruction in the README for the admin (`createsuperuser`).

---

## 5. Phase 4 — Tests ("real tests, not just coverage")

```
tests/
  conftest.py                    # fixtures: api_client, order (via OrderFactory), settings tweaks
  orders/test_api.py             # DRF APIClient: create → 201 + row exists; invalid amount → 400;
                                 # list filter by status; pagination shape
  orders/test_services.py        # create_order creates row AND enqueues task
                                 # (mock .delay / use django_capture_on_commit_callbacks)
  integrations/test_client.py    # responses-stubbed partner API: success parse, 500 → raises,
                                 # timeout behavior
  integrations/test_tasks.py     # eager Celery: task syncs order; partner 500 → retry path;
                                 # idempotency (second run is a no-op)
  integrations/test_webhooks.py  # bad secret → 401; good payload → 202, WebhookEvent row,
                                 # processing task ran (eager)
  test_query_counts.py           # django_assert_num_queries on the list endpoint —
                                 # the anti-N+1 regression test (the "actually scaling" nod)
```

Requirements:
- All DB tests use `@pytest.mark.django_db` — real Postgres test database, transaction-rolled-back per test. **Never** mock the ORM; never swap in SQLite.
- `factory_boy` for all model construction; no hand-rolled dicts of model fields.
- `responses` for every outbound HTTP assertion (including asserting the request body sent to the partner).
- One `freezegun` usage (e.g., created_at determinism).
- Parametrize validation cases with `@pytest.mark.parametrize`.
- Quality gates all green: `uv run pytest`, `uv run ruff check .`, `uv run ruff format --check .`, `uv run mypy .`

---

## 6. Phase 5 — Developer workflow artifacts

- **`api.http`**: create order, list orders, filtered list, webhook POST with secret header, health check.
- **`Makefile`** (or `justfile`): `up` (compose), `run` (`manage.py runserver`), `worker` (`celery -A config worker -l info`), `beat`, `flower`, `test`, `lint`, `type`, `migrate`.
- **`README.md`**: prerequisites; `uv sync`; compose up; migrate; three-terminal dev loop (server, worker, flower); URLs (`/api/orders/`, `/admin/`, RabbitMQ UI :15672, Flower :5555); stack-rationale table from §1.
- **`.gitignore`**: `.venv/`, `.env`, `__pycache__/`, `.mypy_cache/`, `.pytest_cache/`, `.ruff_cache/`.
- Optional but nice: `.pre-commit-config.yaml` running Ruff + mypy.

---

## 7. Verification checklist (run all; fix failures before finishing)

```bash
uv sync && docker compose up -d
uv run python manage.py migrate
uv run pytest -q                          # all green, incl. query-count test
uv run ruff check . && uv run mypy .      # clean
uv run python manage.py runserver &       # :8000
uv run celery -A config worker -l info &  # separate terminal in real use
curl -s localhost:8000/health/                                # {"status": "ok"}
curl -s -X POST localhost:8000/api/orders/ \
  -H 'Content-Type: application/json' \
  -d '{"customer_name": "Ada", "total_amount": "42.50"}'      # 201; worker log shows sync task
curl -s -X POST localhost:8000/webhooks/partner/ \
  -H 'X-Partner-Secret: <from .env>' -H 'Content-Type: application/json' \
  -d '{"event": "order.updated", "id": "123"}'                # 202; WebhookEvent row created
# open http://localhost:8000/admin/ — Orders CRUD for free
# open http://localhost:15672 — see the celery queue; http://localhost:5555 — Flower
```

---

## 8. Guardrails for Claude Code while executing

1. Resolve latest stable versions via uv at run time; do not hand-pin unless a compatibility issue forces it (then document why).
2. If Docker is unavailable: deliver everything else, keep `CELERY_TASK_ALWAYS_EAGER` tests working, and mark DB-dependent tests as requiring Docker — do **not** substitute SQLite to force green.
3. Never put slow work (external HTTP, email) in request handlers — it goes through Celery, including in the demo.
4. Keep the no-DI idiom: no dependency-injector frameworks; seams are module functions + mock.patch/fixtures.
5. mypy and Ruff failures are build failures, not warnings.
6. Commit in phases (env → scaffold → domain → tests → workflow files) with clear messages if a git repo is in play.
