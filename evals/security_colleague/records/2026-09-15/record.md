# Validation record — 2026-09-15

Smoke run proving the harness executes end to end. Not a benchmark: one eval,
one run per arm. Cite this record the way a CI run URL is cited.

- Harness: `evals/security_colleague/` at commit-time state of branch `claude/new-session-igalvt`
- Skill under test: `plugins/security-colleague/skills/security-colleague/` (package 0.3.0)
- Runners: `/mnt/skills/examples/skill-creator/scripts/` (`run_eval.py`, `aggregate_benchmark.py`)
- CLI: `claude` 2.1.272, model `claude-sonnet-5` (the model the CLI selected; no effort setting exposed)
- Operator: automated session, headless `claude -p`

## 1. Benchmark path — eval 1 `brief-mode-rule-shape`, 1 run per arm

| Arm | Pass rate | Wall time | Total tokens | Cost (list) | Turns |
| --- | --- | --- | --- | --- | --- |
| `with_skill` | 5/5 (1.00) | 74.0 s | 148,977 | $0.3048 | 4 |
| `without_skill` | 0/5 (0.00) | 33.3 s | 43,088 | $0.0686 | 1 |

Aggregator output (`benchmark.md`): pass rate 100% ± 0% vs 0% ± 0%, delta **+1.00**.

Every one of the five assertions discriminated. The baseline opened with the
host table and never named a rule shape; the grader's evidence line for the
baseline reads: "The response never names or invokes any of the three shapes."
The with-skill reply opened with a verdict ("Push an allowlist of the 4 hosts
staff actually need, plus one explicit block ... evaluated above whatever your
current default action is") before the first hostname.

Grading was performed by a separate `claude -p` invocation following
`agents/grader.md`: 65 s / $0.230 for the with-skill run, 62 s / $0.188 for the
baseline. The grader was told which run directory it was reading, so it was not
blind to the arm — the same exposure skill-creator's own flow has.

The grader also returned `eval_feedback` on assertion 5 of eval 1: the
assertion checks only that no separate artifact or file was produced, while the
in-chat reply was itself fairly report-shaped (five bold headers, a five-row
table, a fenced block). Worth tightening on the next pass.

Files: `eval-1-brief-mode-rule-shape/` — `benchmark.json`, `benchmark.md`,
`eval_metadata.json`, and per arm `response.md`, `grading.json`, `timing.json`.

## 2. Trigger path — `run_eval.py` on a 2-query subset

Ran three times against the same description, same model. The results moved:

| Invocation | Runs per query | Positive query trigger rate | Negative query trigger rate | Passed |
| --- | --- | --- | --- | --- |
| A (stdout captured in session transcript only) | 1 | 1/1 | 0/1 | 2/2 |
| B (`...-runs1-b.json`) | 1 | 0/1 | 1/1 | 0/2 |
| C (`...-runs3.json`) | 3 | 0/3 | 1/3 | 1/2 |

Invocation A was not redirected to a file, so only B and C are stored here; A is
reported from the session transcript and is not a runner-written artifact.

Two things this shows. First, the runner is wired: it builds the temporary
command file, drives `claude -p`, detects triggering from the stream, and
reports per-query rates. Second, single-run trigger measurement is noise —
which is why `--runs-per-query 3` is the default and why a whole eval set, not a
two-query subset, is the unit that means anything.

The aggregate over all five measured runs of the positive query is 1/5. That is
a finding about the description to hand to the optimization loop, not a harness
failure; note also that `run_eval.py` counts a run as triggered only when the
FIRST tool call names the skill, so a turn that answers directly in chat scores
as not triggered.
