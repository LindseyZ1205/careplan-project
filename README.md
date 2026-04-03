## CarePlan MVP (Django + PostgreSQL + Redis + Docker)

- **Submit** creates **Patient / Doctor / Order / CarePlan** with `CarePlan.status=pending`, then **`RPUSH`s `careplan_id`** to Redis list `careplan:pending` (after DB commit via `transaction.on_commit`).
- **HTTP response** returns immediately: `{"message":"已收到","careplan_id":...,"status":"pending"}` (API **202**). No worker in this repo yet — nothing consumes the queue or calls the LLM.
- **PostgreSQL** + **Redis** via Docker Compose; `migrate` runs before `runserver`.

### Run with Docker Compose

```bash
docker compose build
docker compose up
```

Open `http://localhost:8000`. Postgres **5432**, Redis **6379** (queue key `careplan:pending` by default).

### Run locally without Docker

Without `POSTGRES_HOST`, settings fall back to **SQLite** (`db.sqlite3`) so you can still develop quickly.

To use local Postgres instead, export:

```bash
export POSTGRES_HOST=localhost
export POSTGRES_DB=careplan
export POSTGRES_USER=careplan
export POSTGRES_PASSWORD=careplan
```

Then:

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```

### Models

| Model    | Role |
|----------|------|
| Patient  | `first_name`, `last_name`, optional `mrn` |
| Doctor   | `name`, optional `npi` |
| Order    | FK → Patient, Doctor; `medication_name`, `diagnosis`, `notes` |
| CarePlan | OneToOne → Order; `careplan_text`, `status` |

### API

- `GET /api/careplan/` — usage message.
- `POST /api/careplan/` — enqueue: DB row `pending` + Redis; **202** + `careplan_id`.
- `GET /api/careplan/<id>/` — fetch CarePlan by id (text empty until a future worker fills it).

### Redis queue

- List key: `CAREPLAN_REDIS_QUEUE_KEY` (default `careplan:pending`). Values: stringified CarePlan primary keys.
- If `REDIS_HOST` is unset, enqueue is skipped (local SQLite-only dev).

### Admin

```bash
python manage.py createsuperuser
```

Then open `/admin/` to browse tables.
