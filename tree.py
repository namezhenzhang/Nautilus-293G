from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, Iterable, Iterator, List, Optional, Tuple

Path = Tuple[int, ...]


@dataclass
class Node:
    symbol: str
    is_terminal: bool = False
    value: Optional[str] = None
    children: List["Node"] = field(default_factory=list)

    def clone(self) -> "Node":
        return Node(
            symbol=self.symbol,
            is_terminal=self.is_terminal,
            value=self.value,
            children=[child.clone() for child in self.children],
        )


@dataclass
class Tree:
    root: Node

    def clone(self) -> "Tree":
        return Tree(self.root.clone())

    def unparse(self) -> str:
        return "".join(self._iter_terminals(self.root))

    def size(self) -> int:
        return sum(1 for _ in self.walk())

    def depth(self) -> int:
        def _depth(node: Node) -> int:
            if not node.children:
                return 1
            return 1 + max(_depth(child) for child in node.children)

        return _depth(self.root)

    def walk(self) -> Iterator[Tuple[Path, Node]]:
        stack: List[Tuple[Path, Node]] = [((), self.root)]
        while stack:
            path, node = stack.pop()
            yield path, node
            for idx in range(len(node.children) - 1, -1, -1):
                stack.append((path + (idx,), node.children[idx]))

    def nodes_by_nonterminal(self) -> Dict[str, List[Path]]:
        out: Dict[str, List[Path]] = {}
        for path, node in self.walk():
            if node.is_terminal:
                continue
            out.setdefault(node.symbol, []).append(path)
        return out

    def get_node(self, path: Path) -> Node:
        node = self.root
        for idx in path:
            node = node.children[idx]
        return node

    def replace_subtree(self, path: Path, subtree: Node) -> "Tree":
        if not path:
            return Tree(subtree.clone())

        new_root = self.root.clone()
        parent = new_root
        for idx in path[:-1]:
            parent = parent.children[idx]
        parent.children[path[-1]] = subtree.clone()
        return Tree(new_root)

    def recursive_paths(self) -> List[Path]:
        recursive: List[Path] = []
        for path, node in self.walk():
            if node.is_terminal:
                continue
            if self._has_descendant_symbol(node, node.symbol):
                recursive.append(path)
        return recursive

    def _iter_terminals(self, node: Node) -> Iterable[str]:
        if node.is_terminal:
            if node.value is not None:
                yield node.value
            return
        for child in node.children:
            yield from self._iter_terminals(child)

    def _has_descendant_symbol(self, node: Node, symbol: str) -> bool:
        stack = list(node.children)
        while stack:
            cur = stack.pop()
            if not cur.is_terminal and cur.symbol == symbol:
                return True
            stack.extend(cur.children)
        return False
