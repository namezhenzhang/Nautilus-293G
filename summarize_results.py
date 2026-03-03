from __future__ import annotations

import argparse
import json
from pathlib import Path
from statistics import mean, stdev

GROUPS = ["random_grammar", "afl_like", "nautilus_no_feedback", "nautilus_full"]


def load_runs(results_dir: Path, group: str) -> list[dict]:
    runs = []
    for path in sorted((results_dir / group).glob("run_*.json")):
        with open(path, "r", encoding="utf-8") as f:
            runs.append(json.load(f))
    return runs


def fmt(v: float) -> str:
    return f"{v:.3f}"


def summarize(results_dir: Path) -> str:
    metrics: dict[str, dict[str, float]] = {}

    for group in GROUPS:
        runs = load_runs(results_dir, group)
        if not runs:
            continue
        branch = [float(r.get("final_branch_coverage_pct", 0.0)) for r in runs]
        line_cov = [float(r.get("final_coverage", 0.0)) for r in runs]
        inputs = [float(r.get("total_inputs", 0.0)) for r in runs]
        metrics[group] = {
            "n": float(len(runs)),
            "branch_mean": mean(branch),
            "branch_std": stdev(branch) if len(branch) > 1 else 0.0,
            "line_mean": mean(line_cov),
            "line_std": stdev(line_cov) if len(line_cov) > 1 else 0.0,
            "inputs_mean": mean(inputs),
            "inputs_std": stdev(inputs) if len(inputs) > 1 else 0.0,
        }

    baseline = metrics.get("random_grammar", {}).get("branch_mean", 0.0)
    lines = []
    lines.append("# Result Summary (Branch Coverage Primary)")
    lines.append("")
    lines.append("| Group | Runs | Final Branch Coverage % (mean ± std) | Delta vs Random (pp) | Final Line Coverage (mean ± std) | Total Inputs (mean ± std) |")
    lines.append("|---|---:|---:|---:|---:|---:|")
    for group in GROUPS:
        if group not in metrics:
            continue
        m = metrics[group]
        delta = m["branch_mean"] - baseline
        lines.append(
            "| "
            + f"{group} | {int(m['n'])} | {fmt(m['branch_mean'])} ± {fmt(m['branch_std'])}"
            + f" | {fmt(delta)} | {fmt(m['line_mean'])} ± {fmt(m['line_std'])}"
            + f" | {fmt(m['inputs_mean'])} ± {fmt(m['inputs_std'])} |"
        )

    lines.append("")
    lines.append("Notes:")
    lines.append("- Primary metric follows Nautilus paper style: branch coverage percentage.")
    lines.append("- Delta is in percentage points (pp) against `random_grammar`.")
    return "\n".join(lines) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--results", type=str, default="results")
    parser.add_argument("--out", type=str, default="results/summary_branch_coverage.md")
    args = parser.parse_args()

    root = Path(__file__).resolve().parent
    results_dir = root / args.results
    out_path = root / args.out
    out_path.parent.mkdir(parents=True, exist_ok=True)

    content = summarize(results_dir)
    out_path.write_text(content, encoding="utf-8")
    print(content, end="")
    print(f"\n[written] {out_path}")


if __name__ == "__main__":
    main()
