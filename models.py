
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

class LogEvent(BaseModel):
    timestamp: datetime = Field(..., description="ISO timestamp when the event occurred")
    source: str = Field(..., description="Origin of the event, e.g., 'web-firewall'")
    ip: Optional[str] = Field(None, description="Source IP if available")
    message: str = Field(..., description="Raw event message text")
    user: Optional[str] = Field(None, description="Optional user identifier")
    severity: Optional[str] = Field(None, description="Info | Warn | Error | Critical")

class Alert(BaseModel):
    created_at: datetime
    event: LogEvent
    detector: str
    severity: str
    reason: str
