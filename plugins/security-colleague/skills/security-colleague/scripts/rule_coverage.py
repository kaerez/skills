#!/usr/bin/env python3
"""Measure set coverage of a proposed host rule list against supplied evidence; no network, no DNS.

Answers the question a hand-written host list cannot answer for itself: which
observed hosts no rule names, which rules name nothing that was observed, and
whether the surface left over is finite. A rule set whose effective default is
allow leaves an unbounded surface reachable, so the tool says so instead of
publishing a count it cannot compute.
"""

import argparse
import ipaddress
import json
import sys
from pathlib import Path

from har_inventory import endpoint
from har_minimize import load_document

VERSION = "0.1.0"

ACTIONS = ("allow", "block")
RULE_KINDS = ("fqdn", "domain")
INVENTORY_KINDS = ("hostname", "ip_literal")
FORBIDDEN_IN_HOST = "/?#@%\t\r\n "


def normalize_host(value):
    """Validate one bare host and canonicalize it with the inventory URL parser."""
    if not isinstance(value, str):
        raise ValueError("A host must be text")
    text = value.strip().lower()
    if text.startswith("[") and text.endswith("]"):
        text = text[1:-1]
    if not text or any(character in text for character in FORBIDDEN_IN_HOST):
        raise ValueError(f"Not a bare host: {value!r}")
    try:
        address = ipaddress.ip_address(text)
    except ValueError:
        pass
    else:
        return address.compressed, "ip_literal"
    if ":" in text:
        raise ValueError(f"A host carries no scheme or port here: {value!r}")
    try:
        host, kind, _, _ = endpoint("https://" + text)
    except (ValueError, UnicodeError):
        raise ValueError(f"Not a valid host: {value!r}") from None
    return host, kind


def parse_rule(spec):
    """Parse one ACTION:KIND:VALUE rule, for example block:domain:example.invalid."""
    if not isinstance(spec, str):
        raise ValueError("A rule specification must be text")
    parts = spec.strip().split(":")
    if len(parts) != 3:
        raise ValueError(f"Use ACTION:KIND:VALUE for a rule, not {spec.strip()!r}")
    action, kind, value = (part.strip().lower() for part in parts)
    if action not in ACTIONS:
        raise ValueError(f"Rule action must be allow or block, not {action!r}")
    if kind not in RULE_KINDS:
        raise ValueError(f"Rule kind must be fqdn or domain, not {kind!r}")
    host, host_kind = normalize_host(value)
    if host_kind != "hostname":
        raise ValueError("Rule values must be DNS names; address rules are out of scope")
    if kind == "domain" and "." not in host:
        raise ValueError(f"A domain rule needs at least two labels, not {host!r}")
    return {"action": action, "kind": kind, "value": host, "spec": f"{action}:{kind}:{host}"}


def rule_matches(rule, host):
    """fqdn matches the exact name; domain matches the domain itself and any subdomain.

    Labels are compared as whole labels, never as a string suffix, so a domain
    rule for example.invalid does not match notexample.invalid.
    """
    if rule["kind"] == "fqdn":
        return host == rule["value"]
    host_labels = host.split(".")
    value_labels = rule["value"].split(".")
    return (len(host_labels) >= len(value_labels)
            and host_labels[len(host_labels) - len(value_labels):] == value_labels)


def decide(rules, host, default_action):
    """Apply the ordered rule list to one host, first match wins."""
    for index, rule in enumerate(rules):
        if rule_matches(rule, host):
            return {"host": host, "decision": rule["action"],
                    "matched_rule": rule["spec"], "matched_index": index}
    return {"host": host, "decision": default_action,
            "matched_rule": None, "matched_index": None}


def classify_shape(rules, default_action):
    """Name the shape of the rule set, because the shape decides the failure mode."""
    if not rules:
        return "empty"
    actions = {rule["action"] for rule in rules}
    if actions == {"block"} and default_action == "allow":
        return "blocklist"
    if actions == {"allow"} and default_action == "block":
        return "allowlist"
    return "combined"


