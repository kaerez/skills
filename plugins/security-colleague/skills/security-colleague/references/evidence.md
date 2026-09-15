# Evidence and research

Use this reference for material security conclusions.

Record an evidence identifier, source type/location, observation/retrieval date, relevant client/OS/tool/service versions, tenant/region, identity role, workflow state, and confidence. Use safe aliases in reports; keep raw identifiers and secret-bearing URLs out of exported evidence.

Preserve originals in the authorized environment and work on derivatives. Record integrity hashes locally when needed, treating hashes of private inputs as sensitive metadata rather than publishing them automatically. Record transformations, parser versions, exclusions and errors. Keep secrets and redaction mappings out of logs, filenames, tracebacks and reports.

| Fact | Does not establish |
| --- | --- |
| Request appeared in a capture | It is necessary for the business workflow |
| Endpoint is reachable | Authorization permits the prohibited operation |
| HTTP response succeeded | The application accepted or committed the operation |
| Browser simulation blocked a request | A production firewall or endpoint policy does so |
| UI element is hidden | API, native client or existing-session access is blocked |
| Package/version string is present | That component runs on the vulnerable path |
| Delivered client code contains an authoring or upload path | The endpoint is reachable, authorized, or that the operation would succeed |
| A sanitized output passed a scan | The output is clean, when the scan reused the redactor's own patterns or skipped percent-decoding |
| A hostname resolves | A service answers there, or the name is in use for this workflow |
| A generated hostname variant returns NXDOMAIN | The vendor has no other regions or clusters |

Prefer vendor advisories, documentation, release notes, standards, source repositories and maintainer reports. Use secondary sources as leads and label reliance on them. Verify the exact feature, edition/license, deployment, client support and version range before producing native configuration.

Keep installed/observed versions, assessment-tool versions, target-component versions and current supported baselines separate. A latest release is not proof of the deployed build. A reduced user-agent or unverified banner does not establish exact versions.

When sources disagree, record each source and the conflict. Prefer evidence applicable to the exact surface/version; do not silently choose the convenient answer. If browsing is restricted, date supplied evidence and state which current claims remain unverified.

Give confidence per claim based on provenance and coverage. Describe the minimum test that resolves an important gap. Record expected and actual results separately. Stay within existing authorization and use a local fixture or supplied result where it resolves the question without side effects.
