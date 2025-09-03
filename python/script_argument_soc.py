"""
MAIN GOAL: Minimal SOC/DevOps CLI to emit a JSONL security event.

Simplest usage:
  python main_script_argument.py --kind auth --message "Failed login" \
    --username alice --ip 203.0.113.25

Severity defaults to 'medium'. Override with --severity low|medium|high|critical.
Use SOC_AUDIT_LOG to change the output file.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from typing import Any, Dict


def print_usage() -> None:
    """Print usage examples and environment options."""
    print("Usage examples:\n")
    print("  python main_script_argument.py \\")
    print("    --kind auth \\")
    print('    --message "Failed login" \\')
    print('    --username alice --ip 203.0.113.25')
    print("")
    print("  SOC_AUDIT_LOG=custom_audit.jsonl python main_script_argument.py \\")
    print("    --kind network --severity high \\")
    print('    --message "Port scan detected"')
    print("")
    print("Environment:")
    print("  SOC_AUDIT_LOG   Path to JSONL audit log (default: soc_audit_log.jsonl)")


def main() -> None:
    # Create an argparse-based CLI suitable for SOC/DevOps tooling.
    # argparse provides clear help output, defaults, and type handling.
    parser = argparse.ArgumentParser(
        description="Emit a SOC/SecOps JSONL event to an audit log",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )

    # Core fields
    # Required minimal fields
    parser.add_argument("--kind", required=True, help="Event kind, e.g. auth, network, file")
    parser.add_argument("--message", required=True, help="Human-readable message")
    parser.add_argument(
        "--severity",
        default="medium",
        choices=["low", "medium", "high", "critical"],
        help="Event severity",
    )

    # Optional context
    # Optional enrichment fields
    parser.add_argument("--username", help="Username involved")
    parser.add_argument("--ip", help="IP address involved")

    # Output
    # Honor SOC_AUDIT_LOG so environments can control the sink without changing code.
    parser.add_argument(
        "--audit-log",
        default=os.getenv("SOC_AUDIT_LOG", "soc_audit_log.jsonl"),
        help="Path to JSONL audit log file (can set SOC_AUDIT_LOG env)",
    )
    parser.add_argument(
        "--usage",
        action="store_true",
        help="Print usage examples and exit",
    )

    # Parse CLI arguments
    args = parser.parse_args()

    if args.usage:
        print_usage()
        parser.print_help()
        sys.exit(0)

    # Build a compact event ready for JSON Lines storage.
    # Use UTC timestamps for consistency across systems.
    event: Dict[str, Any] = {
        "ts": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "func": "cli",
        "status": "ok",
        "duration_ms": 0,
        "kind": args.kind,
        "severity": args.severity,
        "message": args.message,
    }
    # Attach optional context only when provided to keep entries minimal.
    if args.username:
        event["username"] = args.username
    if args.ip:
        event["ip"] = args.ip
    # src/dst IP are omitted in the simplified CLI to keep usage minimal.

    try:
        # Append one compact JSON object per line (JSONL) for easy ingestion.
        with open(args.audit_log, "a", encoding="utf-8") as f:
            f.write(json.dumps(event, separators=(",", ":")) + "\n")
        print(f"Wrote event to {args.audit_log}")
    except OSError as e:
        print(f"Error writing to audit log '{args.audit_log}': {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
