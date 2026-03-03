from __future__ import annotations

import json
import random
from dataclasses import dataclass
from typing import Dict, List

from tree import Node, Tree


@dataclass
class Grammar:
    start: str
    rules: Dict[str, List[List[str]]]
    min_depth: Dict[str, int]

    @classmethod
    def from_file(cls, path: str) -> "Grammar":
        with open(path, "r", encoding="utf-8") as f:
            raw = json.load(f)

        start = raw["start"]
        rules = raw["rules"]
        min_depth = cls._compute_min_depth(rules)
        return cls(start=start, rules=rules, min_depth=min_depth)

    @staticmethod
    def _compute_min_depth(rules: Dict[str, List[List[str]]]) -> Dict[str, int]:
        inf = 10**9
        depth = {nt: inf for nt in rules}
        changed = True

        while changed:
            changed = False
            for nt, productions in rules.items():
                best = depth[nt]
                for prod in productions:
                    candidate = 1
                    valid = True
                    for sym in prod:
                        if sym in rules:
                            if depth[sym] == inf:
                                valid = False
                                break
                            candidate = max(candidate, 1 + depth[sym])
                    if valid:
                        best = min(best, candidate)
                if best != depth[nt]:
                    depth[nt] = best
                    changed = True

        for nt, val in depth.items():
            if val == inf:
                depth[nt] = 1
        return depth

    def is_nonterminal(self, symbol: str) -> bool:
        return symbol in self.rules


class NaiveGenerator:
    def __init__(self, grammar: Grammar, max_depth: int = 10, rng: random.Random | None = None):
        self.grammar = grammar
        self.max_depth = max_depth
        self.rng = rng or random.Random()

    def generate_tree(self, symbol: str | None = None, depth: int = 0) -> Tree:
        root_symbol = symbol or self.grammar.start
        root = self._expand_nonterminal(root_symbol, depth)
        return Tree(root)

    def generate_subtree(self, symbol: str, depth: int = 0) -> Node:
        return self._expand_nonterminal(symbol, depth)

    def _expand_nonterminal(self, symbol: str, depth: int) -> Node:
        productions = self.grammar.rules[symbol]
        chosen = self._choose_production(symbol, productions, depth)
        node = Node(symbol=symbol, is_terminal=False)
        for token in chosen:
            if self.grammar.is_nonterminal(token):
                node.children.append(self._expand_nonterminal(token, depth + 1))
            else:
                node.children.append(Node(symbol="TERMINAL", is_terminal=True, value=token))
        return node

    def _choose_production(self, symbol: str, productions: List[List[str]], depth: int) -> List[str]:
        if depth < self.max_depth:
            return self.rng.choice(productions)

        # At depth budget: pick production with smallest expansion depth.
        scored = []
        for prod in productions:
            score = 1
            for token in prod:
                if self.grammar.is_nonterminal(token):
                    score = max(score, 1 + self.grammar.min_depth.get(token, 1))
            scored.append((score, prod))
        scored.sort(key=lambda x: x[0])
        return scored[0][1]
