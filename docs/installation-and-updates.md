# Installation and updates

**TLP:GREEN · (C) Erez Kalman**

Prepared 2026-09-15. Source: `https://github.com/kaerez/skills`. Current package version: `0.4.0`. Initial published version: `0.1.0`. Both catalogs use marketplace name `ksec`; plugin name is `security-colleague`. The OpenAI catalog display name is `KSEC`. The marketplace was renamed from `personal` to `ksec`; existing client registrations and installed plugin identifiers must be checked separately. Changing these catalog files does not establish that an existing installation has migrated to the new name.

## Status

The handoff retains the installed skill's workflows, scripts, and asset; provenance notes were updated for repository publication. Its exported OpenAI display metadata omits the runtime-only `policy.products` field rejected by the plugin validator; the installed skill is unchanged. Its earlier release archive was not recovered. The repository wrappers, tests, and documentation in this handoff were reconstructed. The repository package is being published with the author's explicit authorization to use this public repository, given on 2026-09-15 after visibility was confirmed. Write access was verified. The earlier private-repository prerequisite is superseded for this package publication only. No evidence, captures, or reports are authorized for publication by that decision.

The earlier choice of automatic-update destinations, “Both,” means **this ChatGPT workspace and local Codex installations**, as clarified in the supplied source conversation. Claude remains an additional compatibility target. None of these external update configurations has been activated by this export.

## ChatGPT workspace

After uploading, a workspace administrator can open **Admin > Plugins > Add > Import marketplace**, enter the repository URL, leave Path empty, and select the reviewed branch (currently `main`) or an immutable revision. Authorize repository access, review import results, and install Security Colleague individually. New imports have daily sync enabled; a branch receives future commits, while a fixed revision stays pinned. “Sync now” requests an immediate refresh. This remains untested in the user's workspace. [Official import and sync documentation](https://learn.chatgpt.com/docs/enterprise/plugin-management), checked 2026-09-15.

## Local Codex

The `.codex-plugin/plugin.json` manifest and `.agents/plugins/marketplace.json` catalog are supplied. Local Codex product, OS, version, credentials, and supported update mechanism remain unknown. Verify these before configuring installation or automatic updates. Do not infer local updating from successful workspace sync. If using a manual skill-directory installation supported by the selected client, copy the entire `plugins/security-colleague/skills/security-colleague/` folder, preserving relative paths. Copying files is not an automatic updater. No local Codex installation, auto-update, or active-session reload was tested here. [Official plugin management entry point](https://learn.chatgpt.com/docs/enterprise/plugin-management).

## Claude Code

Use a Git repository source, not the raw marketplace JSON URL, so relative package paths resolve. After publication, with authorized GitHub access:

```sh
claude plugin marketplace add https://github.com/kaerez/skills.git
claude plugin install security-colleague@ksec
```

Use `/plugin` → Marketplaces → ksec → Enable auto-update if desired. Third-party marketplace automatic updates are disabled by default. Use the host credential mechanism; do not embed tokens in this repository. These commands and settings are documentation-based, not installation-tested. [Marketplace sources](https://code.claude.com/docs/en/plugin-marketplaces), [plugin updates](https://code.claude.com/docs/en/discover-plugins), checked 2026-09-15.

## Claude chat and APIs

Package only the `security-colleague/` core folder with its `SKILL.md` and resources for a custom-skill upload where supported. The repository ZIP is not a Claude custom-skill upload. Check the chosen product's current upload interface, plan, and runtime before installing. API deployment is separate and needs its own versioned upload and selected skill identifier. No Claude chat or API upload was tested. [Custom skills documentation](https://support.claude.com/en/articles/12512180-use-skills-in-claude) is a reference entry point, not an installation verified in this handoff.

## Release, local changes, and rollback

Keep one source copy of each core skill. Before releasing changed content, increment both plugin manifest versions and the skill's package version; keep script release metadata and changelog consistent. Claude uses declared versions to determine whether an update is needed, so changing files without a version bump can retain the cached package. [Version management](https://code.claude.com/docs/en/plugins-reference#version-management), checked 2026-09-15.

Run validation, review the diff, and record the actual GitHub commit after upload. The publishing commit in this repository records the exact source revision; no release tag has been created. Tag reviewed releases, for example `security-colleague-v0.1.0`. Keep local edits in a separate branch; commit or back them up before refreshing, and never automatically overwrite a dirty checkout. For rollback, select a known-good immutable revision where the client supports pinning, or restore reviewed content in a new release with a higher version. Confirm the installed version afterward.

Repository refresh, installed-package update, and active-session reload are separate events. Claude Code can require `/reload-plugins` or a new session after a background update. Follow the actual Codex client's documented reload behavior; it remains unverified here. Keep credentials in platform credential stores, not skill files. Do not describe updates as working until each destination has fetched, installed, and loaded a changed version.

## Validation record

`0.4.0`, 2026-09-16. GitHub Actions ran `tools/validate_repository.py` and the
full regression suite on Python 3.12 across Linux, macOS and Windows: validation
passed and all 60 tests passed on every job. [Verified run for 0.4.0](https://github.com/kaerez/skills/actions/runs/35053423387).
The validator now also checks markdown table shape, link fragments, changelog
section claims and the frontmatter description bound; each guard was shown
failing against a deliberately broken copy before it was kept.

A skill eval harness lives at `evals/security_colleague/`. Its first recorded
run compares the skill against a no-skill baseline on a brief-mode consumption
review: 3/3 with the skill, 0/3 without. These runners call a model, so they are
non-deterministic, cost tokens, and are deliberately not wired into CI; run them
on demand and commit the dated record under `evals/security_colleague/records/`.

`0.3.0`, 2026-09-15. GitHub Actions ran `tools/validate_repository.py` and the
full regression suite on Python 3.12 across Linux, macOS and Windows: validation
passed and all 59 tests passed on every job — 41 inherited plus 18 for the new
rule-coverage check. [Verified run for 0.3.0](https://github.com/kaerez/skills/actions/runs/34998754101).
The suite was also re-run locally on Python 3.11.15 (Linux) before the push,
with the same result.

`0.2.0`, 2026-09-15. GitHub Actions ran `tools/validate_repository.py` and the
full regression suite on Python 3.12 across Linux, macOS and Windows: validation
passed and all 41 tests passed on every job.
[Verified run for 0.2.0](https://github.com/kaerez/skills/actions/runs/34990618029). The suite was also re-run locally on Python
3.11.15 (Linux) before the push, with the same result; 3.12 remains the tested
baseline and the CI run is the evidence for it. The host-probe wire codec is
exercised against a local stub resolver, so the tests need no outbound DNS.

Not run for this release: ChatGPT workspace import, local Codex or Claude
installation, automatic updates, session reloads, and any live enforcement test.
No real capture is included in the repository.

## Compatibility limits

The shared instructions avoid proprietary tool names as core requirements; scripts use Python's standard library. Local validation uses Python 3.12 on Linux. GitHub Actions passed the repository checks and all 41 synthetic tests on Linux, macOS, and Windows. [Verified run for the published package](https://github.com/kaerez/skills/actions/runs/34990618029); the [0.1.0 run](https://github.com/kaerez/skills/actions/runs/34972621145) covered 8 tests. Neither Claude Code nor local Codex is installed in the validation environment. Manifest validation and readable Markdown do not establish end-to-end compatibility. No live service enforcement tests were run for this handoff.
