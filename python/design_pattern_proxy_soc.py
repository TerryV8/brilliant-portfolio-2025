"""
Understanding the Proxy Design Pattern

The Proxy Design Pattern is a structural pattern that provides a surrogate or placeholder for another object to control access to it.
It's like having a personal assistant who handles all your requests to a busy executive.

Simple Explanation
Think of the proxy pattern like a bank teller:
- Subject: The bank account interface
- Real Subject: Your actual bank account
- Proxy: The bank teller who controls access to your account

Example:
1. You ask the teller (proxy) to check your balance
2. The teller verifies your ID (access control)
3. Only then does the teller access the real bank account

Key Concepts
- Subject: The interface that both RealSubject and Proxy implement
- RealSubject: The actual object that does the real work
- Proxy: Controls access to the RealSubject, adding extra behavior

Real-World Example from This Code
In this file, we implement a SIEM (Security Information and Event Management) sender proxy:
- Subject: AlertSender interface
- RealSubject: RealSIEMSender that sends alerts to a SIEM
- Proxy: SIEMSenderProxy that adds authentication, rate limiting, and lazy initialization
"""

# Proxy Design Pattern in a DevOps/SOC context (Protection + Virtual Proxy)
#
# Goal:
# - Wrap a real SIEM sender with a proxy that enforces access control (auth token),
#   rate limiting, and lazy initialization. Client code uses the proxy via an
#   interface and is unaware of the underlying checks.

from __future__ import annotations

import os
import time
import json
from abc import ABC, abstractmethod
from typing import Any, Dict

# Simple alias to make type hints shorter and clearer in this example
Event = Dict[str, Any]


# Subject interface
class AlertSender(ABC):
    """Abstract sender that can deliver SOC/DevOps alerts to a SIEM."""

    @abstractmethod
    def send(self, event: Event) -> None: ...


# RealSubject: connects to SIEM (Elastic, Splunk, etc.)
class RealSIEMSender(AlertSender):
    """Concrete sender that would talk to a real SIEM over HTTP.

    For demo purposes, we just print the outgoing payload.
    """

    def __init__(self, endpoint: str, token: str) -> None:
        # Simulate an expensive setup (e.g., building an HTTP session)
        print("[RealSIEMSender] Initializing HTTP session...")
        time.sleep(0.2)
        self.endpoint = endpoint
        self.token = token
        print("[RealSIEMSender] Ready")

    def send(self, event: Event) -> None:
        # In real life: HTTP POST with retries/backoff
        payload = json.dumps(event, separators=(",", ":"))
        print(f"[SIEM] POST {self.endpoint} auth=*** body={payload}")


# Proxy: validates auth, rate-limits, and lazily creates RealSIEMSender on first use
class SIEMSenderProxy(AlertSender):
    """Protection + virtual proxy for a SIEM sender.

    - Enforces presence of an auth token (basic access control).
    - Applies a naive fixed-window rate limit.
    - Lazily creates the real sender on first use to avoid upfront cost.
    """

    def __init__(
        self,
        endpoint: str | None = None,
        token: str | None = None,
        rate_limit_per_sec: int = 5,
    ) -> None:
        # Resolve configuration with sensible fallbacks for the demo
        self.endpoint = endpoint or os.getenv(
            "SIEM_ENDPOINT", "https://siem.example/api/events"
        )
        self.token = token or os.getenv("SIEM_TOKEN")

        # Internal state
        self._real: RealSIEMSender | None = None
        self.rate_limit_per_sec = rate_limit_per_sec
        self._last_window_start = time.time()
        self._count_in_window = 0

    def _ensure_real(self) -> None:
        if self._real is None:
            if not self.token:
                raise PermissionError(
                    "Missing SIEM auth token. Set SIEM_TOKEN or pass token explicitly."
                )
            self._real = RealSIEMSender(self.endpoint, self.token)

    def _allow(self) -> bool:
        # Simple fixed-window rate limit
        now = time.time()
        if now - self._last_window_start >= 1.0:
            self._last_window_start = now
            self._count_in_window = 0
        if self._count_in_window < self.rate_limit_per_sec:
            self._count_in_window += 1
            return True
        return False

    def send(self, event: Event) -> None:
        # Access control
        if not self.token:
            raise PermissionError("Unauthorized: SIEM token not configured")
        # Rate limiting
        if not self._allow():
            print("[Proxy] Rate limit exceeded, dropping event:", event.get("message"))
            return
        # Lazy creation of the real sender
        self._ensure_real()
        self._real.send(event)  # type: ignore[union-attr]


# Client code uses the proxy as if it were the real sender
class AuthMonitor:
    def __init__(self, sender: AlertSender) -> None:
        self.sender = sender

    def record_failed_login(self, username: str, ip: str) -> None:
        event = {
            "kind": "auth",
            "severity": "medium",
            "message": "Failed login detected",
            "username": username,
            "ip": ip,
        }
        self.sender.send(event)


class FirewallMonitor:
    def __init__(self, sender: AlertSender) -> None:
        self.sender = sender

    def record_port_scan(self, src_ip: str, dst_ip: str) -> None:
        event = {
            "kind": "network",
            "severity": "high",
            "message": "Port scan detected",
            "src_ip": src_ip,
            "dst_ip": dst_ip,
        }
        self.sender.send(event)


if __name__ == "__main__":
    # Configure token in env or pass explicitly
    os.environ.setdefault("SIEM_TOKEN", "demo-token")

    proxy = SIEMSenderProxy(rate_limit_per_sec=2)  # intentionally low to demo limiting
    auth = AuthMonitor(proxy)
    fw = FirewallMonitor(proxy)

    # First two allowed, third dropped by rate limiter
    auth.record_failed_login(username="alice", ip="203.0.113.25")
    fw.record_port_scan(src_ip="198.51.100.10", dst_ip="10.0.0.5")
    auth.record_failed_login(username="bob", ip="198.51.100.23")
