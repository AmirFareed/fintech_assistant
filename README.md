# fintech_assistant

Flask chatbot for PSID-based digital payment guidance backed by Supabase and Groq.

## Free Hosting Recommendation

For this codebase, the best free target is currently Render. The app is a long-running Flask service and is a better match for a Python web service than a serverless-only platform.

## Render Deployment

This repo now includes [render.yaml](/c:/Users/cs001/Downloads/fintech_assistant/render.yaml), so you can deploy it in either of these ways:

1. Recommended: in Render, click `New` -> `Blueprint`, connect this GitHub repo, and let Render read `render.yaml`.
2. Manual: create a `Web Service` from this GitHub repository and use the settings below.

Manual settings:

1. Branch: `main`
2. Environment: `Python`
3. Build command:
   `pip install -r requirements.txt`
4. Start command:
   `gunicorn --bind 0.0.0.0:$PORT app:app`
5. Health check path:
   `/healthz`
6. Add environment variables:
   `SECRET_KEY`
   `SUPABASE_URL`
   `SUPABASE_KEY`
   `SUPABASE_BUCKET`
   `SUPABASE_TIMEOUT_SECONDS`
   `ADMIN_USERNAME`
   `ADMIN_PASSWORD`
   `GROQ_API_KEY`
   `GROQ_MODEL`
   `LLM_PROVIDER`
   `QEHWA_MODEL_ID`
   `QEHWA_DEVICE`
   `QEHWA_MAX_NEW_TOKENS`
   `QEHWA_TEMPERATURE`
   `WIDGET_ALLOWED_ORIGINS`

## Notes

- For Render free tier, set `LLM_PROVIDER=groq` and provide `GROQ_API_KEY`. The local `qehwa` fallback is too heavy for a free 512 MB instance.
- The `uploads/` folder is local filesystem storage. Render free web services do not persist local files across restarts or redeploys, so uploaded source files should be treated as temporary.
- `/health` checks Supabase connectivity.
- `/healthz` is a lightweight liveness endpoint for the host platform.
- Heavy ML dependencies are lazy-loaded so the app can boot before embedding or fallback-model code is needed.
