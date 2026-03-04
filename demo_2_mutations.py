#!/usr/bin/env python3
"""
Demo 2: Tree Mutations
Shows the three tree-aware mutation operators.
"""

from grammar_engine import Grammar, NaiveGenerator
from mutations import MutationEngine
import json
import os

def print_tree_info(tree, label):
    code = tree.unparse()
    print(f"\n{label}:")
    print("-" * 50)
    print(f"Length: {len(code)} chars")
    print(f"Code: {code[:100]}{'...' if len(code) > 100 else ''}")

def main():
    print("=" * 70)
    print("DEMO 2: Tree Mutations")
    print("=" * 70)
    print()
    print("Three mutation operators:")
    print("  1. Random Mutation: Replace subtree with same-type new subtree")
    print("  2. Splicing Mutation: Swap subtree with one from corpus")
    print("  3. Recursive Mutation: Amplify nesting depth by 2^n")
    print()

    # Setup
    grammar = Grammar.from_file("grammar/lua_grammar.json")
    gen = NaiveGenerator(grammar, max_depth=5)
    mutator = MutationEngine(gen)

    # Generate base tree and register it
    print("Generating base tree...")
    base_tree = gen.generate_tree()
    mutator.register_tree(base_tree)
    print_tree_info(base_tree, "Original Tree")

    # 1. Random Mutation
    print("\n\n--- 1. Random Mutation ---")
    random_mut = mutator.random_mutation(base_tree)
    print_tree_info(random_mut, "After Random Mutation")

    # 2. Splicing Mutation
    print("\n\n--- 2. Splicing Mutation ---")
    # Register another tree for splicing pool
    donor_tree = gen.generate_tree()
    mutator.register_tree(donor_tree)
    splice_mut = mutator.splicing_mutation(base_tree)
    print_tree_info(splice_mut, "After Splicing Mutation")

    # 3. Recursive Mutation
    print("\n\n--- 3. Recursive Mutation ---")
    recursive_mut = mutator.random_recursive_mutation(base_tree)
    print_tree_info(recursive_mut, "After Recursive Mutation")

    # Compare recursive depth
    print(f"\nRecursive depth comparison:")
    print(f"  Original recursive paths: {len(base_tree.recursive_paths())}")
    print(f"  Mutated recursive paths: {len(recursive_mut.recursive_paths())}")

    # Save mutations to file
    os.makedirs("results", exist_ok=True)
    mutations = {
        "original": base_tree.unparse(),
        "random_mutation": random_mut.unparse(),
        "splicing_mutation": splice_mut.unparse(),
        "recursive_mutation": recursive_mut.unparse()
    }
    with open("results/demo_2_mutations.json", "w") as f:
        json.dump(mutations, f, indent=2)
    print(f"\n✓ Saved to results/demo_2_mutations.json")

    # Save individual Lua files
    for name, code in mutations.items():
        safe_name = name.replace("_mutation", "").replace("_", "-")
        with open(f"results/demo_2_{safe_name}.lua", "w") as f:
            f.write(code)
    print(f"✓ Saved to results/demo_2_*.lua")

    print()
    print("=" * 70)
    print("Key Observations:")
    print("  - All mutations preserve syntactic correctness")
    print("  - Splicing recombines interesting parts from different inputs")
    print("  - Recursive mutation increases nesting for deeper code testing")
    print("=" * 70)

if __name__ == "__main__":
    main()
