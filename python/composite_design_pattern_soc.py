# Composite Design Pattern in a DevOps/SOC context
#
# Goal:
# - Treat individual SIEM senders and groups of senders uniformly.
# - Build a tree of destinations (Elastic, Splunk, region groups, on-call group, etc.).
# - Client code sends an event to the root, and it fans out to all leaves.
#
# Benefits:
# - Uniform interface for leaves and composites.
# - Easy to reconfigure routing by restructuring the tree.
# - Add/remove destinations without changing producers (monitors).

from __future__ import annotations

import json
from abc import ABC, abstractmethod
from typing import Any, Dict, Iterable, List

Event = Dict[str, Any]


# Component
class AlertSink(ABC):
    @abstractmethod
    def send(self, event: Event) -> None: ...


# Leaf 1
class ElasticSink(AlertSink):
    def __init__(self, endpoint: str, token: str) -> None:
        self.endpoint = endpoint
        self.token = token

    def send(self, event: Event) -> None:
        payload = json.dumps(event, separators=(",", ":"))
        print(f"[Elastic] POST {self.endpoint} auth=*** body={payload}")


# Leaf 2
class SplunkSink(AlertSink):
    def __init__(self, hec_url: str, hec_token: str) -> None:
        self.hec_url = hec_url
        self.hec_token = hec_token

    def send(self, event: Event) -> None:
        payload = json.dumps(event, separators=(",", ":"))
        print(f"[Splunk] POST {self.hec_url} auth=*** body={payload}")


# Composite: can contain children that are either leaves or other composites
class CompositeSink(AlertSink):
    def __init__(
        self, name: str = "group", children: Iterable[AlertSink] | None = None
    ) -> None:
        self.name = name
        self._children: List[AlertSink] = list(children or [])

    def add(self, child: AlertSink) -> None:
        self._children.append(child)

    def remove(self, child: AlertSink) -> None:
        self._children.remove(child)

    def send(self, event: Event) -> None:
        print(f"[Composite:{self.name}] Fan-out to {len(self._children)} child(ren)")
        for c in self._children:
            c.send(event)


# Optional: a composite that only forwards specific severities/kinds
class FilteredCompositeSink(CompositeSink):
    def __init__(
        self,
        name: str,
        allowed_severities: set[str] | None = None,
        allowed_kinds: set[str] | None = None,
        children: Iterable[AlertSink] | None = None,
    ) -> None:
        super().__init__(name=name, children=children)
        self.allowed_severities = allowed_severities
        self.allowed_kinds = allowed_kinds

    def send(self, event: Event) -> None:
        sev_ok = (self.allowed_severities is None) or (
            event.get("severity") in self.allowed_severities
        )
        kind_ok = (self.allowed_kinds is None) or (
            event.get("kind") in self.allowed_kinds
        )
        if not (sev_ok and kind_ok):
            print(f"[Composite:{self.name}] Dropped by filter: {event.get('message')}")
            return
        super().send(event)


# Producers (client code) depend only on the AlertSink interface
class AuthMonitor:
    def __init__(self, sink: AlertSink) -> None:
        self.sink = sink

    def record_failed_login(self, username: str, ip: str) -> None:
        event = {
            "kind": "auth",
            "severity": "medium",
            "message": "Failed login detected",
            "username": username,
            "ip": ip,
        }
        self.sink.send(event)


class FirewallMonitor:
    def __init__(self, sink: AlertSink) -> None:
        self.sink = sink

    def record_port_scan(self, src_ip: str, dst_ip: str) -> None:
        event = {
            "kind": "network",
            "severity": "high",
            "message": "Port scan detected",
            "src_ip": src_ip,
            "dst_ip": dst_ip,
        }
        self.sink.send(event)


if __name__ == "__main__":
    # Leaves
    elastic = ElasticSink(
        endpoint="https://elastic.example/_bulk", token="elastic-token"
    )
    splunk = SplunkSink(
        hec_url="https://splunk.example:8088/services/collector",
        hec_token="splunk-token",
    )

    # Sub-groups
    region_eu = CompositeSink(name="eu", children=[elastic])
    region_us = CompositeSink(name="us", children=[splunk])

    # Filtered on-call group (only high severity)
    oncall_high = FilteredCompositeSink(
        name="oncall-high", allowed_severities={"high"}, children=[splunk]
    )

    # Root group that fans out to all
    root = CompositeSink(name="root", children=[region_eu, region_us, oncall_high])

    # Client code (producers) use the root sink uniformly
    auth = AuthMonitor(root)
    fw = FirewallMonitor(root)

    auth.record_failed_login(username="alice", ip="203.0.113.25")
    fw.record_port_scan(src_ip="198.51.100.10", dst_ip="10.0.0.5")
