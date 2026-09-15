# Web technology investigation

Read with the evidence and sanitization references. Choose tools based on detected content, not only the filename, and record which layers were inspected.

## Inventory and bounded decoding

Identify media type, encoding, compression, archive membership, size, completeness, provenance and tooling versions. Handle BOMs, text encodings, URL/HTML/JSON escaping, base64, gzip/Brotli and nested payloads only with supported decoders. Set size, recursion, time and decompression limits. Report malformed, truncated, encrypted, unknown-extension or unsupported content and preserve the original.

Treat HAR as a transport record with possible exporter extensions, omitted bodies, cache entries and synthetic fields. Inspect request/response URLs, redirects, methods, headers, cookies, bodies, statuses, initiators, timings and available connection information. Include failed/blocked requests. HAR may omit WebSocket messages, service-worker activity, cache traffic or runtime operations; obtain supplemental evidence instead of inventing it.

## Correlate by action and state

Create a timeline: identity/role and session -> user action -> DOM element/frame -> initiator/script -> request/operation -> destination -> response -> business result -> effective control. Use stable evidence IDs and safe pseudonyms. Compare anonymous viewing, viewer registration, authenticated viewing, creator login, existing sessions and prohibited operations where relevant.

Identify shared GraphQL/RPC paths, batched operations, WebSockets, WebTransport, service workers, signed media/storage URLs, redirects, embeds and custom tenant domains. Methods are evidence, not business permissions. Check playback segments, captions, DRM/license requests and session refresh where they affect consumption.

| Material | Investigate | Limits to record |
| --- | --- | --- |
| DOM/HTML/accessibility trees | Forms, hidden fields, links/share permissions, iframes, shadow roots, rendered states, bindings | Visibility is not authorization; cross-origin frames and closed shadow roots may be unavailable |
| JS/modules/source maps | Parsed syntax, imports, bundles, request clients, SDKs, endpoints, flags, authentication and mapped source | Strings may be dead code; banners and minified names are weak version evidence |
| CSS/assets | Imports, URLs, generated content, comments, source maps and embedded data | Sensitive data can occur here; hiding controls does not enforce permissions |
| WASM/WebAssembly/WAT | Module validation, imports/exports, custom/debug sections, string/data regions and JS glue | Stripped, optimized or encrypted regions may be opaque; do not claim complete source recovery |
| JSON/XML/protobuf/gRPC/multipart | Schema-aware parsing, operations, fields, attachments and encodings | Unknown schemas and opaque attachments create coverage gaps |
| Media/fonts/PDFs/archives/other objects | Relevant embedded metadata/text, manifests and references using suitable tools | Use extractors/OCR when available and report unexamined regions |

Prefer AST or format-aware parsing. Pretty-printing and strings extraction are aids, not complete semantic analysis. Default to static review of unknown executable content. Use scoped isolation when dynamic execution is authorized and needed.

For created HARs, state whether they are captured, converted, minimized or synthetic; record sources and transformations. Never manufacture observations or timings. Preserve parseable structure and label omitted/replaced data and invalidated signatures/checksums. Structural validity does not establish replay or reproduction of the original session.

Primary entry points: [Chrome Network](https://developer.chrome.com/docs/devtools/network/reference/), [WebAssembly](https://webassembly.org/specs/), [WHATWG](https://spec.whatwg.org/), [W3C](https://www.w3.org/TR/), [HAR 1.2](https://w3c.github.io/web-performance/specs/HAR/Overview.html). Recheck current versions when using them.
