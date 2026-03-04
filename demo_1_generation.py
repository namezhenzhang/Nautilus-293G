#!/usr/bin/env python3
"""
Demo 1: Grammar-based Tree Generation
Shows how Nautilus generates syntactically correct Lua code from grammar.
"""

from grammar_engine import Grammar, NaiveGenerator
from tree import Tree
import json
import os

def main():
    print("=" * 70)
    print("DEMO 1: Grammar-based Tree Generation")
    print("=" * 70)
    print()

    # Load grammar
    print("Loading Lua grammar from grammar/lua_grammar.json...")
    grammar = Grammar.from_file("grammar/lua_grammar.json")
    print(f"✓ Loaded {len(grammar.rules)} production rules")
    print(f"✓ Start symbol: {grammar.start}")
    print()

    # Create generator
    gen = NaiveGenerator(grammar, max_depth=6)

    # Generate 3 example trees
    examples = []
    print("Generating 3 random Lua programs:")
    print("-" * 70)

    examples_generated = 0
    attempts = 0
    while examples_generated < 3 and attempts < 20:
        attempts += 1
        tree = gen.generate_tree()
        lua_code = tree.unparse()

        # Skip empty or whitespace-only outputs for demo
        if lua_code.strip() == "":
            continue

        examples_generated += 1
        examples.append({
            "id": examples_generated,
            "depth": tree.depth(),
            "size": tree.size(),
            "length": len(lua_code),
            "code": lua_code
        })

        print(f"\nExample {examples_generated}:")
        print("-" * 40)
        print(lua_code)
        print("-" * 40)
        print(f"Tree depth: {tree.depth()}")
        print(f"Node count: {tree.size()}")
        print(f"Code length: {len(lua_code)} characters")

    # Write to file
    os.makedirs("results", exist_ok=True)
    with open("results/demo_1_generations.json", "w") as f:
        json.dump(examples, f, indent=2)
    print(f"\n✓ Saved to results/demo_1_generations.json")

    # Also save individual Lua files
    for i, ex in enumerate(examples):
        with open(f"results/demo_1_example_{i+1}.lua", "w") as f:
            f.write(ex["code"])
    print(f"✓ Saved to results/demo_1_example_*.lua")

    print()
    print("=" * 70)
    print("Key Observation:")
    print("  All generated programs are syntactically correct Lua code!")
    print("  This is the power of grammar-based generation.")
    print("=" * 70)

if __name__ == "__main__":
    main()
