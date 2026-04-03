## CarePlan MVP (Django + PostgreSQL + Redis + Celery + Docker)

- **Submit** creates **Patient / Doctor / Order / CarePlan** with `status=pending`, then **`transaction.on_commit`** schedules **`generate_care_plan_task.delay(careplan_id)`** (Celery broker = Redis).
- **HTTP** returns **202** + `careplan_id` immediately. **No polling, no SSE, no auto-refresh** — you only see `completed` + `careplan_text` after **you** reload the page or call **GET** `/api/careplan/<id>/` again.
- **Celery worker** runs **`core.tasks.generate_care_plan_task`**: sets `processing` → calls **LLM** (`core/llm.py`: OpenAI if `OPENAI_API_KEY`, else template text) → `completed`; on failure **retries up to 3 times** with **exponential backoff** (1s, 2s, 4s), then **`failed`**.

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
4. **Optional: OpenAI** — Set `OPENAI_API_KEY` (and optionally `OPENAI_MODEL`, default `gpt-4o-mini`) on **web** and **celery** services in `docker-compose.yml` to use the real API; without it, the worker uses the **template** generator (still async).

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
| `OPENAI_API_KEY` | If set, calls OpenAI Chat Completions; otherwise template text |
| `OPENAI_MODEL` | Default `gpt-4o-mini` |

### Admin

```bash
python manage.py createsuperuser
```

Then open `/admin/` to inspect **CarePlan** rows and statuses.
