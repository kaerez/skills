# Decision report

Use this for a requested detailed consumption review. Follow the intake's chosen depth and delivery location; for brief-only output, condense it to the decision, material overlap and next step. Keep domain decisions and overlap tradeoffs explicit. Use Markdown tables for mappings. Do not produce an unselected long memo or separate file.

## Opening decision

State the target, analysis date, selected enforcement layer, scope, and outcome:

- **Separable at domain level:** Evidence supports distinct dependencies for the covered consumption and prohibited workflows. State tested scope and limitations.
- **Partially separable:** Some workflows or dependencies can be separated; identify the shared hosts and the actions they expose.
- **Not separable at domain level:** At least one indispensable permitted workflow requires a host that also supports a prohibited action that the available control cannot distinguish.
- **Insufficient evidence:** Host roles or dependencies remain unverified. Give a useful provisional set and the concrete evidence needed.

Distinguish demonstrated conflict from possible conflict. Choose one main outcome, qualify it by workflow where needed, and explain whether it rests on documentation, captured behavior, or an enforced policy test.

## Action scope

| Action or workflow | Desired outcome | Authentication/registration treatment | Evidence or assumption |
| --- | --- | --- | --- |
| Requested viewing or playback | Allow | State public/viewer/attendee requirement | Link or observed result |
| Viewer registration/session renewal | Allow if needed for consumption | State what identity/capabilities it grants | Confirmed, inferred, or unknown |
| Creation/editing/uploading and other prohibited actions | Block | Include existing sessions and anonymous routes where relevant | Evidence or untested path |

Include downloads, live participation, comments, or similar actions only when they matter. Mark ambiguous activities as assumptions or options rather than silently expanding permission.

## Domain decisions

| Exact hostname or explicit pattern | Role and covered workflow | Evidence, date, confidence | Recommended action / scenario | Consumption loss if blocked | Additional capability or exposure if allowed |
| --- | --- | --- | --- | --- | --- |

Use **Allow**, **Block**, **Conditional**, or **Unresolved**. Keep the last two out of the unconditional allow set. Separate required viewing hosts, viewer-registration dependencies, dedicated prohibited-function hosts, shared dependencies, and optional requests using rows or a short grouping column as needed.

Attach a supporting primary-source link or capture reference near each material role/necessity claim. Mark a role inferred from a name as unverified. Explain global/shared-provider effects in the affected row; don't hide them in a generic warning.

Show exact-host and wildcard semantics and policy scope. If the platform is unknown, label syntax as vendor-neutral intent. Give an actionable exact-host set where evidence supports it; do not refuse all analysis merely because some hosts remain unknown. State explicitly when a sample does not support a complete list.

## Overlap options

Create one row per actual or plausible decision-changing overlap. Name both the useful capability X and the extra capability Y and the shared host or endpoint.

| Shared dependency and evidence | Allow X: working consumption and extra Y exposed | Block X: prohibited capability removed and consumption lost | Narrower alternative and required control | Recommendation / residual gap |
| --- | --- | --- | --- | --- |

For every material overlap provide both allowing and withholding the dependency, even if one is inconvenient. Do not claim Y succeeds merely because its host is reachable; say “endpoint reachable; operation unverified” when appropriate. Likewise do not claim blocking one host removes all routes to Y without evidence.

If there are multiple coupled hosts, give consistent end-to-end configurations:

| Scenario | Exact allow/block decisions or changes from common baseline | What works | What remains possible / unknown | Additional control required |
| --- | --- | --- | --- | --- |
| Restriction first | Withhold inseparable dependencies | State surviving consumption, including none if applicable | State remaining gaps | None beyond stated baseline, or specify |
| Consumption first | Allow indispensable shared dependencies | State supported consumption | State prohibited activity still reachable/possible | State absent protection plainly |
| Stronger separation, if viable | Add evidenced finer controls | State intended supported consumption | State validation still needed | Identify exact required capability |

Label each scenario's assurance level. A consumption-first exception is not a consumption-only guarantee. Avoid placing contradictory actions for the same exact hostname in one scenario; distinguish a service-scope fallback block from its explicit exceptions and verify precedence.

## Finer controls and verification

Keep URL paths, methods, API operations, account restrictions, and browser controls in their own table when applicable:

| Control / match | Required enforcement feature | Permitted workflow preserved | Prohibited action prevented | Known limit and evidence |
| --- | --- | --- | --- | --- |

End with a short test matrix separating desired from observed outcomes. Mark unrun tests clearly. List only the next observations needed to resolve important unknowns; when useful, give concise vendor questions about viewer-specific domains, shared APIs, guest editing, uploads, tenant boundaries, and supported viewer restrictions. Do not send those questions without a request.

Provide copyable allow/block lists or engine-native rules when requested or short enough to help implementation. Label provisional entries and scenario membership, include matching/default-action assumptions, and exclude tracking parameters, credentials, session tokens, and unsupported syntax. Report complete configurations per scenario so a reader cannot accidentally combine incompatible alternatives.
