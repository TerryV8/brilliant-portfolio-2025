"""
MAIN GOAL: Simple ownership restore after compromise (SOC/DevOps demo).

Show a clear CLI that:
- Walks a target path
- Detects files/dirs not owned by the expected user (and optionally group)
- Logs JSONL audit entries
- Either prints what would change (default) or applies changes with --apply

Run with sudo to actually change ownership.
"""

from __future__ import annotations

import argparse
import json
import os
import pwd
import grp
import sys
import time
import subprocess
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

AUDIT_LOG_DEFAULT = os.getenv("SOC_AUDIT_LOG", "soc_audit_log.jsonl")


def jsonl_write(path: Path, obj: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(obj, separators=(",", ":")) + "\n")


def audit_event(
    kind: str,
    message: str,
    *,
    severity: str = "medium",
    status: str = "ok",
    extra: Optional[Dict[str, Any]] = None,
    audit_log: Path = Path(AUDIT_LOG_DEFAULT),
) -> None:
    evt: Dict[str, Any] = {
        "ts": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "func": "ownership_restore",
        "status": status,
        "duration_ms": 0,
        "kind": kind,
        "severity": severity,
        "message": message,
    }
    if extra:
        evt.update(extra)
    jsonl_write(audit_log, evt)


def git_root(start: Path) -> Path:
    """Return git repo root if available, else the given start.

    Kept minimal for demo; not strictly required for operation.
    """
    try:
        out = subprocess.check_output(
            ["git", "-C", str(start), "rev-parse", "--show-toplevel"],
            stderr=subprocess.DEVNULL,
        )
        return Path(out.decode().strip())
    except Exception:
        return start


def resolve_ids(owner: str, group: Optional[str]) -> Tuple[int, Optional[int]]:
    uid = pwd.getpwnam(owner).pw_uid
    gid = grp.getgrnam(group).gr_gid if group else None
    return uid, gid


def within_path(child: Path, parent: Path) -> bool:
    """Simple safety check used only for messaging; not critical in this demo."""
    try:
        child_resolved = child.resolve()
        parent_resolved = parent.resolve()
        return parent_resolved in child_resolved.parents or child_resolved == parent_resolved
    except FileNotFoundError:
        return False


def restore_ownership(
    root: Path,
    owner: str,
    group: Optional[str],
    *,
    apply: bool = False,
    audit_log: Path = Path(AUDIT_LOG_DEFAULT),
) -> Tuple[int, int, int]:
    """Walk root and restore ownership. Returns (checked, changed, failed).

    Simpler signature: pass --apply to actually change; otherwise it's a dry-run.
    """
    uid, gid = resolve_ids(owner, group)
    checked = changed = failed = 0

    for path in root.rglob("*"):
        if not path.exists():
            continue
        try:
            st = path.lstat()
        except FileNotFoundError:
            continue
        checked += 1
        need_change = (st.st_uid != uid) or (gid is not None and st.st_gid != gid)
        if not need_change:
            continue

        detail = {
            "path": str(path),
            "current_uid": st.st_uid,
            "current_gid": st.st_gid,
            "target_user": owner,
            "target_group": group or "(keep)",
        }
        if not apply:
            audit_event("file", "Would change ownership (dry-run)", severity="low", extra=detail, audit_log=audit_log)
            changed += 1
            continue
        try:
            os.chown(str(path), uid, st.st_gid if gid is None else gid)
            audit_event("file", "Ownership changed", severity="medium", extra=detail, audit_log=audit_log)
            changed += 1
        except PermissionError as e:
            failed += 1
            audit_event(
                "file",
                f"Permission denied: {e.__class__.__name__}",
                severity="high",
                status="error",
                extra=detail,
                audit_log=audit_log,
            )
        except OSError as e:
            failed += 1
            audit_event(
                "file",
                f"OS error: {e.__class__.__name__}",
                severity="high",
                status="error",
                extra=detail,
                audit_log=audit_log,
            )

    return checked, changed, failed


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Restore ownership under a path",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("--owner", required=True, help="Expected username (target owner)")
    parser.add_argument("--group", help="Expected group (optional; if omitted, group unchanged)")
    parser.add_argument("--root", type=Path, default=Path.cwd(), help="Target root (default: CWD)")
    parser.add_argument("--apply", action="store_true", help="Actually change ownership (default: dry-run)")
    parser.add_argument(
        "--audit-log",
        type=Path,
        default=Path(AUDIT_LOG_DEFAULT),
        help="JSONL audit log path (or env SOC_AUDIT_LOG)",
    )

    args = parser.parse_args()

    audit_event(
        "file",
        "Start ownership audit",
        severity="low",
        extra={"root": str(args.root), "owner": args.owner, "group": args.group or "(keep)", "apply": args.apply},
        audit_log=args.audit_log,
    )

    try:
        checked, changed, failed = restore_ownership(
            args.root, args.owner, args.group, apply=args.apply, audit_log=args.audit_log
        )
    except KeyError as e:
        print(f"Lookup error for user/group: {e}")
        audit_event("file", f"Lookup error: {e}", severity="high", status="error", extra={"owner": args.owner, "group": args.group}, audit_log=args.audit_log)
        sys.exit(1)

    summary = {"checked": checked, "changed": changed, "failed": failed}
    print(f"Checked={checked} Changed={changed} Failed={failed}")
    audit_event("file", "Ownership audit complete", severity="low", extra=summary, audit_log=args.audit_log)


if __name__ == "__main__":
    main()
