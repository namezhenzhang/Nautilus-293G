from __future__ import annotations

import random
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

from grammar_engine import NaiveGenerator
from tree import Node, Path, Tree


@dataclass
class CorpusEntry:
    tree: Tree
    tree_id: int


class MutationEngine:
    def __init__(self, generator: NaiveGenerator, rng: random.Random | None = None):
        self.generator = generator
        self.rng = rng or random.Random()
        self._next_tree_id = 1
        self.nt_index: Dict[str, List[Tuple[int, Path, Node]]] = {}

    def register_tree(self, tree: Tree) -> int:
        tree_id = self._next_tree_id
        self._next_tree_id += 1
        for path, node in tree.walk():
            if node.is_terminal:
                continue
            self.nt_index.setdefault(node.symbol, []).append((tree_id, path, node.clone()))
        return tree_id

    def random_mutation(self, tree: Tree) -> Tree:
        nts = [(path, node) for path, node in tree.walk() if not node.is_terminal]
        if not nts:
            return tree.clone()
        path, node = self.rng.choice(nts)
        subtree = self.generator.generate_subtree(node.symbol)
        return tree.replace_subtree(path, subtree)

    def splicing_mutation(self, tree: Tree) -> Tree:
        nts = [(path, node) for path, node in tree.walk() if not node.is_terminal]
        self.rng.shuffle(nts)
        for path, node in nts:
            pool = self.nt_index.get(node.symbol, [])
            if not pool:
                continue
            _, _, donor = self.rng.choice(pool)
            return tree.replace_subtree(path, donor)
        return tree.clone()

    def random_recursive_mutation(self, tree: Tree) -> Tree:
        recursive_paths = tree.recursive_paths()
        if not recursive_paths:
            return tree.clone()
        chosen = self.rng.choice(recursive_paths)
        node = tree.get_node(chosen)
        repeated = node.clone()
        repeat_times = 2 ** self.rng.randint(1, 5)

        # Grow by repeatedly wrapping with freshly generated same-symbol nodes.
        for _ in range(repeat_times):
            wrapper = self.generator.generate_subtree(node.symbol)
            insertion = self._find_first_nonterminal_path(wrapper, node.symbol)
            if insertion is None:
                break
            wrapper_tree = Tree(wrapper)
            wrapper = wrapper_tree.replace_subtree(insertion, repeated).root
            repeated = wrapper

        return tree.replace_subtree(chosen, repeated)

    def _find_first_nonterminal_path(self, root: Node, symbol: str) -> Optional[Path]:
        stack: List[Tuple[Path, Node]] = [((), root)]
        while stack:
            path, node = stack.pop()
            if not node.is_terminal and node.symbol == symbol and path:
                return path
            for idx in range(len(node.children) - 1, -1, -1):
                stack.append((path + (idx,), node.children[idx]))
        return None
