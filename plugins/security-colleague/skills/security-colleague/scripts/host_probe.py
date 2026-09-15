#!/usr/bin/env python3
"""Resolve candidate hosts and their alias chains using DNS only; never send HTTP.

Enumerates regional and cluster variants a vendor may not document, records the
CNAME chain and the terminating provider, and compares answers across chosen
resolvers so split-horizon or geo-DNS differences are visible. Resolution proves
a name exists, not that a service is reachable or that an action would succeed.
"""

import argparse
import ipaddress
import json
import random
import re
import socket
import struct
import sys
from pathlib import Path

VERSION = "0.2.0"

NAMED_RESOLVERS = {
    "system": [],
    "google": ["8.8.8.8", "8.8.4.4"],
    "cloudflare": ["1.1.1.1", "1.0.0.1"],
    "quad9": ["9.9.9.9", "149.112.112.112"],
    "opendns": ["208.67.222.222", "208.67.220.220"],
}
TYPES = {"A": 1, "AAAA": 28, "CNAME": 5}
HOSTNAME = re.compile(r"(?i)\A[0-9a-z]([0-9a-z-]{0,61}[0-9a-z])?(\.[0-9a-z]([0-9a-z-]{0,61}[0-9a-z])?)+\.?\Z")
CLUSTER_LABEL = re.compile(r"(?i)\A(?P<stem>[a-z-]*?)(?P<number>[0-9]+)\Z")

# Terminating-provider classification by alias suffix. Extend deliberately.
PROVIDERS = (
    (".cloudfront.net", "AWS CloudFront"),
    (".elb.amazonaws.com", "AWS Elastic Load Balancing"),
    (".amazonaws.com", "AWS (other service)"),
    (".cdn.cloudflare.net", "Cloudflare"),
    (".cloudflare.net", "Cloudflare"),
    (".edgekey.net", "Akamai"),
    (".akamaiedge.net", "Akamai"),
    (".akamai.net", "Akamai"),
    (".fastly.net", "Fastly"),
    (".azureedge.net", "Azure CDN"),
    (".trafficmanager.net", "Azure Traffic Manager"),
    (".ghs.googlehosted.com", "Google"),
    (".googlehosted.com", "Google"),
)
REGION_IN_NAME = re.compile(r"(?i)\b((?:us|eu|ap|ca|sa|me|af|il)-(?:east|west|central|north|south|northeast|southeast)-?[0-9]?)\b")


def classify(name):
    lowered = name.lower().rstrip(".")
    for suffix, provider in PROVIDERS:
        if lowered.endswith(suffix):
            region = REGION_IN_NAME.search(lowered)
            return provider + (" (%s)" % region.group(1) if region else "")
    return "unclassified"


def encode_name(name):
    parts = [part for part in name.rstrip(".").split(".") if part]
    out = b""
    for part in parts:
        encoded = part.encode("idna") if not part.isascii() else part.encode("ascii")
        if not 1 <= len(encoded) <= 63:
            raise ValueError("Invalid DNS label")
        out += bytes([len(encoded)]) + encoded
    return out + b"\x00"


def decode_name(data, offset, depth=0):
    labels = []
    if depth > 10:
        raise ValueError("Compression loop")
    while True:
        if offset >= len(data):
            raise ValueError("Truncated name")
        length = data[offset]
        if length == 0:
            return ".".join(labels), offset + 1
        if length & 0xC0 == 0xC0:
            if offset + 1 >= len(data):
                raise ValueError("Truncated pointer")
            pointer = ((length & 0x3F) << 8) | data[offset + 1]
            nested, _ = decode_name(data, pointer, depth + 1)
            labels.append(nested) if nested else None
            return ".".join(labels), offset + 2
        offset += 1
        if offset + length > len(data):
            raise ValueError("Truncated label")
        labels.append(data[offset:offset + length].decode("ascii", "replace"))
        offset += length


