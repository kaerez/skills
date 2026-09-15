# Changelog

**TLP:GREEN · (C) Erez Kalman**

## 0.1.0 — Initial repository handoff, 2026-09-15

- Export the existing installed Security Colleague core unchanged.
- Supply OpenAI and Claude Code plugin manifests over one shared core; omit runtime-only `policy.products` from exported OpenAI metadata for plugin-schema compatibility.
- Supply repository catalogs, validation, synthetic regression tests, and manual upload guidance.
- Preserve explicit limitations: HAR inventory and lossy minimization are bundled; general entity recognition and format-specific sanitizers are not.
- Repository publication, external installations, automatic updates, and client reloads remain unverified.
