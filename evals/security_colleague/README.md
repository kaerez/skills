# security-colleague — eval harness

**TLP:GREEN · (C) Erez Kalman**

Quantitative evals for `plugins/security-colleague/skills/security-colleague/`,
built on the [skill-creator](https://github.com/anthropics/skills) harness at
`/mnt/skills/examples/skill-creator/`. Two things are measured, and they are
independent:

- **Behaviour** — with the skill loaded, does the run do what the skill exists to
  make it do? Measured by `evals.json` + the benchmark flow below.
- **Triggering** — does the frontmatter `description` cause Claude to reach for
  the skill at all? Measured by `trigger_queries.json` + `run_eval.py`.

A skill can pass one and fail the other, so neither number stands in for the
other.

## Why the evals live here and not in the skill directory

skill-creator puts evals inside the skill folder (`<skill>/evals/`). This repo
deliberately does not, and that is not an oversight to correct.

`docs/installation-and-updates.md` tells users to install by copying the entire
`plugins/security-colleague/skills/security-colleague/` folder, preserving
relative paths. Everything in that folder ships to every user on every install.
Eval prompts, fixtures, workspace trees and benchmark output would ride along
and be useful to nobody downstream — they verify the skill, they are not part of
it.

Top level also mirrors what the repo already does: `tests/security_colleague/`
holds the unit tests for the bundled scripts, outside the shipped folder, for
the same reason. `evals/security_colleague/` is the same convention for the
things that verify the skill's *behaviour* rather than its scripts.

The skill-creator runners all take paths as arguments, so pointing them outward
costs nothing but the flags shown below.

## Layout

```
evals/security_colleague/
├── README.md                 this file
├── evals.json                the 5 behavioural evals (skill-creator evals.json schema)
├── trigger_queries.json      20 queries for description triggering (10 should / 10 should-not)
├── scripts/make_workspace.py materializes the run directory layout the runners expect
├── records/<YYYY-MM-DD>/     committed validation records (see "Records", below)
└── workspace/                run artifacts — git-ignored, regenerated on demand
```

`evals.json` follows `references/schemas.md` exactly (`skill_name`, and per eval
`id`, `prompt`, `expected_output`, `files`, `expectations`) with one repo-local
addition: a `name` field, which `make_workspace.py` copies into
`eval_metadata.json` as `eval_name` — a field skill-creator's own schema has and
`evals.json` does not. The eval viewer reads `benchmark.json`, whose field names
are fixed and unforgiving; do not rename anything by hand.

## The five evals

Each one comes from a real observed failure in two reviewed transcripts where
the skill under-performed. The assertion is what should have happened.

| id | name | The failure it pins down |
| --- | --- | --- |
| 1 | `brief-mode-rule-shape` | The rule-shape verdict lived only in the detailed-report reference, so brief-chat mode produced host lists with no shape, no deciding fact, and no statement of what the shape cannot do. |
| 2 | `followup-missed-host` | A follow-up naming a host the analysis missed was answered as a one-host lookup — "good catch, I probed the wrong spelling and got NXDOMAIN, so I missed it" — instead of as a defect in the enumeration method. |
| 3 | `completeness-bound-volunteered` | The completeness bound of a host set was stated only after the user asked "are you 100% sure?". |
| 4 | `capture-requested-on-unresolved` | Neither run ever asked for a capture, including for hosts whose role read-only retrieval could not settle. |
| 5 | `no-maturity-label` | A "Recommended pilot" table stood in for a statement of coverage, and drew "no pilot's, no half baked answers". |

## Writing or changing an eval

Two rules, both load-bearing:

**An assertion that passes with or without the skill measures nothing.** This is
skill-creator's own analyzer finding, and it is the main way an eval suite rots:
it fills up with assertions any competent generic answer satisfies, the pass
rate goes to 100% in both arms, and the suite stops being able to detect a
regression. Write each assertion so that a baseline run *without* the skill
would plausibly fail it, and check that against the baseline arm — if both arms
pass an assertion every time, the assertion is decoration. The 2026-09-15 record
shows what a working assertion looks like: 5/5 with the skill, 0/5 without.

**Synthetic hostnames only.** Every host in every prompt uses the `.invalid`
TLD, and no prompt names a real vendor, product, tenant or company. These
prompts get pasted into model calls and committed to a public repository; a real
customer's host list in an eval fixture is an evidence-handling problem, and the
skill's own TLP marking does not clear evidence for sharing.

## Running the evals

All commands are run from the repository root unless stated. `SC` and `SK` below
are just to keep the commands readable:

```sh
SC=/mnt/skills/examples/skill-creator
SK=/workspace/skills/plugins/security-colleague/skills/security-colleague
H=/workspace/skills/evals/security_colleague
```

Adjust `/workspace/skills` to wherever the repository is checked out, and `$SC`
to wherever skill-creator lives — it is not vendored here.

### 1. Trigger evals (does the description fire?)

```sh
cd "$H" && env -u CLAUDECODE PYTHONPATH="$SC" python3 -m scripts.run_eval \
  --eval-set "$H/trigger_queries.json" \
  --skill-path "$SK" \
  --runs-per-query 3 \
  --num-workers 10 \
  --timeout 30 \
  --model claude-sonnet-5 \
  --verbose \
  > "$H/records/$(date +%F)/trigger-eval.json"
```

Notes that will save an hour:

- Run it with `$H` as the working directory. `run_eval.py` writes a temporary
  slash-command file into the nearest `.claude/commands/` **above the working
  directory**; from `$H` that lands in `evals/security_colleague/.claude/`,
  which `.gitignore` covers. From the repository root it would create a
  `.claude/` directory next to `plugins/`.
- `env -u CLAUDECODE` is belt-and-braces: `run_eval.py` already strips that
  variable from the environment of the `claude -p` children it spawns, but a
  direct `claude -p` call (the executor step below) needs it to nest inside a
  Claude Code session.
- `--model` should be the model the users of this skill actually run, so the
  triggering test matches their experience.
- A run counts as triggered only when the *first* tool call names the skill. A
  turn that answers directly in chat scores as not triggered, which is the
  intended semantics but does make short queries look like failures.

### 2. With/without-skill benchmark (does the skill change the answer?)

Create the run directories, then fill them. One eval, one run per arm, is the
cheap smoke test; `--evals-only` and `--runs` are the knobs.

```sh
python3 "$H/scripts/make_workspace.py" --iteration 1 --runs 3           # all five evals
python3 "$H/scripts/make_workspace.py" --iteration 1 --runs 1 --evals-only 1   # smoke test
```

For each `eval-<id>-<name>/` directory this creates `eval_metadata.json`,
`prompt.txt`, and `with_skill/run-<k>/outputs/` plus `without_skill/run-<k>/outputs/`.

Then, for every run directory:

1. **Execute.** Spawn both arms in the same batch so they finish together. The
   with-skill arm is given the skill; the baseline arm is given the identical
   prompt and nothing else. In Claude Code, subagents; headless, the shape that
   produced the 2026-09-15 record was:

   ```sh
   W="$H/workspace/iteration-1/eval-1-brief-mode-rule-shape"
   env -u CLAUDECODE claude -p "Before answering, read the skill at $SK/SKILL.md and follow it, \
   including any reference files it tells you to load. Then answer the user message below as their \
   security colleague, in chat. Do not ask me anything back; produce your answer.

   --- user message ---
   $(cat "$W/prompt.txt")" --output-format json --allowedTools "Read,Glob,Grep" \
     > "$W/with_skill/run-1/raw_result.json"
   ```

   Save the reply to `<run>/outputs/response.md` and write `<run>/timing.json`
   with `total_tokens`, `duration_ms` and `total_duration_seconds` — the token
   and duration numbers are only available at this moment and are not recoverable
   afterwards.

2. **Grade.** One grader invocation per run, following
   `$SC/agents/grader.md`, writing `<run>/grading.json`. The `expectations`
   array must use the field names `text`, `passed`, `evidence` — the viewer
   breaks on anything else.

3. **Aggregate.**

   ```sh
   cd "$H" && PYTHONPATH="$SC" python3 -m scripts.aggregate_benchmark \
     "$H/workspace/iteration-1" \
     --skill-name security-colleague \
     --skill-path "$SK"
   ```

   Writes `benchmark.json` and `benchmark.md` next to the iteration directory,
   with mean ± stddev per configuration and the delta. `with_skill` sorts before
   `without_skill`, so the delta is (skill − baseline).

4. **Review.** Optional, and needs a browser or `--static`:

   ```sh
   python3 "$SC/eval-viewer/generate_review.py" "$H/workspace/iteration-1" \
     --skill-name security-colleague \
     --benchmark "$H/workspace/iteration-1/benchmark.json" \
     --static "$H/workspace/iteration-1/review.html"
   ```

Three aggregator quirks found while wiring this up, none of them worth patching
upstream but all worth knowing:

- `metadata.runs_per_configuration` is hardcoded to `3`. If you ran a different
  number, fix it in `benchmark.json` by hand or the header lies.
- Token columns come out `0` when `grading.json` carries a `timing` block: the
  aggregator only falls back to `timing.json` (where `total_tokens` lives) if
  the grading file gave it no duration. Either omit `timing` from `grading.json`
  or put the count in `execution_metrics`.
- `runs[]` entries carry `eval_id` but not `eval_name`, so viewer section
  headers fall back to the id.

### 3. Description-optimization loop

```sh
cd "$H" && env -u CLAUDECODE PYTHONPATH="$SC" python3 -m scripts.run_loop \
  --eval-set "$H/trigger_queries.json" \
  --skill-path "$SK" \
  --model claude-sonnet-5 \
  --max-iterations 5 \
  --runs-per-query 3 \
  --holdout 0.4 \
  --results-dir "$H/loop-results" \
  --report none \
  --verbose
```

It splits `trigger_queries.json` 60/40 into train and held-out test, scores the
current description, asks a model to propose a better one, re-scores, and
repeats — returning `best_description`, chosen by *test* score to avoid
overfitting. `--report none` suppresses the browser open on a headless box;
drop it if you have a display.

**Its output is a rewritten frontmatter `description`, and nothing here applies
it.** The description is the skill's entire trigger surface: it is what Claude
sees before it has read a single line of the skill, and it is simultaneously the
contract this repo publishes to two plugin catalogs. A model optimizing it
against twenty queries will happily trade away a clause that no query covers —
the TLP marking, the "applies for the whole engagement" sentence, the
follow-up-hosts clause — because nothing in the eval set punishes losing it.
Read the proposal, diff it against the current description, keep what it got
right, and edit `SKILL.md` by hand. Then check the constraints the repo's own
validator enforces (`python tools/validate_repository.py`): the description must
stay a `>-` folded block and stay at or under 1024 characters, and a content
change means both plugin manifest versions and the package version in `SKILL.md`
move together.

## Why this is not in CI, and what to do instead

Every runner here calls a model. That means:

- **Non-deterministic.** The same eval, same model, same description gives
  different numbers between invocations — the 2026-09-15 record has the same
  two-query trigger subset scoring 2/2, then 0/2, then 1/2 in the space of ten
  minutes. A single run is an anecdote; `--runs-per-query 3` and multiple
  benchmark runs exist for exactly this reason. Treat a one-run delta as a
  direction, not a measurement.
- **Token-costed.** The one-eval, one-run-per-arm smoke test in the record cost
  roughly $0.79 in list-price tokens across four model invocations. A full five
  eval benchmark with a baseline arm at three runs per configuration is on the
  order of 60 invocations and $10–20; a five-iteration description loop over the
  twenty trigger queries is on the order of 300 short invocations.
- **Credential-bearing.** Running any of this in GitHub Actions would require an
  API credential in repository secrets, on a public repository whose CI
  currently needs no secret at all. `.github/workflows/validate.yml` runs
  `tools/validate_repository.py` and the unit tests — offline, deterministic,
  free, and safe to run on a fork's pull request. Adding a paid, flaky,
  secret-dependent job to that workflow would cost more than it tells anyone.

So: **these run on demand, not on push.** They are deliberately absent from
`.github/workflows/`.

### Records

Run them when the skill's behaviour changes — a new procedure, a reworded
deliverable rule, a description rewrite — and commit the dated output under
`records/<YYYY-MM-DD>/` as a validation record, cited in the pull request or
changelog the way a CI run URL is cited today. A record says what was run,
against which skill version, on which model, and what came out; that is what
makes a behavioural claim checkable by someone who was not there. `workspace/`
stays git-ignored — the record is the curated copy, not the scratch tree.

Start from `records/2026-09-15/record.md`, which is the wiring proof for this
harness and the shape a later record should follow.
