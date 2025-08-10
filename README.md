
# About me

This project is basicaly a production-leaning demo of a scalable, event-driven backend for real-time threat detection. It ingests security logs over an HTTP API, streams them through Kafka, processes them in a detection pipeline, and sends out alerts. I’ve also instrumented it with Prometheus metrics so the system’s health and performance are always visible.

Designed it to handle high-throughput workloads. Kafka decouples ingestion from processing, letting each scale independently. The async architecture ensures low-latency detection without dropping messages, even under heavy load.

The detection pipeline is fully modular.Rules can be updated without redeploying, and the LLM component can be swapped or extended as needed. With Prometheus I tracked throughput, latency, and alert patterns in real time, making it easier to catch performance bottlenecks before they escalate.

While compact, the codebase uses patterns you’d find in production systems: streaming for scalability, loose coupling for reliability, and observability built in from the start.

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
```bash
For exploration; you can keep it easy by using a stub version by using a keyword-based stub so the service keeps running. 
For contributions : use any LLM API and extend as you like! 
---

## Kafka 

This service can consume events from Kafka. A minimal local setup is included in `docker-compose.yml`.

Start Kafka locally:
```bash
docker compose up -d kafka
export KAFKA_BROKERS=localhost:9092
export KAFKA_TOPIC=security-events
```
# Test

## Send a sample message into Kafka:
```bash
python kafka_producer.py
# the running app will consume it and process normally
```
## OR use Realtime Feeds 

AlienVault OTX: https://otx.alienvault.com/  
CIRCL’s AIL feed: https://www.circl.lu/services/misp-feed/


#### Thanks for checking it out :) 
