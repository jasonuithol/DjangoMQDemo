# platform-service

A small demo Django platform slice — **REST APIs, background jobs, and a
third-party integration** — proving out a Django / DRF / Celery / PostgreSQL /
RabbitMQ stack. Everything (app + tooling + infrastructure) runs in containers
via rootless **podman-compose**, so the host stays clean.

## Architecture

A single pod of four containers:

| Container | Image | Role |
|---|---|---|
| `app` | built from `Containerfile` (Python 3.12 + uv) | your code + all tooling; idles, you exec in |
| `postgres` | postgres:16 | database |
| `rabbitmq` | rabbitmq:3-management | Celery broker |
| `redis` | redis:7 | Celery result backend |

Your working tree is bind-mounted into `app` at `/workspace`, so edits on the
host are live inside the container. The virtualenv lives in a named volume at
`/opt/venv`, off the host tree.

## Prerequisites

- **podman** (rootless) and **podman-compose** (`uv tool install podman-compose`)
- That's it — Python, uv, Django, and every other tool live inside the `app` container.

## Quickstart

```bash
cp .env.example .env   # first checkout only (.env is git-ignored)
make build             # build the app image
make up                # start all four containers
make migrate           # apply migrations to Postgres
make superuser         # (optional) create an admin login
make run               # Django dev server on :8000
```

In separate terminals, for the async parts:

```bash
make worker         # Celery worker (consumes from RabbitMQ)
make flower         # task monitor on :5555
```

Then open **http://localhost:8000/** for the hands-on UI: create an order and
watch it flip `pending → synced` as the worker syncs it to the local mock
partner, and send test webhooks. (The UI is a single Django-served page that
loads React from a CDN — no build step; it needs browser internet access.)

Then try the API with `api.http` (VS Code REST Client) or `curl`:

```bash
curl -s localhost:8000/health/
curl -s -X POST localhost:8000/api/orders/ \
  -H 'Content-Type: application/json' \
  -d '{"customer_name": "Ada", "total_amount": "42.50"}'
```

## URLs

| URL | What |
|---|---|
| http://localhost:8000/ | **Hands-on UI** — create orders, watch them sync, send webhooks |
| http://localhost:8000/api/orders/ | Orders REST API |
| http://localhost:8000/webhooks/partner/ | Partner webhook receiver |
| http://localhost:8000/health/ | Health check (DB round-trip) |
| http://localhost:8000/admin/ | Django admin (needs `make superuser`) |
| http://localhost:15672 | RabbitMQ management UI (guest/guest) |
| http://localhost:5555 | Flower (when `make flower` is running) |

## Testing & quality gates

```bash
make test           # pytest against the real Postgres test database
make lint           # ruff check + ruff format --check
make type           # mypy (strict, django-stubs + drf-stubs)
make check          # all of the above
```

Tests hit a real Postgres test DB (rolled back per test) — the ORM is never
mocked. Only boundaries are mocked: outbound HTTP (`responses`), time
(`freezegun`), and task dispatch. Celery runs eagerly in tests, so no broker is
needed. See `.pre-commit-config.yaml` to optionally run the gates on commit.

Run `make help` for the full list of targets.

## Project layout

```
config/            # project: split settings (base/local/test), celery.py, urls, health
orders/            # Order model, DRF serializer/viewset, services.create_order, factory, admin
integrations/      # PartnerClient, Celery tasks, webhook receiver, WebhookEvent model
tests/             # pytest suite mirroring the apps
compose.yaml       # the four-container pod
Containerfile      # the app image (Python 3.12 + uv)
Makefile           # dev workflow
api.http           # example requests
```

## Conventions

- **Thin views, logic in `services.py`** — plain functions, no DI container;
  mock at boundaries with pytest fixtures / `mock.patch`.
- **Celery tasks take IDs, never ORM objects**; every task is idempotent;
  integration tasks use `acks_late` + retry-with-backoff.
- **No slow work in request handlers** — external HTTP goes through Celery.
- Type hints everywhere; `mypy` and `ruff` failures are build failures.

## Stack rationale (for a C#/.NET or Java/Spring background)

| Concern | Choice | Nearest analog |
|---|---|---|
| Framework | Django 6.x | Spring Boot / ASP.NET Core, batteries included |
| API layer | Django REST Framework | serializers ≈ records + validation; ViewSets ≈ controllers |
| ORM | Django ORM | Active Record (not Data Mapper); watch N+1 → `select_related` |
| Migrations | Django migrations | EF Migrations / Flyway |
| Background jobs | Celery + RabbitMQ + Redis | Hangfire / MassTransit |
| Dependency mgmt | uv + `pyproject.toml` + `uv.lock` | NuGet / Maven; lockfile ≈ packages.lock.json |
| Lint/format | Ruff | analyzers + dotnet format / Black+flake8+isort |
| Type checking | mypy (+ django-stubs) | type hints, CI-enforced |
| Testing | pytest + pytest-django | xUnit / JUnit; bare `assert` |
| Test data | factory_boy | AutoFixture / Instancio |
| HTTP stubbing | responses | WireMock (for `requests`) |
| DI container | none — deliberately | plain modules + fixtures |
| Config | split `settings/` + env via django-environ | appsettings / application.yml (12-factor) |

## Notes

- **Settings selection:** `DJANGO_SETTINGS_MODULE` is intentionally unset in
  `.env`. `manage.py` and `celery.py` default to `config.settings.local`;
  pytest uses `config.settings.test` (via `pyproject.toml`).
- **Service hostnames** inside the pod are the compose service names
  (`postgres`, `rabbitmq`, `redis`), not `localhost` — see `.env`.
- **RabbitMQ** runs as uid 999 (`user: "999:999"` in `compose.yaml`) to avoid a
  rootless-podman Erlang-cookie permission error.
