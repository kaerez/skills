#!/usr/bin/env python3
"""Derive a route-level sanitized HAR that keeps workflow evidence; never replay traffic.

Unlike har_minimize.py, this retains the evidence a consumption-only review needs:
method, path shape, GraphQL/RPC operation name, status and MIME type. It removes
header values, cookies, query values and bodies. Percent-encoded text is decoded
before redaction, and the output is re-scanned with independently constructed
patterns. Structural validity is not a de-identification certification.
"""

import argparse
import json
import re
import sys
from collections import Counter
from pathlib import Path
from urllib.parse import parse_qsl, unquote, urlsplit

from har_inventory import METHODS, SCHEMES, endpoint
from har_minimize import load_document, write_new

VERSION = "0.2.0"

# Redaction rules, applied per decoded path segment.
UUID_SHAPE = re.compile(r"(?i)[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}")
HEX_SEGMENT = re.compile(r"(?i)\A[0-9a-f]{12,}\Z")
TOKEN_SEGMENT = re.compile(r"(?i)\A[0-9a-z_-]{24,}\Z")
NUMERIC_SEGMENT = re.compile(r"\A[0-9]{6,}\Z")
SAFE_SEGMENT = re.compile(r"(?i)\A[0-9a-z][0-9a-z._@+-]{0,63}\Z")
OPERATION_NAME = re.compile(r"(?i)\A[a-z_][0-9a-z_]{0,63}\Z")
GRAPHQL_KEYWORD = re.compile(r"(?i)\b(query|mutation|subscription)\b")

# Query keys that carry tracking or recipient-scoped values: dropped, not placeheld.
TRACKING_KEYS = {
    "utm_source", "utm_medium", "utm_campaign", "utm_term", "utm_content", "utm_id",
    "mkt_tok", "gclid", "fbclid", "msclkid", "mc_cid", "mc_eid", "_hsenc", "_hsmi",
    "vero_id", "trk", "trkemail", "elqtrackid", "elqtrack", "pk_campaign",
}
# Header names whose presence is evidence; values are never retained.
SECURITY_HEADERS = {
    "authorization", "proxy-authorization", "cookie", "set-cookie", "x-api-key",
    "x-auth-token", "x-csrf-token", "x-xsrf-token", "x-amz-security-token",
    "www-authenticate", "origin", "referer", "sec-fetch-mode", "sec-fetch-site",
}

# Residual scan patterns. Built independently of the rules above: unanchored,
# no word boundaries, applied to raw, decoded and double-decoded output text.
RESIDUAL = {
    "uuid": re.compile(r"(?i)[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}"),
    "email": re.compile(r"(?i)[0-9a-z._%+-]+@[0-9a-z.-]+\.[a-z]{2,}"),
    "jwt": re.compile(r"[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}"),
    "long_token": re.compile(r"[A-Za-z0-9_-]{32,}"),
    "digit_run": re.compile(r"[0-9]{9,}"),
    "auth_scheme": re.compile(r"(?i)\b(bearer|basic|negotiate)\s+\S{8,}"),
    "private_key": re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----"),
}
# Placeholders this tool emits, excluded from residual matching.
PLACEHOLDER = re.compile(r"\{(?:uuid|token|hex|number|value|host)-?[0-9]*\}")


class Placeholders:
    """Stable per-run placeholders. The mapping is never written to the derivative."""

    def __init__(self):
        self.maps = {}
        self.order = []

    def get(self, kind, value):
        table = self.maps.setdefault(kind, {})
        if value not in table:
            table[value] = "{%s-%d}" % (kind, len(table) + 1)
            self.order.append({"kind": kind, "placeholder": table[value]})
        return table[value]

    def mapping(self):
        return {kind: dict(table) for kind, table in sorted(self.maps.items())}

    def counts(self):
        return {kind: len(table) for kind, table in sorted(self.maps.items())}


def shape_segment(segment, marks):
    """Replace an identifier-looking decoded segment; keep readable route names."""
    if not segment:
        return segment
    if UUID_SHAPE.fullmatch(segment):
        return marks.get("uuid", segment)
    if UUID_SHAPE.search(segment):
        return UUID_SHAPE.sub(lambda m: marks.get("uuid", m.group(0)), segment)
    if HEX_SEGMENT.fullmatch(segment):
        return marks.get("hex", segment)
    if TOKEN_SEGMENT.fullmatch(segment):
        return marks.get("token", segment)
    if NUMERIC_SEGMENT.fullmatch(segment):
        return marks.get("number", segment)
    if SAFE_SEGMENT.fullmatch(segment):
        return segment
    return marks.get("token", segment)


