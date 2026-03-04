#!/usr/bin/env python3
"""
Quick verification script for presentation.

This script assumes full experiment results are already pulled from Git and:
1) verifies required result files exist
2) regenerates summary markdown
3) regenerates plots
4) runs demo scripts for live presentation artifacts
"""

import os
import subprocess
import sys


RESULT_GROUPS = [
    "random_grammar",
    "afl_like",
    "nautilus_no_feedback",
    "nautilus_full",
]

def run_cmd(cmd):
    print(f"\n{'='*60}")
    print(f"Running: {cmd}")
    print('='*60)
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    print(result.stdout)
    if result.stderr:
        print("STDERR:", result.stderr)
    return result.returncode == 0


def check_results():
    ok = True
    print("\n[2/6] Checking pulled experiment results (5 seeds each)...")
    for group in RESULT_GROUPS:
        for seed in range(5):
            path = f"results/{group}/run_{seed}.json"
            if os.path.exists(path):
                print(f"  ✓ {path}")
            else:
                print(f"  ✗ {path} (MISSING)")
                ok = False
    return ok

def main():
    print("="*60)
    print("NAUTILUS PRESENTATION VERIFICATION")
    print("="*60)

    # Check files exist
    files = [
        "grammar/lua_grammar.json",
        "grammar_engine.py",
        "tree.py",
        "mutations.py",
        "minimizer.py",
        "target_lua.py",
        "scheduler.py",
        "run_experiments.py",
        "plot_results.py",
        "summarize_results.py",
        "demo_1_generation.py",
        "demo_2_mutations.py",
        "demo_3_minimization.py",
        "CLAUDE.md",
        "README.md",
        "IMPLEMENTATION_COMPARISON.md",
    ]

    print("\n[1/6] Checking required source files...")
    all_exist = True
    for f in files:
        if os.path.exists(f):
            print(f"  ✓ {f}")
        else:
            print(f"  ✗ {f} (MISSING)")
            all_exist = False

    if not all_exist:
        print("ERROR: Some files are missing!")
        return 1

    if not check_results():
        print("\nERROR: Missing pulled results. Run `git pull` first.")
        return 1

    print("\n[3/6] Regenerating summary table from pulled results...")
    if not run_cmd("python summarize_results.py"):
        return 1

    print("\n[4/6] Regenerating plots from pulled results...")
    if not run_cmd("python plot_results.py"):
        return 1

    print("\n[5/6] Running demo 1 (generation)...")
    run_cmd("python demo_1_generation.py")

    print("\n[6/6] Running demo 2 and demo 3...")
    run_cmd("python demo_2_mutations.py")
    run_cmd("python demo_3_minimization.py")

    print("\n" + "="*60)
    print("VERIFICATION COMPLETE")
    print("="*60)
    print("\nGenerated files:")
    print("  results/*/run_*.json (pulled full experiment results)")
    print("  results/summary_branch_coverage.md")
    print("  plots/coverage_time.png")
    print("  plots/final_coverage_bar.png")
    print("  results/demo_*.json")
    print("  results/demo_*.lua")

    return 0

if __name__ == "__main__":
    sys.exit(main())
