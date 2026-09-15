# Security investigation and remediation

Establish goals, assets, identities, existing authorization, environments and expected outcome. Distinguish static/local review and public research from active tests affecting another system. Use test identities/content and the least-impact proof that resolves the question. Analysis does not authorize unrelated targets or production changes.

Record the component and exact version/configuration, exposure path, trust boundary, attacker prerequisites, evidence, reproducibility, impact, uncertainty and mitigations. Consider authentication/authorization, tenant isolation, data flows, supply-chain dependencies, browser policies, TLS, DNS and network controls. Investigate alternate routes within scope and pair them with defensive tests and mitigations.

Use supported parsers, primary research, static analysis and scoped dynamic analysis according to actual capabilities. A dependency name/version substring alone does not establish a vulnerability: verify affected version ranges and relevant code/path applicability. Preserve CVE status such as rejected, disputed or awaiting analysis.

| Reference | Proper use |
| --- | --- |
| CVE/vendor advisories | Identify the vulnerability and affected/fixed versions using applicable evidence |
| NVD | Enrichment, references, affected-product data and analysis status; record dates and gaps |
| CWE | Weakness/root cause |
| MITRE ATT&CK | Relevant adversary behavior, not severity |
| CVSS, including v4 | Version, full vector, scorer/source and assumptions; distinguish published/self-assessed values |
| EPSS | Dated exploitation probability and percentile when used; distinct from severity or proof of exploitation |
| CISA KEV/exploitation evidence | Dated evidence and applicability rather than inferring exploitation from a score |
| TLP | Source sharing restrictions, not severity or software licensing |

Validate CVSS vectors/scores with current official or maintained implementations for the requested version. Explain unknown environmental/threat inputs rather than inventing precision. Use dated EPSS evidence alongside exposure and business impact.

For TLS, inspect versions, trust chains, hostname validation, cipher/configuration support, mTLS, inspection and pinning on the real path. For TCP/UDP, firewalls, proxies, routing, switches, VLANs, hubs and segmentation, identify layer, direction, translated addresses/identities, state and visibility. Name the specific misconfiguration or risk; device categories alone do not establish effective boundaries.

Prefer supported patches/configurations addressing the cause. Provide scope, prerequisites, verified steps, operational impact, compensating controls and gaps, rollback and meaningful retests. Separate proposed/applied/verified changes and confirm both security behavior and business workflows.

Primary entry points: [CVE](https://www.cve.org/), [NVD](https://nvd.nist.gov/), [CWE](https://cwe.mitre.org/), [ATT&CK](https://attack.mitre.org/), [CVSS v4](https://www.first.org/cvss/v4.0/), [EPSS](https://www.first.org/epss/), [TLP](https://www.first.org/tlp/), [CISA KEV](https://www.cisa.gov/known-exploited-vulnerabilities-catalog), [OWASP WSTG](https://owasp.org/www-project-web-security-testing-guide/), [IETF](https://www.rfc-editor.org/).
