# Consumption-only access review

Produce an evidence-backed decision about which domains to allow or block for the user's requested consumption workflows. Preserve necessary viewer registration and authentication when permitted. Make every material conflict between consumption and prohibited activity explicit, including options with and without the shared dependency.

## Establish the boundary

Identify the service, example content URLs, intended audience, required consumption workflows, and available enforcement layer. Use the supplied URLs as research seeds, not as a complete dependency list. Keep an exact host distinct from its parent domain, and one content item distinct from all content on that host.

Use these defaults unless the user specifies otherwise:

| Activity | Policy intent |
| --- | --- |
| Read, view, present, watch, listen, navigate, or search existing content | Allow as needed for the requested consumption workflow. |
| Register for an event, use a magic link, sign in as a viewer, renew a viewing session | Allow when needed for consumption; establish what else the resulting identity can do. |
| Create, edit, generate, duplicate into a workspace, upload, import, publish, or administer content | Block. Include anonymous or existing-account routes where applicable. |
| Sign up or log in to an authoring/creator account | Block unless the user explicitly permits it; show an overlap decision if the same account flow is required for viewing. |
| Download/export existing content, comment, chat, ask questions, react, vote, or transmit microphone/camera | State a service-specific assumption or option where material. Do not silently treat participation or new content generation as passive viewing. |

Classify registration by its purpose and granted capabilities. An attendee registration record and its necessary personal details are a permitted exception when the user allows registration for viewing; do not classify them as a prohibited upload merely because they use POST or write server-side data. Allow only the viewer functionality intended by the user; flag participation or authoring that comes with it. If a viewer account can also become a creator, mark the identity flow as shared rather than assuming the label “viewer” enforces a boundary.

Treat a specific user prohibition on login as binding, including in the recommended strict configuration. Still describe the consumption that would be lost and, when helpful, an explicitly different policy option. Do not weaken a stated requirement silently.

Use the intake answers to identify the enforcement product, deployment, license, browser/native client, operating systems, identities, and policy scope. If the user leaves the control unspecified after intake, label a domain-only baseline as provisional and separate optional finer controls. Do not assume TLS inspection, application controls, enterprise licensing, or tenant-admin access.

## Research the actual flows

Use current primary sources: the target service's documentation, supplied public pages, official networking/sharing/authentication guidance, and the selected enforcement vendor's documentation. Browse for current service architecture and product capabilities unless the user requests an analysis limited to supplied evidence. Treat official full-service allowlists as discovery candidates; they commonly cover functionality the user wants blocked. Do not copy them wholesale.

Use the host environment's authorized public research tools for an analysis request. Use interactive browser tooling only when the user explicitly requests site interaction or interactive validation, and then follow the available browser skill. A service URL alone does not authorize signing in, submitting registration, accepting an invitation, creating content, or changing controls. Use existing authorization where it applies. When a page is inaccessible or JavaScript-only, report that limitation and continue with documents and supplied evidence; do not claim to have tested it.

Remove marketing query parameters from search queries and reports. Keep any functional signed parameters or magic links only where necessary for an authorized read; do not search for, echo, or persist their secret values. Do not submit forms, send messages, create accounts, or change production policy as part of an analysis-only request.

Build a workflow-to-host map for the relevant states: public viewing; viewer registration; authenticated consumption and session refresh; creator signup/login; and prohibited actions. Record dedicated hosts and shared hosts for landing pages, embeds, scripts/assets, media, APIs, identity, CAPTCHA, and relevant third parties. Investigate redirects and custom/tenant domains. Use [enforcement.md](enforcement.md) for control limits, dependency discovery, evidence calibration, and relevant official entry points.

For each host, distinguish:

- The request was observed versus it is necessary for the requested workflow.
- A capability is documented versus it succeeded in a captured or tested workflow.
- It is required for consumption versus it serves only consumption.
- A prohibited endpoint is reachable versus the prohibited action can actually succeed.

Cite the source or capture and its observation/check date near each material claim. Label inferences and unknowns explicitly. Resolve conflicting documentation and captures by workflow, date, tenant, region, or client when possible; do not hide the conflict. Never invent subdomains from names or present an unobserved endpoint as confirmed.

### Use HAR evidence when available

Run the bundled local helper to compare host use across labeled captures:

```bash
python3 <skill-directory>/scripts/har_inventory.py \
  --capture public-view=/path/to/view.har \
  --capture viewer-registration=/path/to/registration.har \
  --capture creator-session=/path/to/creator.har \
  --output /path/to/host-inventory.json
```

Use only the captures available; omit missing ones. The helper reads files without making network requests. It omits URL paths, query strings, fragments, userinfo, bodies, cookies, and header values from its report. It distinguishes captured requests from redirect references and identifies IP literals. Review skipped-entry counts, including unsupported URLs or ambiguous IDN mappings; obtain the browser's ASCII hostname for unresolved IDNs. It does not sanitize the original HAR, infer actions, prove necessity, or certify an allowlist. Hostnames and workflow labels can still identify tenants. Inspect only the relevant sanitized route or operation evidence locally if host overlap needs explanation; request the smallest additional capture that resolves an important gap.

## Decide what can actually be enforced

Judge policy at the available control's granularity. Domain-only rules cannot distinguish paths, methods, event IDs, users, account types, or application operations on the same hostname. Allowing a host for an embedded player also allows direct requests to that host. DNS cannot limit access to one event, share permission, content owner, or URL path on it.

Check shared frontends, authentication services, APIs, media/storage hosts, and alternate creator routes. Blocking login does not establish consumption-only access: guest editing and pre-existing sessions may remain possible. A public share link may grant edit permission. Network reachability, service authorization, and UI affordances are separate facts.

Do not infer business permissions from HTTP methods. Viewing may require POST requests for login, GraphQL queries, search, DRM, progress, or token refresh. Blocking all POST/PUT/PATCH requests can break consumption while leaving other creation routes. Shared RPC/GraphQL paths or WebSockets may carry both reads and writes; URL filtering alone may still be insufficient. Blocking uploads also does not prevent editing, AI generation, copying, publishing, or imports by URL.

Prefer the narrowest evidenced exact hosts and explicit exceptions within the requested policy scope. Keep optional/incidental hosts out of the necessary set. For shared third-party hosts, identify other tenants/services enabled if allowed and collateral breakage if blocked. Explain wildcard, apex, CNAME, rule precedence, and default-action semantics before treating a list as implementable. Verify engine-specific syntax against current official documentation.

Assign each host **Allow**, **Block**, **Conditional**, or **Unresolved**, with evidence, confidence, and both directions of impact. Keep conditional and unknown dependencies out of unconditional allow recommendations. Do not call a proposed block effective until its coverage is supported; uncertainty should remain visible without preventing useful partial decisions.

For every dependency that enables allowed capability X and prohibited or unwanted capability Y, give all of the following:

1. **Allow the dependency:** Name the consumption retained and the additional activity or exposure enabled or left reachable; state whether Y is verified or only possible.
2. **Block the dependency:** Name the consumption lost and the prohibited routes actually removed; do not imply all routes to Y disappear without evidence.
3. **Use finer controls, if viable:** Identify the precise URL, method/operation, application, tenant/role, or managed-browser capability required and its residual gaps. Distinguish verified support from a candidate to investigate.

When overlaps interact, give internally consistent restriction-first and consumption-first configurations, plus an optional stronger-control configuration. Do not combine incompatible allow/block actions into a single prescription. Recommend an option aligned with the user's stated priority, and mark a consumption-first exception as a compromise rather than a guarantee.

## Deliver a decision and verification plan

Use the chosen depth and delivery format. Consult [report-format.md](report-format.md) for a requested detailed consumption review; return only a brief decision when no full report was selected. Lead with whether domain-only separation is supported, partial, impossible for a required flow, or unresolved. Include the action boundary, evidenced domain decisions, explicit allow/block overlap options, and the smallest useful next verification steps. Give copyable rules when the engine and evidence support them; label vendor-neutral intent or provisional lists honestly.

Verify viewing and prohibited actions independently, using supplied results or authorized scoped tests. Record actual versus expected outcomes; mark unrun tests as unrun. Include fresh viewing, necessary registration/session refresh, anonymous routes, and existing creator sessions where they affect the conclusion. Do not equate a loaded landing page with working playback or a failed login with blocked creation.

Finish useful read-only analysis autonomously. Apply policy changes only if requested or already authorized, using the user's established change scope. Preserve dated evidence and any user-requested reusable report through the environment's supported file workflow; do not retain raw session secrets in reusable output.
