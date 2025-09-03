"""
MAIN GOAL: Async SOC/DevOps event emitter (no extra deps).

- Emits compact JSONL events concurrently using asyncio.
- Uses SOC_AUDIT_LOG env or defaults to 'soc_audit_log.jsonl'.
- Demonstrates high-throughput, non-blocking writes via asyncio.to_thread.
"""

from __future__ import annotations

import asyncio
import json
import os
import time
from typing import Any, Dict, Optional

LOG_PATH = os.getenv("SOC_AUDIT_LOG", "soc_audit_log.jsonl")


def _write_jsonl_sync(path: str, obj: Dict[str, Any]) -> None:
    """Blocking write of one JSON object as a JSONL line."""
    with open(path, "a", encoding="utf-8") as f:
        f.write(json.dumps(obj, separators=(",", ":")) + "\n")


async def emit_event(
    kind: str,
    message: str,
    severity: str = "medium",
    *,
    username: Optional[str] = None,
    ip: Optional[str] = None,
    func: str = "async",
    audit_log: Optional[str] = None,
) -> None:
    """Emit one SOC audit event asynchronously.

    This function builds a compact JSON object and offloads the file append
    to a background thread via asyncio.to_thread, avoiding blocking the loop.
    """
    path = audit_log or LOG_PATH
    event: Dict[str, Any] = {
        "ts": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "func": func,
        "status": "ok",
        "duration_ms": 0,
        "kind": kind,
        "severity": severity,
        "message": message,
    }
    if username:
        event["username"] = username
    if ip:
        event["ip"] = ip

    await asyncio.to_thread(_write_jsonl_sync, path, event)


async def demo() -> None:
    print("[Async Demo] Writing to:", LOG_PATH)
    # Fire a burst of concurrent events.
    tasks = [
        emit_event("auth", "Failed login (async)", username="alice", ip="203.0.113.25"),
        emit_event("network", "Port scan detected (async)", severity="high"),
        emit_event("file", "Malware signature found (async)", severity="critical"),
        emit_event("auth", "MFA challenge sent (async)", severity="low", username="bob"),
    ]
    await asyncio.gather(*tasks)
    print("[Async Demo] Done.")


if __name__ == "__main__":
    asyncio.run(demo())
