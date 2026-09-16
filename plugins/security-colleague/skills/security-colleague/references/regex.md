# Regex work

Ask for source/target engines, exact versions, flags, matching API, input/replacement context, intended behavior and positive/negative examples. Separate regex syntax from JSON/YAML/shell/URL escaping and replacement syntax. Never execute untrusted shell fragments while passing a pattern.

Handle ECMAScript, Python `re`/third-party `regex`, PCRE/PCRE2, .NET, Java, ICU, RE2, Rust regex, POSIX BRE/ERE, Swift Regex and product-specific dialects according to the actual engine/version. A product field called regex may expose a restricted implementation.

1. Explain anchors, captures, lookarounds, backreferences, quantifiers, alternation and flags in that dialect.
2. Check Unicode properties, graphemes, case folding, normalization, boundaries, newlines, RTL/mixed scripts and ASCII-versus-Unicode shorthand classes.
3. Test full-match versus search, empty/overlapping matches, escaping, replacements and group numbering/names.
4. Compare source/target behavior on realistic and boundary examples. Limit equivalence claims to established scope. Report unsupported constructs/semantic loss and use procedural validation or multiple passes when one equivalent regex is impossible.
5. Test adversarial lengths and ambiguous repetition with process resource limits or an engine timeout. Do not run an unbounded potentially catastrophic pattern in the main session. Distinguish engine complexity from surrounding code.

Run tests using the target engine when available; otherwise provide a runnable harness and label predictions unexecuted. Never silently substitute Python/JavaScript for a PCRE2, Swift or .NET engine and report target-engine success.

For redaction and detection patterns, percent-decode, and where needed double-decode, before applying the pattern. An encoded separator hides structure: a path-segment rule never sees a real segment while `/` remains `%2F`, and a word-boundary anchor will not match an identifier preceded by an encoded character. Verifying a redaction with the redactor's own expression confirms only what the redactor already matched; construct the check pattern independently of the redaction rules and run it over the raw, decoded and double-decoded text. See [sanitization.md](sanitization.md).

For hostname/URL controls, parse URLs where possible, normalize correctly, anchor at DNS label boundaries and account for escaping, wildcard/apex behavior and IDNs. A loose substring match is not an exact-host policy. Exact-host, apex, wildcard scope and rule precedence are treated in full in [enforcement.md](enforcement.md); follow it there rather than rebuilding the semantics from the pattern.

Primary sources: [RE2](https://github.com/google/re2/wiki/Syntax), [PCRE2](https://www.pcre.org/current/doc/html/), [ECMAScript](https://tc39.es/ecma262/), [Python re](https://docs.python.org/3/library/re.html), [Swift Regex](https://developer.apple.com/documentation/swift/regex). Consult current target-engine documentation.
