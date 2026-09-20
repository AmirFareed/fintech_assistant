# Deploying: backend on Oracle Cloud, frontend on Render

```
Browser ──► Render (static frontend)
   │
   └──HTTPS──► Caddy on the Oracle VM ──► backend container ──► PostgreSQL + pgvector container
              (chat.<ip>.sslip.io)         (127.0.0.1:8001)       (no public port)
```

The browser loads the frontend from Render and calls the backend directly, so the backend must be
served over **HTTPS** (browsers block http calls from an https page) and must allow the Render origin (CORS).

## 1. Oracle VM (Ubuntu, Ampere A1 works fine)

**Open the ports.** Ingress TCP **80** and **443** from `0.0.0.0/0` in the VCN security list (or NSG). Ubuntu
images on OCI also ship iptables rules that block them, so on the VM:

```bash
sudo iptables -I INPUT 6 -m state --state NEW -p tcp --dport 80  -j ACCEPT
sudo iptables -I INPUT 6 -m state --state NEW -p tcp --dport 443 -j ACCEPT
sudo netfilter-persistent save
```

Do **not** open 5432 or 8001; the database has no published port and the backend only listens on localhost.

**Install Docker** and log out/in:

```bash
curl -fsSL https://get.docker.com | sudo sh
sudo usermod -aG docker $USER
```

## 2. Configure and start the stack

```bash
git clone https://github.com/AmirFareed/fintech_assistant.git ~/fintech-assistant
cd ~/fintech-assistant

# Root .env: used by docker compose for variable substitution
echo "POSTGRES_PASSWORD=$(openssl rand -hex 24)" > .env

# App settings
cp backend/.env.example backend/.env
nano backend/.env
```

Set at least these in `backend/.env` (`DATABASE_URL` is supplied by the compose file, leave it out):

| Variable | Value |
| --- | --- |
| `SECRET_KEY` | `openssl rand -hex 32` (signs admin tokens; changing it logs admins out) |
| `ADMIN_USERNAME` / `ADMIN_PASSWORD` | your own, strong password |
| `GROQ_API_KEY`, `LLM_PROVIDER=groq` | your Groq key |
| `ENABLE_VECTOR_RETRIEVAL` | `true` (the VM has the memory for it) |
| `WIDGET_ALLOWED_ORIGINS` | your Render URL, e.g. `https://fintech-assistant-frontend.onrender.com` (comma-separate several; no trailing slash) |

Start it and load the knowledge base once:

```bash
docker compose -f docker-compose.prod.yml up -d --build
docker compose -f docker-compose.prod.yml exec backend python -m scripts.reset_and_setup_fintech
docker compose -f docker-compose.prod.yml exec backend python -m scripts.ingest_fintech
```

`reset_and_setup_fintech` **wipes the knowledge base**, so run it only for the first load. The first
ingest downloads the embedding model (a few hundred MB, cached in the `hf_cache` volume).

Check it locally on the VM: `curl localhost:8001/health` should return `"database":"ok"`.

## 3. HTTPS with Caddy

Install Caddy (<https://caddyserver.com/docs/install#debian-ubuntu-raspbian>). With no domain, use a free
`sslip.io` hostname built from the VM's public IP with dashes, e.g. IP `1.2.3.4` becomes `chat.1-2-3-4.sslip.io`.
In `/etc/caddy/Caddyfile`:

```caddy
chat.1-2-3-4.sslip.io {
    reverse_proxy 127.0.0.1:8001
}
```

```bash
sudo systemctl reload caddy
curl https://chat.1-2-3-4.sslip.io/healthz     # from your own machine
```

Caddy fetches and renews the Let's Encrypt certificate by itself (ports 80/443 must be reachable). If the VM
already runs another app behind Caddy, just add this as a second site block.

## 4. Frontend on Render

1. Render dashboard → **New → Blueprint**, pick this repo (it reads `render.yaml`). Or create a **Static Site** by hand:
   root directory `frontend`, build command `sh ./render-build.sh`, publish directory `.`.
2. Set the environment variable **`API_BASE_URL`** to the backend's HTTPS URL, no trailing slash
   (`https://chat.1-2-3-4.sslip.io`). The build writes it into `config.js` and fails if it is missing.
3. After the first deploy, take the Render URL and put it in `WIDGET_ALLOWED_ORIGINS` on the VM, then:
   `docker compose -f docker-compose.prod.yml up -d backend`

If the frontend loads but every call fails with a CORS error in the browser console, the origin in
`WIDGET_ALLOWED_ORIGINS` doesn't exactly match the Render URL (scheme + host, no path, no trailing slash).

## 5. Verify

- `https://<render-url>/` shows the chat and answers a question.
- `https://<render-url>/admin/login.html` accepts your admin credentials; Dashboard, Knowledge Base and Test Chatbot load.
- Upload a small `.txt` in Knowledge Base; it appears in the list and is searchable.

## Redeploying

Backend change:

```bash
cd ~/fintech-assistant && git pull && docker compose -f docker-compose.prod.yml up -d --build backend
```

Frontend change: push to the branch Render tracks; Render rebuilds automatically.

`backend/database/schema.sql` change: `docker compose -f docker-compose.prod.yml exec backend python -m scripts.init_db`
(safe to re-run; the compose file only applies the schema automatically when the database volume is first created).

## Backups

```bash
docker compose -f docker-compose.prod.yml exec -T db pg_dump -U fintech fintech | gzip > ~/backup-$(date +%F).sql.gz
```

Run it from cron and copy the file off the VM. Original uploaded files live in the `uploads` Docker volume.

## Notes

- Admin login is rate-limited (10/min per client IP) and the backend trusts `X-Forwarded-For` only when
  `TRUST_PROXY=true`, which the production compose file sets. Don't expose port 8001 publicly, or clients could spoof their IP.
- Render's free static hosting has no cold starts, but the backend on the VM must stay up: both containers use `restart: always`.
- Never commit `.env` files. Rotate `ADMIN_PASSWORD` and `SECRET_KEY` from any values used during development.