def build_query(name, qtype, qid):
    header = struct.pack("!HHHHHH", qid, 0x0100, 1, 0, 0, 0)
    return header + encode_name(name) + struct.pack("!HH", qtype, 1)


def parse_response(data, qid, question=None):
    """Accept an answer only if it is a reply to the query actually sent.

    The transaction id alone is 16 bits. Require the response bit and, when the
    caller supplies the name it asked for, require the question section to echo
    it. This raises the cost of an off-path forgery; it does not authenticate
    the answer, which still has no DNSSEC validation.
    """
    if len(data) < 12:
        raise ValueError("Short response")
    rid, flags, qdcount, ancount, _, _ = struct.unpack("!HHHHHH", data[:12])
    if rid != qid:
        raise ValueError("Transaction id mismatch")
    if not flags & 0x8000:
        raise ValueError("Not a response")
    truncated = bool(flags & 0x0200)
    rcode = flags & 0x000F
    offset = 12
    asked = []
    for _ in range(qdcount):
        echoed, offset = decode_name(data, offset)
        asked.append(echoed.lower().rstrip("."))
        offset += 4
    if question is not None and asked != [question.lower().rstrip(".")]:
        raise ValueError("Question section does not echo the query")
    answers = []
    for _ in range(ancount):
        owner, offset = decode_name(data, offset)
        if offset + 10 > len(data):
            raise ValueError("Truncated record")
        rtype, _, ttl, rdlength = struct.unpack("!HHIH", data[offset:offset + 10])
        offset += 10
        rdata = data[offset:offset + rdlength]
        if rtype == TYPES["CNAME"]:
            target, _ = decode_name(data, offset)
            answers.append({"owner": owner, "type": "CNAME", "value": target, "ttl": ttl})
        elif rtype == TYPES["A"] and rdlength == 4:
            answers.append({"owner": owner, "type": "A", "value": str(ipaddress.IPv4Address(rdata)), "ttl": ttl})
        elif rtype == TYPES["AAAA"] and rdlength == 16:
            answers.append({"owner": owner, "type": "AAAA", "value": str(ipaddress.IPv6Address(rdata)), "ttl": ttl})
        offset += rdlength
    return {"rcode": rcode, "truncated": truncated, "answers": answers}


def ask(resolver, name, qtype, timeout, retries=2, port=53):
    """One UDP query with TCP fallback on truncation. No HTTP, no DoH.

    The datagram socket is connected before sending so the kernel discards
    replies from any source other than the chosen resolver.
    """
    last = None
    for _ in range(retries):
        qid = random.SystemRandom().randrange(1, 65535)
        packet = build_query(name, TYPES[qtype], qid)
        family = socket.AF_INET6 if ":" in resolver else socket.AF_INET
        try:
            with socket.socket(family, socket.SOCK_DGRAM) as sock:
                sock.settimeout(timeout)
                sock.connect((resolver, port))
                sock.send(packet)
                data = sock.recv(4096)
            parsed = parse_response(data, qid, name)
            if not parsed["truncated"]:
                return parsed
            with socket.socket(family, socket.SOCK_STREAM) as sock:
                sock.settimeout(timeout)
                sock.connect((resolver, port))
                sock.sendall(struct.pack("!H", len(packet)) + packet)
                prefix = sock.recv(2)
                length = struct.unpack("!H", prefix)[0] if len(prefix) == 2 else 0
                body = b""
                while len(body) < length:
                    chunk = sock.recv(length - len(body))
                    if not chunk:
                        break
                    body += chunk
            return parse_response(body, qid, name)
        except (OSError, ValueError, struct.error) as error:
            last = "%s: %s" % (type(error).__name__, error)
    return {"error": last or "no answer"}