def shape_path(path, marks):
    """Percent-decode first, then redact. Encoded separators must not hide segments."""
    decoded = unquote(unquote(path)) if "%25" in path else unquote(path)
    decoded = decoded.replace("\\", "/")
    parts = [shape_segment(part, marks) for part in decoded.split("/")]
    return "/".join(parts) or "/"


def shape_query(query, marks, retain_keys):
    kept, dropped = [], []
    for name, value in parse_qsl(query, keep_blank_values=True):
        lowered = name.lower()
        if lowered in TRACKING_KEYS:
            dropped.append(lowered)
            continue
        if not SAFE_SEGMENT.fullmatch(name):
            name = marks.get("token", name)
        if lowered in retain_keys and SAFE_SEGMENT.fullmatch(value):
            kept.append({"name": name, "value": value})
        else:
            kept.append({"name": name, "value": "{value}" if value else ""})
    return kept, dropped


def text_of(container):
    text = container.get("text") if isinstance(container, dict) else None
    return text if isinstance(text, str) else ""


def operation_of(request):
    """Extract a GraphQL or RPC operation name without retaining the body."""
    found = {"name": None, "type": None, "source": None}
    post = request.get("postData")
    body = text_of(post)
    if body:
        try:
            parsed = json.loads(body)
        except ValueError:
            parsed = None
        candidates = parsed if isinstance(parsed, list) else [parsed]
        for item in candidates:
            if not isinstance(item, dict):
                continue
            name = item.get("operationName") or item.get("method")
            if isinstance(name, str) and OPERATION_NAME.fullmatch(name):
                found["name"] = name
                found["source"] = "postData"
            document = item.get("query")
            if isinstance(document, str):
                keyword = GRAPHQL_KEYWORD.search(document)
                if keyword:
                    found["type"] = keyword.group(1).lower()
            if found["name"]:
                break
    if not found["name"]:
        query = urlsplit(request.get("url", "")).query
        for name, value in parse_qsl(query, keep_blank_values=True):
            if name.lower() == "operationname" and OPERATION_NAME.fullmatch(value):
                found["name"] = value
                found["source"] = "queryString"
                break
    return found


def header_presence(container):
    headers = container.get("headers")
    names = []
    for header in headers if isinstance(headers, list) else []:
        if not isinstance(header, dict):
            continue
        name = header.get("name")
        if isinstance(name, str) and name.lower() in SECURITY_HEADERS:
            names.append(name.lower())
    return sorted(set(names))


def body_key_names(container, marks):
    body = text_of(container)
    if not body:
        return []
    try:
        parsed = json.loads(body)
    except ValueError:
        return []
    if not isinstance(parsed, dict):
        return []
    keys = []
    for key in list(parsed)[:20]:
        keys.append(key if OPERATION_NAME.fullmatch(str(key)) else marks.get("token", str(key)))
    return keys


def mime_of(container):
    content = container.get("content") if isinstance(container, dict) else None
    mime = content.get("mimeType") if isinstance(content, dict) else None
    if isinstance(mime, str) and SAFE_SEGMENT.fullmatch(mime.split(";")[0].replace("/", "-")):
        return mime.split(";")[0]
    return "unknown"


def validate_structure(document):
    """Report what can and cannot be parsed. Used by --validate-only and by sanitizing."""
    report = {
        "parses_as_json": True,
        "has_log_entries": False,
        "entries": 0,
        "malformed_entries": 0,
        "unsupported_urls": 0,
        "entries_with_request_body": 0,
        "entries_with_response_body": 0,
        "websocket_entries": 0,
        "exporter_extensions": [],
        "log_version": None,
        "creator": None,
    }
    log = document.get("log") if isinstance(document, dict) else None
    entries = log.get("entries") if isinstance(log, dict) else None
    if not isinstance(entries, list):
        return report
    report["has_log_entries"] = True
    report["entries"] = len(entries)
    version = log.get("version")
    report["log_version"] = version if isinstance(version, str) else None
    creator = log.get("creator")
    if isinstance(creator, dict) and isinstance(creator.get("name"), str):
        report["creator"] = creator["name"]
    extensions = {key for key in log if isinstance(key, str) and key.startswith("_")}
    for entry in entries:
        if not isinstance(entry, dict):
            report["malformed_entries"] += 1
            continue
        extensions |= {key for key in entry if isinstance(key, str) and key.startswith("_")}
        request = entry.get("request")
        response = entry.get("response")
        if not isinstance(request, dict) or not isinstance(response, dict):
            report["malformed_entries"] += 1
            continue
        try:
            endpoint(request.get("url"))
        except (ValueError, UnicodeError):
            report["unsupported_urls"] += 1
        if text_of(request.get("postData")):
            report["entries_with_request_body"] += 1
        if text_of(response.get("content")):
            report["entries_with_response_body"] += 1
        if entry.get("_webSocketMessages") or str(request.get("url", "")).startswith("ws"):
            report["websocket_entries"] += 1
    report["exporter_extensions"] = sorted(extensions)
    return report


