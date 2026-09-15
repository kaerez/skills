#!/usr/bin/env python3
"""Create a lossy HAR derivative using an explicit metadata allowlist; never replay traffic."""

import argparse
import json
import os
import sys
from pathlib import Path

from har_inventory import METHODS, SCHEMES, endpoint

VERSION = "0.1.0"
HTTP_VERSIONS = {"HTTP/1.0", "HTTP/1.1", "HTTP/2", "HTTP/2.0", "HTTP/3", "HTTP/3.0"}


def reject_constant(_):
    raise ValueError("Non-finite JSON number")


def unique_object(pairs):
    obj = {}
    for key, value in pairs:
        if key in obj:
            raise ValueError("Duplicate JSON key")
        obj[key] = value
    return obj


def load_document(path, max_bytes):
    try:
        with path.open("rb") as handle:
            data = handle.read(max_bytes + 1)
        if len(data) > max_bytes:
            raise ValueError("Input exceeds configured size limit")
        return json.loads(data.decode("utf-8-sig"), parse_constant=reject_constant,
                          object_pairs_hook=unique_object)
    except (OSError, UnicodeError, ValueError, RecursionError):
        raise ValueError("Cannot read bounded, unambiguous UTF-8 HAR JSON; check size, encoding and structure") from None


def minimize_document(document, retain_hosts=False):
    log = document.get("log") if isinstance(document, dict) else None
    source_entries = log.get("entries") if isinstance(log, dict) else None
    if not isinstance(source_entries, list):
        raise ValueError("Input must contain log.entries as an array")
    hosts = {}
    entries = []
    unknown = {"urls": 0, "methods": 0, "statuses": 0, "http_versions": 0}
    for entry in source_entries:
        if not isinstance(entry, dict):
            raise ValueError("Each HAR entry must be an object")
        request, response = entry.get("request"), entry.get("response")
        if not isinstance(request, dict) or not isinstance(response, dict):
            raise ValueError("Each HAR entry must contain request and response objects")
        try:
            host, kind, scheme, port = endpoint(request.get("url"))
        except (ValueError, UnicodeError):
            unknown["urls"] += 1
            url = f"https://unresolved-{unknown['urls']}.invalid/redacted"
        else:
            if retain_hosts:
                target = f"[{host}]" if kind == "ip_literal" and ":" in host else host
            else:
                if host not in hosts:
                    hosts[host] = f"host-{len(hosts) + 1}.invalid"
                target = hosts[host]
            port_text = "" if port == SCHEMES[scheme] else f":{port}"
            url = f"{scheme}://{target}{port_text}/redacted"
        method = request.get("method")
        method = method.upper() if isinstance(method, str) else "UNKNOWN"
        if method not in METHODS:
            method = "UNKNOWN"
            unknown["methods"] += 1
        status = response.get("status")
        if type(status) is not int or not 0 <= status <= 599:
            status = 0
            unknown["statuses"] += 1
        versions = []
        for source in (request, response):
            version = source.get("httpVersion")
            if not isinstance(version, str) or version not in HTTP_VERSIONS:
                version = "unknown"
                unknown["http_versions"] += 1
            versions.append(version)
        entries.append({
            "startedDateTime": "2000-01-01T00:00:00.000Z",
            "time": 0,
            "request": {"method": method, "url": url, "httpVersion": versions[0],
                        "cookies": [], "headers": [], "queryString": [],
                        "headersSize": -1, "bodySize": -1},
            "response": {"status": status, "statusText": "", "httpVersion": versions[1],
                         "cookies": [], "headers": [],
                         "content": {"size": 0, "mimeType": "application/octet-stream"},
                         "redirectURL": "", "headersSize": -1, "bodySize": -1},
            "cache": {}, "timings": {"send": 0, "wait": 0, "receive": 0},
        })
    return {"log": {
        "version": "1.2",
        "creator": {"name": "Security Colleague HAR minimizer", "version": VERSION},
        "entries": entries,
        "_security_colleague": {
            "representation": "lossy reconstruction derived from supplied HAR; not a new capture",
            "host_policy": "validated real hosts/IPs retained" if retain_hosts else "per-file synthetic host pseudonyms",
            "retained": ["entry order/count", "recognized methods/status codes", "recognized HTTP versions", "schemes/ports", "host relationships"],
            "omitted": ["URL credentials/paths/queries/fragments", "headers/cookies", "request/response bodies", "redirect targets", "pages/titles", "timestamps/timings", "connection IDs/IP metadata", "comments", "exporter extensions"],
            "replacements": "fixed placeholder timestamp, synthetic zero timings, unknown sizes, generic MIME type",
            "unknown_fields": unknown,
            "limits": ["not replayable", "not entity detection", "not a complete original capture", "metadata may remain identifying", "not an anonymization certification"],
        },
    }}


def write_new(path, document):
    serialized = json.dumps(document, ensure_ascii=True, allow_nan=False, indent=2) + "\n"
    fd = None
    try:
        fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            fd = None
            handle.write(serialized)
    except OSError:
        if fd is not None:
            os.close(fd)
        raise ValueError("Cannot create output; it must be a new file in an existing writable directory") from None


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--retain-hosts", action="store_true", help="Retain validated real hostnames/IPs, which may identify people or tenants")
    parser.add_argument("--max-bytes", type=int, default=50 * 1024 * 1024)
    args = parser.parse_args()
    if args.max_bytes < 1:
        parser.error("--max-bytes must be positive")
    if args.input.resolve() == args.output.resolve():
        parser.error("Output must not overwrite input")
    try:
        result = minimize_document(load_document(args.input, args.max_bytes), args.retain_hosts)
        write_new(args.output, result)
    except (ValueError, OSError, RecursionError) as error:
        parser.error(str(error) if isinstance(error, ValueError) else "Unable to process HAR")
    print(f"Created minimized HAR with {len(result['log']['entries'])} entries; inspect its embedded coverage note before sharing.")


if __name__ == "__main__":
    main()
