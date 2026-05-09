# EDLP | Inteligencia de Tienda

Dash dashboard for club-store catalog benchmarking (analytics, gap analysis).

## Run locally

```bash
cd dashboard
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r ../requirements.txt
python app.py
```

Open `http://127.0.0.1:8051`.

## Data

- Primary: `Submission/master_data.xlsx` (included for deployment).
- Fallback: `data/master_categorized_corrected.csv` if Excel is missing.

Override path with env var `CLUB_STORES_MASTER_DATA`.

## Deploy (Render.com)

1. Connect this GitHub repo to a **Web Service**.
2. **Build command:** `pip install -r requirements.txt`
3. **Start command:** use the `Procfile` (or equivalent `gunicorn` command).
4. Optional env: `CLUB_STORES_MASTER_DATA` if the workbook lives outside the repo.

Tab icon: `dashboard/assets/edlp-logo.png`.
