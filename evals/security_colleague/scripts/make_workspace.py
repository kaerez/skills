#!/usr/bin/env python3
"""Materialize a skill-creator benchmark workspace from evals.json.

TLP:GREEN. (C) Erez Kalman.

The skill-creator runners (`scripts/aggregate_benchmark.py`,
`eval-viewer/generate_review.py`) read a fixed directory layout:

    <workspace>/iteration-<N>/
      eval-<id>-<name>/
        eval_metadata.json          {eval_id, eval_name, prompt, assertions}
        prompt.txt
        with_skill/run-<k>/outputs/
        without_skill/run-<k>/outputs/

This script creates that layout from `evals.json` so the executor and grader
runs only have to drop `outputs/`, `timing.json` and `grading.json` into
directories that already exist with the right names. It writes no results and
calls no model.

Usage:
    python3 scripts/make_workspace.py --iteration 1 --runs 3
    python3 scripts/make_workspace.py --evals evals.json --out workspace \
        --iteration 2 --runs 1 --evals-only 1
"""
import argparse
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent.parent


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--evals", type=Path, default=HERE / "evals.json",
                        help="Path to evals.json (default: alongside this harness)")
    parser.add_argument("--out", type=Path, default=HERE / "workspace",
                        help="Workspace root (default: <harness>/workspace)")
    parser.add_argument("--iteration", type=int, required=True, help="Iteration number")
    parser.add_argument("--runs", type=int, default=3, help="Runs per configuration")
    parser.add_argument("--configs", default="with_skill,without_skill",
                        help="Comma-separated configuration names; the first is the primary "
                             "arm and the second is the baseline the delta is measured against")
    parser.add_argument("--evals-only", default="", help="Comma-separated eval ids to materialize")
    args = parser.parse_args()

    data = json.loads(args.evals.read_text(encoding="utf-8"))
    wanted = {int(x) for x in args.evals_only.split(",") if x.strip()}
    configs = [c.strip() for c in args.configs.split(",") if c.strip()]
    iteration_dir = args.out / f"iteration-{args.iteration}"

    created = []
    for item in data["evals"]:
        if wanted and item["id"] not in wanted:
            continue
        eval_dir = iteration_dir / f"eval-{item['id']}-{item['name']}"
        eval_dir.mkdir(parents=True, exist_ok=True)
        (eval_dir / "eval_metadata.json").write_text(json.dumps({
            "eval_id": item["id"],
            "eval_name": item["name"],
            "prompt": item["prompt"],
            "assertions": item["expectations"],
        }, indent=2) + "\n", encoding="utf-8")
        (eval_dir / "prompt.txt").write_text(item["prompt"] + "\n", encoding="utf-8")
        for config in configs:
            for run in range(1, args.runs + 1):
                (eval_dir / config / f"run-{run}" / "outputs").mkdir(parents=True, exist_ok=True)
        created.append(eval_dir)

    if not created:
        raise SystemExit(f"No evals matched --evals-only={args.evals_only!r}")
    print(f"Workspace: {iteration_dir}")
    for eval_dir in created:
        print(f"  {eval_dir.name}: {len(configs)} configs x {args.runs} run(s)")


if __name__ == "__main__":
    main()
