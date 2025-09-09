#!/usr/bin/env python3
"""
AWS Lambda: API Gateway -> DynamoDB Ingest (beginner-friendly)

- Accepts API Gateway REST API (proxy) v1 or HTTP API v2 events
- Decodes base64 body when applicable
- Accepts JSON body or plain text; also supports query ?text=...
- Persists payload into DynamoDB with metadata
- Returns JSON + CORS headers

Environment:
- TABLE_NAME: required, DynamoDB table name

DynamoDB item shape (example when JSON body is an object):
{
  "id": "<uuid> or provided id",
  "payload": { ...original JSON... },
  "text": "... when provided as text ...",
  "meta": {
    "source": "apigw",
    "received_at": "2025-08-26T16:00:00Z",
    "ip": "<caller ip if available>"
  }
}

Handler: handler(event, context)
"""

from __future__ import annotations

import base64
import json
import os
import re
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, Optional, Tuple

import boto3
from botocore.exceptions import ClientError

# Pre-compiled regex to extract a plausible client IP from headers if present
RE_IPv4 = re.compile(
    r"\b(?:(?:25[0-5]|2[0-4]\d|1?\d?\d)\.){3}(?:25[0-5]|2[0-4]\d|1?\d?\d)\b"
)

ddb = boto3.resource("dynamodb")


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _table() -> Any:
    table_name = os.environ.get("TABLE_NAME")
    if not table_name:
        raise RuntimeError("TABLE_NAME environment variable is required")
    return ddb.Table(table_name)


def handler(event, context):
    is_apigw = (
        isinstance(event, dict)
        and ("requestContext" in event or "httpMethod" in event or "version" in event)
        and ("body" in event or "queryStringParameters" in event or "headers" in event)
    )

    if not is_apigw:
        # Still accept direct invokes with {"payload": {...}} or {"text": "..."}
        item = _build_item_from_direct_invoke(event)
        return _put_and_respond(item)

    # Parse from API Gateway
    lines_or_obj, status, err = _parse_apigw_input(event)
    if err:
        return _response(status, {"error": err})

    # Build a DynamoDB item
    item = _build_item(lines_or_obj, event)
    return _put_and_respond(item)


def _client_ip_from_event(event: dict) -> Optional[str]:
    # Try common places for client IP
    headers = (
        (event.get("headers") or {}) if isinstance(event.get("headers"), dict) else {}
    )
    # X-Forwarded-For may hold comma-separated list, first is client
    for key in ("X-Forwarded-For", "x-forwarded-for", "X-Real-IP", "x-real-ip"):
        if key in headers and isinstance(headers[key], str):
            m = RE_IPv4.search(headers[key])
            if m:
                return m.group(0)
    # Fallback to requestContext identity
    rc = event.get("requestContext") or {}
    identity = rc.get("identity") or {}
    src_ip = identity.get("sourceIp")
    if isinstance(src_ip, str) and RE_IPv4.fullmatch(src_ip):
        return src_ip
    return None


def _parse_apigw_input(event: dict) -> Tuple[Any, int, Optional[str]]:
    """Parse API Gateway input.
    Returns (payload_or_text, status_code, error)
    - If JSON body: returns the parsed JSON (dict/list/etc.)
    - If text body or query ?text=: returns a string
    """
    headers = event.get("headers") or {}
    headers_ci = (
        {str(k).lower(): v for k, v in headers.items()}
        if isinstance(headers, dict)
        else {}
    )
    ctype = str(headers_ci.get("content-type", ""))

    body = event.get("body")
    is_b64 = bool(event.get("isBase64Encoded"))

    if body is not None:
        if is_b64:
            try:
                body = base64.b64decode(body).decode("utf-8", errors="replace")
            except Exception:
                return None, 400, "Invalid base64 body"
        # JSON body
        if "application/json" in ctype:
            try:
                data = json.loads(body) if isinstance(body, str) else body
            except Exception:
                return None, 400, "Invalid JSON body"
            return data, 200, None
        # Plain text
        return str(body), 200, None

    # Query string text
    qs = event.get("queryStringParameters") or {}
    if isinstance(qs, dict) and "text" in qs and isinstance(qs["text"], str):
        return qs["text"], 200, None

    return None, 400, "No body or query parameter provided"


def _build_item(payload_or_text: Any, event: dict) -> Dict[str, Any]:
    # Determine id
    provided_id: Optional[str] = None
    if isinstance(payload_or_text, dict):
        provided_id = (
            payload_or_text.get("id")
            if isinstance(payload_or_text.get("id"), str)
            else None
        )
    item_id = provided_id or str(uuid.uuid4())

    ip = _client_ip_from_event(event)

    item: Dict[str, Any] = {
        "id": item_id,
        "meta": {
            "source": "apigw",
            "received_at": _now_iso(),
        },
    }
    if ip:
        item["meta"]["ip"] = ip

    # Persist either as 'payload' (when JSON) or 'text' (when string)
    if isinstance(payload_or_text, dict):
        item["payload"] = payload_or_text
    else:
        item["text"] = str(payload_or_text)

    return item


def _build_item_from_direct_invoke(event: dict) -> Dict[str, Any]:
    item_id = event.get("id") if isinstance(event.get("id"), str) else str(uuid.uuid4())
    item: Dict[str, Any] = {
        "id": item_id,
        "meta": {
            "source": "direct",
            "received_at": _now_iso(),
        },
    }
    if isinstance(event.get("payload"), dict):
        item["payload"] = event["payload"]
    if isinstance(event.get("text"), str):
        item["text"] = event["text"]
    return item


def _put_and_respond(item: Dict[str, Any]) -> dict:
    table = _table()
    try:
        table.put_item(Item=item)
    except ClientError as e:
        return _response(500, {"error": "dynamodb_put_failed", "detail": str(e)})

    return _response(200, {"id": item["id"], "status": "stored"})


def _response(status: int, payload: dict) -> dict:
    return {
        "statusCode": status,
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "OPTIONS,GET,POST",
            "Access-Control-Allow-Headers": "Content-Type,Authorization",
        },
        "body": json.dumps(payload),
    }
