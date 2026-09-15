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
| Solve a CAPTCHA or bot-defence challenge in a permitted registration or viewing flow | Allow. It is usually a hard dependency on a provider-wide host that cannot be scoped to this service, and it is the most common silent cause of a registration that fails while the page loads perfectly. An authentication-style status on an attestation path is often normal, not a block. |

Classify registration by its purpose and granted capabilities. An attendee registration record and its necessary personal details are a permitted exception when the user allows registration for viewing; do not classify them as a prohibited upload merely because they use POST or write server-side data. Allow only the viewer functionality intended by the user; flag participation or authoring that comes with it. If a viewer account can also become a creator, mark the identity flow as shared rather than assuming the label “viewer” enforces a boundary.

Treat a specific user prohibition on login as binding, including in the recommended strict configuration. Still describe the consumption that would be lost and, when helpful, an explicitly different policy option. Do not weaken a stated requirement silently.

Use the intake answers to identify the enforcement product, deployment, license, browser/native client, operating systems, identities, and policy scope. If the user leaves the control unspecified after intake, label a domain-only baseline as provisional and separate optional finer controls. Do not assume TLS inspection, application controls, enterprise licensing, or tenant-admin access.

## Retrieve before requesting evidence

Exhaust read-only retrieval before asking the user for a capture. A JavaScript
shell is the first rung of this ladder, not the end of it. Record which rungs
ran, which the environment refused, and what each produced.

1. **Fetch the supplied URL with tracking parameters stripped.** A recipient-scoped
   marketing or click token can attribute an open or click to a real person, and
   it does not belong in a report or a search query. Keep a functional signed
   parameter only where the authorized read genuinely needs it.
2. **Follow and record the redirect chain**, including any email click tracker or
   link shortener. That entry-link host is required for the supplied URL to work
   and is shared across every message from that sender, which makes it an overlap
   decision rather than an incidental hop.
3. **Parse the returned document** for script, stylesheet, iframe, image and form
   `action` references, plus any inline configuration naming hosts or endpoints.
4. **Fetch the referenced bundles and read them** for hostnames, API paths,
   operation names and authoring routes. When a supplied capture contains
   response bodies, those bundles are already in hand and cost nothing to inspect.
   Delivered code proves the client ships a capability; it does not prove the
   endpoint is reachable or that the operation would succeed. Label it that way.
5. **Retrieve the prohibited surface's own application.** The supplied URL is
   usually the permitted surface; the hosts that serve the prohibited one are
   declared in *its* client. Fetch the authoring console, admin application or
   creator entry point named in documentation, and read its configuration and
   bundles for API backends, upload endpoints and feature hosts. Configuration
   shipped in code outranks a negative DNS result: a name absent from DNS can
   still be a configured backend, a path on another host, or a tenant domain.
6. **Resolve every candidate host** with `../scripts/host_probe.py`: alias chain,
   terminating provider, and the documented and undocumented regional and cluster
   variants. Honour any instruction about which resolvers to use or avoid.
7. **Mine the organization's own gateway, firewall or proxy events** for the
   service. Existing telemetry enumerates the hosts users actually reach,
   including regional and vanity hosts, at no test-traffic cost.
8. **Only then request evidence**, naming the single smallest capture or log
   extract that would resolve what is still open.

Rungs 3 to 6 are independent per surface. Where the host offers subagents, tasks
or parallel execution, fan the enumeration out across the distinct surfaces at
once: the permitted application, the prohibited application, published API
documentation, DNS regional and cluster variants, and the organization's own
gateway logs. One serial pass over one surface is how a region, or an entire
application, goes unenumerated. Each returned report is a claim to verify under
the same evidence labels as any other source, not a result to adopt. Where the
host offers no such capability, run the surfaces serially and say so in the
coverage statement.

Stop conditions worth stating plainly: a tool refusing a URL is a capability
limit to record and route around, not a fact about the service; an empty result
from one rung does not close the next; and none of this authorizes submitting a
form, registering, signing in or changing a control.

### State the bound with the set

Publish every enumerated set with its method and its bound in the same breath:
which surfaces were searched, what the method would not have found, and whether
anything outside the set is permitted by default. Volunteer this at the first
host list; never wait to be asked whether the set is complete. If a user supplies
a host the analysis should have found, that is a finding about the method. Widen
it, re-run it, and say what else the same gap would have hidden.