def resolve_with(resolver, name, timeout, port=53):
    chain, addresses, errors = [], [], []
    current = name
    for _ in range(6):
        answer = ask(resolver, current, "A", timeout, port=port)
        if "error" in answer:
            errors.append(answer["error"])
            break
        if answer["rcode"] == 3:
            return {"exists": False, "rcode": "NXDOMAIN", "chain": chain, "addresses": [], "errors": errors}
        if answer["rcode"] != 0:
            errors.append("rcode=%d" % answer["rcode"])
            break
        cnames = [record["value"] for record in answer["answers"] if record["type"] == "CNAME"]
        addresses = [record["value"] for record in answer["answers"] if record["type"] == "A"]
        if cnames:
            chain.extend(cnames)
            if addresses:
                break
            current = cnames[-1]
            continue
        break
    return {"exists": bool(addresses or chain), "rcode": "NOERROR" if addresses or chain else "UNKNOWN",
            "chain": chain, "addresses": addresses, "errors": errors}


def resolve_system(name):
    try:
        canonical, aliases, addresses = socket.gethostbyname_ex(name)
    except OSError as error:
        return {"exists": False, "rcode": "NXDOMAIN" if getattr(error, "errno", None) in (-2, -5) else "ERROR",
                "chain": [], "addresses": [], "errors": ["%s: %s" % (type(error).__name__, error)]}
    chain = [entry for entry in ([canonical] + list(aliases)) if entry and entry != name]
    return {"exists": True, "rcode": "NOERROR", "chain": chain, "addresses": addresses, "errors": []}


def variants(host, region_labels, cluster_span):
    """Generate plausible regional and cluster siblings. Candidates, not findings."""
    out = {host}
    labels = host.split(".")
    for region in region_labels:
        if len(labels) > 1:
            out.add(".".join([labels[0], region] + labels[1:]))
        out.add(".".join(labels[:1] + [labels[1] + "-" + region] + labels[2:]) if len(labels) > 2 else host)
    for index, label in enumerate(labels):
        match = CLUSTER_LABEL.fullmatch(label)
        if not match:
            continue
        number = int(match.group("number"))
        for delta in range(-cluster_span, cluster_span + 1):
            if delta == 0 or number + delta < 0:
                continue
            sibling = list(labels)
            sibling[index] = "%s%d" % (match.group("stem"), number + delta)
            out.add(".".join(sibling))
        for region in region_labels:
            sibling = list(labels)
            sibling[index] = "%s%s-%d" % (match.group("stem"), region, number)
            out.add(".".join(sibling))
    return sorted(name for name in out if HOSTNAME.fullmatch(name))