def sanitize_document(document, retain_hosts=False, retain_query=(), retain_body_keys=False):
    log = document.get("log") if isinstance(document, dict) else None
    source_entries = log.get("entries") if isinstance(log, dict) else None
    if not isinstance(source_entries, list):
        raise ValueError("Input must contain log.entries as an array")
    marks = Placeholders()
    retain_keys = {key.lower() for key in retain_query}
    entries = []
    hosts = {}
    skipped = Counter()
    dropped_query_keys = Counter()
    operations = Counter()

    def host_mark(value):
        if retain_hosts:
            return value
        return marks.get("host", value).strip("{}")

    for entry in source_entries:
        if not isinstance(entry, dict):
            raise ValueError("Each HAR entry must be an object")
        request, response = entry.get("request"), entry.get("response")
        if not isinstance(request, dict) or not isinstance(response, dict):
            raise ValueError("Each HAR entry must contain request and response objects")
        split = urlsplit(str(request.get("url", "")))
        try:
            host, kind, scheme, port = endpoint(request.get("url"))
        except (ValueError, UnicodeError):
            skipped["unsupported_url"] += 1
            host, kind, scheme, port = None, "unknown", "https", 443
        if host is None:
            display = "unresolved-%d.invalid" % skipped["unsupported_url"]
        else:
            display = host_mark(host)
            if kind == "ip_literal" and ":" in display:
                display = "[%s]" % display
            hosts.setdefault(display, {"kind": kind, "requests": 0})
        path_shape = shape_path(split.path or "/", marks)
        query, dropped = shape_query(split.query, marks, retain_keys)
        for key in dropped:
            dropped_query_keys[key] += 1
        method = request.get("method")
        method = method.upper() if isinstance(method, str) else "UNKNOWN"
        if method not in METHODS:
            skipped["unknown_method"] += 1
            method = "UNKNOWN"
        status = response.get("status")
        if type(status) is not int or not 0 <= status <= 599:
            skipped["unknown_status"] += 1
            status = 0
        operation = operation_of(request)
        if operation["name"]:
            operations[operation["name"]] += 1
        if host is not None:
            hosts[display]["requests"] += 1
        port_text = "" if port == SCHEMES.get(scheme, 443) else ":%d" % port
        annotation = {
            "path_shape": path_shape,
            "operation": operation,
            "request_headers_present": header_presence(request),
            "response_headers_present": header_presence(response),
            "request_mime": mime_of({"content": request.get("postData")}),
            "response_mime": mime_of(response),
            "request_body_present": bool(text_of(request.get("postData"))),
            "response_body_present": bool(text_of(response.get("content"))),
            "websocket_messages_present": bool(entry.get("_webSocketMessages")),
        }
        if retain_body_keys:
            annotation["request_body_keys"] = body_key_names(request.get("postData"), marks)
        entries.append({
            "startedDateTime": "2000-01-01T00:00:00.000Z",
            "time": 0,
            "request": {
                "method": method,
                "url": "%s://%s%s%s" % (scheme, display, port_text, path_shape),
                "httpVersion": "unknown",
                "cookies": [], "headers": [], "queryString": query,
                "headersSize": -1, "bodySize": -1,
            },
            "response": {
                "status": status, "statusText": "", "httpVersion": "unknown",
                "cookies": [], "headers": [],
                "content": {"size": 0, "mimeType": annotation["response_mime"]},
                "redirectURL": "", "headersSize": -1, "bodySize": -1,
            },
            "cache": {}, "timings": {"send": 0, "wait": 0, "receive": 0},
            "_security_colleague": annotation,
        })

    structure = validate_structure(document)
    result = {"log": {
        "version": "1.2",
        "creator": {"name": "Security Colleague HAR sanitizer", "version": VERSION},
        "entries": entries,
        "_security_colleague": {
            "representation": "route-level sanitized derivative; not a capture and not replayable",
            "host_policy": "validated real hosts retained" if retain_hosts else "per-run synthetic host placeholders",
            "retained": [
                "entry order and count", "recognized methods and status codes",
                "percent-decoded path shape with identifiers placeheld",
                "query parameter names", "GraphQL/RPC operation names",
                "response MIME types", "presence of security-relevant header names",
            ],
            "omitted": [
                "header values", "cookies", "query parameter values",
                "request and response bodies", "WebSocket message contents",
                "timestamps and timings", "connection and IP metadata",
                "redirect targets", "pages and titles", "exporter extensions",
            ],
            "dropped_tracking_query_keys": dict(sorted(dropped_query_keys.items())),
            "placeholder_counts": marks.counts(),
            "placeholder_mapping_location": "separate --mapping file, or discarded",
            "host_count": len(hosts),
            "operation_names_observed": dict(sorted(operations.items())),
            "skipped": dict(sorted(skipped.items())),
            "source_structure": structure,
            "limits": [
                "not replayable", "not multilingual entity recognition",
                "not a de-identification certification",
                "path shape and operation names may still identify a tenant or product",
                "an omitted body is not an inspected body",
            ],
        },
    }}
    return result, marks


