# Browsers, developer tools and versions

Separate the user's browser/client, assessment browser, automation library, protocol/schema, target app/SDK and enforcement tool. Record build, release channel, architecture, OS, policies, extensions and capture settings when material. Do not substitute a latest version for an observed one.

Cover Chrome/Chromium, Edge, Firefox and Safari on relevant desktop/mobile platforms, native wrappers, webviews and fat clients. Identify the actual engine for the OS/region; a brand is not a universal engine guarantee. Native clients may have different endpoints, token stores, engines, certificate validation and process identities.

Prefer an authorized About/version page, signed package/binary metadata, executable version output, lockfile plus runtime confirmation or a supported automation version API. Preserve provenance and confidence. Reduced user-agents, filenames and banners are hints. Distinguish vendored SDK code from the version invoked in the relevant flow.

Identify DevTools/CDP/WebDriver/WebDriver BiDi/debugging support for the actual build and use its supported schema. CDP methods are not automatically Firefox/Safari methods; do not invent an equivalent endpoint or treat a `tot` schema as deployed support.

- Record navigation interval, Preserve log, cache, service workers, profile/private mode, extensions and login state.
- Inspect CORS, CSP, cookies/SameSite, storage partitioning, frames/sandbox rules, secure contexts and permission policies when relevant.
- Separate browser security restrictions from business authorization and enterprise controls; consider fresh and existing sessions.
- Review DNS/DoH, SNI/CONNECT visibility, ECH, HTTP/2/HTTP/3/QUIC, TLS interception, trust stores, pinning, mTLS, proxies, split tunneling and agent coverage on the actual path. Propose protocol changes only when the selected control needs them, with impact documented.
- Verify effective policy values, scope/precedence, OS/edition/version, mandatory/recommended status and personal-profile coverage. Configuration alone does not prove deployment.
- Treat a vendor browser extension or managed-browser agent as its own enforcement layer with its own coverage. It can reach clients the network path cannot inspect, which is exactly where the uninspectable-OS gaps above bite. Confirm licensing, deployment scope and the browsers actually covered before relying on it, and ask about it during intake.
- Separate endpoint app blocking from action controls inside a running app. Use actual bundle/process/publisher/hash selectors and platform support. Explain how browser consumption is retained if intended.

Verify exact configurations using official browser, automation, Cato and Iru/Kandji documentation. Do not assume every CASB supports every service/action or native client.

Entry points: [Chrome DevTools](https://developer.chrome.com/docs/devtools/), [Chromium UA reduction](https://www.chromium.org/updates/ua-reduction/), [Firefox DevTools](https://firefox-source-docs.mozilla.org/devtools-user/), [Safari tools](https://developer.apple.com/safari/tools/), [Edge](https://learn.microsoft.com/en-us/deployedge/), [WebDriver BiDi](https://www.w3.org/TR/webdriver-bidi/), [Cato](https://knowledge.catonetworks.com/), [Iru](https://docs.iru.com/).
