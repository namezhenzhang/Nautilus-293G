from __future__ import annotations

import argparse
import json
import os
import random
import subprocess
from pathlib import Path
from typing import Optional

from grammar_engine import Grammar, NaiveGenerator
from minimizer import SubtreeMinimizer
from mutations import MutationEngine
from scheduler import NautilusScheduler, apply_full_minimize_mode, config_for_group
from target_lua import LuaTarget

GROUPS = ["random_grammar", "afl_like", "nautilus_no_feedback", "nautilus_full"]


def ensure_lua_build(build_root: Path) -> tuple[str, str]:
    lua_dir = build_root / "lua-5.4.7"
    lua_bin = lua_dir / "src" / "lua"
    if lua_bin.exists():
        return str(lua_bin), str(lua_dir)

    build_root.mkdir(parents=True, exist_ok=True)
    tarball = build_root / "lua-5.4.7.tar.gz"

    if not tarball.exists():
        subprocess.run(
            ["curl", "-R", "-L", "-o", str(tarball), "https://www.lua.org/ftp/lua-5.4.7.tar.gz"],
            check=True,
        )
    subprocess.run(["tar", "zxf", str(tarball), "-C", str(build_root)], check=True)
    subprocess.run(
        ["make", 'MYCFLAGS=--coverage -O0 -g', "MYLDFLAGS=--coverage", "macosx"],
        cwd=str(lua_dir),
        check=True,
    )
    return str(lua_bin), str(lua_dir)


def run_one(
    group: str,
    seed: int,
    seconds: int,
    initial_seeds: int,
    grammar_path: Path,
    lua_bin: str,
    build_dir: str,
    out_dir: Path,
    coverage_sample_interval: int,
    gcov_timeout_sec: Optional[float],
    full_minimize_mode: str,
) -> None:
    rng = random.Random(seed)
    grammar = Grammar.from_file(str(grammar_path))
    generator = NaiveGenerator(grammar=grammar, max_depth=10, rng=rng)
    target = LuaTarget(
        lua_bin=lua_bin,
        build_dir=build_dir,
        timeout_sec=2.0,
        coverage_sample_interval=coverage_sample_interval,
        gcov_timeout_sec=gcov_timeout_sec,
    )
    mutator = MutationEngine(generator=generator, rng=rng)
    minimizer = SubtreeMinimizer(generator=generator, max_attempts=8)
    cfg = config_for_group(group)
    if group == "nautilus_full":
        cfg = apply_full_minimize_mode(cfg, full_minimize_mode)
    cfg.budget_seconds = seconds
    cfg.initial_seeds = initial_seeds
    scheduler = NautilusScheduler(generator, target, mutator, minimizer, cfg, rng=rng)
    stats = scheduler.run()

    out_group = out_dir / group
    out_group.mkdir(parents=True, exist_ok=True)
    out_file = out_group / f"run_{seed}.json"
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(
            {
                "coverage_over_time": stats.coverage_over_time,
                "branch_coverage_over_time": stats.branch_coverage_over_time,
                "final_coverage": stats.final_coverage,
                "final_branch_coverage_pct": stats.final_branch_coverage_pct,
                "total_inputs": stats.total_inputs,
            },
            f,
            indent=2,
        )
    print(f"[done] {group} seed={seed} -> {out_file}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--seconds", type=int, default=600)
    parser.add_argument("--seeds", type=int, default=5)
    parser.add_argument("--grammar", type=str, default="grammar/lua_grammar.json")
    parser.add_argument("--results", type=str, default="results")
    parser.add_argument("--build-root", type=str, default="build")
    parser.add_argument("--group", type=str, default="all", choices=["all"] + GROUPS)
    parser.add_argument("--initial-seeds", type=int, default=200)
    parser.add_argument("--coverage-sample-interval", type=int, default=5)
    parser.add_argument("--gcov-timeout-sec", type=float, default=-1.0)
    parser.add_argument("--full-minimize-mode", choices=["off", "sparse", "full"], default="sparse")
    parser.add_argument("--clean-results", action="store_true")
    args = parser.parse_args()

    root = Path(__file__).resolve().parent
    grammar_path = root / args.grammar
    results_dir = root / args.results
    build_root = root / args.build_root

    lua_bin, build_dir = ensure_lua_build(build_root)

    groups = GROUPS if args.group == "all" else [args.group]
    gcov_timeout_sec = None if args.gcov_timeout_sec <= 0 else args.gcov_timeout_sec
    if args.clean_results:
        for group in groups:
            group_dir = results_dir / group
            if not group_dir.exists():
                continue
            for old in group_dir.glob("run_*.json"):
                old.unlink(missing_ok=True)
    print(
        f"[config] groups={groups} seeds={args.seeds} seconds={args.seconds} "
        f"initial_seeds={args.initial_seeds} coverage_sample_interval={args.coverage_sample_interval} "
        f"gcov_timeout_sec={gcov_timeout_sec} full_minimize_mode={args.full_minimize_mode} "
        f"clean_results={args.clean_results}"
    )
    for group in groups:
        for seed in range(args.seeds):
            print(f"[start] group={group} seed={seed} seconds={args.seconds} initial_seeds={args.initial_seeds}")
            run_one(
                group=group,
                seed=seed,
                seconds=args.seconds,
                initial_seeds=args.initial_seeds,
                grammar_path=grammar_path,
                lua_bin=lua_bin,
                build_dir=build_dir,
                out_dir=results_dir,
                coverage_sample_interval=args.coverage_sample_interval,
                gcov_timeout_sec=gcov_timeout_sec,
                full_minimize_mode=args.full_minimize_mode,
            )


if __name__ == "__main__":
    main()
