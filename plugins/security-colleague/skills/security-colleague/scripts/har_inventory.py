#!/usr/bin/env python3
"""Summarize local HAR requests by host and workflow, without copying URL paths or secrets."""

import argparse
import ipaddress
import json
import re
import sys
import unicodedata
from collections import Counter
from pathlib import Path
from urllib.parse import urljoin, urlsplit


SCHEMES = {"http": 80, "https": 443, "ws": 80, "wss": 443}
METHODS = {"GET", "HEAD", "POST", "PUT", "DELETE", "CONNECT", "OPTIONS", "TRACE", "PATCH"}
REDIRECT_STATUSES = {300, 301, 302, 303, 307, 308}
LABEL = re.compile(r"[A-Za-z0-9][A-Za-z0-9_.-]{0,63}\Z")
DNS_LABEL = re.compile(r"[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\Z")


def endpoint(url):
    if not isinstance(url, str) or any(ord(c) < 32 for c in url):
        raise ValueError("Invalid URL")
    parsed = urlsplit(url.strip())
    if parsed.scheme not in SCHEMES or not parsed.hostname:
        raise ValueError("Unsupported URL")
    hostname = parsed.hostname.lower()
    if hostname.endswith("."):
        hostname = hostname[:-1]
    try:
        address = ipaddress.ip_address(hostname)
    except ValueError:
        ascii_hostname = hostname.encode("idna").decode("ascii").lower()
        # Reject lossy IDNA2003 mappings (for example, sharp-s to "ss").
        # Use the browser-reported ASCII hostname for such unresolved names.
        if not hostname.isascii() and ascii_hostname.encode("ascii").decode("idna") != unicodedata.normalize("NFC", hostname):
            raise ValueError("Ambiguous IDN mapping")
        hostname = ascii_hostname
        if len(hostname) > 253 or not all(DNS_LABEL.fullmatch(p) for p in hostname.split(".")):
            raise ValueError("Invalid hostname")
        kind = "hostname"
    else:
        if "%" in hostname:
            raise ValueError("Scoped address unsupported")
        hostname = address.compressed
        kind = "ip_literal"
    port = parsed.port if parsed.port is not None else SCHEMES[parsed.scheme]
    if not 1 <= port <= 65535:
        raise ValueError("Invalid port")
    return hostname, kind, parsed.scheme, port


def host_row(hosts, host, kind):
    if host not in hosts:
        hosts[host] = {
            "host": host,
            "kind": kind,
            "captured_requests": 0,
            "by_workflow": {},
            "redirect_references_by_workflow": Counter(),
        }
    return hosts[host]


def workflow_row(host, label):
    if label not in host["by_workflow"]:
        host["by_workflow"][label] = {
            "requests": 0,
            "methods": Counter(),
            "schemes": Counter(),
            "ports": Counter(),
            "response_statuses": Counter(),
        }
    return host["by_workflow"][label]


def load_capture(path, label):
    try:
        with path.open(encoding="utf-8-sig") as handle:
            document = json.load(handle)
    except (OSError, UnicodeError, ValueError):
        raise ValueError(f"Cannot read valid JSON for capture {label}") from None
    log = document.get("log") if isinstance(document, dict) else None
    entries = log.get("entries") if isinstance(log, dict) else None
    if not isinstance(entries, list):
        raise ValueError(f"Capture {label} must contain log.entries as an array")
    return entries


