# Demo Files for Nautilus 293G Project

This directory contains demo scripts for presenting the Nautilus fuzzer implementation.

## Demo Scripts

### 1. demo_1_generation.py
**Topic**: Grammar-based Tree Generation
**Shows**: How Nautilus generates syntactically correct Lua code from grammar rules
**Key concepts**:
- Context-free grammar (CFG) loading from JSON
- Recursive tree generation with depth limits
- Tree unparse to Lua source code
**Run**: `python demo_1_generation.py`

### 2. demo_2_mutations.py
**Topic**: Tree Mutation Operators
**Shows**: Three mutation operators (random, splicing, recursive)
**Key concepts**:
- Random mutation: replace subtree with same-type new subtree
- Splicing mutation: swap subtree with one from corpus
- Recursive mutation: amplify nesting depth by 2^n
**Run**: `python demo_2_mutations.py`

### 3. demo_3_minimization.py
**Topic**: Subtree Minimization
**Shows**: How minimization shrinks test cases while preserving coverage
**Key concepts**:
- Pre-computing minimal subtrees for each non-terminal
- Testing replacements while preserving required coverage
- Benefits: smaller inputs, faster execution, easier debugging
**Run**: `python demo_3_minimization.py`

## Generated Results

### Demo Files (auto-generated on run)

#### Demo 1: Generation
- `results/demo_1_generations.json` - JSON of 3 generated examples
- `results/demo_1_example_*.lua` - Individual Lua source files

#### Demo 2: Mutations
- `results/demo_2_mutations.json` - JSON of mutation examples
- `results/demo_2_original.lua` - Original tree
- `results/demo_2_random.lua` - After random mutation
- `results/demo_2_splicing.lua` - After splicing mutation
- `results/demo_2_recursive.lua` - After recursive mutation

#### Demo 3: Minimization
- `results/demo_3_minimization.json` - Minimization results
- `results/demo_3_original.lua` - Original input
- `results/demo_3_minimized.lua` - Minimized input

### Plots
- `plots/coverage_time.png` - Coverage vs Time curves for all 4 experiment groups
- `plots/final_coverage_bar.png` - Final coverage comparison with error bars

### Results
- `results/random_grammar/run_0.json` - Random grammar baseline results
- `results/afl_like/run_0.json` - AFL-like byte mutation results
- `results/nautilus_no_feedback/run_0.json` - Nautilus without feedback results
- `results/nautilus_full/run_0.json` - Full Nautilus results
- `results/summary_branch_coverage.md` - Markdown summary table

## Running a Full Experiment

```bash
# Quick test (2 seconds per group, 1 seed)
python run_experiments.py --seconds 2 --seeds 1 --initial-seeds 20

# Generate plots
python plot_results.py

# Generate summary table
python summarize_results.py
```

## Presentation Order

1. **Introduction** (3 min)
   - Problem: Traditional fuzzers struggle with structured inputs
   - Solution: Grammar-based + coverage-guided approach

2. **Demo 1: Generation** (2 min)
   - Show 3 generated Lua programs
   - Explain syntax correctness

3. **Demo 2: Mutations** (2 min)
   - Show splicing recombining inputs
   - Show recursive mutation increasing depth

4. **Demo 3: Minimization** (2 min)
   - Show size reduction while preserving coverage

5. **Results** (3 min)
   - Show coverage-time curves
   - Explain why Nautilus Full performs best

6. **Implementation Comparison** (2 min)
   - See IMPLEMENTATION_COMPARISON.md
   - Clarify: re-implementation of paper ideas, not code port
