# Backend

## Local run

`powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn app.main:app --reload`

Health check:

http://localhost:8000/health

## Hosted judge runtime

For a hosted backend-root deployment:

```powershell
python -m uvicorn hosted_runtime:app --host 0.0.0.0 --port $PORT
```

Hosted routes:

- `GET /health`
- `GET /mission-control-status`

The hosted entrypoint starts the existing autonomous Band listener in the
background and serves only the sanitized Mission Control status JSON. Deployment
variables are documented with placeholders in
`../docs/hosted-judge-runtime.md`.
