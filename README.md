## CarePlan MVP (Django + PostgreSQL + Redis + Celery + Docker)

- **Submit** creates **Patient / Doctor / Order / CarePlan** with `status=pending`, then **`transaction.on_commit`** schedules **`generate_care_plan_task.delay(careplan_id)`** (Celery broker = Redis).
- **HTTP** returns **202** + `careplan_id` immediately. **No polling, no SSE, no auto-refresh** — you only see `completed` + `careplan_text` after **you** reload the page or call **GET** `/api/careplan/<id>/` again.
- **Celery worker** consumes tasks from the **Redis broker** (not a hand-written `BLPOP` loop). **`generate_care_plan_task`** sets `processing` → **`generate_careplan_with_llm`** (`core/llm.py`, mode from **`LLM_MODE`**) → `completed`; on failure **retries up to 3 times** with exponential backoff, then **`failed`**.

### Run with Docker Compose

```bash
docker compose build
docker compose up
```

Services: **web** (port **8000**), **db** (Postgres **5432**), **redis** (**6379**), **celery** (worker).

Open `http://localhost:8000` for the Django template form, or **`http://localhost:5173`** for the **React** app (Vite dev server). The React UI **polls** `GET /api/careplan/<id>/status/` every **3 seconds** until `completed` (shows `content`) or `failed` (shows error).

Watch **celery** logs for `Task core.tasks.generate_care_plan_task[...] succeeded`.

### Status API (polling)

- **`GET /api/careplan/<id>/status/`** → `{ careplan_id, status, content, error }`  
  - `content` is set only when `status === "completed"`.  
  - `error` is set when `status === "failed"`.

React uses a **Vite proxy** (`/api` → Django). For a separate origin, set **`CORS_ALLOWED_ORIGINS`** on Django (see `settings.py`).

### How to verify Celery is working

1. **Logs** — In the terminal where `docker compose up` runs, the **celery** service should print lines like:
   - `Task core.tasks.generate_care_plan_task[<uuid>] received`
   - `Task core.tasks.generate_care_plan_task[<uuid>] succeeded`
2. **Redis** — `docker compose exec redis redis-cli MONITOR` (briefly) or `KEYS *` can show Celery/kombu traffic; easiest is still **worker logs** + **GET** API.
3. **Database / API** — After a few seconds, **GET** `/api/careplan/<careplan_id>/` should show `"status": "completed"` and a non-empty `careplan_text` (or `"failed"` if LLM kept erroring after retries).
4. **LLM modes** — Default in Compose for **celery** is **`LLM_MODE=mock`** (fixed fake text, no network). For production, set **`LLM_MODE=openai`** plus **`OPENAI_API_KEY`** on **celery** (and **web** if needed). Use **`LLM_MODE=template`** for deterministic text from DB fields without OpenAI.

### Local dev without Docker

Set `POSTGRES_*`, `REDIS_HOST=localhost`, install deps, run Postgres + Redis, then:

```bash
python manage.py migrate
python manage.py runserver   # terminal 1
celery -A config worker -l info   # terminal 2
```

For synchronous debugging only:

```bash
export CELERY_TASK_ALWAYS_EAGER=1
```

### LLM env vars

| Variable | Purpose |
|----------|---------|
| `LLM_MODE` | **`mock`** (default in `docker-compose` for celery) — fixed mock body via `mock_llm_generate_careplan`. **`template`** — `generate_careplan_template_text` from order/patient fields. **`openai`** — real Chat Completions (requires `OPENAI_API_KEY`). |
| `OPENAI_API_KEY` | Required when `LLM_MODE=openai` |
| `OPENAI_MODEL` | Default `gpt-4o-mini` |
| `MOCK_LLM_BODY_FILE` | Optional path to a text file replacing the built-in mock body |

### Admin

```bash
python manage.py createsuperuser
```

Then open `/admin/` to inspect **CarePlan** rows and statuses.
