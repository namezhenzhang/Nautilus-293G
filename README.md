# Nautilus 293G Course Project

This project re-implements core Nautilus ideas:

- Grammar-based tree generation
- Tree-aware mutations (random, splicing, random-recursive)
- Coverage-guided scheduling
- Lightweight subtree minimization
- Baselines and plotting scripts

## 0) Implementation Logic

This section explains how the system is implemented end-to-end.

### Overall data flow

1. Load Lua grammar from `grammar/lua_grammar.json`.
2. Generate AST-like trees using non-terminal expansions.
3. Unparse trees into Lua source strings.
4. Execute inputs on coverage-instrumented Lua (`--coverage` build).
5. Collect coverage from `gcov`, compare with known global coverage.
6. If new coverage is found, keep the input in queue and mutate further.
7. Record coverage-over-time and final coverage for each experiment group.

### Core modules and responsibilities

- `grammar_engine.py`
  - Loads grammar JSON (`start`, `rules`).
  - Computes `min_depth` for each non-terminal.
  - Implements naive generation with `max_depth` guard.
  - Near depth limit, selects shortest/lowest-depth expansions to avoid runaway recursion.

- `tree.py`
  - Defines `Node` and `Tree`.
  - Supports deep cloning, DFS walk, subtree replacement, unparse.
  - Provides `nodes_by_nonterminal()` for mutation indexing.
  - Detects recursive non-terminal regions used by recursive mutation.

- `target_lua.py`
  - Implements `LuaTarget.run(input_str)`.
  - Clears previous `.gcda`, runs Lua input with timeout.
  - Runs `gcov`, parses covered lines into a coverage set.
  - Computes `new_coverage` and `is_new` against global known coverage.
  - Uses a quick hash path on `.gcda` metadata to skip redundant parsing.

- `mutations.py`
  - `random_mutation`: replace one non-terminal subtree with newly generated subtree of same type.
  - `splicing_mutation`: replace with subtree sampled from corpus index of same non-terminal.
  - `random_recursive_mutation`: pick recursive structure and amplify nesting depth.
  - Maintains global non-terminal index: `nonterminal -> [(tree_id, path, subtree)]`.

- `minimizer.py`
  - Implements subtree minimization.
  - Tries replacing nodes with minimal candidates while preserving required coverage bits.
  - Keeps reduced tree if coverage condition remains satisfied.

- `scheduler.py`
  - Implements the queue-based fuzzing loop.
  - Seed generation -> execute -> enqueue feedback-worthy inputs -> mutate -> repeat.
  - Per-second coverage timeline recording.
  - Supports group-specific behavior switches via `SchedulerConfig`.

- `run_experiments.py`
  - Orchestrates all groups and seeds.
  - Auto-downloads/builds Lua 5.4.7 with coverage flags if not present.
  - Writes `results/{group}/run_{seed}.json`.

- `plot_results.py`
  - Reads all run JSON files.
  - Plots coverage-time curves with std shading.
  - Plots final coverage bar chart with error bars.

## 1) Environment

```bash
conda create -n nautilus-293g python=3.10 -y
conda activate nautilus-293g
pip install matplotlib
```

## 2) Run Experiments

Default command runs all 4 groups, 5 seeds each, 10 minutes each:

```bash
python run_experiments.py
```

Useful overrides:

```bash
python run_experiments.py --seconds 60 --seeds 1
python run_experiments.py --group nautilus_full --seconds 120 --seeds 2
python run_experiments.py --group nautilus_full --full-minimize-mode off --seconds 120 --seeds 2
python run_experiments.py --seconds 300 --seeds 1 --initial-seeds 50 --coverage-sample-interval 1 --clean-results

```

The script automatically downloads and builds Lua 5.4.7 with coverage flags under `build/`.

## 3) Plot Results

```bash
python plot_results.py
```

Outputs:

- `plots/coverage_time.png`
- `plots/final_coverage_bar.png`

## 4) Summarize Results (Report Table)

Generate a markdown summary table with:

- final branch coverage % (mean/std)
- delta vs random baseline (percentage points)
- final line coverage and total inputs

```bash
python summarize_results.py
```

Default output:

- `results/summary_branch_coverage.md`

## 5) Result Format

Each run writes:

`results/{group_name}/run_{seed}.json`

```json
{
  "coverage_over_time": [[0, 5], [1, 8], [2, 12]],
  "final_coverage": 420,
  "total_inputs": 5000
}
```

## 6) Groups

- `random_grammar`
- `afl_like`
- `nautilus_no_feedback`
- `nautilus_full`

### Group switch logic

- `random_grammar`: grammar generation only, no feedback queue selection, no tree mutation.
- `afl_like`: byte-level mutation style with coverage feedback.
- `nautilus_no_feedback`: tree mutations enabled, but no coverage-guided selection.
- `nautilus_full`: tree mutations + coverage feedback (full Nautilus-style mode).

### Nautilus full minimization modes

- `--full-minimize-mode sparse` (default): only minimize periodically to balance throughput and quality.
- `--full-minimize-mode full`: minimize every new-coverage input (closest to heavy version).
- `--full-minimize-mode off`: disable minimization for ablation and speed comparison.

## 7) Reproducibility Notes

- Recommended quick smoke test:

```bash
python run_experiments.py --seconds 2 --seeds 1 --initial-seeds 20
python plot_results.py
```

- Full run (course evaluation setting):

```bash
python run_experiments.py --seconds 600 --seeds 5 --initial-seeds 200
python plot_results.py
```
