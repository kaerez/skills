# Validation — 2026-09-15

**TLP:GREEN · (C) Erez Kalman**

- Python 3.12.14 on Linux: all 8 bundled synthetic HAR regression tests passed.
- OpenAI plugin validator: passed after excluding runtime-only policy.products from exported UI metadata.
- Installed core skill frontmatter validator: passed. Scripts were exported unchanged; core provenance notes were updated for publication.
- Repository checks: catalogs, names, versions, markings, relative references, and Python syntax passed.
- Archive integrity and all member hashes checked during handoff.

GitHub Actions passed repository validation and all 8 HAR tests on Ubuntu, Windows, and macOS for published commit `140569c81a4611ae6688cdaeddbe26ce46de57fa`. [Verified CI run](https://github.com/kaerez/skills/actions/runs/34972621145). All 29 package file Git blob hashes matched the published tree; the existing LICENSE blob was preserved.

Not run: local Codex or Claude installation, workspace import, automatic updates, reloads, or live enforcement tests. Tests do not prove universal sanitization or language-aware detection. No real captures are included.
