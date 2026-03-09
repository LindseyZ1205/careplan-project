## CarePlan MVP (Django + Docker)

This is a minimal end‑to‑end MVP to:

- show a very simple **HTML front‑end form**
- send data to a **synchronous Django view**
- generate a basic **care plan text** (placeholder for an LLM)
- keep submitted care plans in **memory only** (Python list), no database modelling yet

No validation rules, warnings, error design, queues, WebSockets or background workers are implemented here on purpose.

### How to run (Docker, recommended)

From the `careplan` directory:

```bash
docker compose build
docker compose up
```

Then open `http://localhost:8000` in your browser.

### Development (without Docker)

You can also run it locally if you have Python and Django installed:

```bash
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```

Then visit `http://127.0.0.1:8000/`.

### Where the main flow lives

- `core/views.py`:
  - `careplan_form` – renders the HTML page, synchronously generates the care plan when you submit the form.
  - `_generate_careplan_text` – a very small function that now just templates text; later you can swap this to call a real LLM.
- `core/templates/core/index.html`:
  - Simple modern‑looking form + output area.

All state is stored in an in‑memory list `_CAREPLANS` inside `core/views.py`. When you restart the server or container, the data is reset.

