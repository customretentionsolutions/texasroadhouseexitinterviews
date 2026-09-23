# Client Portal

Password-protected, client-facing view of exit interview responses,
pulled from SurveyMonkey. Currently configured for Texas Roadhouse
(two collectors, combined).

## What's here right now

- Login page (one shared password per client, set via environment variable)
- A dashboard that pulls responses from SurveyMonkey and shows them in a
  table, with a brand tab (only one brand configured so far)
- Responses are cached for 15 minutes per collector to avoid hitting
  SurveyMonkey's API on every page load

Filtering, sorting, and charts are not built yet — this is the
skeleton to build on top of.

## Local setup

1. Install dependencies:
   ```
   pip install -r requirements.txt
   ```
2. Copy `.env.example` to `.env` and fill in:
   - `SURVEYMONKEY_API_TOKEN` — your read-only API token
   - `CLIENT_TEXAS_ROADHOUSE_PASSWORD` — whatever password you want the client to use
   - `FLASK_SECRET_KEY` — any long random string
3. Load the `.env` file into your environment, then run:
   ```
   python app.py
   ```
4. Visit http://localhost:5000 and log in with the password you set.

## Adding a new brand for this client

Edit `config.py` and add a new entry under `texas-roadhouse` → `brands`
with that brand's collector IDs. No other code changes needed — it'll
show up automatically as a new tab.

## Adding a new client entirely

Add a new top-level entry in `config.py`'s `CLIENTS` dict, with its own
`password_env` name and its own `brands`. Then set that new environment
variable (locally in `.env`, and in Render's dashboard once deployed).

## Deploying to Render

1. Push this project to a GitHub repo.
2. In Render, create a new Web Service pointing at that repo.
3. Build command: `pip install -r requirements.txt`
4. Start command: `gunicorn app:app`
5. Add environment variables in Render's dashboard (same names as `.env.example`).
