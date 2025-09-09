"""
Understanding the Singleton Design Pattern

The Singleton Design Pattern is a creational pattern that ensures a class has only one instance and provides
a global point of access to that instance. It's like having a single, shared resource that needs to be accessed
consistently across an entire application.

Simple Explanation
Think of the Singleton pattern like a company's main reception desk:
- There's only one main reception desk for the entire company
- Everyone uses the same reception desk for their needs
- The reception desk maintains consistent state and operations

Key Concepts
- Single Instance: Only one instance of the class exists in the application
- Global Access: The instance is globally accessible
- Lazy Initialization: The instance is created only when needed
- Thread Safety: In multi-threaded environments, the singleton must be thread-safe

In this SOC Context
We implement a Singleton SIEM (Security Information and Event Management) client that ensures:
- Only one connection to the SIEM server exists
- Configuration is loaded once and shared
- Event logging is consistent across the application
- Resource usage is optimized by avoiding duplicate connections
"""

# Singleton in a DevOps/SOC context: central SIEM client
#
# Goal: Ensure only one configured client exists to send security events to a SIEM
# (e.g., Elastic, Splunk, Chronicle). Centralizing avoids duplicated connections,
# inconsistent configs, and enables shared features like buffering or rate-limits.

from __future__ import annotations

import os
import json
import time
from typing import Any, Dict


class SIEMClient:
    """Singleton SIEM client using a classmethod accessor.

    - Access via SIEMClient.get_instance() to ensure a single instance.
    - Reads configuration once from env variables.
    - Provides send_event() to standardize event format.
    """

    _instance: "SIEMClient | None" = None

    def __init__(self) -> None:
        if getattr(self, "_initialized", False):
            return
        # Load config once
        self.endpoint = os.getenv("SIEM_ENDPOINT", "https://siem.example/api/events")
        self.token = os.getenv("SIEM_TOKEN", "demo-token")
        self.source = os.getenv("SIEM_SOURCE", "SOC-Python-Agent")
        self.buffer: list[Dict[str, Any]] = []  # naive buffer for demo
        self._initialized = True

    @staticmethod
    def get_instance() -> "SIEMClient":
        if SIEMClient._instance is None:
            SIEMClient._instance = SIEMClient()
        return SIEMClient._instance

    def send_event(self, kind: str, severity: str, message: str, **extra: Any) -> None:
        event = {
            "ts": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "source": self.source,
            "kind": kind,  # e.g., auth, network, system, vuln
            "severity": severity,  # info, low, medium, high, critical
            "message": message,
            "extra": extra,
        }
        # In real life: HTTP POST with retries/backoff. Here we print and buffer.
        print(f"[SIEM] POST {self.endpoint} auth=*** body={json.dumps(event)}")
        self.buffer.append(event)


# Example SOC utilities that all reuse the same SIEMClient instance
class AuthMonitor:
    def __init__(self) -> None:
        self.siem = SIEMClient.get_instance()

    def record_failed_login(self, username: str, ip: str) -> None:
        self.siem.send_event(
            kind="auth",
            severity="medium",
            message="Failed login detected",
            username=username,
            ip=ip,
        )


class FirewallMonitor:
    def __init__(self) -> None:
        self.siem = SIEMClient.get_instance()

    def record_port_scan(self, src_ip: str, dst_ip: str) -> None:
        self.siem.send_event(
            kind="network",
            severity="high",
            message="Port scan detected",
            src_ip=src_ip,
            dst_ip=dst_ip,
        )


if __name__ == "__main__":
    # Both monitors obtain the same SIEMClient instance
    auth = AuthMonitor()
    fw = FirewallMonitor()

    auth.record_failed_login(username="alice", ip="203.0.113.25")
    fw.record_port_scan(src_ip="198.51.100.10", dst_ip="10.0.0.5")

    client = SIEMClient.get_instance()
    print("\nSingleton check: buffer length:", len(client.buffer))
    print("All events (buffered):")
    for e in client.buffer:
        print(" -", e["kind"], e["message"])
