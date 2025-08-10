
import asyncio
import os
import time
from datetime import datetime

from fastapi import FastAPI, BackgroundTasks, HTTPException
from fastapi.responses import PlainTextResponse
from prometheus_client import Counter, Histogram, Gauge, generate_latest, CONTENT_TYPE_LATEST

from models import LogEvent, Alert
from detectors import RuleBasedDetector, LLMDetector, notify_slack
from kafka_stream import start_kafka_consumer

app = FastAPI(title="Realtime Threat Guardian", version="0.1.0")

# Prometheus metrics
INGEST_COUNTER = Counter("rtg_ingest_total", "Total ingested events")
PROCESSING_COUNTER = Counter("rtg_processed_total", "Total processed events")
ALERT_COUNTER = Counter("rtg_alerts_total", "Total alerts raised", labelnames=["detector", "severity"])
ERROR_COUNTER = Counter("rtg_errors_total", "Total processing errors" )
LATENCY_HIST = Histogram("rtg_process_latency_seconds", "Processing latency per event" )
QUEUE_GAUGE = Gauge("rtg_queue_depth", "In-memory queue depth" )

# In-memory queue & storage (swap with Kafka/DB later)
event_queue: asyncio.Queue[LogEvent] = asyncio.Queue(maxsize=10000)
recent_alerts: list[Alert] = []

rule_detector = RuleBasedDetector()
llm_detector = LLMDetector()

# Background task: consumer loop
async def worker_loop():
    while True:
        event = await event_queue.get()
        start = time.perf_counter()
        try:
            # Rule-based detector
            alert = rule_detector.evaluate(event)
            # LLM-based detector (async)
            if alert is None:
                alert = await llm_detector.evaluate(event)

            if alert:
                recent_alerts.append(alert)
                ALERT_COUNTER.labels(detector=alert.detector, severity=alert.severity).inc()
                await notify_slack(alert)

            PROCESSING_COUNTER.inc()
        except Exception:
            ERROR_COUNTER.inc()
        finally:
            LATENCY_HIST.observe(time.perf_counter() - start)
            QUEUE_GAUGE.set(event_queue.qsize())
            event_queue.task_done()

@app.on_event("startup")
async def startup_event():
    # launch worker
    app.state.worker_task = asyncio.create_task(worker_loop())
    # optional: launch Kafka consumer if configured
    app.state.kafka_task = await start_kafka_consumer(asyncio.get_running_loop(), event_queue)

@app.on_event("shutdown")
async def shutdown_event():
    task = getattr(app.state, "worker_task", None)
    if task:
        task.cancel()

@app.post("/ingest", status_code=202)
async def ingest(event: LogEvent, background: BackgroundTasks):
    try:
        event_queue.put_nowait(event)
        INGEST_COUNTER.inc()
        QUEUE_GAUGE.set(event_queue.qsize())
        return {"status": "queued"}
    except asyncio.QueueFull:
        raise HTTPException(status_code=503, detail="Ingestion queue full")


@app.get("/alerts", response_model=list[Alert])
async def get_alerts(limit: int = 50):
    return recent_alerts[-limit:]


@app.get("/healthz", response_class=PlainTextResponse)
async def healthz():
    return "ok"

@app.get("/metrics")
def metrics():
    return PlainTextResponse(generate_latest(), media_type=CONTENT_TYPE_LATEST)