def residual_findings(serialized):
    """Scan the derivative with independently constructed patterns."""
    variants = {"as_written": serialized}
    decoded = unquote(serialized)
    if decoded != serialized:
        variants["percent_decoded"] = decoded
    twice = unquote(decoded)
    if twice != decoded:
        variants["double_decoded"] = twice
    findings = []
    for form, text in variants.items():
        scrubbed = PLACEHOLDER.sub(" ", text)
        for name, pattern in RESIDUAL.items():
            matches = pattern.findall(scrubbed)
            if matches:
                findings.append({"form": form, "pattern": name, "count": len(matches)})
    return findings


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path)
    parser.add_argument("--output", type=Path, help="Write the sanitized derivative here (new file only).")
    parser.add_argument("--mapping", type=Path, help="Write the placeholder mapping here. Treat as sensitive; never share it.")
    parser.add_argument("--retain-hosts", action="store_true", help="Retain validated real hostnames, which may identify tenants.")
    parser.add_argument("--retain-query", action="append", default=[], metavar="KEY", help="Retain this query parameter's value when it is a safe token.")
    parser.add_argument("--retain-body-keys", action="store_true", help="Retain top-level JSON request body key names.")
    parser.add_argument("--validate-only", action="store_true", help="Report parse coverage without writing a derivative.")
    parser.add_argument("--force", action="store_true", help="Write even when the residual scan reports findings.")
    parser.add_argument("--max-bytes", type=int, default=200 * 1024 * 1024)
    args = parser.parse_args()
    if args.max_bytes < 1:
        parser.error("--max-bytes must be positive")
    try:
        document = load_document(args.input, args.max_bytes)
    except ValueError as error:
        parser.error(str(error))
    if args.validate_only:
        sys.stdout.write(json.dumps(validate_structure(document), indent=2, sort_keys=True) + "\n")
        return
    if not args.output:
        parser.error("--output is required unless --validate-only is used")
    for path in (args.output, args.mapping):
        if path and path.resolve() == args.input.resolve():
            parser.error("Output and mapping must not overwrite the input")
    try:
        result, marks = sanitize_document(
            document, args.retain_hosts, args.retain_query, args.retain_body_keys)
    except ValueError as error:
        parser.error(str(error))
    serialized = json.dumps(result, ensure_ascii=True, allow_nan=False, indent=2)
    findings = residual_findings(serialized)
    result["log"]["_security_colleague"]["residual_scan"] = findings or "no findings within declared patterns"
    if findings and not args.force:
        sys.stderr.write(
            "Residual scan findings; nothing written. Review, widen redaction, or re-run with --force:\n"
            + json.dumps(findings, indent=2) + "\n")
        raise SystemExit(2)
    try:
        write_new(args.output, result)
        reparsed = json.loads(args.output.read_text(encoding="utf-8"))
        if len(reparsed["log"]["entries"]) != len(result["log"]["entries"]):
            parser.error("Output failed re-parse validation")
        if args.mapping:
            write_new(args.mapping, {"warning": "sensitive: keep out of shareable output",
                                     "mapping": marks.mapping()})
    except (ValueError, OSError, KeyError) as error:
        parser.error(str(error) if isinstance(error, ValueError) else "Cannot write output")
    print("Sanitized %d entries across %d hosts; residual scan: %s. Read log._security_colleague before sharing."
          % (len(result["log"]["entries"]),
             result["log"]["_security_colleague"]["host_count"],
             "findings present" if findings else "no findings within declared patterns"))


if __name__ == "__main__":
    main()
