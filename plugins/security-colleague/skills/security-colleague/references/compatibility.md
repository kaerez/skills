# Compatibility and distribution

Use the Agent Skills structure: a `security-colleague` folder with `SKILL.md`, scripts, references and assets. Keep the frontmatter name `security-colleague` and display name Security Colleague. Resolve resources relative to the skill. OpenAI `agents/openai.yaml` is optional host metadata, not a core dependency.

Intended repository: https://github.com/kaerez/skills. Package: `plugins/security-colleague/`. Each skill is individually installable and versioned, with one copy of its instructions. `.codex-plugin/plugin.json` and `.claude-plugin/plugin.json` describe the same package; root `.agents/plugins/marketplace.json` and `.claude-plugin/marketplace.json` catalogs reference it.

| Capability | Requirement/fallback |
| --- | --- |
| Instruction analysis | Host can read the skill and relevant evidence |
| Bundled HAR tools | Python 3.12 and authorized file access are the tested baseline; standard library only; verify other runtimes |
| Bundled host probe | Outbound DNS on UDP/TCP 53 to the selected resolvers, or a usable system resolver; standard library only; no HTTP and no DNS-over-HTTPS |
| Deep parsing/targeted sanitization | Suitable parsers, schemas, detectors and versions; declare missing coverage |
| Regex execution | Actual requested engine/version; otherwise deliver a harness and label predictions untested |
| Current research | Authorized research/network tools; otherwise state evidence dates and currency limits |
| Browser/dynamic tests | Actual browser or supported protocol, available access and scoped authorization |
| Artifacts/canvas | Supported output capability; offer an available format when canvas is absent |

Manifest validation is not execution compatibility. Record tested host/product/version, OS, runtime and feature coverage. ChatGPT/Codex, Claude/Claude Code, APIs and other Agent Skills-compatible clients may expose different capabilities.

## Source and updates

Source URL and version are provenance metadata. They do not enable an updater or authorize arbitrary downloaded code. Use platform/installer settings; do not self-modify this skill during an ordinary security review.

Before publication, verify repository visibility/access, preserve TLP:GREEN, and inspect existing instructions/licensing. Do not publish publicly unless the source authorizes wider sharing.

ChatGPT workspace GitHub-managed marketplace sync is configured by an administrator. Local Codex and Claude Code need their own supported installation/update settings. Claude chat ZIPs and API skill uploads are separate distributions. Verify current instructions for each product/version; one upload or source URL does not update every surface.

Track a reviewed release branch for automatic updates. Immutable tags identify reproducible releases. Keep manifest versions equal and increment them for each changed release. Validate packages and record source revision, compatibility and rollback information. If an updater is unavailable, state that and provide a verified manual process. Store update credentials in the host credential mechanism, never in skill files or URLs.

The author authorized publication of this initial package to the public source repository on 2026-09-15. External updates remain pending. Entry points: [Agent Skills](https://agentskills.io/specification), [OpenAI management](https://learn.chatgpt.com/docs/enterprise/plugin-management), [Claude Code marketplaces](https://code.claude.com/docs/en/plugin-marketplaces), [Claude custom skills](https://support.claude.com/en/articles/12512180-use-skills-in-claude).
