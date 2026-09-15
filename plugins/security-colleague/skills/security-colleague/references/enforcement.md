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
| Managed browser / browser isolation | Supported input, upload, clipboard, and navigation restrictions | Actual controls and their scope. Disabling file upload does not automatically prevent typing, editing, server-side copying, publishing, or importing by URL. |
| Endpoint app execution controls | Launch/use of selected native apps by supported process, bundle, publisher, path or hash selectors | Actual OS, agent/MDM support, alternate binaries/webviews and policy coverage. App blocking does not provide read-only actions inside an allowed native app. Evaluate browser consumption separately. |

Treat stronger controls as conditional proposals until current primary documentation or an authorized test establishes their support. Do not invent a product-specific toggle or rule language. If an engine is named, verify its current official documentation before emitting native syntax.

## Represent rules precisely

- Preserve each observed FQDN. Normalize case, IDNs, and a trailing DNS dot without collapsing to a parent domain. Identify IP literals separately from hostname rules.
- Label exact host, apex, descendants, and wildcard scope explicitly. State whether a pattern includes the apex and how deep it matches in the chosen engine. Do not assume `*.example.com` includes `example.com`, or that a product's field called “domain” is an exact-host match.
- Anchor any regex at DNS label boundaries. Keep URL schemes, ports, paths, queries, and fragments out of a domain-only list; put supported finer controls in a separate table.
- Explain the effective order and default action. An exact-host allow inside a broader service block works only when the engine supports that exception and evaluates it as intended. Avoid assuming either “allow wins” or “block wins.”
- Scope any default deny to the requested service and policy group. Do not silently turn a service exception into an Internet-wide block policy.
- Do not broadly allow or globally block shared provider parents such as cloud storage, CDN, identity, or CAPTCHA domains solely for one service. Prefer observed tenant/asset hosts; if requests use a provider-wide hostname, explain the cross-service exposure and limits of domain rules.
- Treat a DNS alias target and a browser redirect as different dependencies. A CNAME does not by itself change the HTTP hostname or create a separate browser request. Whether the alias also needs an exception depends on the DNS engine's evaluation.
- Track geography, tenant, custom-domain, cluster, and signed-media host variation when observed or documented. One numbered host does not justify a wildcard for every cluster. Avoid presenting one sample's host set as globally complete.

## Look beyond obvious pages

Trace the requested landing page, redirects, embeds, player, assets, APIs, identity, CAPTCHA, and media delivery. For playback, check manifests, segments, range requests/seeking, captions, signed-URL refresh, and license services if present. Keep live-event speaker/WebRTC dependencies separate from on-demand viewing unless evidence shows they are required.

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

1. Establish a baseline and change only the candidate rule in a scoped test policy. Compare allowed and blocked runs to distinguish dependencies from incidental requests.
2. Verify viewing: cold load, redirects, embed load, permitted registration/login, player start, seek, captions where needed, and session/media refresh. Test required workflows separately.
3. Verify prohibited actions: creator signup/login if prohibited, anonymous editing, fresh creation, editing with an existing session, uploads, copying/importing, and publishing as relevant. Use an authorized test resource; do not create or alter live user content merely to test the policy.
4. Record the policy, identity state, client, observation date, outcome, evidence, and untested routes. A failed login is not proof that creation is blocked; a page loading is not proof that playback works.
5. If a dependency remains shared, compare allowing and blocking it explicitly. If a test is unavailable, give a provisional recommendation with the unresolved gap rather than fabricating verification.

## Primary documentation entry points

Reopen the relevant sources when conducting a live analysis; these are research entry points, not frozen configuration. Located on 2026-09-15:

- [Cloudflare DNS policies](https://developers.cloudflare.com/cloudflare-one/traffic-policies/dns-policies/): examples of exact-host versus domain matching and DNS response/CNAME evaluation. Apply its semantics only to that product.
- [Cloudflare HTTP policies](https://developers.cloudflare.com/cloudflare-one/traffic-policies/http-policies/): examples of HTTPS inspection requirements and URL/method selectors. Verify the selected engine independently.
- [Canva firewall guidance](https://www.canva.com/help/allow-canva-through-firewall/): full-product connectivity candidates; do not turn the broad list into a consumption-only recommendation.
- [Canva sharing and guest permissions](https://www.canva.com/help/collaborate-with-anyone-variantb/): investigate anonymous editing and permission-dependent share links. Do not equate blocking login with blocking editing.
- [Goldcast network and firewall guidance](https://help.goldcast.io/en_US/troubleshooting/4408141111323-configuring-your-connection-settings-network-vpn-and-firewall): distinguish general event, speaker, streaming, and on-demand requirements.
- [Goldcast attendee guide](https://help.goldcast.io/en_US/for-attendees/4404983265947-the-goldcast-attendee-guide): investigate attendee registration/magic links and participation capabilities separately from organizer authoring. Do not adopt advice to disable organizational security controls.
