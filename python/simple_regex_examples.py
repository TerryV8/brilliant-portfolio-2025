#!/usr/bin/env python3
"""
Simple Regex Examples

Three practical DevOps/SOC regex tasks in one tiny script:
- extract-ips:      find IPv4 addresses
- extract-emails:   find email addresses
- extract-fr-phone: find French phone numbers
- log-criticality:  detect/count log levels (DEBUG..FATAL)

Examples:
  python python/simple_regex_examples.py extract-ips sample.txt
  python python/simple_regex_examples.py extract-fr-phone sample.txt
  python python/simple_regex_examples.py extract-emails sample.txt
  python python/simple_regex_examples.py log-criticality --count /var/log/app.log
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path
from typing import Iterator, Optional, Tuple

# Simple regex patterns
RE_IPv4 = re.compile(r"\b(?:(?:25[0-5]|2[0-4]\\d|1?\\d?\\d)\\.){3}(?:25[0-5]|2[0-4]\\d|1?\\d?\\d)\\b")
RE_EMAIL = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\\.[A-Za-z]{2,}")
RE_FR_PHONE = re.compile(r"\b(?:\\+33\\s?[1-9](?:[ .-]?\\d{2}){4}|0[1-9](?:[ .-]?\\d{2}){4})\\b")
RE_LOG_LEVEL = re.compile(r"\\b(DEBUG|INFO|WARN|WARNING|ERROR|CRITICAL|FATAL)\\b", re.IGNORECASE)


def read_lines(path: Optional[Path]) -> Iterator[Tuple[int, str]]:
    if path is None or str(path) == "-":
        for i, line in enumerate(sys.stdin, 1):
            yield i, line.rstrip("\n")
    else:
        with path.open("r", encoding="utf-8", errors="replace") as f:
            for i, line in enumerate(f, 1):
                yield i, line.rstrip("\n")


def extract(pattern: re.Pattern, path: Optional[Path]) -> None:
    seen = set()
    for _, line in read_lines(path):
        for m in pattern.findall(line):
            seen.add(m if isinstance(m, str) else m[0])
    for item in sorted(seen):
        print(item)


def log_criticality(path: Optional[Path], count: bool) -> None:
    counters = {}
    for _, line in read_lines(path):
        m = RE_LOG_LEVEL.search(line)
        if not m:
            continue
        lvl = m.group(1).upper()
        if count:
            counters[lvl] = counters.get(lvl, 0) + 1
        else:
            print(f"{lvl}: {line}")
    if count:
        for lvl in ["DEBUG", "INFO", "WARN", "WARNING", "ERROR", "CRITICAL", "FATAL"]:
            if lvl in counters:
                print(f"{lvl}: {counters[lvl]}")


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Simple Regex Examples")
    sub = p.add_subparsers(dest="cmd", required=True)

    p_ips = sub.add_parser("extract-ips", help="extract IPv4 addresses")
    p_ips.add_argument("file", nargs="?", help="path or - for stdin")

    p_em = sub.add_parser("extract-emails", help="extract email addresses")
    p_em.add_argument("file", nargs="?", help="path or - for stdin")

    p_fr = sub.add_parser("extract-fr-phone", help="extract French phone numbers")
    p_fr.add_argument("file", nargs="?", help="path or - for stdin")

    p_lvl = sub.add_parser("log-criticality", help="detect or count log levels")
    p_lvl.add_argument("file", nargs="?", help="path or - for stdin")
    p_lvl.add_argument("--count", action="store_true")

    return p


def main(argv=None) -> int:
    args = build_parser().parse_args(argv)
    path = Path(args.file) if getattr(args, "file", None) and args.file != "-" else None

    if args.cmd == "extract-ips":
        extract(RE_IPv4, path)
    elif args.cmd == "extract-emails":
        extract(RE_EMAIL, path)
    elif args.cmd == "extract-fr-phone":
        extract(RE_FR_PHONE, path)
    elif args.cmd == "log-criticality":
        log_criticality(path, args.count)
    else:
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
