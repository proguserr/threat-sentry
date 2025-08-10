
# Who am I?

A production-leaning demo of a scalable, event-driven backend for real-time threat detection.
It ingests security logs via an HTTP API, processes them through a pluggable detection pipeline (rule-based + LLM), emits alerts, and exposes Prometheus metrics for observability.

Engineered a real-time analytics engine with FastAPI and Kafka (Redpanda) for event streaming, demonstrating expertise in high-throughput backend systems.

Designed a pluggable detection pipeline with both rule-based logic and a stub LLM function, showcasing an extensible architecture for AI integration.Instrumented the system with a Prometheus Client for custom metrics and observability, enabling monitoring of key performance indicators like processing latency.This portfolio project was designed to showcase expertise in backend, streaming, and observability with AI integration.

---

## Highlights
- **FastAPI** backend with **async ingestion** and a background worker
- **Pluggable detectors** (signature/rule-based + LLM -> you can wire to OpenAI, Claude, or local LLMs)
- **Alert routing hooks** (stdout + Slack webhook)
- **Prometheus metrics** at `/metrics`: event throughput, processing latency, alerts count, error count
- Clean, minimal codebase you can extend (Kafka, PostgreSQL, LangGraph, etc.)

---

## Quickstart

### 1) Setup
```bash
python -m venv .venv && source .venv/bin/activate  # on Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### 2) Configure LLM + Slack
Create `.env` file (or export env vars directly):
```
OPENAI_API_KEY=sk-...
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/XXX/YYY/ZZZ
LLM_ENABLED=false
```

### 3) Run
```bash
uvicorn app:app --reload
```

### 4) Send test events
```bash
curl -X POST http://localhost:8000/ingest -H "Content-Type: application/json" -d '{
  "timestamp": "2025-08-09T12:00:00Z",
  "source": "web-firewall",
  "ip": "203.0.113.5",
  "message": "Multiple failed logins detected; possible brute force"
}'
```

### 5) Metrics
Open http://localhost:8000/metrics to see Prometheus metrics.

---

## Project Structure
```
.
├── app.py               # FastAPI app, routes, background worker, metrics
├── detectors.py         # RuleBasedDetector + LLMDetector (stub)
├── models.py            # Pydantic models for LogEvent and Alert
├── requirements.txt
├── .env.example
└── README.md
```

---

## Roadmap 
- Swap in **Kafka** for the in-memory queue
- Add **PostgreSQL** for alert persistence + simple dashboard
- Implement **rate limiting** (token bucket) on `/ingest`
- Replace LLM stub with real **RAG** (vector DB + embeddings) for context-aware detection
- Add **Grafana** dashboard JSON with panels: QPS, p95 latency, alerts/min, error rate

---

## License
MIT — you can use this for your portfolio or anything useful.


---

## Enable Real LLM Detection

Set these env vars (supports LLM-compatible endpoints):  

```bash
export LLM_ENABLED=true
export OPENAI_API_KEY=sk-...          # required for live calls
export OPENAI_MODEL=gpt-4o-mini       # or any chat-completions model
# optional if you use a compatible gateway:
# export OPENAI_BASE_URL=https://api.openai.com/v1
```

Run the app and send events as usual. 

For exploration; you can keep it easy by using a stub version by using a keyword-based stub so the service keeps running. 

for contributions : use any LLM API and extend as you like! 
---

## Kafka 

This service can consume events from Kafka (Redpanda). A minimal local setup is included in `docker-compose.yml`.

Start Redpanda:
```bash
docker compose up -d redpanda
export KAFKA_BROKERS=localhost:9092
export KAFKA_TOPIC=security-events
```

Send a sample message into Kafka:
```bash
python kafka_producer.py
# the running app will consume it and process normally
```

#Thanks for checking it out :) 