def hosts_from_inventory(path):
    document = json.loads(path.read_text(encoding="utf-8"))
    rows = document.get("hosts") if isinstance(document, dict) else None
    found = []
    for row in rows if isinstance(rows, list) else []:
        name = row.get("host") if isinstance(row, dict) else None
        if isinstance(name, str) and row.get("kind") == "hostname":
            found.append(name)
    return found


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--host", action="append", default=[], help="Repeat for each candidate host.")
    parser.add_argument("--from-inventory", type=Path, help="Read hostnames from har_inventory.py JSON output.")
    parser.add_argument("--resolver", action="append", default=[], metavar="NAME_OR_IP",
                        help="system, google, cloudflare, quad9, opendns, or an IP address. Repeatable.")
    parser.add_argument("--exclude-resolver", action="append", default=[], metavar="NAME",
                        help="Named resolver to exclude, for instructions such as 'do not use Google DNS'.")
    parser.add_argument("--variants", action="store_true", help="Also probe generated regional and cluster siblings.")
    parser.add_argument("--region-label", action="append", default=["eu", "us", "ap"], metavar="LABEL")
    parser.add_argument("--cluster-span", type=int, default=1, help="Probe cluster numbers within this distance.")
    parser.add_argument("--timeout", type=float, default=3.0)
    parser.add_argument("--dry-run", action="store_true", help="Print candidates and perform zero lookups.")
    parser.add_argument("--output", type=Path, help="Write JSON here; otherwise print to stdout.")
    args = parser.parse_args()

    candidates = list(args.host)
    if args.from_inventory:
        try:
            candidates += hosts_from_inventory(args.from_inventory)
        except (OSError, ValueError):
            parser.error("Cannot read hostnames from the supplied inventory JSON")
    candidates = [name.lower().rstrip(".") for name in candidates]
    bad = [name for name in candidates if not HOSTNAME.fullmatch(name)]
    if bad:
        parser.error("Not valid hostnames: %s" % ", ".join(sorted(set(bad))[:5]))
    if not candidates:
        parser.error("Supply --host or --from-inventory")
    if args.cluster_span < 0:
        parser.error("--cluster-span must not be negative")

    targets = sorted(set(candidates))
    if args.variants:
        expanded = set()
        for name in candidates:
            expanded |= set(variants(name, args.region_label, args.cluster_span))
        targets = sorted(expanded)

    excluded = {name.lower() for name in args.exclude_resolver}
    selected = []
    for choice in args.resolver or ["system"]:
        lowered = choice.lower()
        if lowered in excluded:
            continue
        if lowered in NAMED_RESOLVERS:
            selected.append({"label": lowered, "addresses": NAMED_RESOLVERS[lowered]})
        else:
            try:
                ipaddress.ip_address(choice)
            except ValueError:
                parser.error("Unknown resolver %r; use a name or an IP address" % choice)
            selected.append({"label": choice, "addresses": [choice]})
    if not selected:
        parser.error("Every requested resolver was excluded")

    report = {
        "schema_version": 1,
        "tool": {"name": "host_probe", "version": VERSION},
        "scope": "DNS queries only; no HTTP request, no TLS handshake, no traffic to the service.",
        "limitations": [
            "Resolution proves a name exists, not that a service is reachable or an action succeeds.",
            "NXDOMAIN for a generated variant does not prove a vendor has no other clusters or regions.",
            "Addresses rotate; do not build address-based rules from this output.",
            "Provider classification comes from alias suffixes and may be incomplete.",
            "Generated variants are candidates, not evidence of vendor architecture.",
            "Answers are unauthenticated: no DNSSEC validation. Replies from a source other than "
            "the chosen resolver are discarded, and the question section must echo the query, but "
            "an on-path attacker can still forge an answer. Corroborate across resolvers and treat "
            "this as discovery, not proof.",
        ],
        "resolvers": [item["label"] for item in selected],
        "excluded_resolvers": sorted(excluded),
        "candidates": targets,
        "candidate_count": len(targets),
        "dry_run": bool(args.dry_run),
        "results": [],
    }
    if not args.dry_run:
        for name in targets:
            row = {"host": name, "by_resolver": {}, "providers": [], "divergent": False}
            seen = set()
            for item in selected:
                if item["label"] == "system":
                    answer = resolve_system(name)
                else:
                    answer = resolve_with(item["addresses"][0], name, args.timeout)
                answer["providers"] = sorted({classify(target) for target in answer["chain"]} - {"unclassified"})
                row["by_resolver"][item["label"]] = answer
                seen.add(tuple(sorted(answer["chain"])) if answer["exists"] else ("__absent__",))
            row["divergent"] = len(seen) > 1
            chains = [answer["chain"] for answer in row["by_resolver"].values() if answer["exists"]]
            row["providers"] = sorted({classify(target) for chain in chains for target in chain} - {"unclassified"})
            row["exists"] = any(answer["exists"] for answer in row["by_resolver"].values())
            report["results"].append(row)
        report["resolved_count"] = sum(1 for row in report["results"] if row["exists"])
        report["divergent_count"] = sum(1 for row in report["results"] if row["divergent"])

    serialized = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if args.output:
        try:
            args.output.write_text(serialized, encoding="utf-8")
        except OSError:
            parser.error("Cannot write the output file")
    else:
        sys.stdout.write(serialized)


if __name__ == "__main__":
    main()
