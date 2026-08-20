#!/usr/bin/env python3
"""
A/B gate for system-prompt changes.

The plain pass rate over all 36 golden cases cannot decide a prompt change:
9 cases never reach the LLM (deterministic card paths in
webservice/routers/chat.py return before the agent is invoked) and 4 more are
driven by an inline [System: ...] instruction that overrides system.md. Only
the 23 cases tagged path="agent" can move when the prompt moves.

Run-to-run judge noise on this suite is real — two runs of the same code on
2026-08-13 flipped 6 of 36 verdicts. So a single run per arm proves nothing.
This script requires repeats, measures the noise band from those repeats, and
only calls a delta real when it clears that band.

Usage
  # 1. collect repeats for each arm (rebuild/restart backend between arms)
  python3 scripts/ab_compare.py --collect --label baseline  --repeats 3
  python3 scripts/ab_compare.py --collect --label trimmed   --repeats 3

  # 2. compare
  python3 scripts/ab_compare.py --baseline baseline --candidate trimmed
"""

import argparse
import glob
import json
import statistics
import subprocess
import sys
from collections import defaultdict
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
RESULTS_DIR = REPO_ROOT / "evals" / "results"
SCORED_PATH = "agent"  # only these cases can respond to a prompt change


def collect(label: str, repeats: int, base_url: str, judge_model: str) -> None:
    """Run the eval + judge `repeats` times, tagging every run with `label`."""
    for i in range(1, repeats + 1):
        print(f"\n=== {label}: repeat {i}/{repeats} ===", file=sys.stderr)
        # eval_runner exits 1 when any case fails, which is normal here.
        subprocess.run(
            [sys.executable, "scripts/eval_runner.py",
             "--base-url", base_url, "--label", label],
            cwd=REPO_ROOT, check=False,
        )
        runs = sorted(glob.glob(str(RESULTS_DIR / f"*_{label}.json")))
        if not runs:
            print(f"ERROR: no run file produced for {label}", file=sys.stderr)
            sys.exit(1)
        subprocess.run(
            [sys.executable, "scripts/judge.py",
             "--run", runs[-1], "--model", judge_model],
            cwd=REPO_ROOT, check=False,
        )


def load_arm(label: str) -> list[dict]:
    files = sorted(glob.glob(str(RESULTS_DIR / f"*_{label}_judged.json")))
    if not files:
        sys.exit(f"ERROR: no judged runs found for arm '{label}' "
                 f"(expected evals/results/*_{label}_judged.json)")
    return [json.load(open(f)) for f in files]


def arm_fingerprint(runs: list[dict], label: str) -> dict:
    """Every repeat in an arm must have served the same prompt and the same code."""
    prompts = {json.dumps(r.get("system_prompt"), sort_keys=True) for r in runs}
    shas = {r.get("git_sha") for r in runs}
    if len(prompts) > 1:
        sys.exit(f"ERROR: arm '{label}' mixes {len(prompts)} different system prompts. "
                 "Each arm must be a single prompt version.")
    if "unknown" in shas:
        print(f"WARNING: arm '{label}' has runs with git_sha=unknown — "
              "mount .git into the container so runs are attributable.", file=sys.stderr)
    return runs[0].get("system_prompt") or {}


def pass_rate(run: dict, path_filter: str | None) -> tuple[int, int]:
    """(passes, scored) for one run, optionally restricted to one code path."""
    passes = scored = 0
    for r in run["results"]:
        if path_filter and r.get("path", "agent") != path_filter:
            continue
        verdict = (r.get("judge") or {}).get("verdict")
        if verdict is None:
            continue
        scored += 1
        passes += verdict == "pass"
    return passes, scored


def noise_band(runs: list[dict], path_filter: str | None) -> tuple[float, dict]:
    """Spread of the pass count across repeats of the SAME arm.

    This is the floor for what counts as a real difference: anything smaller
    than the arm's own run-to-run swing is indistinguishable from noise.
    """
    counts = [pass_rate(r, path_filter)[0] for r in runs]
    spread = (max(counts) - min(counts)) if len(counts) > 1 else float("nan")

    flips = defaultdict(set)
    for run in runs:
        for r in run["results"]:
            if path_filter and r.get("path", "agent") != path_filter:
                continue
            v = (r.get("judge") or {}).get("verdict")
            if v:
                flips[r["id"]].add(v)
    unstable = sorted(i for i, vs in flips.items() if len(vs) > 1)
    return spread, {"counts": counts, "unstable_cases": unstable}


def dim_means(runs: list[dict], path_filter: str | None) -> dict:
    dims = ["correctness", "groundedness", "tool_use", "completeness", "style"]
    out = {}
    for d in dims:
        vals = [j[d] for run in runs for r in run["results"]
                if (not path_filter or r.get("path", "agent") == path_filter)
                and (j := (r.get("judge") or {})) and d in j]
        out[d] = statistics.mean(vals) if vals else 0.0
    return out


