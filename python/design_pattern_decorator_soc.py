"""
Understanding the Decorator Design Pattern

The Decorator Design Pattern is a structural pattern that lets you add new functionality to objects
dynamically without altering their structure. It's like adding toppings to a pizza - the base remains
the same, but you can add different combinations of toppings to enhance it.

Simple Explanation
Think of the decorator pattern like customizing your coffee:
- Component: Basic coffee
- Decorators: Milk, sugar, whipped cream, etc.

Each decorator wraps the original coffee, adding its own flavor. You can combine them in any order.

Key Concepts
- Component: The base interface (e.g., Coffee)
- Concrete Component: The basic implementation (e.g., SimpleCoffee)
- Decorator: Abstract class that implements the Component interface
- Concrete Decorators: Specific additions (e.g., MilkDecorator, SugarDecorator)

Real-World Example from This Code
In this file, we implement an audit logging system:
- Component: Any function that needs auditing (e.g., login, file operations)
- Decorator: @audit_event that wraps functions to add logging
- The decorator adds timing, status tracking, and structured logging
- Preserves the original function's metadata and signature
"""

# Decorator Design Pattern in a DevOps/SOC context
#
# Goal:
# - Add audit logging to functions without modifying their core logic
# - Track execution time, success/failure, and relevant context
# - Write structured logs in JSONL format for easy processing
#
# Benefits:
# - Separation of concerns: security logging is separate from business logic
# - Reusable: apply the same audit logic to any function
# - Non-intrusive: no changes needed to existing function implementations

from typing import Callable, Any, TypeVar
from functools import wraps
import time
import json
import os
from pathlib import Path

"""
MAIN GOAL: SOC/DevOps-focused decorator for audit logging.

This file shows:
- Creating a reusable audit decorator for security events
- Using @wraps to preserve function metadata
- Writing compact JSONL audit entries with duration and status
- Minimal demo with two monitors (auth, firewall)
"""


F = TypeVar("F", bound=Callable[..., Any])


def audit_event(func: F) -> F:
    """Audit decorator: logs security-relevant fields to a JSONL file.

    Records: timestamp, function name, status (ok/error), duration_ms and any
    of these fields if present in kwargs: kind, severity, username, ip, src_ip,
    dst_ip, message.
    """

    @wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        start = time.time()
        status = "ok"
        result: Any = None
        try:
            result = func(*args, **kwargs)
            return result
        except Exception:
            status = "error"
            raise
        finally:
            duration_ms = int((time.time() - start) * 1000)
            event = {
                "ts": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                "func": func.__name__,
                "status": status,
                "duration_ms": duration_ms,
            }
            for k in (
                "kind",
                "severity",
                "username",
                "ip",
                "src_ip",
                "dst_ip",
                "message",
            ):
                if k in kwargs:
                    event[k] = kwargs[k]
            log_path = os.getenv("SOC_AUDIT_LOG", "soc_audit_log.jsonl")
            with open(log_path, "a", encoding="utf-8") as f:
                f.write(json.dumps(event, separators=(",", ":")) + "\n")

    return wrapper  # type: ignore


@audit_event
def record_failed_login(username: str, ip: str, **audit: Any) -> None:
    """Simulate handling a failed login event.

    Pass audit fields like kind/severity/message as keyword args (captured by **audit)
    so the decorator can include them in the JSON log.
    """
    print(f"[Auth] Failed login for {username} from {ip}")


@audit_event
def record_port_scan(src_ip: str, dst_ip: str, **audit: Any) -> None:
    """Simulate handling a firewall port scan event (src -> dst)."""
    print(f"[Firewall] Port scan {src_ip} -> {dst_ip}")


# Simple audited file operations (module-level)
@audit_event
def append_line(file: str | Path, line: str, **audit: Any) -> None:
    """Append a line to a text file (creates file if missing).

    Additional audit fields (kind/severity/message) can be passed via kwargs.
    """
    p = Path(file)
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open("a", encoding="utf-8") as f:
        f.write(line + "\n")


@audit_event
def read_text(file: str | Path, **audit: Any) -> str:
    """Read the entire contents of a text file and return it."""
    p = Path(file)
    with p.open("r", encoding="utf-8") as f:
        return f.read()


# Demo
if __name__ == "__main__":
    # Show where audit entries will be written
    print("[Demo] Audit log:", os.getenv("SOC_AUDIT_LOG", "soc_audit_log.jsonl"))

    record_failed_login(
        username="alice",
        ip="203.0.113.25",
        kind="auth",
        severity="medium",
        message="Failed login detected",
    )
    record_port_scan(
        src_ip="198.51.100.10",
        dst_ip="10.0.0.5",
        kind="network",
        severity="high",
        message="Port scan detected",
    )
    # ---- Simple file log example (append and read) ----
    log_file = Path("demo_app.log")
    append_line(
        file=log_file,
        line="service=auth action=failed_login user=alice ip=203.0.113.25",
        kind="file",
        severity="low",
        message="Append to demo log",
    )
    contents = read_text(
        file=log_file,
        kind="file",
        severity="low",
        message="Read demo log",
    )
    print("[Demo] demo_app.log contents:\n" + contents)
