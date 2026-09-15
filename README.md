# Erez Kalman — Skills

**TLP:GREEN · (C) Erez Kalman**

Individually installable skills. Publication source: https://github.com/kaerez/skills.

| Package | Version | Core skill |
| --- | --- | --- |
| Security Colleague | 0.1.0 | [Instructions](plugins/security-colleague/skills/security-colleague/SKILL.md) |

Security Colleague reviews consumption-only service access, shared dependencies, enforcement options, HAR/web evidence, sanitization, regex, browser versions, and scoped security findings. It asks about available controls, client scope, and report depth. Its bundled Python tools provide host inventory and lossy HAR minimization. Deeper parsing and multilingual entity detection require suitable tools and verification; they are not bundled universal sanitizers.

See [UPLOAD.md](UPLOAD.md) for exact file destinations and [installation and updates](docs/installation-and-updates.md) for platform-specific instructions and unverified items.

Both platform catalogs reference `plugins/security-colleague/`. The shared core is self-contained under `plugins/security-colleague/skills/security-colleague/`; future packages belong in `plugins/<skill-name>/` and receive separate versions and catalog entries.

Validate from the repository root with Python 3.12:

```sh
python tools/validate_repository.py
python -m unittest discover -s tests/security_colleague -v
```

TLP, copyright, and licensing are separate. This handoff does not replace or amend the repository's existing `LICENSE`. The package marking does not authorize sharing evidence, captures, or reports. Use non-public distribution consistent with the author's TLP:GREEN instructions.