def fail_open_note(default_action):
    """State whether the unenumerated surface is finite, without inventing a count."""
    if default_action == "allow":
        return {
            "unbounded": True,
            "explanation": (
                "The effective default is allow, so every host no rule names stays reachable. "
                "That residual surface is unbounded BY CONSTRUCTION: it is every name the client "
                "can resolve, present and future, and it cannot be enumerated from any capture. "
                "No count of at-risk hosts is emitted here because no honest count exists."),
        }
    return {
        "unbounded": False,
        "explanation": (
            "The effective default is block, so every host no rule names is denied. "
            "The reachable surface is finite and is exactly the set of hosts the allow rules "
            "match, which is listed host by host in effective_decisions."),
    }


def hosts_from_inventory(document):
    """Read hosts[].host and hosts[].kind from har_inventory.py output."""
    rows = document.get("hosts") if isinstance(document, dict) else None
    if not isinstance(rows, list):
        raise ValueError("Inventory evidence must contain hosts as an array")
    found = []
    for row in rows:
        if not isinstance(row, dict):
            raise ValueError("Each inventory host row must be an object")
        host, kind = normalize_host(row.get("host"))
        declared = row.get("kind")
        if declared not in INVENTORY_KINDS:
            raise ValueError("Each inventory host row needs kind hostname or ip_literal")
        if declared != kind:
            raise ValueError(f"Inventory kind {declared!r} disagrees with the parsed host {host!r}")
        found.append(host)
    return found


def hosts_from_lines(text):
    """Read a newline-delimited host list, as a gateway or firewall export supplies it."""
    found = []
    for number, line in enumerate(text.splitlines(), start=1):
        entry = line.split("#", 1)[0].strip()
        if not entry:
            continue
        try:
            host, _ = normalize_host(entry)
        except ValueError as error:
            raise ValueError(
                f"Evidence line {number} is not a bare host; the line is not echoed because "
                "evidence may carry tokens") from None
        found.append(host)
    if not found:
        raise ValueError("Evidence holds neither inventory JSON nor any host line")
    return found


def read_text(path, max_bytes):
    """Read one bounded UTF-8 text file."""
    try:
        with path.open("rb") as handle:
            data = handle.read(max_bytes + 1)
        if len(data) > max_bytes:
            raise ValueError("Input exceeds configured size limit")
        return data.decode("utf-8-sig")
    except (OSError, UnicodeError, ValueError):
        raise ValueError("Cannot read bounded UTF-8 evidence; check size, encoding and structure") from None


def load_evidence(path, max_bytes):
    """Accept har_inventory.py JSON or a plain host list; JSON is tried first."""
    try:
        document = load_document(path, max_bytes)
    except ValueError:
        return hosts_from_lines(read_text(path, max_bytes))
    return hosts_from_inventory(document)


def rules_from_file(path, max_bytes):
    """Read one rule specification per line; blank lines and # comments are ignored."""
    specs = []
    for line in read_text(path, max_bytes).splitlines():
        entry = line.split("#", 1)[0].strip()
        if entry:
            specs.append(entry)
    return specs


