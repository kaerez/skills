**Rules to push (exact-host entries — do not use a `*.vendorco.invalid` wildcard):**

| Host | Action |
|---|---|
| `portal.vendorco.invalid` | Allow |
| `static-cdn.vendorco.invalid` | Allow |
| `api-edge.vendorco.invalid` | Allow |
| `sso.vendorco.invalid` | Allow |
| `ingest-upload.vendorco.invalid` | **Block** |

Use exact-host matches for all five, not a suffix wildcard — a `*.vendorco.invalid` allow would also match `ingest-upload.vendorco.invalid` and silently defeat the block. TLS inspection being on for this category means the gateway will see the real SNI/host for all five, so exact matching will hold.

**Gap to flag on the ticket before you call this "read-only" enforcement:** the HAR is from a *viewer* session only, so it never exercised the create/upload/edit flows. `ingest-upload.vendorco.invalid` is a reasonable guess for bulk file upload, but if in-page edit/save/create actions POST back to `api-edge.vendorco.invalid` (the same host the page already uses for read calls), this gateway **cannot** separate that traffic — it matches domain only, not method or path. Blocking `ingest-upload` would stop obvious file uploads but not necessarily in-app edits/creates that ride on `api-edge`.

Recommendation to note on the ticket: treat this push as an interim/partial control, and before/after the 16:00 window capture a HAR of an actual create/edit/upload attempt against the vendor site to confirm whether it hits `ingest-upload` exclusively or also `api-edge`. If it's the latter, this SWG rule set alone can't fully enforce "view-only" — you'd need either a vendor-side read-only role/permission for staff accounts, or a CASB/proxy control capable of method-level (not just domain-level) inspection.