#!/usr/bin/env python3
"""
DevOps Regex Utilities (SOC-friendly)

Quick, stdlib-only helpers for common DevOps/SOC tasks using regex:
- grep: search files with a regex (print matches + line numbers)
- extract-ips | extract-urls | extract-emails: pull IOCs from text/files
- validate: validate IPv4 and CIDR strings
- parse-nginx: parse NGINX access logs (common/combined) to JSONL
- bump-semver: bump x.y.z in a file (first occurrence)
- tail-match: read stdin and print lines that match a regex (for piping)

Usage examples:
  # grep for errors in a log
  python python/devops_regex_tools.py grep -p "ERROR|CRITICAL" /var/log/app.log

  # extract IPs and URLs from a phishing email
  python python/devops_regex_tools.py extract-ips email.eml
  python python/devops_regex_tools.py extract-urls email.eml

  # validate an address and CIDR
  python python/devops_regex_tools.py validate --ip 10.10.1.5 --cidr 10.10.0.0/16

  # parse nginx logs to JSONL
  python python/devops_regex_tools.py parse-nginx /var/log/nginx/access.log > access.jsonl

  # bump semantic version in a file
  python python/devops_regex_tools.py bump-semver -v minor ./VERSION

  # tail logs and match pattern
  tail -f /var/log/syslog | python python/devops_regex_tools.py tail-match -p "(error|fail|denied)"
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
import os
from typing import Iterable, Iterator, Optional, Tuple

# Basic regexes
RE_IPv4 = re.compile(r"\b(?:(?:25[0-5]|2[0-4]\d|1?\d?\d)\.){3}(?:25[0-5]|2[0-4]\d|1?\d?\d)\b")
RE_CIDR = re.compile(r"^((?:(?:25[0-5]|2[0-4]\d|1?\d?\d)\.){3}(?:25[0-5]|2[0-4]\d|1?\d?\d))\/(\d|[12]\d|3[0-2])$")
RE_URL = re.compile(r"\bhttps?://[^\s\]\[<>\)\(\"']+", re.IGNORECASE)
RE_EMAIL = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
RE_FR_PHONE = re.compile(r"\b(?:\+33\s?[1-9](?:[ .-]?\d{2}){4}|0[1-9](?:[ .-]?\d{2}){4})\b")
RE_LOG_LEVEL = re.compile(r"\b(DEBUG|INFO|WARN|WARNING|ERROR|CRITICAL|FATAL)\b", re.IGNORECASE)


# NGINX common/combined log format (best-effort)
RE_NGINX = re.compile(
    r"^(?P<remote_addr>\S+)\s+-\s+(?P<remote_user>\S+)\s+\[(?P<time_local>[^\]]+)\]\s+\"(?P<request>[A-Z]+\s+[^\s]+\s+HTTP/[0-9.]+)\"\s+" \
    r"(?P<status>\d{3})\s+(?P<body_bytes_sent>\d+)\s+\"(?P<http_referer>[^\"]*)\"\s+\"(?P<http_user_agent>[^\"]*)\""
)


def read_lines(path: Optional[Path]) -> Iterator[Tuple[int, str]]:
    if path is None or str(path) == "-":
        for i, line in enumerate(sys.stdin, 1):
            yield i, line.rstrip("\n")
    else:
        with path.open("r", encoding="utf-8", errors="replace") as f:
            for i, line in enumerate(f, 1):
                yield i, line.rstrip("\n")


def cmd_grep(pattern: str, path: Optional[Path]):
    rx = re.compile(pattern)
    for ln, line in read_lines(path):
        if rx.search(line):
            print(f"{ln}: {line}")


 


def cmd_extract(pattern: re.Pattern, path: Optional[Path]):
    hits = set()
    for _, line in read_lines(path):
        hits.update(pattern.findall(line))
    for h in sorted(hits):
        print(h)


def cmd_extract_fr_phone(path: Optional[Path]):
    """Extract French phone numbers in various formats.
    Examples: 0612345678, 06 12 34 56 78, 06-12-34-56-78, +33 6 12 34 56 78
    """
    return cmd_extract(RE_FR_PHONE, path)


def cmd_log_criticality(path: Optional[Path], count: bool):
    """Detect log criticality levels. If count=True, print totals per level; else print level and line."""
    levels = {}
    for ln, line in read_lines(path):
        m = RE_LOG_LEVEL.search(line)
        if m:
            lvl = m.group(1).upper()
            if count:
                levels[lvl] = levels.get(lvl, 0) + 1
            else:
                print(f"{lvl}: {line}")
    if count:
        for lvl in ["DEBUG","INFO","WARN","WARNING","ERROR","CRITICAL","FATAL"]:
            if lvl in levels:
                print(f"{lvl}: {levels[lvl]}")


def is_valid_ipv4(ip: str) -> bool:
    return bool(RE_IPv4.fullmatch(ip))


def is_valid_cidr(cidr: str) -> bool:
    return bool(RE_CIDR.fullmatch(cidr))


def cmd_validate(ip: Optional[str], cidr: Optional[str]):
    result = {"ip": None, "cidr": None}
    if ip is not None:
        result["ip"] = {"value": ip, "valid": is_valid_ipv4(ip)}
    if cidr is not None:
        result["cidr"] = {"value": cidr, "valid": is_valid_cidr(cidr)}
    print(json.dumps(result, indent=2))


def parse_nginx_line(line: str) -> Optional[dict]:
    m = RE_NGINX.match(line)
    if not m:
        return None
    d = m.groupdict()
    # Split request
    try:
        method, path, http = d["request"].split()
    except Exception:
        method, path, http = None, None, None
    d.update({"method": method, "path": path, "http": http})
    return d


def cmd_parse_nginx(path: Optional[Path]):
    for _, line in read_lines(path):
        parsed = parse_nginx_line(line)
        if parsed:
            print(json.dumps(parsed, ensure_ascii=False))


def bump_semver_in_text(text: str, part: str) -> Tuple[str, Optional[str]]:
    m = re.search(r"\b(\d+)\.(\d+)\.(\d+)\b", text)
    if not m:
        return text, None
    major, minor, patch = map(int, m.groups())
    if part == "major":
        major, minor, patch = major + 1, 0, 0
    elif part == "minor":
        minor, patch = minor + 1, 0
    else:
        patch += 1
    new = f"{major}.{minor}.{patch}"
    start, end = m.span()
    return text[:start] + new + text[end:], new


def cmd_bump_semver(path: Path, part: str):
    text = path.read_text(encoding="utf-8")
    new_text, new_ver = bump_semver_in_text(text, part)
    if new_ver is None:
        print("No x.y.z semantic version found", file=sys.stderr)
        sys.exit(1)
    path.write_text(new_text, encoding="utf-8")
    print(new_ver)


def cmd_tail_match(pattern: str):
    rx = re.compile(pattern)
    for line in sys.stdin:
        if rx.search(line):
            sys.stdout.write(line)
            sys.stdout.flush()


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="DevOps Regex Utilities")
    sub = p.add_subparsers(dest="cmd", required=True)

    p_grep = sub.add_parser("grep", help="grep a file/stdin with regex")
    p_grep.add_argument("-p", "--pattern", required=False, help="regex pattern; or set ENV REGEX_PATTERN")
    p_grep.add_argument("file", nargs="?", help="path or - for stdin")


    p_ips = sub.add_parser("extract-ips", help="extract IPv4 addresses")
    p_ips.add_argument("file", nargs="?", help="path or - for stdin")

    p_urls = sub.add_parser("extract-urls", help="extract URLs")
    p_urls.add_argument("file", nargs="?", help="path or - for stdin")

    p_em = sub.add_parser("extract-emails", help="extract email addresses")
    p_em.add_argument("file", nargs="?", help="path or - for stdin")

    p_fr = sub.add_parser("extract-fr-phone", help="extract French phone numbers")
    p_fr.add_argument("file", nargs="?", help="path or - for stdin")

    p_val = sub.add_parser("validate", help="validate IP and CIDR strings")
    p_val.add_argument("--ip", help="IPv4 to validate; or set ENV IP")
    p_val.add_argument("--cidr", help="CIDR to validate; or set ENV CIDR")

    p_ng = sub.add_parser("parse-nginx", help="parse NGINX access log -> JSONL")
    p_ng.add_argument("file", nargs="?", help="path or - for stdin")

    p_bump = sub.add_parser("bump-semver", help="bump first x.y.z in file")
    p_bump.add_argument("-v", "--part", choices=["major", "minor", "patch"], default="patch")
    p_bump.add_argument("file")

    p_tail = sub.add_parser("tail-match", help="print lines from stdin matching regex")
    p_tail.add_argument("-p", "--pattern", required=True)

    p_lvl = sub.add_parser("log-criticality", help="detect or count log levels (DEBUG..FATAL)")
    p_lvl.add_argument("file", nargs="?", help="path or - for stdin")
    p_lvl.add_argument("--count", action="store_true", help="print counts per level instead of lines; or set ENV LOG_LEVEL_COUNT=1")

    return p


def main(argv: Optional[Iterable[str]] = None) -> int:
    args = build_parser().parse_args(argv)

    # Resolve pattern and file via environment fallbacks
    # File: use INPUT_FILE if not provided
    env_file = os.getenv("INPUT_FILE")
    file_arg = getattr(args, "file", None) or env_file
    path_opt = Path(file_arg) if file_arg and file_arg != "-" else None

    # Single dispatch for extract commands
    extract_map = {
        "extract-ips": RE_IPv4,
        "extract-urls": RE_URL,
        "extract-emails": RE_EMAIL,
        "extract-fr-phone": RE_FR_PHONE,
    }

    if args.cmd in extract_map:
        cmd_extract(extract_map[args.cmd], path_opt)
    elif args.cmd == "grep":
        pattern = args.pattern or os.getenv("REGEX_PATTERN", None)
        if not pattern:
            print("grep: pattern missing (provide -p/--pattern or set REGEX_PATTERN)", file=sys.stderr)
            return 2
        cmd_grep(pattern, path_opt)
    elif args.cmd == "validate":
        ip = getattr(args, "ip", None) or os.getenv("IP")
        cidr = getattr(args, "cidr", None) or os.getenv("CIDR")
        cmd_validate(ip, cidr)
    elif args.cmd == "parse-nginx":
        cmd_parse_nginx(path_opt)
    elif args.cmd == "bump-semver":
        cmd_bump_semver(Path(args.file), args.part)
    elif args.cmd == "tail-match":
        cmd_tail_match(args.pattern)
    elif args.cmd == "log-criticality":
        count_env = os.getenv("LOG_LEVEL_COUNT")
        count_flag = args.count or (str(count_env).lower() in ["1", "true", "yes", "on"]) if count_env is not None else args.count
        cmd_log_criticality(path_opt, count_flag)
    else:
        print("Unknown command", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
