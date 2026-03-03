from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Set

from grammar_engine import NaiveGenerator
from target_lua import LuaTarget
from tree import Node, Tree


@dataclass
class MinimizeResult:
    tree: Tree
    changed: bool


class SubtreeMinimizer:
    def __init__(self, generator: NaiveGenerator, max_attempts: int = 24):
        self.generator = generator
        self._cache: Dict[str, Node] = {}
        self.max_attempts = max(1, max_attempts)

    def minimize(self, tree: Tree, target: LuaTarget, required_new_coverage: Set[str]) -> MinimizeResult:
        current = tree.clone()
        changed = False

        # Use a stable snapshot of paths/symbols from initial tree shape.
        # Later replacements may invalidate some paths; those are skipped.
        snapshot = [(path, node.symbol) for path, node in current.walk() if not node.is_terminal]
        attempts = 0
        for path, symbol in snapshot:
            if attempts >= self.max_attempts:
                break
            if not self._path_exists(current, path):
                continue
            minimal = self._minimal_subtree(symbol)
            try:
                candidate = current.replace_subtree(path, minimal)
            except (IndexError, AttributeError):
                continue
            attempts += 1
            result = target.run(candidate.unparse())
            if required_new_coverage.issubset(result.coverage_set):
                current = candidate
                changed = True
        return MinimizeResult(tree=current, changed=changed)

    def _minimal_subtree(self, symbol: str) -> Node:
        if symbol in self._cache:
            return self._cache[symbol].clone()

        subtree = self.generator.generate_subtree(symbol, depth=self.generator.max_depth)
        self._cache[symbol] = subtree.clone()
        return subtree

    def _path_exists(self, tree: Tree, path: tuple[int, ...]) -> bool:
        node = tree.root
        for idx in path:
            if idx < 0 or idx >= len(node.children):
                return False
            node = node.children[idx]
        return True