### When to request a capture

A capture request is a triggered step, not a last resort. Any one of these
requires asking now, naming the smallest sufficient capture:

- A host that would enter the decision table as Unresolved.
- A host serving both permitted and prohibited operations where the decision
  turns on which.
- A prohibited capability found in shipped code with no observed request.
- A rule shape that cannot be chosen without knowing whether a shared host
  carries writes.

Make the ask specific: which workflow, which surface, what it must contain. State
that the capture is sanitized with `../scripts/har_sanitize.py` before it is
sent. Requesting a capture is not a failure of the ladder; continuing to answer
without one, when a trigger has fired, is.

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

Run the bundled local helpers. Compare host use across labeled captures first:

```bash
python3 <skill-directory>/scripts/har_inventory.py \
  --capture public-view=/path/to/view.har \
  --capture viewer-registration=/path/to/registration.har \
  --capture creator-session=/path/to/creator.har \
  --output /path/to/host-inventory.json
```

Use only the captures available; omit missing ones. The helper reads files without making network requests. It omits URL paths, query strings, fragments, userinfo, bodies, cookies, and header values from its report. It distinguishes captured requests from redirect references and identifies IP literals. Review skipped-entry counts, including unsupported URLs or ambiguous IDN mappings; obtain the browser's ASCII hostname for unresolved IDNs. It does not sanitize the original HAR, infer actions, prove necessity, or certify an allowlist. Hostnames and workflow labels can still identify tenants. Quote counts from its `totals` block rather than counting rows by hand.

Host and method counts cannot separate a permitted write from a prohibited one.
A registration submission and an authoring mutation can both appear as one POST
to one host. When that distinction decides the recommendation, derive route-level
evidence with `../scripts/har_sanitize.py`, which keeps method, decoded path
shape, operation name, status and MIME type while removing header values,
cookies, query values and bodies:

```bash
python3 <skill-directory>/scripts/har_sanitize.py /path/to/view.har \
  --output /path/to/view-routes.har --mapping /path/to/placeholders.json
```

Do not improvise this in-session. Ad-hoc redaction has failed on percent-encoded
path separators and then reported itself clean because the check reused the same
pattern as the redactor. Inspect only the relevant sanitized route or operation evidence locally if host overlap needs explanation; request the smallest additional capture that resolves an important gap.

## Decide what can actually be enforced

Judge policy at the available control's granularity. Domain-only rules cannot distinguish paths, methods, event IDs, users, account types, or application operations on the same hostname. Allowing a host for an embedded player also allows direct requests to that host. DNS cannot limit access to one event, share permission, content owner, or URL path on it.

Replacing a default-deny application block with an enumerated blocklist inverts
the posture from fail-closed to fail-open for every host not on the list, and an
enumerated blocklist is not equivalent to "authoring blocked". Prefer a narrow
allow rule evaluated above the existing block, so anything unenumerated stays
blocked. If a time-boxed fail-open step is accepted deliberately, say so, enable
event logging, and tighten once the observed host set is known.

Check shared frontends, authentication services, APIs, media/storage hosts, and alternate creator routes. Blocking login does not establish consumption-only access: guest editing and pre-existing sessions may remain possible. A public share link may grant edit permission. Network reachability, service authorization, and UI affordances are separate facts.

Do not infer business permissions from HTTP methods. Viewing may require POST requests for login, GraphQL queries, search, DRM, progress, or token refresh. Blocking all POST/PUT/PATCH requests can break consumption while leaving other creation routes. Shared RPC/GraphQL paths or WebSockets may carry both reads and writes; URL filtering alone may still be insufficient. Blocking uploads also does not prevent editing, AI generation, copying, publishing, or imports by URL.

Telemetry hosts deserve one specific check rather than a blanket dismissal: a
browser monitoring or analytics beacon commonly re-exports the entry URL, which
can carry the recipient-scoped tracking token, to a third party. Where blocking
such a host costs no observed consumption, the privacy improvement and the rule
simplification coincide. Any regulatory conclusion belongs with Legal, Risk and
Compliance rather than in this analysis.

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