def summarize(captures):
    hosts = {}
    redirects = Counter()
    summaries = []
    for label, path in captures:
        entries = load_capture(path, label)
        summary = {
            "workflow": label,
            "entries": len(entries),
            "captured_requests": 0,
            "skipped_requests": 0,
            "skipped_redirects": 0,
        }
        for entry in entries:
            request = entry.get("request") if isinstance(entry, dict) else None
            if not isinstance(request, dict):
                summary["skipped_requests"] += 1
                continue
            url = request.get("url")
            try:
                hostname, kind, scheme, port = endpoint(url)
            except (ValueError, UnicodeError):
                summary["skipped_requests"] += 1
                continue
            host = host_row(hosts, hostname, kind)
            usage = workflow_row(host, label)
            host["captured_requests"] += 1
            summary["captured_requests"] += 1
            usage["requests"] += 1
            method = request.get("method")
            method = method.upper() if isinstance(method, str) else "UNKNOWN"
            usage["methods"][method if method in METHODS else "OTHER_OR_UNKNOWN"] += 1
            usage["schemes"][scheme] += 1
            usage["ports"][str(port)] += 1
            response = entry.get("response")
            if not isinstance(response, dict):
                response = {}
            status = response.get("status")
            status_key = str(status) if type(status) is int and 0 <= status <= 599 else "unknown"
            usage["response_statuses"][status_key] += 1

            # Prefer HAR's redirectURL; inspect Location only as a fallback.
            target = response.get("redirectURL")
            if not target and type(status) is int and status in REDIRECT_STATUSES:
                headers = response.get("headers", [])
                for header in headers if isinstance(headers, list) else []:
                    if not isinstance(header, dict):
                        continue
                    name = header.get("name")
                    if isinstance(name, str) and name.lower() == "location":
                        target = header.get("value")
                        break
            if target:
                try:
                    if not isinstance(target, str) or any(ord(c) < 32 for c in target):
                        raise ValueError("Invalid redirect")
                    dest, dest_kind, _, _ = endpoint(urljoin(url, target))
                except (ValueError, UnicodeError):
                    summary["skipped_redirects"] += 1
                else:
                    target_row = host_row(hosts, dest, dest_kind)
                    target_row["redirect_references_by_workflow"][label] += 1
                    redirects[(label, hostname, dest)] += 1
        summary["hosts_with_captured_requests"] = sum(
            1 for row in hosts.values() if label in row["by_workflow"])
        summaries.append(summary)
    shared = sorted(
        name for name, row in hosts.items() if len(row["by_workflow"]) > 1)
    totals = {
        "host_count": len(hosts),
        "hostname_count": sum(1 for row in hosts.values() if row["kind"] == "hostname"),
        "ip_literal_count": sum(1 for row in hosts.values() if row["kind"] == "ip_literal"),
        "hosts_with_captured_requests": sum(
            1 for row in hosts.values() if row["captured_requests"]),
        "redirect_only_host_count": sum(
            1 for row in hosts.values() if not row["captured_requests"]),
        "shared_across_workflows_count": len(shared),
        "shared_across_workflows": shared,
        "captured_request_count": sum(row["captured_requests"] for row in hosts.values()),
    }
    return {
        "schema_version": 2,
        "totals": totals,
        "scope": "Host inventory only; workflow labels are supplied, not inferred actions.",
        "omitted": [
            "input filenames", "URL paths", "queries", "fragments", "userinfo",
            "cookies", "header values", "request bodies", "response bodies",
        ],
        "limitations": [
            "Observed requests and redirect references do not prove necessity or action success.",
            "A redirect target with no captured requests was not observed being fetched.",
            "Absence from a capture does not prove an action is blocked or a host is unused.",
            "No network requests, DNS resolution, action classification, or rule generation performed.",
            "Review skipped-request counts: invalid/unsupported URLs and lossily mapped IDNs are omitted.",
            "Hostnames and workflow labels may themselves identify tenants; review before sharing.",
            "Quote counts from totals rather than counting host rows by hand.",
            "Host-level methods cannot separate a permitted write from a prohibited one; use har_sanitize.py for route evidence.",
        ],
        "captures": summaries,
        "hosts": [hosts[name] for name in sorted(hosts)],
        "redirect_host_edges": [
            {"workflow": label, "from_host": source, "to_host": target, "references": count}
            for (label, source, target), count in sorted(redirects.items())
        ],
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--capture", action="append", required=True, metavar="WORKFLOW=FILE.har",
        help="Repeat for each workflow capture; labels must be unique and contain no personal information.",
    )
    parser.add_argument("--output", type=Path, help="Write JSON here; otherwise print to stdout.")
    args = parser.parse_args()
    captures = []
    labels = set()
    for item in args.capture:
        label, separator, filename = item.partition("=")
        if not separator or not LABEL.fullmatch(label) or not filename:
            parser.error("Use WORKFLOW=FILE.har with a 1-64 character alphanumeric/dot/dash/underscore label")
        if label in labels:
            parser.error(f"Duplicate workflow label: {label}")
        labels.add(label)
        captures.append((label, Path(filename)))
    if args.output and any(args.output.resolve() == path.resolve() for _, path in captures):
        parser.error("Output must not overwrite an input capture")
    try:
        report = summarize(captures)
    except ValueError as exc:
        parser.error(str(exc))
    serialized = json.dumps(report, ensure_ascii=True, indent=2, sort_keys=True) + "\n"
    if args.output:
        try:
            args.output.write_text(serialized, encoding="utf-8")
        except OSError:
            parser.error("Cannot write the output file")
    else:
        sys.stdout.write(serialized)


if __name__ == "__main__":
    main()
