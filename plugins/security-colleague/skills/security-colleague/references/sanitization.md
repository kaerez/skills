# Sensitive information sanitization

## Establish the useful output

Ask what must remain useful: domains, routes, operation names, account/tenant relationships, timings, headers, schemas or executable behavior. Establish recipients and handling restrictions. Prefer consistent placeholders within an engagement when correlation matters, and omission when structure is unnecessary. Explain analysis/replay losses and never overwrite originals.

Inventory personal names, usernames, addresses, emails, phones, national/tax/SSN IDs, dates of birth, health information and contextual patient references, financial/payment data, security codes, passwords, sessions, cookies, bearer tokens, API/private keys, OAuth state/code/verifier values, magic links, signed URLs, internal names and tenant identifiers. Health information may remain sensitive without an obvious identifier.

## Language and format coverage

Cover the requested English variants, European languages, Russian and Hebrew through an explicit locale inventory and tested recognizers. EU/EEC/EC labels are not a single language list or ID schema; resolve countries/languages/local formats when detection depends on them. Handle Unicode, diacritics, mixed scripts, RTL/bidi controls and normalization. Do not assume English keywords cover translated labels, inflected names or free text.

Combine format-aware parsing, secret/header rules, structural context, jurisdiction-specific ID recognizers/checksums, tested multilingual entity recognition and targeted review. Regex alone cannot reliably find every person, health reference or contextual secret. State actual detectors, models, versions, thresholds and untested coverage. Do not send evidence to an external recognition service without authorization for that destination.

## Pipeline

0. Percent-decode, and where needed double-decode, before applying any rule. Encoded separators hide structure: a path segment rule never sees a real segment while `/` remains `%2F`, and a pattern anchored on word boundaries will not match an identifier preceded by an encoded character. Decode, then split, then redact.
1. Inventory every input and nested object; preserve originals and set bounded decoding limits.
2. Parse the detected format and decode supported layers, recording skipped/unresolved regions.
3. Inspect keys/values, URLs, headers, cookies, bodies, metadata, comments, source maps, HTML attributes/hidden inputs, CSS URLs/content, WASM custom/debug/data sections and embedded objects.
4. Redact, omit or pseudonymize with safe placeholders. Keep mappings private and separate. Hashing low-entropy identifiers alone does not anonymize them.
5. Re-encode with format-aware tooling; validate syntax/structure. Update lengths/checksums only where meaningful. Report invalidated signatures, SRI, signed/encrypted payloads, source maps or executable behavior. Arbitrary WASM byte replacement is not module validation.
6. Reparse and scan output with patterns constructed independently of the redaction rules, over the raw, decoded and double-decoded text, and test seeded synthetic identifiers. A second pass with the same blind spots is not independent proof; a scan that reuses the redactor's own expression will confirm whatever the redactor missed.
7. Deliver a coverage manifest: processed formats/languages, transformations, retained sensitive categories, counts, exclusions and errors. Use statuses such as completed within declared scope, partial or blocked. Do not certify universal PII/PHI removal or regulatory de-identification from automated scanning alone.

For unsupported/encrypted/opaque regions, omit them and report the loss when that meets the goal. If omission makes the derivative misleading or unusable, withhold it and request the smallest missing decoder, schema or review. Never pass unexamined bytes through while calling the entire result sanitized.

## Bundled HAR sanitizer

```bash
python3 <skill-directory>/scripts/har_sanitize.py capture.har \
  --output routes.har --mapping placeholders.json
```

Use this when the analysis needs route-level evidence rather than a host list. It
percent-decodes before redacting, then retains entry order, methods, status codes,
decoded path shape with identifiers placeheld, query parameter names, GraphQL and
RPC operation names, response MIME types, and the presence of security-relevant
header names. It removes header values, cookies, query values, request and
response bodies, WebSocket message contents, timestamps, timings and exporter
extensions, and drops known tracking query keys outright rather than placeholding
them. Placeholders are stable within one run so the same identifier correlates
across hosts; the mapping is written only to `--mapping` and must stay out of
shareable output. The derivative is re-parsed, and an independent residual scan
runs over the raw, decoded and double-decoded text; findings block the write
unless `--force` is given. `--validate-only` reports parse coverage, malformed
entries, unsupported URLs, body presence and exporter extensions without
producing a derivative.

Path shape and operation names can still identify a tenant or a product. Review
the embedded coverage note before sharing, and remember that an omitted body is
not an inspected body. A host inventory is not a sanitized HAR, and neither is
this a de-identification certification.

## Bundled HAR minimizer

```bash
python3 <skill-directory>/scripts/har_minimize.py capture.har --output minimized.har
```

This creates a deliberately lossy derivative. It preserves order, recognized methods/status codes, schemes, ports and host relationships using synthetic `.invalid` hostnames. It replaces paths, clears headers/cookies/queries/bodies, removes timestamps/extensions and supplies explicitly synthetic zero timings. It does not recognize multilingual entities; omission operates independently of language. It does not inspect or preserve body content, HTML/JS/CSS/WASM semantics or replay behavior.

Use `--retain-hosts` only when retaining validated real hostnames/IPs fits the chosen scope, and disclose that they may identify people, tenants or internal systems. Pseudonyms are scoped to one invocation and are not stable across separately produced files.

The helper requires JSON with `log.entries`, has an input-size limit, refuses existing output files, rejects malformed entries and counts replaced unknown URL/metadata fields. The output labels its reconstruction. It does not certify anonymous metadata or detect all personal information.

Chrome's sanitized HAR export removes certain sensitive headers; still inspect URLs, bodies and other fields. Verify the actual exporter against [official documentation](https://developer.chrome.com/docs/devtools/network/reference/).
