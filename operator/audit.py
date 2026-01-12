"""
Audit logging for BlackRoad Operator.

Every operation is logged for:
1. Compliance and accountability
2. Performance analysis
3. Future ledger/blockchain integration
"""

import json
import asyncio
from datetime import datetime
from pathlib import Path
from typing import Any, Optional
import structlog
import aiofiles

from .config import get_settings
from .models.audit import AuditEntry


# Configure structured logging
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer()
    ],
    wrapper_class=structlog.stdlib.BoundLogger,
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger("blackroad.audit")


class AuditLogger:
    """
    Audit logger that writes JSON lines to a file.

    Every operation through the Operator is logged for:
    - Compliance tracking
    - Performance analysis
    - Cost tracking
    - Future RoadChain integration
    """

    def __init__(self, log_path: Optional[str] = None):
        settings = get_settings()
        self._log_path = Path(log_path or settings.audit_log_path)
        self._log_path.parent.mkdir(parents=True, exist_ok=True)
        self._buffer: list[AuditEntry] = []
        self._buffer_size = 10
        self._lock = asyncio.Lock()

    async def log(self, entry: AuditEntry) -> None:
        """Log an audit entry."""
        async with self._lock:
            self._buffer.append(entry)

            # Also log to structured logger
            logger.info(
                "audit_entry",
                audit_id=entry.id,
                request_type=entry.request_type,
                intent=entry.intent_detected,
                provider=entry.provider_selected,
                success=entry.success,
                latency_ms=entry.latency_ms,
                cost_usd=entry.cost_usd,
            )

            # Flush if buffer is full
            if len(self._buffer) >= self._buffer_size:
                await self._flush()

    async def _flush(self) -> None:
        """Flush buffer to file."""
        if not self._buffer:
            return

        try:
            async with aiofiles.open(self._log_path, "a") as f:
                for entry in self._buffer:
                    await f.write(entry.to_json_line())
            self._buffer.clear()
        except Exception as e:
            logger.error("audit_flush_failed", error=str(e))

    async def close(self) -> None:
        """Close the logger, flushing any remaining entries."""
        async with self._lock:
            await self._flush()

    async def query(
        self,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        provider: Optional[str] = None,
        success_only: bool = False,
        limit: int = 100,
    ) -> list[AuditEntry]:
        """Query audit log entries."""
        entries = []

        try:
            async with aiofiles.open(self._log_path, "r") as f:
                async for line in f:
                    try:
                        data = json.loads(line.strip())
                        entry = AuditEntry(**data)

                        # Apply filters
                        if start_time and entry.timestamp < start_time:
                            continue
                        if end_time and entry.timestamp > end_time:
                            continue
                        if provider and entry.provider_selected != provider:
                            continue
                        if success_only and not entry.success:
                            continue

                        entries.append(entry)

                        if len(entries) >= limit:
                            break
                    except (json.JSONDecodeError, ValueError):
                        continue
        except FileNotFoundError:
            pass

        return entries

    async def get_stats(self, hours: int = 24) -> dict[str, Any]:
        """Get statistics for the last N hours."""
        from datetime import timedelta

        start_time = datetime.utcnow() - timedelta(hours=hours)
        entries = await self.query(start_time=start_time, limit=10000)

        if not entries:
            return {
                "period_hours": hours,
                "total_requests": 0,
                "success_rate": 0,
                "avg_latency_ms": 0,
                "total_cost_usd": 0,
                "by_provider": {},
                "by_intent": {},
            }

        total = len(entries)
        successful = sum(1 for e in entries if e.success)
        total_latency = sum(e.latency_ms for e in entries)
        total_cost = sum(e.cost_usd or 0 for e in entries)

        # Group by provider
        by_provider: dict[str, int] = {}
        for e in entries:
            by_provider[e.provider_selected] = by_provider.get(e.provider_selected, 0) + 1

        # Group by intent
        by_intent: dict[str, int] = {}
        for e in entries:
            by_intent[e.intent_detected] = by_intent.get(e.intent_detected, 0) + 1

        return {
            "period_hours": hours,
            "total_requests": total,
            "success_rate": successful / total if total > 0 else 0,
            "avg_latency_ms": total_latency / total if total > 0 else 0,
            "total_cost_usd": total_cost,
            "by_provider": by_provider,
            "by_intent": by_intent,
        }


# Global audit logger instance
audit_logger = AuditLogger()
