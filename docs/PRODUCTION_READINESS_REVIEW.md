# Production Readiness Review — Flow (200+ users)

_Reviewer: GitHub Copilot · Date: 6 May 2026_

**Overall verdict: NOT production-ready for 200+ active users as currently
configured.** The product works, but several blockers around concurrency,
secrets, and persistence will surface as soon as you scale beyond a handful
of testers. Most issues are fixable in a single sprint.

Items are grouped by severity.

---

## 🔴 BLOCKERS — must fix before onboarding 200 users

### 1. Flask dev server in production
[api_server.py](../api_server.py#L1904) ends with:
```python
app.run(host='0.0.0.0', port=5001, debug=True)
```
- `debug=True` exposes the **Werkzeug debugger** (RCE if PIN leaks) and disables threading guarantees.
- Werkzeug is single-threaded by default and explicitly **not for production** (Flask warns this on every start).
- The systemd unit [deploy/aliran-whatsapp.service](../deploy/aliran-whatsapp.service) uses `flask run` — same problem.

**Fix:** run both apps under **gunicorn** (or uvicorn+ASGI wrapper). Example:
```ini
ExecStart=/opt/aliran-tunai/current/venv/bin/gunicorn \
  --workers 4 --threads 8 --timeout 60 \
  --bind 127.0.0.1:5001 api_server:app
```
For the WhatsApp webhook, use 2–4 workers max (see #2 about shared state).

### 2. In-memory state breaks under multiple workers
[whatsapp_business_api.py](../whatsapp_business_api.py) holds three global dicts:
- `pending_transactions = {}` (line 1092)
- `pending_registrations = {}` (line 1243)
- `pending_resets = {}` (line 2303)

Plus `request_counts = defaultdict(list)` in [api_server.py](../api_server.py#L59) for rate limiting.

The moment you run **>1 worker** or scale to a second instance, half the
user replies will land on a worker that has no memory of the pending state —
registration loops will break, clarification flows will lose context, and
rate limits will be silently bypassed.

**Fix:** move all of this to **Redis** (TTL keys are perfect:
`pending:tx:{wa_id}`, `pending:reg:{wa_id}`, `ratelimit:{ip}`). Redis is
also already needed for #4.

### 3. Default JWT secret
[api_server.py](../api_server.py#L160):
```python
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "your-secret-key-change-in-production")
```
If `JWT_SECRET_KEY` is missing in `.env`, **anyone can forge tokens for any
user**. The fallback must be removed and the process must refuse to start
without it.

**Fix:**
```python
JWT_SECRET_KEY = os.environ["JWT_SECRET_KEY"]  # KeyError on boot if missing
if len(JWT_SECRET_KEY) < 32:
    raise RuntimeError("JWT_SECRET_KEY must be ≥32 chars")
```

### 4. Rate limiter is per-process and unbounded memory
[api_server.py](../api_server.py#L59) keeps every IP's request timestamps in
a process-local `defaultdict`. With multiple workers, the limit becomes
`200 × N workers`. The dict also never evicts inactive IPs → slow memory leak.

**Fix:** use `flask-limiter` with a Redis backend, or `nginx`'s `limit_req`
zone (simpler and zero code). Also drop the limit for `/api/auth/*` to
~5/min/phone (currently 20/min/IP — a single IP can brute-force OTPs across
many phones).

### 5. Auth-endpoint rate limit is a no-op bug
The auth tightening at [api_server.py](../api_server.py#L103) sets
`rate_limit = 20` but then calls `check_rate_limit(client_ip)` which always
uses the global 200 — **the local `rate_limit` variable is unused**. OTP
brute-force protection is currently disabled.

### 6. Receipts stored as base64 inside transaction documents
[whatsapp_business_api.py](../whatsapp_business_api.py#L2912) embeds full
base64 receipt images directly in the `entries` document. With 200 users
averaging 5 receipts/day at 200 KB each:
- ~200 MB/day of inflated documents.
- MongoDB's **16 MB document limit** is one large receipt away.
- Every dashboard query that returns transactions will pull megabytes per
  request → slow API + huge egress costs.

**Fix:** store images in **S3 / Cloudflare R2** and keep only the URL + hash
in MongoDB. Use GridFS only as a stopgap.

---

## 🟠 HIGH — fix in the first month

### 7. No connection pooling tuning + ad-hoc reconnects
Both Flask apps share a single `MongoClient` per process and call
`connect_to_mongodb()` on cache misses. Under concurrent load you'll see
"MongoClient not available" race conditions. Set explicit pool sizes:
```python
MongoClient(MONGO_URI, maxPoolSize=50, minPoolSize=5, retryWrites=True)
```
and stop reassigning the global on every miss — let pymongo's built-in
reconnect handle it.

### 8. CORS allows credentials with hard-coded origins
[api_server.py](../api_server.py#L33) allows `http://localhost:5173` and
`:3000` with `supports_credentials=True`. This is fine in dev but should be
**stripped from production builds**. Drive the origin list from env:
`CORS_ALLOWED_ORIGINS`.

### 9. Verbose logging of full headers and request bodies
[api_server.py](../api_server.py#L120) logs `dict(request.headers)` for
every `/api/*` and `/whatsapp/*` call → logs the
`Authorization: Bearer <jwt>` and any cookies. JWTs in logs = session theft
if logs leak.

**Fix:** redact `Authorization`, `Cookie`, and never log full headers in
production.

### 10. Threading in WhatsApp handler
`schedule_background_transaction_processing` and
`schedule_background_ai_processing` spawn a `threading.Thread(daemon=True)`
per inbound message. Under burst load (200 users × multiple messages):
- Unbounded threads can exhaust the OS limit.
- All threads share the GIL — OpenAI/network calls are I/O-bound so this
  *mostly* works, but errors swallow silently because they're daemon
  threads with no monitoring.

**Fix:** use a bounded `ThreadPoolExecutor(max_workers=20)` module-level,
or move to Celery / RQ / Dramatiq with Redis as broker. This also enables
retries on OpenAI/Mongo failures.

### 11. OTP storage and reuse window
OTPs are stored in `db.otp_codes` but there's no (a) TTL index or (b)
**rate limit per phone number**. A determined attacker can request unlimited
OTPs.

**Fix:**
- Add MongoDB TTL: `otp_collection.create_index('expires_at', expireAfterSeconds=0)`.
- Cap to **1 OTP / 60s** and **5 OTPs / hour** per phone.
- Cap **5 verification attempts per OTP**, then invalidate.

### 12. No request size limits
Flask's default body limit is unlimited. Someone can POST a 1 GB JSON to
`/api/transactions`. Add:
```python
app.config['MAX_CONTENT_LENGTH'] = 4 * 1024 * 1024  # 4 MB
```

### 13. No HTTPS / HSTS enforcement at the app layer
[nginx-aliran-tunai.conf](../nginx-aliran-tunai.conf) should:
- Redirect HTTP → HTTPS.
- Send `Strict-Transport-Security`, `X-Content-Type-Options: nosniff`,
  `X-Frame-Options: DENY`, `Referrer-Policy: same-origin`.
- Use `limit_req_zone` for `/api/auth/*` (e.g. 10 r/m).

### 14. No retries / circuit breaker for OpenAI
Every receipt photo and "smart parse" hits OpenAI. At 200 users the API
will rate-limit you (org TPM/RPM). There's no backoff or fallback path —
the user just gets silence because the work is in a daemon thread.

**Fix:** wrap with `tenacity` retries + exponential backoff, and on
persistent failure send the user "I couldn't process this, please type it
manually" via WhatsApp.

---

## 🟡 MEDIUM — important for a clean operation

### 15. Schema/index review
For 200 users × ~50 transactions/month = ~10k docs/month. Quick wins:
- Compound index `{wa_id: 1, timestamp: -1}` on `entries`.
- Index `{phone_number: 1}` on `users`.
- TTL on `otp_codes` (see #11).
- TTL on `pending_resets` keys in Redis after migration.

### 16. Mock data leaks in production responses
[api_server.py](../api_server.py) `get_mock_ccc_data()` is invoked when
Mongo is down and returns made-up numbers with `'mock_data': True`. The
frontend doesn't appear to check that flag — users will see fake
"RM 15,000 in sales". Either remove the mock or have the frontend surface
a clear "data unavailable" banner.

### 17. PM2 vs systemd duplication
You ship both [ecosystem.config.js](../ecosystem.config.js) (with a
hard-coded `cwd: '/Users/abuhuzaifahbidin/...'` — that path won't exist on
EC2) and three systemd units. Pick one. systemd is simpler for a single VM;
PM2 is fine if you also use it for the frontend.

### 18. No structured logging / observability
- Logs go to stdout via `logging.basicConfig` only.
- No correlation IDs (incoming WhatsApp message → AI call → DB save).
- No metrics (request rate, OpenAI latency, Mongo errors).

**Minimum:** add `gunicorn --access-logformat`, ship logs to CloudWatch /
Loki, and add `/metrics` with `prometheus_client` for at least: request
count, error count, OpenAI call latency, Mongo op latency.

### 19. No alerting / uptime monitoring
[scripts/health_check.py](../scripts/health_check.py) is a one-shot script.
You need a continuous monitor — UptimeRobot, BetterStack, or
`node_exporter` + Alertmanager — for `/api/health`, `/whatsapp/webhook`
GET, and Mongo ping.

### 20. No data backups
MongoDB Atlas has automated backups on the M10+ tier. Confirm your cluster
tier supports continuous backup; on M0/M2/M5 you must script a daily
`mongodump` to S3.

### 21. No DB migrations / schema doc
You're using a schemaless DB but still have implicit schemas (`wa_id`,
`chat_id`, `action`, `terms`...). Document them in a `schemas.md` or use
`pydantic` models so the bot, API, and dashboard agree.

---

## 🟢 LOW — nice to have

- Run `pytest --cov` — coverage is unknown; aim for ≥70% on
  `api_server.py` and `whatsapp_business_api.py`.
- Add **CI** (GitHub Actions) that runs `pytest`, `npm run lint`, and a
  Docker build on every PR.
- Containerise (`Dockerfile` + `docker-compose.yml`) — simplifies
  onboarding and deployment.
- Pin `requirements.txt` with `pip-compile` and add a
  `requirements-dev.txt`.
- Add `frontend/.env.example`.
- Replace `Flask-CORS` with explicit origin headers (smaller surface).
- Use `python-multipart` size validation for receipt uploads.
- Add `pytest-asyncio` config — tests already import it but no markers are
  set.
- Internationalise the dashboard the way the bot already is (currently
  dashboard is English-only).

---

## Capacity estimate (back-of-envelope)

For **200 daily-active users**, expect:

| Metric                       | Average  | Peak     |
| ---------------------------- | -------- | -------- |
| Inbound WhatsApp messages/day | ~2 000   | ~5 RPS   |
| Receipt photos/day            | ~500     | —        |
| OpenAI Vision spend/day       | ~$5–$10  | —        |
| Dashboard API calls/day       | ~10 000  | ~10 RPS  |

A **single t3.small EC2** (2 vCPU / 2 GB) running gunicorn (4 workers each)
+ Redis + Nginx will handle this comfortably **once the blockers above are
fixed**. MongoDB Atlas M10 is sufficient.

---

## Suggested fix order (1–2 weeks of work)

| Day | Task                                                                      |
| --- | ------------------------------------------------------------------------- |
| 1   | Remove default JWT secret; fix auth rate-limit bug (#3, #5).              |
| 2   | Switch both services to gunicorn; add `MAX_CONTENT_LENGTH` (#1, #12).     |
| 3–4 | Stand up Redis; migrate pending dicts + rate limiter (#2, #4).            |
| 5   | Move receipt images to S3 (#6).                                           |
| 6   | OTP TTL index + per-phone caps + retries on OpenAI (#11, #14).            |
| 7   | Header/JWT redaction in logs; HSTS + nginx security headers (#9, #13).    |
| 8   | Add Mongo indexes; remove mock data from prod path (#15, #16).            |
| 9   | Replace `threading.Thread` with bounded executor (#10).                   |
| 10  | Add Prometheus metrics + UptimeRobot alerts; backups verified (#18–20).   |

Once those are done, you can confidently onboard 200+ users and have a
clear path to scale to 2 000+ by adding a second instance behind a load
balancer (because state will live in Redis + Mongo, not in process memory).

---

## Quick checklist

### Blockers
- [ ] #1  Replace `app.run(debug=True)` and `flask run` with gunicorn
- [ ] #2  Move pending dicts to Redis
- [ ] #3  Remove default `JWT_SECRET_KEY` fallback
- [ ] #4  Replace in-memory rate limiter with Redis or nginx
- [ ] #5  Fix unused `rate_limit` variable on `/api/auth/*`
- [ ] #6  Move receipt images out of MongoDB documents

### High
- [ ] #7  Tune `MongoClient` pool sizes; stop reassigning globals
- [ ] #8  CORS origins from env; remove localhost in prod
- [ ] #9  Redact `Authorization` / `Cookie` from logs
- [ ] #10 Bounded `ThreadPoolExecutor` (or task queue)
- [ ] #11 OTP TTL index + per-phone caps + verify-attempt cap
- [ ] #12 `MAX_CONTENT_LENGTH` on both Flask apps
- [ ] #13 HTTPS redirect + security headers in nginx
- [ ] #14 OpenAI retries + user-facing failure path

### Medium / Low
- [ ] #15 Mongo indexes + TTLs
- [ ] #16 Remove mock CCC data from prod responses
- [ ] #17 Pick one of PM2 / systemd; fix hard-coded `cwd`
- [ ] #18 Structured logs + `/metrics`
- [ ] #19 Continuous uptime monitoring + alerts
- [ ] #20 Verify Atlas backup tier or add `mongodump` cron
- [ ] #21 Document schemas / add pydantic models
- [ ] CI pipeline, Dockerfile, dashboard i18n, etc.
