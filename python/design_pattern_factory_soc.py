"""
Understanding the Factory Design Pattern

The Factory Design Pattern is a creational pattern that provides an interface for creating objects in a superclass,
but allows subclasses to alter the type of objects that will be created.
It's like ordering food from a menu - you ask for a dish, and the kitchen (factory) decides how to prepare it.

Simple Explanation
Think of the factory pattern like ordering at a coffee shop:
- Factory: The coffee shop/barista
- Product: Different coffee types (Latte, Americano, Cappuccino)
- Client: You, who just orders a coffee without knowing how it's made

Example:
1. You order a "latte" (client makes a request)
2. The barista (factory) knows how to make it
3. You get your latte without needing to know the recipe

Key Concepts
- Creator: Declares the factory method that returns product objects
- Concrete Creator: Implements the factory method to create specific products
- Product: The interface of objects the factory creates
- Concrete Product: The actual objects created by the factory

Real-World Example from This Code
In this file, we implement a SIEM (Security Information and Event Management) event sender factory:
- Product: EventSender interface
- Concrete Products: ElasticSender, SplunkSender, etc.
- Creator: EventSenderFactory that creates the appropriate sender
- Client: AuthMonitor, FirewallMonitor that use the sender
"""

# Factory Design Pattern in a DevOps/SOC context
#
# Goal: Choose which SIEM sender implementation to use (Elastic, Splunk, etc.)
# at runtime, while client code depends only on the EventSender interface.
#
# Benefits:
# - Decouple creation from usage (Open/Closed Principle)
# - Centralize config/validation for transports
# - Easy to add new vendors without touching client code

from __future__ import annotations

import os
import json
from abc import ABC, abstractmethod
from typing import Any, Dict


# Product interface
class EventSender(ABC):
    @abstractmethod
    def send(self, event: Dict[str, Any]) -> None: ...


# Concrete Product: Elastic
class ElasticSender(EventSender):
    def __init__(self, endpoint: str, token: str) -> None:
        self.endpoint = endpoint
        self.token = token

    def send(self, event: Dict[str, Any]) -> None:
        # In real life: HTTP POST with auth header
        print(
            f"[Elastic] POST {self.endpoint} auth=*** body={json.dumps(event, separators=(',', ':'))}"
        )


# Concrete Product: Splunk
class SplunkSender(EventSender):
    def __init__(self, hec_url: str, hec_token: str) -> None:
        self.hec_url = hec_url
        self.hec_token = hec_token

    def send(self, event: Dict[str, Any]) -> None:
        print(
            f"[Splunk] POST {self.hec_url} auth=*** body={json.dumps(event, separators=(',', ':'))}"
        )


# Concrete Product: Stdout (fallback / local dev)


# Simple Factory
class EventSenderFactory:
    _registry = {
        "elastic": ElasticSender,
        "splunk": SplunkSender,
    }

    @staticmethod
    def create(vendor: str | None = None, **config: Any) -> EventSender:
        """Create an EventSender for a given vendor.

        If vendor is None, read SIEM_VENDOR from env. No default fallback.
        """
        key_env = os.getenv("SIEM_VENDOR")
        key_source = vendor if vendor is not None else key_env
        if not key_source:
            raise ValueError(
                "SIEM vendor not specified. Set SIEM_VENDOR or pass vendor explicitly (elastic|splunk)."
            )
        key = key_source.strip().lower()

        if key == "elastic":
            endpoint = config.get("endpoint") or os.getenv(
                "ELASTIC_ENDPOINT", "https://elastic.example/_bulk"
            )
            token = config.get("token") or os.getenv("ELASTIC_TOKEN", "demo-token")
            return ElasticSender(endpoint, token)

        if key == "splunk":
            hec_url = config.get("hec_url") or os.getenv(
                "SPLUNK_HEC_URL", "https://splunk.example:8088/services/collector"
            )
            hec_token = config.get("hec_token") or os.getenv(
                "SPLUNK_HEC_TOKEN", "demo-hec-token"
            )
            return SplunkSender(hec_url, hec_token)

        raise ValueError(f"Unknown SIEM vendor: {vendor!r}")


# Example SOC producers that depend only on EventSender
class AuthMonitor:
    def __init__(self, sender: EventSender) -> None:
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
    def __init__(self, sender: EventSender) -> None:
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
    # Choose vendor via env SIEM_VENDOR or pass explicitly to factory
    # Examples: elastic, splunk
    sender = EventSenderFactory.create(vendor="elastic")  # explicit for demo

    auth = AuthMonitor(sender)
    fw = FirewallMonitor(sender)

    auth.record_failed_login(username="alice", ip="203.0.113.25")
    fw.record_port_scan(src_ip="198.51.100.10", dst_ip="10.0.0.5")
