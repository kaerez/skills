# Installation and updates

**TLP:GREEN · (C) Erez Kalman**

Prepared 2026-09-15. Source: `https://github.com/kaerez/skills`. Initial package version: `0.1.0`. Both catalogs use marketplace name `personal`; plugin name is `security-colleague`. Avoid registering a second unrelated marketplace with that same name; rename both catalog names together before first installation if needed.

## Status

The handoff reuses the installed skill's instructions, scripts, references, and asset unchanged. Its exported OpenAI display metadata omits the runtime-only `policy.products` field rejected by the plugin validator; the installed skill is unchanged. Its earlier release archive was not recovered. The repository wrappers, tests, and documentation in this handoff were reconstructed. This is an export, not a new installation or publication. GitHub reported the destination public and the connected account without write access on 2026-09-15. Make the repository private before uploading under the agreed distribution scope.

The earlier choice of automatic-update destinations, “Both,” means **this ChatGPT workspace and local Codex installations**, as clarified in the supplied source conversation. Claude remains an additional compatibility target. None of these external update configurations has been activated by this export.

## ChatGPT workspace

After uploading, a workspace administrator can open **Admin > Plugins > Add > Import marketplace**, enter the repository URL, leave Path empty, and select the reviewed branch (currently `main`) or an immutable revision. Authorize repository access, review import results, and install Security Colleague individually. New imports have daily sync enabled; a branch receives future commits, while a fixed revision stays pinned. “Sync now” requests an immediate refresh. This remains untested in the user's workspace. [Official import and sync documentation](https://learn.chatgpt.com/docs/enterprise/plugin-management), checked 2026-09-15.

## Local Codex

The `.codex-plugin/plugin.json` manifest and `.agents/plugins/marketplace.json` catalog are supplied. Local Codex product, OS, version, credentials, and supported update mechanism remain unknown. Verify these before configuring installation or automatic updates. Do not infer local updating from successful workspace sync. If using a manual skill-directory installation supported by the selected client, copy the entire `plugins/security-colleague/skills/security-colleague/` folder, preserving relative paths. Copying files is not an automatic updater. No local Codex installation, auto-update, or active-session reload was tested here. [Official plugin management entry point](https://learn.chatgpt.com/docs/enterprise/plugin-management).

## Claude Code

Use a Git repository source, not the raw marketplace JSON URL, so relative package paths resolve. After publication, with authorized GitHub access:

```sh
claude plugin marketplace add https://github.com/kaerez/skills.git
claude plugin install security-colleague@personal
```

Use `/plugin` → Marketplaces → personal → Enable auto-update if desired. Third-party marketplace automatic updates are disabled by default. Use the host credential mechanism; do not embed tokens in this repository. These commands and settings are documentation-based, not installation-tested. [Marketplace sources](https://code.claude.com/docs/en/plugin-marketplaces), [plugin updates](https://code.claude.com/docs/en/discover-plugins), checked 2026-09-15.

## Claude chat and APIs

Package only the `security-colleague/` core folder with its `SKILL.md` and resources for a custom-skill upload where supported. The repository ZIP is not a Claude custom-skill upload. Check the chosen product's current upload interface, plan, and runtime before installing. API deployment is separate and needs its own versioned upload and selected skill identifier. No Claude chat or API upload was tested. [Custom skills documentation](https://support.claude.com/en/articles/12512180-use-skills-in-claude) is a reference entry point, not an installation verified in this handoff.

## Release, local changes, and rollback

Keep one source copy of each core skill. Before releasing changed content, increment both plugin manifest versions and the skill's package version; keep script release metadata and changelog consistent. Claude uses declared versions to determine whether an update is needed, so changing files without a version bump can retain the cached package. [Version management](https://code.claude.com/docs/en/plugins-reference#version-management), checked 2026-09-15.

Run validation, review the diff, and record the actual GitHub commit after upload. No GitHub source commit or release tag exists for these new files yet. Tag reviewed releases, for example `security-colleague-v0.1.0`. Keep local edits in a separate branch; commit or back them up before refreshing, and never automatically overwrite a dirty checkout. For rollback, select a known-good immutable revision where the client supports pinning, or restore reviewed content in a new release with a higher version. Confirm the installed version afterward.

Repository refresh, installed-package update, and active-session reload are separate events. Claude Code can require `/reload-plugins` or a new session after a background update. Follow the actual Codex client's documented reload behavior; it remains unverified here. Keep credentials in platform credential stores, not skill files. Do not describe updates as working until each destination has fetched, installed, and loaded a changed version.

## Compatibility limits

The shared instructions avoid proprietary tool names as core requirements; scripts use Python's standard library. Local validation uses Python 3.12 on Linux. The CI file proposes Linux, macOS, and Windows checks; remote CI has not run. Neither Claude Code nor local Codex is installed in the validation environment. Manifest validation and readable Markdown do not establish end-to-end compatibility. No live service enforcement tests were run for this handoff.
