## CarePlan MVP (Django + PostgreSQL + Docker)

- **HTML form** → synchronous Django view → template “LLM” text (replace later with a real LLM).
- **PostgreSQL** via Django ORM: **Patient**, **Doctor**, **Order**, **CarePlan** with foreign keys.
- **CarePlan.status**: `pending` → `processing` → `completed` or `failed`.
- **Docker Compose** runs **Postgres** and **web**; `migrate` runs before `runserver`.

### Run with Docker Compose

```bash
docker compose build
docker compose up
```

Open `http://localhost:8000`. Postgres is on host port **5432** (user/db/password: `careplan`).

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

- `GET /api/careplan/` — short usage message.
- `POST /api/careplan/` — create patient/doctor/order/care plan; returns JSON including `id` (CarePlan pk) and `status`.
- `GET /api/careplan/<id>/` — fetch one care plan by CarePlan id.

### Admin

```bash
python manage.py createsuperuser
```

Then open `/admin/` to browse tables.
