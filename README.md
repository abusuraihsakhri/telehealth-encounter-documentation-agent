# Telehealth Encounter Documentation Agent

A Python rule-evaluation demonstration with a REST API, CLI, HMAC-chained in-memory audit records, and an optional static browser interface.

**Scope:** Despite the repository name and earlier module labels, the implemented logic evaluates synthetic numeric measurements and status keywords. It does **not** structure clinical encounter notes, validate CMS telehealth claims, check provider licensure, establish clinical safety, or perform clinical decision support. The thresholds (primary >25, secondary >12 in the main implementation; different thresholds in the legacy module) are illustrative only.

## Try the browser interface

Open [web/index.html](web/index.html) locally to use the entirely client-side demonstration. It mirrors the primary worker trigger logic, labels its output as a preview, and **does not** create HMAC signatures. It needs no build step, Python runtime, Pyodide, or network requests when opened as a local file.

GitHub Pages deployment is defined in [pages.yml](.github/workflows/pages.yml). If the site is not yet enabled, the repository administrator must choose **Settings → Pages → Build and deployment → GitHub Actions**. Do not assume the site is live until its deployment and URL are verified.

## Python CLI and API

Python 3.10 or later:

```bash
python -m pip install -e ".[api]"
python cli.py audit --task-id DEMO-001 --target SYNTHETIC-01 --primary 29.4 --secondary 14.8
python cli.py batch -i sample.csv -o results.csv
python cli.py verify-audit
python cli.py serve --host 127.0.0.1 --port 8000
```

The source-checkout API serves the same console at http://127.0.0.1:8000/ and exposes:

| Route | Function |
|---|---|
| GET `/health` | Service status |
| POST `/api/audit` | Run the main deterministic workers and record an in-memory signed audit entry |
| POST `/api/chat` | Return a mock supervisor response |
| GET `/api/audit/logs` | Inspect the in-process audit chain and check HMAC signatures |
| GET `/metrics` | Return JSON counts for the current process (not Prometheus exposition) |

The installable console script `telehealth-encounter-documentation-engine` runs the **separate legacy** `telehealth_audit` CLI, whereas `python cli.py` runs the main multi-worker implementation. Both paths remain available for compatibility. The legacy workflow uses different thresholds; their outputs are not interchangeable.

## Tests

```bash
python -m pip install -e ".[api,test]"
python -m pytest -q
python -m compileall -q agents telehealth_audit cli.py enrichment.py simulator.py
node --check web/app.js
```

GitHub Actions tests Python 3.10, 3.11, and 3.12, as well as browser-script syntax.

## Data protection and limitations

- **Only synthetic inputs.** PHI detection uses regular expressions and cannot reliably identify or de-identify all protected health information. It is not HIPAA compliance certification.
- **No authentication.** The development API is not suitable for exposure on the public internet or use with real patient data.
- **Browser demo:** When opened from a file or GitHub Pages, the local preview runs in browser memory without sending task data to a server. It does not persist records or compute HMACs.
- **Backend:** Evaluation results and audit entries reside in process memory. `/api/audit/logs` reports a signed chain, but the ledger is neither durable nor externally anchored. Restarting loses the records, even if the signing key is persistent.
- **Audit secrets:** Set a strong, stable `AUDIT_SECRET_KEY` for long-lived server sessions; otherwise an ephemeral key is generated. The Docker Compose configuration refuses to start without this variable. Never put it in client code, Pages, or source control.
- **Rule validity:** Demonstration thresholds and alerts must not guide medical, regulatory, billing, or patient-safety decisions.

## Docker

```bash
export AUDIT_SECRET_KEY="$(python -c 'import secrets; print(secrets.token_urlsafe(48))')"
docker compose up --build
```

The development service listens on port 8000. Do not publish it to an untrusted network without implementing authentication, transport protection, data retention controls, and appropriate clinical validation.

## Technology and compatibility

Python, Pydantic 2, FastAPI, Uvicorn, HTML, CSS, and vanilla JavaScript. The static browser demo uses modern standard browser APIs and requires no third-party JavaScript dependency. Server mode requires a running FastAPI process; GitHub Pages cannot host that process.

## License

[MIT](LICENSE).