def report(base_label: str, cand_label: str) -> int:
    base_runs, cand_runs = load_arm(base_label), load_arm(cand_label)
    base_fp = arm_fingerprint(base_runs, base_label)
    cand_fp = arm_fingerprint(cand_runs, cand_label)

    print(f"\n{'='*72}\nPROMPT A/B — {base_label} vs {cand_label}\n{'='*72}")
    print(f"{base_label:<12} prompt {base_fp.get('sha256')} "
          f"{base_fp.get('chars')} chars (~{base_fp.get('approx_tokens')} tok) "
          f"x{len(base_runs)} runs")
    print(f"{cand_label:<12} prompt {cand_fp.get('sha256')} "
          f"{cand_fp.get('chars')} chars (~{cand_fp.get('approx_tokens')} tok) "
          f"x{len(cand_runs)} runs")

    if base_fp.get("sha256") == cand_fp.get("sha256"):
        print("\n❌ ABORT: both arms served the SAME prompt. The backend never picked "
              "up the edit — rebuild/restart it between arms:\n"
              "     docker compose up -d --force-recreate backend")
        return 2

    for r in (base_runs, cand_runs):
        if len(r) < 2:
            print("\n⚠️  At least 2 repeats per arm are required to estimate noise. "
                  "Re-run with --collect --repeats 3.")
            return 2

    tok_delta = (base_fp.get("approx_tokens", 0) or 0) - (cand_fp.get("approx_tokens", 0) or 0)

    verdict_code = 0
    for path_filter, title in ((SCORED_PATH, "SCORED SUBSET (path=agent — the gate)"),
                               (None, "ALL CASES (context only — diluted by card paths)")):
        b_counts = [pass_rate(r, path_filter) for r in base_runs]
        c_counts = [pass_rate(r, path_filter) for r in cand_runs]
        n = b_counts[0][1]
        b_mean = statistics.mean(p for p, _ in b_counts)
        c_mean = statistics.mean(p for p, _ in c_counts)
        b_band, b_info = noise_band(base_runs, path_filter)
        c_band, c_info = noise_band(cand_runs, path_filter)
        band = max(b_band, c_band)
        delta = c_mean - b_mean

        print(f"\n--- {title} ---")
        print(f"  {base_label:<12} {b_mean:.1f}/{n} ({b_mean/n:.0%})  runs={[p for p,_ in b_counts]}")
        print(f"  {cand_label:<12} {c_mean:.1f}/{n} ({c_mean/n:.0%})  runs={[p for p,_ in c_counts]}")
        print(f"  delta        {delta:+.1f} cases   noise band ±{band:.0f} "
              f"(largest within-arm swing)")
        print(f"  unstable     {len(set(b_info['unstable_cases']) | set(c_info['unstable_cases']))} "
              f"cases flipped verdict across repeats")

        bd, cd = dim_means(base_runs, path_filter), dim_means(cand_runs, path_filter)
        print("  " + "  ".join(f"{d[:5]} {cd[d]-bd[d]:+.2f}" for d in bd))

        if path_filter == SCORED_PATH:
            gate = (delta, band)

    # Verdict last, so it is the final thing on screen.
    delta, band = gate
    print(f"\n{'='*72}\nGATE  (decided on the {SCORED_PATH}-path cases only)\n{'='*72}")
    print(f"  token saving: {tok_delta:+d} tokens/request")
    if delta < -band:
        print(f"  ❌ REJECT — regression of {abs(delta):.1f} cases exceeds the "
              f"±{band:.0f} noise band.")
        verdict_code = 1
    elif delta > band:
        print(f"  ✅ SHIP — improvement of {delta:+.1f} cases clears the "
              f"±{band:.0f} noise band, and saves {tok_delta} tokens.")
    elif tok_delta > 0:
        print(f"  ✅ SHIP on tokens — quality is flat within noise "
              f"(delta {delta:+.1f}, band ±{band:.0f}); take the "
              f"{tok_delta}-token saving.")
    else:
        print("  ⚠️  NO SIGNAL — quality flat and no token saving. Nothing to ship.")
        verdict_code = 1
    print()
    return verdict_code


def main():
    ap = argparse.ArgumentParser(description="A/B gate for system-prompt changes")
    ap.add_argument("--collect", action="store_true",
                    help="Run eval+judge N times for one arm instead of comparing")
    ap.add_argument("--label", help="Arm name (with --collect)")
    ap.add_argument("--repeats", type=int, default=3)
    ap.add_argument("--base-url", default="http://localhost:8000")
    ap.add_argument("--judge-model", default="gpt-4o")
    ap.add_argument("--baseline", help="Baseline arm label")
    ap.add_argument("--candidate", help="Candidate arm label")
    args = ap.parse_args()

    if args.collect:
        if not args.label:
            sys.exit("ERROR: --collect requires --label")
        collect(args.label, args.repeats, args.base_url, args.judge_model)
        return
    if not (args.baseline and args.candidate):
        sys.exit("ERROR: need --baseline and --candidate (or --collect --label)")
    sys.exit(report(args.baseline, args.candidate))


if __name__ == "__main__":
    main()
