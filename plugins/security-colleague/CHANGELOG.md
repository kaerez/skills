# Changelog

**TLP:GREEN · (C) Erez Kalman**

## 0.2.0 — Retrieval ladder and route-level evidence, 2026-09-15

Verified locally on Python 3.12.3 (Linux): repository validation and the full
regression suite pass. Unverified: remote CI, macOS and Windows jobs, any client
installation, update or session reload, and live enforcement behaviour.

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
