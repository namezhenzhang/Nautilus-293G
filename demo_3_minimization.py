#!/usr/bin/env python3
"""
Demo 3: Subtree Minimization
Shows how minimization shrinks test cases while preserving coverage.
"""

from grammar_engine import Grammar, NaiveGenerator
from minimizer import SubtreeMinimizer
from tree import Tree
import json
import os

def main():
    print("=" * 70)
    print("DEMO 3: Subtree Minimization")
    print("=" * 70)
    print()

    # Setup
    grammar = Grammar.from_file("grammar/lua_grammar.json")
    gen = NaiveGenerator(grammar, max_depth=5)

    # Generate enough trees to get non-empty output
    tree = None
    for _ in range(20):
        tree = gen.generate_tree()
        if tree.unparse().strip():
            break

    if tree is None or not tree.unparse().strip():
        print("Warning: Could not generate non-empty tree for demo")
        print("Using minimal example instead...")
        print()
        print("=" * 70)
        print("DEMO 3: Subtree Minimization")
        print("=" * 70)
        print()
        print("Subtree minimization shrinks test cases while preserving coverage.")
        print("Example: Replace a large table constructor with a minimal one.")
        print()
        print("Benefits:")
        print("  1. Smaller inputs = faster execution")
        print("  2. Simpler inputs = easier to debug crashes")
        print("  3. Preserves coverage = still tests the same code paths")
        print("=" * 70)

        # Save basic info
        os.makedirs("results", exist_ok=True)
        with open("results/demo_3_minimization.json", "w") as f:
            json.dump({
                "status": "fallback",
                "message": "Could not generate non-empty tree",
                "benefits": [
                    "Smaller inputs = faster execution",
                    "Simpler inputs = easier to debug crashes",
                    "Preserves coverage = still tests the same code paths"
                ]
            }, f, indent=2)
        print("\n✓ Saved to results/demo_3_minimization.json")
        return

    original_code = tree.unparse()
    print(f"\nOriginal tree:")
    print(f"  Code length: {len(original_code)} characters")
    print(f"  Code preview: {original_code[:80]}...")

    # Get minimal candidates for each non-terminal
    minimizer = SubtreeMinimizer(gen)

    print("\nPre-computing minimal subtrees for each non-terminal...")
    # Trigger some minimal subtree generation
    for _ in range(5):
        tree = gen.generate_tree()
        for path, node in tree.walk():
            if not node.is_terminal:
                minimizer._minimal_subtree(node.symbol)
    print(f"  Found {len(minimizer._cache)} non-terminals with minimal candidates")

    # Show example minimization for a specific non-terminal
    print("\n" + "=" * 70)
    print("Example: Minimizing a specific subtree")
    print("=" * 70)

    results = {
        "original_code": original_code,
        "original_length": len(original_code),
        "minimizations": []
    }

    # Find a non-terminal to minimize
    for path, node in tree.walk():
        if not node.is_terminal:
            symbol = node.symbol
            print(f"\nMinimizing node: {symbol}")
            subtree_tree = Tree(node.clone())
            print(f"  Original subtree length: {len(subtree_tree.unparse())}")

            # Get minimal candidate
            if symbol in minimizer._cache:
                minimal = minimizer._cache[symbol]
                minimal_tree = Tree(minimal)
                original_len = len(subtree_tree.unparse())
                minimal_len = len(minimal_tree.unparse())
                reduction = original_len - minimal_len
                pct = 100 * (1 - minimal_len / original_len) if original_len > 0 else 0

                print(f"  Minimal subtree length: {len(minimal_tree.unparse())}")
                print(f"  Reduction: {reduction} characters ({pct:.1f}%)")

                results["minimizations"].append({
                    "symbol": symbol,
                    "original_length": original_len,
                    "minimal_length": minimal_len,
                    "reduction": reduction,
                    "percentage": pct,
                    "original_subtree": subtree_tree.unparse(),
                    "minimal_subtree": minimal_tree.unparse()
                })
            break

    # Save to file
    os.makedirs("results", exist_ok=True)
    with open("results/demo_3_minimization.json", "w") as f:
        json.dump(results, f, indent=2)
    print(f"\n✓ Saved to results/demo_3_minimization.json")

    # Save Lua files
    with open("results/demo_3_original.lua", "w") as f:
        f.write(original_code)
    print(f"✓ Saved to results/demo_3_original.lua")

    if results["minimizations"]:
        with open("results/demo_3_minimized.lua", "w") as f:
            f.write(results["minimizations"][0]["minimal_subtree"])
        print(f"✓ Saved to results/demo_3_minimized.lua")

    print()
    print("=" * 70)
    print("Key Benefits:")
    print("  1. Smaller inputs = faster execution")
    print("  2. Simpler inputs = easier to debug crashes")
    print("  3. Preserves coverage = still tests the same code paths")
    print("=" * 70)

if __name__ == "__main__":
    main()
