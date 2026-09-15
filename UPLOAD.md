# Upload these files

**TLP:GREEN · (C) Erez Kalman**

1. Make `kaerez/skills` private before adding this TLP:GREEN package.
2. Extract `security-colleague-repository-files.zip`.
3. Copy the extracted contents directly into the repository root, alongside its existing `LICENSE`. Do not upload the ZIP itself or add a wrapping `security-colleague-handoff` folder.
4. Replace the existing `README.md`; leave the existing `LICENSE` untouched. Include the dot-prefixed directories `.agents`, `.claude-plugin`, and `.github`, plus `.gitignore`. On macOS, Command+Shift+Period reveals these in Finder.
5. Commit your reviewed files. Package installation and update configuration are separate; see `docs/installation-and-updates.md`.

The table gives exact paths relative to the repository root. All folders are already present inside the ZIP.

| File destination | Action |
| --- | --- |
| `.agents/plugins/marketplace.json` | Add |
| `.claude-plugin/marketplace.json` | Add |
| `.github/workflows/validate.yml` | Add |
| `.gitignore` | Add |
| `README.md` | Replace existing |
| `SHA256SUMS.txt` | Add |
| `UPLOAD.md` | Add |
| `VALIDATION.md` | Add |
| `docs/installation-and-updates.md` | Add |
| `plugins/security-colleague/.claude-plugin/plugin.json` | Add |
| `plugins/security-colleague/.codex-plugin/plugin.json` | Add |
| `plugins/security-colleague/CHANGELOG.md` | Add |
| `plugins/security-colleague/skills/security-colleague/SKILL.md` | Add |
| `plugins/security-colleague/skills/security-colleague/agents/openai.yaml` | Add |
| `plugins/security-colleague/skills/security-colleague/assets/icon.svg` | Add |
| `plugins/security-colleague/skills/security-colleague/references/browser-versions.md` | Add |
| `plugins/security-colleague/skills/security-colleague/references/compatibility.md` | Add |
| `plugins/security-colleague/skills/security-colleague/references/consumption-review.md` | Add |
| `plugins/security-colleague/skills/security-colleague/references/enforcement.md` | Add |
| `plugins/security-colleague/skills/security-colleague/references/evidence.md` | Add |
| `plugins/security-colleague/skills/security-colleague/references/regex.md` | Add |
| `plugins/security-colleague/skills/security-colleague/references/report-format.md` | Add |
| `plugins/security-colleague/skills/security-colleague/references/sanitization.md` | Add |
| `plugins/security-colleague/skills/security-colleague/references/security-investigation.md` | Add |
| `plugins/security-colleague/skills/security-colleague/references/web-investigation.md` | Add |
| `plugins/security-colleague/skills/security-colleague/scripts/har_inventory.py` | Add |
| `plugins/security-colleague/skills/security-colleague/scripts/har_minimize.py` | Add |
| `tests/security_colleague/test_har.py` | Add |
| `tools/validate_repository.py` | Add |
