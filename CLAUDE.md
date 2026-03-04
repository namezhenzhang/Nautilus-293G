# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

A Nautilus-style grammar-aware coverage-guided fuzzer for Lua 5.4.7. Implements and compares four fuzzing strategies using tree-structured grammar generation, tree mutations, and gcov-based branch coverage feedback.

## Environment Setup

```bash
conda create -n nautilus-293g python=3.10 -y
conda activate nautilus-293g
pip install matplotlib
```

## Common Commands

```bash
# Run all 4 experiment groups (5 seeds, 10 min each) — downloads/builds Lua automatically
python run_experiments.py

# Quick smoke test (2 sec per group, 1 seed, 20 initial seeds)
python run_experiments.py --seconds 2 --seeds 1 --initial-seeds 20

# Run a single group
python run_experiments.py --group nautilus_full --seconds 120 --seeds 2

# Generate coverage-time plots from results/
python plot_results.py

# Generate markdown summary table
python summarize_results.py
```

Key flags for `run_experiments.py`:
- `--seconds`: Budget per run (default: 600)
- `--seeds`: Random seeds to run (default: 5)
- `--group`: One of `random_grammar`, `afl_like`, `nautilus_no_feedback`, `nautilus_full`, or `all`
- `--initial-seeds`: Initial population size (default: 200)
- `--coverage-sample-interval`: Gcov parse frequency, higher = faster (default: 5)
- `--clean-results`: Clear old results before running

## Architecture

The pipeline has three layers:

**1. Generation layer** (`grammar_engine.py`, `tree.py`): `Grammar` loads `grammar/lua_grammar.json` and computes min-expansion depths. `NaiveGenerator` builds random `Tree` objects (composed of `Node`s) up to a max depth, then calls `tree.unparse()` to emit Lua source.

**2. Mutation layer** (`mutations.py`, `minimizer.py`): Three tree-aware operators — random subtree replacement, corpus splicing (cross-tree non-terminal swap), and recursive depth amplification. `SubtreeMinimizer` shrinks interesting inputs while preserving their coverage bits.

**3. Execution/feedback layer** (`target_lua.py`): `LuaTarget` runs the Lua binary (2s timeout), invokes `gcov`, and returns a `RunResult` with the set of newly-covered branches. Coverage is sampled every N runs (configurable) to reduce gcov overhead; `.gcda` hash checking skips redundant parses.

**Orchestration** (`scheduler.py`): `NautilusScheduler` holds a queue seeded with initial random inputs that trigger new coverage. Each queue entry is optionally minimized, then mutated repeatedly; mutations triggering new coverage are enqueued. `SchedulerConfig` flags toggle feedback, tree mutations, byte mutations, and minimization to produce the four experimental groups.

**Experiment groups**:
| Group | Grammar gen | Tree mutations | Coverage feedback |
|-------|-------------|---------------|-------------------|
| `random_grammar` | ✓ | ✗ | ✗ |
| `afl_like` | ✗ | ✗ | ✓ (byte mutations) |
| `nautilus_no_feedback` | ✓ | ✓ | ✗ |
| `nautilus_full` | ✓ | ✓ | ✓ |

**Results format** (`results/{group}/run_{seed}.json`):
```json
{"coverage_over_time": [[second, lines], ...], "branch_coverage_over_time": [[second, pct], ...],
 "final_coverage": 420, "final_branch_coverage_pct": 42.3, "total_inputs": 5000}
```

## Key Files

- `grammar/lua_grammar.json` — ~150 Lua production rules; edit here to expand language coverage
- `scheduler.py:SchedulerConfig` — central knob for enabling/disabling fuzzer features
- `target_lua.py:LuaTarget` — all gcov interaction; adjust `coverage_sample_interval` for speed vs. accuracy tradeoff
- `mutations.py` — three mutation operators + corpus `nt_index` for splicing
- `build/` — generated directory containing Lua 5.4.7 source and `--coverage`-instrumented binary
