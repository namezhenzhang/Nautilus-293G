from __future__ import annotations

import json
from pathlib import Path
from statistics import mean, stdev
from typing import Dict, List

import matplotlib.pyplot as plt

GROUPS = ["random_grammar", "afl_like", "nautilus_no_feedback", "nautilus_full"]


def load_group_runs(results_dir: Path, group: str) -> List[dict]:
    runs = []
    for path in sorted((results_dir / group).glob("run_*.json")):
        with open(path, "r", encoding="utf-8") as f:
            runs.append(json.load(f))
    return runs


def plot_coverage_time(results_dir: Path, out_dir: Path) -> None:
    plt.figure(figsize=(10, 6))
    for group in GROUPS:
        runs = load_group_runs(results_dir, group)
        if not runs:
            continue
        max_t = 0
        for r in runs:
            if r.get("branch_coverage_over_time"):
                max_t = max(max_t, int(r["branch_coverage_over_time"][-1][0]))
            elif r.get("coverage_over_time"):
                max_t = max(max_t, int(r["coverage_over_time"][-1][0]))
        if max_t <= 0:
            max_t = 1

        series = [
            _aligned_second_series(
                r.get("branch_coverage_over_time", r.get("coverage_over_time", [])),
                max_t,
            )
            for r in runs
        ]
        avg = [mean(vals) for vals in zip(*series)]
        err = [stdev(vals) if len(vals) > 1 else 0.0 for vals in zip(*series)]
        xs = list(range(max_t + 1))
        lower = [a - e for a, e in zip(avg, err)]
        upper = [a + e for a, e in zip(avg, err)]
        plt.plot(xs, avg, label=group)
        plt.fill_between(xs, lower, upper, alpha=0.2)

    plt.xlabel("Time (s)")
    plt.ylabel("Branch coverage (%)")
    plt.title("Branch coverage over time")
    plt.legend()
    plt.tight_layout()
    out_dir.mkdir(parents=True, exist_ok=True)
    plt.savefig(out_dir / "coverage_time.png", dpi=200)
    plt.close()


def _aligned_second_series(coverage_over_time: List[List[int]], max_t: int) -> List[float]:
    """
    Convert sparse/irregular time samples [[t, cov], ...] into per-second
    step-function samples on [0, max_t].
    """
    if not coverage_over_time:
        return [0.0] * (max_t + 1)

    points = sorted((int(t), float(cov)) for t, cov in coverage_over_time)
    series: List[float] = []
    idx = 0
    cur = points[0][1] if points[0][0] == 0 else 0.0
    for sec in range(max_t + 1):
        while idx < len(points) and points[idx][0] <= sec:
            cur = points[idx][1]
            idx += 1
        series.append(cur)
    return series


def plot_final_bar(results_dir: Path, out_dir: Path) -> None:
    vals: Dict[str, List[float]] = {}
    for group in GROUPS:
        runs = load_group_runs(results_dir, group)
        vals[group] = [r.get("final_branch_coverage_pct", float(r.get("final_coverage", 0))) for r in runs]

    x = list(range(len(GROUPS)))
    y = [mean(vals[g]) if vals[g] else 0.0 for g in GROUPS]
    e = [stdev(vals[g]) if len(vals[g]) > 1 else 0.0 for g in GROUPS]

    plt.figure(figsize=(10, 6))
    plt.bar(x, y, yerr=e, capsize=5)
    plt.xticks(x, GROUPS, rotation=20)
    plt.ylabel("Final branch coverage (%)")
    plt.title("Final branch coverage comparison")
    plt.tight_layout()
    out_dir.mkdir(parents=True, exist_ok=True)
    plt.savefig(out_dir / "final_coverage_bar.png", dpi=200)
    plt.close()


def main() -> None:
    root = Path(__file__).resolve().parent
    results_dir = root / "results"
    out_dir = root / "plots"
    plot_coverage_time(results_dir, out_dir)
    plot_final_bar(results_dir, out_dir)
    print(f"plots written to {out_dir}")


if __name__ == "__main__":
    main()
