# Changelog

**TLP:GREEN · (C) Erez Kalman**

## 0.4.0 — Make the rules reach a run, then measure them, 2026-09-16

Verified: repository validation and all 60 regression tests pass on Python 3.12
on Linux, macOS and Windows ([CI run](https://github.com/kaerez/skills/actions/runs/35053423387)).
Unverified: any client installation, update or session reload, and live
enforcement behaviour.

A full-package audit after 0.3.0 found that release did not deliver its headline
fix in the delivery mode where the failure was observed. `SKILL.md` is always
loaded; `report-format.md` is consulted only for a requested detailed report,
and a brief engagement is told to return a decision without it. The rule-shape
verdict lived only in `report-format.md`, so a brief consumption review — the
shape that motivated 0.3.0 — never produced one.

- **Reach.** State the rule-shape verdict at every depth, brief included, with
  the precedence a default-deny-plus-allows shape needs to mean anything: the
  same two rules in the opposite order is a different policy. State in
  `SKILL.md` that a fired capture trigger interrupts the ladder, rather than
  leaving only the unqualified "exhaust read-only retrieval first". Restore the
  Provisional and Unresolved carve-out dropped on the way into `SKILL.md`, where
  a blanket ban contradicted six passages requiring the word.
- **`scripts/rule_coverage.py` is now invoked by the procedures that decide a
  rule set**, with a command block. It shipped in 0.3.0 referenced only by the
  tool inventory, so a run would hand-assert fail-openness and never call the
  checker written to compute it.
- **Three disciplines for every task**, in `SKILL.md` above the procedure table:
  publish the bound with the set, state the verdict before the evidence, and let
  an unresolved item name the evidence that would resolve it. These were written
  for the consumption-review track only; the other task types now inherit them.
  `references/security-investigation.md` gains the bound requirement it lacked.
- **One evidence vocabulary.** `SKILL.md`'s observed / documented / inferred /
  unknown / tested is canonical. A reference may refine a label but not
  introduce a competing set; `report-format.md`'s stray "Confirmed" is gone.
- **`references/regex.md`** learns about the defect that caused 0.2.0:
  percent-decode before applying a pattern, and construct the verifying pattern
  independently of the redacting one. It was documented in three other files and
  absent from the one a regex author opens.
- **Deterministic prose guards** in `tools/validate_repository.py`: markdown
  table shape, `#anchor` fragment resolution, an assertion that every section a
  changelog bullet names still exists in the file it names, and a 1024-character
  frontmatter description bound. Each was shown failing against a deliberately
  broken copy before it counted. The table guard reproduces the `eff80d4`
  defect, which the validator previously passed and a human caught.
- **A security review of `scripts/rule_coverage.py`**, owed from 0.3.0 and not
  run then. Matching is correct across trailing dots, case, lookalike
  registrable names and homoglyphs, which punycode-normalize and so surface as
  uncovered rather than silently matching an ASCII rule. Two findings fixed: a
  malformed evidence line was echoed in the error, and evidence derived from a
  captured service may carry a token, so the line is no longer reproduced; and
  a bare label that is not a host is accepted and reaches the report, now named
  in the tool's own limitations.
- **An eval harness** at `evals/security_colleague/`, outside the shipped skill
  directory so fixtures do not reach every install. Five evals derived from
  observed failures, with a baseline arm, because an assertion that passes with
  or without the skill measures nothing. The runners call a model, so they are
  deliberately not wired into CI: run on demand and commit the dated record.

## 0.3.0 — Enumeration completeness, capture triggers, rule-shape verdict, 2026-09-15

Verified: repository validation and all 59 regression tests pass on Python 3.12
on Linux, macOS and Windows ([CI run](https://github.com/kaerez/skills/actions/runs/34998754101)) — 41
inherited plus 18 for the new rule-coverage check. Unverified: any client
installation, update or session reload, and live enforcement behaviour.

Two reviewed transcripts of one consumption review, both running 0.2.0, failed
the same way: each produced a host blocklist that read as complete, stated its
bound only when interrogated, never asked for a capture, and never said which
rule shape was right. Both had retrieved the permitted surface and neither had
retrieved the prohibited one, where the missing hosts were declared in shipped
configuration — including one filed as absent on a negative DNS result.

- Report format: new **Rule shape** section, required and stated before any host
  list. It names blocklist, allowlist and combined, the fact that decides
  between them, and each shape's failure mode. A blocklist must be complete to
  work and cannot be shown to be; an allowlist must be complete to avoid
  breakage and shows its own gaps.
- Consumption review: new retrieval rung — retrieve the prohibited surface's own
  application and read its configuration and bundles. Configuration shipped in
  code outranks a negative DNS result.
- Consumption review: state every enumerated set's method and bound in the same
  breath, volunteered at the first host list rather than on request; a host the
  user has to supply is a finding about the method.
- Consumption review: requesting a capture becomes a triggered step with four
  named triggers, not a last resort.
- Consumption review: fan enumeration out across surfaces where the host offers
  parallel execution; each returned report is a claim to verify.
- Enforcement: enumerating to block and enumerating to allow are not symmetric,
  and the asymmetry decides the rule shape.
- SKILL.md: the skill governs every later turn of the session, including
  follow-ups, tool results and answers from another model; a follow-up naming a
  missed host is a finding about the enumeration method, not a lookup request.
- SKILL.md: report the model and reasoning effort the host exposes, and state
  that a weaker model or reduced effort degrades these results.
- SKILL.md and report format: do not substitute a maturity label — pilot, draft,
  first pass, proof of concept — for a statement of coverage. Provisional and
  Unresolved remain correct when tied to a named gap and a next observation.
- Report format: an Unresolved row must name the capture that would resolve it.
- Evidence: four new rows, including that NXDOMAIN does not establish absence and
  that a bounded sweep does not establish completeness.
- Add `scripts/rule_coverage.py`: check a proposed allow/block list against the
  hosts actually in evidence — uncovered hosts, rules matching nothing, the
  effective decision per host after precedence, and whether the shape is
  fail-open. Under a default-allow shape it reports the surface as unbounded by
  construction rather than publishing a count it cannot compute.
- Remove third-party vendor and product names from the skill text and fixtures.
  Enforcement entry points keep their lessons without the names; generic
  engine-semantics references and provider classification code are unaffected.

## 0.2.0 — Retrieval ladder and route-level evidence, 2026-09-15

Verified: repository validation and all 41 regression tests pass on Python 3.12
on Linux, macOS and Windows ([CI run](https://github.com/kaerez/skills/actions/runs/34990618029)).
Unverified: any client installation, update or session reload, and live
enforcement behaviour.

- Add `scripts/har_sanitize.py`: route-level sanitized HAR derivative that keeps
  method, decoded path shape, operation name, status and MIME type while removing
  header values, cookies, query values and bodies. Percent-decodes before
  redacting, keeps the placeholder mapping in a separate file, re-parses the
  output and re-scans it with independently constructed patterns. Includes a
  `--validate-only` parse-coverage mode for arbitrary input.
- Add `scripts/host_probe.py`: DNS-only host probe with selectable and excludable
  resolvers, alias-chain and terminating-provider reporting, regional and cluster
  variant enumeration, cross-resolver divergence detection and a zero-query
  `--dry-run`. Sends no HTTP.
- `scripts/host_probe.py`: accept a DNS answer only from the resolver actually
  queried (the datagram socket is connected, so the kernel discards off-path
  replies), require the response bit, and require the question section to echo
  the name asked. Answers remain unauthenticated: there is no DNSSEC validation
  and an on-path attacker can still forge one.
- `scripts/har_inventory.py`: report `totals` including host counts and hosts
  shared across workflows; `schema_version` 1 to 2. Fixes reviews quoting a
  hand-counted host total.
- Consumption review: require read-only retrieval before requesting a capture,
  with an explicit ladder and stop conditions; treat CAPTCHA as a hard
  registration dependency on an unscopable host; require bundle inspection when a
  capture carries bodies; name the fail-open blocklist inversion; check telemetry
  hosts for re-export of the entry URL's tracking token.
- Enforcement: state that inline application controls only see flows the network
  layer allowed; require alias-chain and provider resolution; require enumeration
  of regional and cluster siblings; put existing gateway and firewall logs first
  in verification; cover elevated in-event roles; add the vendor browser
  extension as its own control layer.
- Evidence: delivered client code is not a working server operation; a self-scan
  reusing the redactor's patterns is not verification; resolution is not
  reachability; NXDOMAIN on a generated variant proves nothing about other
  regions.
- Sanitization: decode before redacting; scan with independent patterns.
- Report format: alias chain and provider column, supply-chain exposure section,
  counts taken from tool totals.
- Tests: add sanitizer and host-probe suites, including regressions for the
  percent-encoded identifier leak, the self-scan blind spot and the host count.

## 0.1.0 — Initial repository handoff, 2026-09-15

- Export the existing installed Security Colleague workflows and scripts; update provenance notes for publication.
- Supply OpenAI and Claude Code plugin manifests over one shared core; omit runtime-only `policy.products` from exported OpenAI metadata for plugin-schema compatibility.
- Supply repository catalogs, validation, synthetic regression tests, and manual upload guidance.
- Preserve explicit limitations: HAR inventory and lossy minimization are bundled; general entity recognition and format-specific sanitizers are not.
- Publish the package to the selected public repository with explicit author authorization dated 2026-09-15. External installations, automatic updates, and client reloads remain unverified.