def build_report(evidence_hosts, rule_specs, default_action="allow"):
    """Compare an ordered rule list against the evidence and report what it misses."""
    if default_action not in ACTIONS:
        raise ValueError(f"Default action must be allow or block, not {default_action!r}")
    hostnames, literals = set(), set()
    for value in evidence_hosts:
        host, kind = normalize_host(value)
        if kind == "ip_literal":
            literals.add(host)
        else:
            hostnames.add(host)
    rules = [parse_rule(spec) for spec in rule_specs]
    decisions = [decide(rules, host, default_action) for host in sorted(hostnames)]
    uncovered = sorted(row["host"] for row in decisions if row["matched_rule"] is None)
    inert = sorted({rule["spec"] for rule in rules
                    if not any(rule_matches(rule, host) for host in hostnames)})
    return {
        "schema_version": 1,
        "tool": {"name": "rule_coverage", "version": VERSION},
        "scope": ("Set coverage of a proposed rule list against supplied evidence; no network, "
                  "no DNS, and no proof that the evidence itself is complete."),
        "default_action": default_action,
        "shape": classify_shape(rules, default_action),
        "fail_open": fail_open_note(default_action),
        "rules": [{"index": index, "action": rule["action"], "kind": rule["kind"],
                   "value": rule["value"], "spec": rule["spec"]}
                  for index, rule in enumerate(rules)],
        "uncovered_evidence_hosts": uncovered,
        "inert_rules": inert,
        "effective_decisions": decisions,
        "totals": {
            "evidence_hosts": len(hostnames),
            "ip_literals": len(literals),
            "rules": len(rules),
            "uncovered": len(uncovered),
            "inert": len(inert),
            "allowed": sum(1 for row in decisions if row["decision"] == "allow"),
            "blocked": sum(1 for row in decisions if row["decision"] == "block"),
        },
        "limitations": [
            "Coverage is measured only against the supplied evidence, so this report proves "
            "nothing about hosts absent from it and is not evidence that the host list is complete.",
            "Only driving the prohibited surface's own application and capturing the traffic it "
            "produces can find the hosts an evidence set never recorded; no review of a rule list can.",
            "An inert rule matched nothing in this evidence, which does not make it wrong: it may "
            "be a deliberate defensive entry for a host this evidence never reached.",
            "Matching semantics are modelled generically as exact-name and whole-label domain "
            "membership, so the selected engine's own parsing, wildcards, precedence and case "
            "folding must be verified against its documentation before these results are relied on.",
            "An evidence entry that is a valid DNS label but not a host - a bare token, an "
            "internal codename - is accepted and appears in this report, so review the evidence "
            "before sharing the output.",
            "No DNS resolution and no network input or output are performed, so a rule value that "
            "resolves to nothing is indistinguishable here from one that resolves correctly.",
            "Effective decisions describe the modelled rule list alone and do not prove that any "
            "enforcement point carries that list or that it is working.",
            "IP literals are counted but never matched, because name-based rules do not constrain "
            "a client that connects to an address directly.",
            "A rule set that defaults to allow leaves every host it does not name reachable, and "
            "any number offered as the size of that set is fabricated.",
        ],
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--evidence", action="append", default=[], type=Path, metavar="PATH",
        help="Repeat for each evidence file: har_inventory.py JSON or a newline-delimited host list.")
    parser.add_argument(
        "--rule", action="append", default=[], metavar="ACTION:KIND:VALUE",
        help="Repeatable and ordered, first match wins; ACTION is allow or block, KIND is fqdn or domain.")
    parser.add_argument(
        "--rules-file", type=Path, metavar="PATH",
        help="One rule specification per line, read after any --rule; # comments allowed.")
    parser.add_argument(
        "--default-action", choices=ACTIONS, default="allow",
        help="Action for a host no rule matches; allow models a firewall with no catch-all.")
    parser.add_argument("--max-bytes", type=int, default=50 * 1024 * 1024)
    parser.add_argument("--output", type=Path, help="Write JSON here; otherwise print to stdout.")
    args = parser.parse_args()
    if args.max_bytes < 1:
        parser.error("--max-bytes must be positive")
    if not args.evidence:
        parser.error("Supply --evidence at least once")
    inputs = list(args.evidence) + ([args.rules_file] if args.rules_file else [])
    if args.output and any(args.output.resolve() == path.resolve() for path in inputs):
        parser.error("Output must not overwrite an input file")
    try:
        specs = list(args.rule)
        if args.rules_file:
            specs += rules_from_file(args.rules_file, args.max_bytes)
        hosts = []
        for path in args.evidence:
            hosts += load_evidence(path, args.max_bytes)
        report = build_report(hosts, specs, args.default_action)
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
