# fintech_assistant

Flask chatbot for PSID-based digital payment guidance backed by Supabase and Groq.

## Free Hosting Recommendation

For this codebase, the best free target is currently Render. The app is a long-running Flask service and is a better match for a Python web service than a serverless-only platform.

## Render Deployment

1. Create a new Web Service from this GitHub repository.
2. Use branch `main`.
3. Environment: `Python`.
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

- `/health` checks Supabase connectivity.
- `/healthz` is a lightweight liveness endpoint for the host platform.
- Heavy ML dependencies are lazy-loaded so the app can boot before embedding or fallback-model code is needed.
