# Enforcement and evidence

Read this reference when mapping candidate hosts to controls, handling shared infrastructure, or designing verification. Keep the analysis scoped to the requested service and users.

## Match the recommendation to the control

| Control | What it can separate | What to establish before claiming separation |
| --- | --- | --- |
| DNS filtering | Different queried hostnames or explicitly supported DNS response properties | Resolver coverage; exact-host versus suffix behavior; CNAME handling; rule precedence. DNS has no visibility into HTTPS paths, methods, accounts, or application actions. |
| Firewall or proxy using hostname/SNI/CONNECT only | Different visible destination hosts, and possibly ports/protocols | Actual hostname visibility and traffic coverage. A hostname rule cannot distinguish viewing from editing on that hostname. |
| HTTPS URL filtering | Distinct request hosts and paths; methods or other selectors only if supported | TLS inspection or equivalent endpoint visibility, managed trust, route stability, redirect coverage, and the product's actual selectors. URL fragments are not sent in HTTP requests. |
| Inline application activity controls | Supported app actions, sometimes tenant/account restrictions | Exact service, action, account type, licensing, client, and deployment support. An API-connected CASB may detect changes after they happen and may not prevent them inline. |
| Service permissions or enterprise policies | Viewer roles, content sharing permissions, supported creation restrictions | Which identities, tenants, resources, anonymous links, and personal accounts the policy covers. Corporate SSO restrictions alone may leave personal or guest routes available. |
| Vendor browser extension or managed-browser agent from the same platform | Supported in-page controls on clients the network path cannot inspect, sometimes including unmanaged or otherwise uninspectable operating systems | Whether it is licensed, deployed to the relevant users, and covers the actual browsers in scope. It is a separate enforcement layer from the network policy, with its own coverage; ask about it during intake rather than assuming the network rule is the only option |
| Managed browser / browser isolation | Supported input, upload, clipboard, and navigation restrictions | Actual controls and their scope. Disabling file upload does not automatically prevent typing, editing, server-side copying, publishing, or importing by URL. |
| Endpoint app execution controls | Launch/use of selected native apps by supported process, bundle, publisher, path or hash selectors | Actual OS, agent/MDM support, alternate binaries/webviews and policy coverage. App blocking does not provide read-only actions inside an allowed native app. Evaluate browser consumption separately. |

Control layers are ordered, and the order defeats some plans outright. An inline
application or activity control normally inspects only flows the network layer
already allowed, so while a service-wide block stands, no finer rule for that
service can ever fire. Opening a narrow exception is therefore a prerequisite for
finer control, not an alternative to it. Say which layer runs first before
promising that a finer rule will constrain anything.

Treat stronger controls as conditional proposals until current primary documentation or an authorized test establishes their support. Do not invent a product-specific toggle or rule language. If an engine is named, verify its current official documentation before emitting native syntax.

## Represent rules precisely

- Preserve each observed FQDN. Normalize case, IDNs, and a trailing DNS dot without collapsing to a parent domain. Identify IP literals separately from hostname rules.
- Label exact host, apex, descendants, and wildcard scope explicitly. State whether a pattern includes the apex and how deep it matches in the chosen engine. Do not assume `*.example.com` includes `example.com`, or that a product's field called “domain” is an exact-host match.
- Anchor any regex at DNS label boundaries. Keep URL schemes, ports, paths, queries, and fragments out of a domain-only list; put supported finer controls in a separate table.
- Explain the effective order and default action. An exact-host allow inside a broader service block works only when the engine supports that exception and evaluates it as intended. Avoid assuming either “allow wins” or “block wins.”
- Scope any default deny to the requested service and policy group. Do not silently turn a service exception into an Internet-wide block policy.
- Do not broadly allow or globally block shared provider parents such as cloud storage, CDN, identity, or CAPTCHA domains solely for one service. Prefer observed tenant/asset hosts; if requests use a provider-wide hostname, explain the cross-service exposure and limits of domain rules.
- Resolve the alias chain and terminating provider for every host in the decision, with `../scripts/host_probe.py`. Hosts you intend to allow and hosts you intend to block frequently terminate on the same CDN or load-balancer namespace, and addresses rotate between queries. Where that is true, no rule keying on resolved address or alias target can separate them, and only the request hostname can.
- Enumerate regional and cluster siblings rather than reasoning about symmetry. Regionalization is commonly asymmetric: an admin console, a public API and a live-event host may each have a regional twin while a shared SDK host does not. A blocklist built from one region is systematically incomplete, and the gap is enumerable without sending a single request to the service.
- Treat a DNS alias target and a browser redirect as different dependencies. A CNAME does not by itself change the HTTP hostname or create a separate browser request. Whether the alias also needs an exception depends on the DNS engine's evaluation.
- Track geography, tenant, custom-domain, cluster, and signed-media host variation when observed or documented. One numbered host does not justify a wildcard for every cluster. Avoid presenting one sample's host set as globally complete.
- Check the proposed rule set against the evidence with `../scripts/rule_coverage.py` before presenting it. The check catches an exact-host rule that misses a cluster-direct or regional twin, a rule that matches nothing in the evidence, and a default-allow shape whose residual surface is unbounded by construction. It measures the list against the supplied evidence only and proves nothing about hosts that evidence never recorded.

Enumerating to block and enumerating to allow are not symmetric, and the
asymmetry decides the rule shape. A blocklist must be complete to work: every
host it misses stays reachable, the failure is silent, and no amount of searching
proves the set is done. An allowlist must also be complete, but its failures are
loud and self-correcting: a missed host breaks consumption, someone reports it,
and it is added. Prefer the shape whose failure mode is visible. Where a
default-deny for the service is available, put it beneath validated consumption
allows and keep explicit blocks only for prohibited hosts that share a parent
with permitted ones.

