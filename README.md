# Telehealth Encounter Documentation Agent

> **Domain:** Clinical Decision Support & Biomedical Computing
> **Reference Guidelines & Standards:** `Standard Clinical Formulations & ISO/IEC Quality Frameworks`

<div align="center">

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
![Python](https://img.shields.io/badge/Python-3.10%20%7C%203.11%20%7C%203.12-3776AB.svg?logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.111-009688.svg?logo=fastapi&logoColor=white)
![Audit Trail](https://img.shields.io/badge/Audit-HMAC--SHA256_Tamper--Evident-brightgreen.svg)
![Zero-PHI Guard](https://img.shields.io/badge/Guard-Zero--PHI_Outbound-blue.svg)
![Docker](https://img.shields.io/badge/Docker-Ready-2496ED.svg?logo=docker&logoColor=white)

</div>

---

## 📖 What It Does

Telehealth Encounter Documentation Agent is an enterprise-grade multi-worker evaluation platform that processes task payloads through specialized analytical workers, produces consensus dossiers with cryptographic audit trails, and enforces zero-PHI outbound data protection.

---

## ⚙️ Key Capabilities & Algorithmic Modules

- **Deterministic Calculation Engine**: Strict compliance with standard reference formulations and thresholds.
- **Risk & Urgency Classification**: Multi-tier categorization with automated clinical/operational action recommendations.
- **Validation & Guardrails**: Rigorous input bounds checking and anomaly detection.
- **Multi-Worker Architecture**: InvariantQCWorker, SafetyEscalationWorker, and ProtocolConformanceWorker for comprehensive evaluation.
- **FastAPI REST API**: OpenAPI 3.1 endpoints for task processing and audit log retrieval.
- **Prometheus Telemetry**: Operational metrics export at `/metrics`.

---

## 💻 CLI Quickstart & Usage

### 1. Run Single Task Evaluation
```bash
python cli.py audit --task-id TASK-001 --target KEY-01 --primary 28.5 --secondary 14.2 --critical --status DISCORDANT
```

### 2. Supervisory Chat Query
```bash
python cli.py chat "What is the system status?"
```

### 3. Batch Process CSV Records
```bash
python cli.py batch -i sample.csv -o results.csv
```

### 4. Verify Audit Trail Integrity
```bash
python cli.py verify-audit
```

### 5. Launch FastAPI REST Server
```bash
python cli.py serve --host 127.0.0.1 --port 8000
```

### Parameter Reference
- `--task-id`: Unique task/case identifier (required)
- `--target`: Target entity identifier (required)
- `--primary`: Primary measurement value (float, required)
- `--secondary`: Secondary measurement value (float, optional)
- `--critical`: Emergency escalation flag (optional)
- `--status`: Status descriptor string (optional)

### Input Data Schema

| Field | Description | Requirement |
|:------|:------------|:------------|
| `task_id` | Unique task identifier | Required |
| `target_identifier` | Target entity identifier | Required |
| `primary_metric` | Primary measurement value | Required |
| `secondary_metric` | Secondary measurement value | Optional |
| `is_critical_flag` | Emergency escalation flag | Optional |
| `status_descriptor` | Status descriptor string | Optional |

---

## 🛡️ Security & Enterprise Architecture

* **Zero-PHI Outbound Interceptor:** Active regex inspection blocking SSNs, MRNs, phone numbers, and patient identifiers.
* **Tamper-Evident HMAC-SHA256 Audit Trail:** Chained, cryptographically signed logs for every evaluation and state transition.
* **Input Validation:** Bounds checking on all input fields with configurable length limits.
* **Secure Defaults:** Ephemeral cryptographic keys generated at runtime if `AUDIT_SECRET_KEY` is not set.

### Environment Variables

| Variable | Description | Default |
|:---------|:------------|:--------|
| `AUDIT_SECRET_KEY` | Secret key for HMAC-SHA256 audit trail signing | Ephemeral (random per session) |
| `MODEL_PROVIDER` | LLM provider selection (`mock`, `ollama`, `claude`, `openai`) | `mock` |

> **Production Note:** Always set `AUDIT_SECRET_KEY` to a persistent, securely generated value. Without it, audit trail integrity cannot be verified across restarts.

---

## 🧪 Testing & Verification

Run the automated test suite:

```bash
pytest -v
```

Execute high-throughput batch simulation benchmarks:

```bash
python simulator.py 1000
```

---

## 🐳 Container Deployment

### Docker
```bash
docker build -t telehealth-encounter-documentation-agent .
docker run -p 8000:8000 -e AUDIT_SECRET_KEY=your-secure-key telehealth-encounter-documentation-agent
```

### Docker Compose
```bash
AUDIT_SECRET_KEY=your-secure-key docker-compose up -d
```

---

## 📁 Project Structure

```
telehealth-encounter-documentation-agent/
├── agents/                      # Core multi-worker evaluation engine
│   ├── __init__.py
│   ├── api.py                   # FastAPI REST endpoints
│   ├── base.py                  # Security guards, audit trail, PHI protection
│   ├── learning.py              # Bayesian calibration engine
│   ├── llm_factory.py           # LLM provider factory
│   ├── metrics.py               # Prometheus metrics collector
│   ├── models.py                # Pydantic data models
│   ├── streamer.py              # WebSocket telemetry broadcaster
│   ├── supervisor.py            # Master orchestrator
│   └── workers.py               # Specialized evaluation workers
├── telehealth_audit/            # CMS billing compliance module
│   ├── __init__.py
│   ├── agents.py                # Specialized audit agents
│   ├── cli.py                   # CLI for audit module
│   ├── engine.py                # Domain evaluation engine
│   ├── models.py                # Data models
│   └── server.py                # FastAPI server factory
├── tests/                       # Automated test suite
│   ├── test_enrichment.py
│   ├── test_telehealth_audit.py
│   └── test_telehealth_encounter_documentation_agent.py
├── web/                         # Operations console (HTML/JS)
├── cli.py                       # Main CLI entry point
├── simulator.py                 # High-throughput simulation
├── enrichment.py                # Feature enrichment engines
├── sample.csv                   # Sample batch input
├── sample_payload.json          # Sample API payload
├── benchmark_dataset.json       # Benchmark test cases
├── pyproject.toml               # Project configuration
├── Dockerfile                   # Container build
├── docker-compose.yml           # Container orchestration
└── openapi_spec.json            # OpenAPI specification
```

---

## 📄 License

MIT License. See [LICENSE](LICENSE) for details.
