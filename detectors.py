
import os
import re
import time
from typing import Optional
from datetime import datetime
import httpx

from models import LogEvent, Alert

# Simple rule-based detector: configurable keyword/regex rules
class RuleBasedDetector:
    def __init__(self):
        self.keyword_rules = {
            "brute_force": re.compile(r"failed\s+login|brute\s*force|too\s+many\s+attempts", re.I),
            "sql_injection": re.compile(r"(UNION\s+SELECT|\'\s*OR\s*1=1|--\s*$)", re.I),
            "exfiltration": re.compile(r"ftp|curl|wget|exfiltrat", re.I),
        }

    def evaluate(self, event: LogEvent) -> Optional[Alert]:
        text = f"{event.source} {event.message}"
        for name, pattern in self.keyword_rules.items():
            if pattern.search(text):
                return Alert(
                    created_at=datetime.utcnow(),
                    event=event,
                    detector=f"RuleBased({name})",
                    severity="High" if name in {"brute_force", "sql_injection"} else "Medium",
                    reason=f"Matched rule: {name}",
                )
        return None

# LLM-based detector: real API call if LLM_ENABLED=true and API key present, else stub
class LLMDetector:
    def __init__(self):
        self.enabled = os.getenv("LLM_ENABLED", "false").lower() == "true"
        self.api_key = os.getenv("OPENAI_API_KEY", "")
        self.model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
        self.base_url = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")

    async def evaluate(self, event: LogEvent) -> Optional[Alert]:
        if not self.enabled:
            return None

        # If no key, fall back to keyword heuristic stub so the app still runs
        if not self.api_key:
            verdict, explanation = self._stub_verdict(event)
            if verdict == "SUSPICIOUS":
                return Alert(
                    created_at=datetime.utcnow(),
                    event=event,
                    detector="LLMDetector(stub)",
                    severity="High",
                    reason=explanation,
                )
            return None

        try:
            prompt = (
                "You are a SOC detector. Read the log and output exactly one JSON object "
                'with keys: verdict ("BENIGN" or "SUSPICIOUS") and reason (short string). '
                f"Log: source={event.source}, ip={event.ip}, user={event.user}, message={event.message}"
            )

            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            }
            payload = {
                "model": self.model,
                "messages": [
                    {"role": "system", "content": "You classify security logs."},
                    {"role": "user", "content": prompt},
                ],
                "temperature": 0.0,
            }

            async with httpx.AsyncClient(timeout=12.0, base_url=self.base_url) as client:
                resp = await client.post("/chat/completions", json=payload, headers=headers)
                resp.raise_for_status()
                data = resp.json()
                content = data["choices"][0]["message"]["content"]

            # Very defensive parse: look for keywords; optionally attempt JSON parse
            verdict = "BENIGN"
            reason = "LLM response could not be parsed; treated as benign"
            try:
                import json as _json
                obj = _json.loads(content)
                verdict = str(obj.get("verdict", "BENIGN")).upper()
                reason = str(obj.get("reason", "")) or "No reason provided"
            except Exception:
                text = (content or "").lower()
                if "suspicious" in text:
                    verdict = "SUSPICIOUS"
                    reason = content.strip()[:200]

            if verdict == "SUSPICIOUS":
                return Alert(
                    created_at=datetime.utcnow(),
                    event=event,
                    detector=f"LLMDetector({self.model})",
                    severity="High",
                    reason=reason,
                )
            return None
        except Exception:
            # Fall back to stub on any API failure
            verdict, explanation = self._stub_verdict(event)
            if verdict == "SUSPICIOUS":
                return Alert(
                    created_at=datetime.utcnow(),
                    event=event,
                    detector="LLMDetector(stub-fallback)",
                    severity="High",
                    reason=explanation,
                )
            return None

    def _stub_verdict(self, event: LogEvent):
        msg = (event.message or "").lower()
        if any(k in msg for k in ["failed login", "brute", "sql", "exfil"]):
            return "SUSPICIOUS", "Keyword heuristic triggered in LLM stub"
        return "BENIGN", "No suspicious keywords in stub"

# Slack notifier
async def notify_slack(alert: Alert):
    url = os.getenv("SLACK_WEBHOOK_URL", "")
    if not url:
        return
    payload = {
        "text": f"[ALERT] {alert.severity} via {alert.detector}: {alert.reason}\n"
                f"source={alert.event.source} ip={alert.event.ip} msg={alert.event.message}"
    }
    try:
        async with httpx.AsyncClient(timeout=5) as client:
            await client.post(url, json=payload)
    except Exception:
        pass