## Look beyond obvious pages

Trace the requested landing page, redirects, embeds, player, assets, APIs, identity, CAPTCHA, and media delivery. For playback, check manifests, segments, range requests/seeking, captions, signed-URL refresh, and license services if present. Keep live-event speaker/WebRTC dependencies separate from on-demand viewing unless evidence shows they are required.

Look for elevated roles that live inside the consumption surface rather than
behind the administration console. A producer, coordinator, moderator or host
role can publish, moderate or configure from within the event or document a
viewer is allowed to open, using the same hostnames the viewing policy permits.
Blocking the administration console does not remove those capabilities.

Classify participation features such as chat, comments, Q&A, polls, reactions, and microphone/camera publishing separately from watching. An attendee role may include these even when it cannot author an event. A successful viewing session may contain analytics, advertisements, help widgets, and speculative prefetches; their presence does not establish necessity.

Check prohibited actions through their actual dependencies: guest editing, existing sessions, direct editor links, creation/copy/AI generation, upload endpoints, pre-signed object-store writes, and imports from a URL or connected cloud account. Blocking only an upload button or multipart form is incomplete. Consider native apps, mobile clients, or APIs only when they fall within the requested policy scope.

If a control depends on inspecting network requests, identify any relevant coverage gap such as uninspected HTTPS, persistent WebSockets, excluded clients, or uncontrolled resolver/egress paths. State applicability and the concrete missing control; avoid an unrelated network-hardening checklist.

## Calibrate evidence to the claim

Maintain these distinctions in host rows and conclusions:

- **Observed request:** A capture contains a request to the host. It does not prove the request is necessary, successful, or consumption-exclusive.
- **Observed action:** A recorded workflow outcome connects requests to an action. A status code alone does not establish that action's success.
- **Documented:** A current primary source states a role or requirement; identify whether it covers the exact workflow or the whole platform.
- **Inferred:** State the observation supporting the inference and what could disprove it. Names such as `view`, `public`, `cdn`, `auth`, or `registration` are clues, not capability evidence.
- **Unknown:** State what cannot be determined and the smallest useful next observation. Keep unknown hosts out of an unconditional allow list.

Use independent labels for evidence and rule readiness. A provisional allow may be justified by product documentation while the exact user's playback flow remains untested. A domain can be required for viewing and also enable authoring. Record both facts.

When captures are available, group them by workflow and identity state. Use `../scripts/har_inventory.py` to produce a host-only comparison, then inspect only the necessary sanitized request details locally for shared endpoints. The helper does not classify actions, prove necessity, inspect WebSocket messages, reconstruct DNS aliases, or show server-to-server calls.

Never conclude “view only” merely because a viewer account lacks edit permission. For a network policy intended to constrain all covered users, check what a pre-existing creator account or an anonymous edit link could do under the same rules. Separate a disabled service permission from a failed network request.

## Verify the two goals separately

Use supplied results or authorized isolated tests. Report a proposed test as **not run** until there is an actual result.

Start with evidence the organization already holds. Gateway, firewall, proxy and
DNS logs for the service over a recent window enumerate the destination hosts
users actually reach, including regional, cluster and vanity hosts, and the
full-path field where inspection applies. That costs no test traffic, reflects the
real estate rather than one sample, and often shows the current posture is leakier
or tighter than assumed. Do this before designing any test request.

1. Establish a baseline and change only the candidate rule in a scoped test policy. Compare allowed and blocked runs to distinguish dependencies from incidental requests.
2. Verify viewing: cold load, redirects, embed load, permitted registration/login, player start, seek, captions where needed, and session/media refresh. Test required workflows separately.
3. Verify prohibited actions: creator signup/login if prohibited, anonymous editing, fresh creation, editing with an existing session, uploads, copying/importing, and publishing as relevant. Use an authorized test resource; do not create or alter live user content merely to test the policy.
4. Record the policy, identity state, client, observation date, outcome, evidence, and untested routes. A failed login is not proof that creation is blocked; a page loading is not proof that playback works.
5. If a dependency remains shared, compare allowing and blocking it explicitly. If a test is unavailable, give a provisional recommendation with the unresolved gap rather than fabricating verification.

## Primary documentation entry points

Reopen the relevant sources when conducting a live analysis; these are research entry points, not frozen configuration. Located on 2026-09-15:

- [Cloudflare DNS policies](https://developers.cloudflare.com/cloudflare-one/traffic-policies/dns-policies/): examples of exact-host versus domain matching and DNS response/CNAME evaluation. Apply its semantics only to that product.
- [Cloudflare HTTP policies](https://developers.cloudflare.com/cloudflare-one/traffic-policies/http-policies/): examples of HTTPS inspection requirements and URL/method selectors. Verify the selected engine independently.
- A platform's own allowlist or connectivity article: full-product connectivity candidates; do not turn the broad list into a consumption-only recommendation.
- A platform's sharing and guest-permission documentation: investigate anonymous editing and permission-dependent share links. Do not equate blocking login with blocking editing.
- A platform's own network and firewall guidance: distinguish general event, speaker, streaming and on-demand requirements; treat the list as discovery candidates, not a recommendation.
- A platform's attendee or viewer guide: investigate registration and magic links and participation capabilities separately from authoring. Do not adopt advice to disable organizational security controls.
