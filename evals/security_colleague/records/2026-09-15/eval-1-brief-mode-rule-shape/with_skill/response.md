**Model/effort:** Claude Sonnet 5 (`claude-sonnet-5`), per the system context; no separate reasoning-effort control is exposed to me here, so I can't report one.

**Verdict:** Push an **allowlist of the 4 hosts staff actually need**, plus one **explicit block** for the upload-looking host, evaluated above whatever your current default action is for this category. Domain-only matching can enforce "no other vendor sites," but it **cannot** enforce "read-only" on a host that carries both viewing and mutation traffic — that's the one fact that decides everything below, and it's why `api-edge` is the risk item, not a footnote.

**Rule shape:** Allowlist (narrow, evidenced) with one hard block above it. Not a blocklist — you have no visibility into the vendor's full host set from one HAR, and a blocklist has to be complete to work; a missed host here just leaks through silently. An allowlist fails loudly (staff report a blocked page) instead.

| Host | Decision | Why (evidence label) |
|---|---|---|
| `portal.vendorco.invalid` | **Allow** (exact host) | The viewer app itself. Observed. |
| `static-cdn.vendorco.invalid` | **Allow** (exact host) | Assets needed to render the portal. Observed; domain-only rule can't *guarantee* it's asset-only, but nothing here suggests a write path. |
| `sso.vendorco.invalid` | **Allow** (exact host) | Needed to authenticate into the viewer session. Observed. Note: SSO grants identity, not capability — it doesn't by itself decide what the account can do downstream. |
| `api-edge.vendorco.invalid` | **Allow, but Unresolved on scope** | Named "edge/api" — this is the classic host where a GraphQL/REST endpoint carries both read queries and write mutations on the *same* hostname. Your gateway matching on domain only (even with TLS inspection on) cannot separate those calls. If you allow it, "no create/edit" is enforced by the vendor's own viewer-role permissions server-side, not by your gateway — that's a **documented/inferred**, not tested, control. |
| `ingest-upload.vendorco.invalid` | **Block** (exact host) | The name says upload/ingest, and it has no business appearing in a *viewer* session capture. Blocking it costs no known viewing capability. Flag this to whoever pulled the HAR: worth a 2-line check on what that request actually was (prefetch? health check? a genuine pre-signed upload call reachable even to viewers?) — but don't let that hold up the 16:00 window; block it now, revisit if it breaks something. |

**Completeness bound (state this in the ticket):** this host set comes from **one HAR of one viewer session** — it is not a full enumeration of the vendor's viewer workflow (no session-refresh/retry variants, no regional or tenant hosts, no confirmation of what `api-edge` actually rejects for a viewer role). Anything outside these 5 hosts stays blocked by the category default, which is the correct fail-closed posture given the gap. Before you fully close this out, pull your SWG's own logs for `*.vendorco.invalid` over the last week — that's free evidence and will show any host this single capture missed.

**Pasteable rule intent (translate to your SWG's exact syntax before pushing):**
```
allow  fqdn  portal.vendorco.invalid
allow  fqdn  static-cdn.vendorco.invalid
allow  fqdn  sso.vendorco.invalid
allow  fqdn  api-edge.vendorco.invalid   # see note: read/write not separable by this control
block  fqdn  ingest-upload.vendorco.invalid
default: block (category default, unchanged)
```
Exact-host (`fqdn`) rules only — do **not** wildcard to `*.vendorco.invalid`; you haven't seen enough of the vendor's other subdomains to justify it, and it would silently pull in whatever else lives under that suffix. Verify your specific gateway's allow-vs-block precedence before pushing — if a block-then-allow evaluation order differs from what you assume, `ingest-upload` could end up allowed instead of blocked.

**Residual risk to note on the ticket:** "No create/upload/edit" is only gateway-enforced for the CDN/portal/SSO hosts. For `api-edge`, enforcement depends on the vendor's viewer-role permissions actually rejecting writes server-side — untested from your side. If that matters for this control's audit trail, get written confirmation from the vendor or test it in a scoped account before relying on it.