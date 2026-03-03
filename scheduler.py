from __future__ import annotations

import random
import time
from dataclasses import dataclass, field
from typing import List

from grammar_engine import NaiveGenerator
from minimizer import SubtreeMinimizer
from mutations import MutationEngine
from target_lua import LuaTarget
from tree import Tree


@dataclass
class SchedulerConfig:
    initial_seeds: int = 200
    budget_seconds: int = 600
    mutation_round: int = 3
    use_tree_mutation: bool = True
    use_feedback: bool = True
    use_byte_mutation: bool = False
    enable_minimization: bool = True
    minimize_every_n_new: int = 3
    warmup_new_coverage: int = 8


@dataclass
class SchedulerStats:
    coverage_over_time: List[List[int]] = field(default_factory=list)
    final_coverage: int = 0
    branch_coverage_over_time: List[List[float]] = field(default_factory=list)
    final_branch_coverage_pct: float = 0.0
    total_inputs: int = 0


class NautilusScheduler:
    def __init__(
        self,
        generator: NaiveGenerator,
        target: LuaTarget,
        mutator: MutationEngine,
        minimizer: SubtreeMinimizer,
        config: SchedulerConfig,
        rng: random.Random | None = None,
    ):
        self.generator = generator
        self.target = target
        self.mutator = mutator
        self.minimizer = minimizer
        self.config = config
        self.rng = rng or random.Random()
        self.queue: List[Tree] = []
        self._queue_idx = 0
        self._deadline = 0.0
        self._new_cov_events = 0

    def run(self) -> SchedulerStats:
        stats = SchedulerStats()
        start = time.time()
        self._deadline = start + self.config.budget_seconds
        next_tick = 0
        self._record_timeline(stats, start, next_tick)
        next_tick = 1

        for _ in range(self.config.initial_seeds):
            if time.time() >= self._deadline:
                break
            tree = self.generator.generate_tree()
            self._execute_and_maybe_enqueue(tree, stats, is_seed=True)
            next_tick = self._record_timeline(stats, start, next_tick)

        while time.time() < self._deadline:
            next_tick = self._record_timeline(stats, start, next_tick)

            if not self.queue:
                tree = self.generator.generate_tree()
                self._execute_and_maybe_enqueue(tree, stats, is_seed=True)
                next_tick = self._record_timeline(stats, start, next_tick)
                continue

            current = self.queue[self._queue_idx]
            self._queue_idx = (self._queue_idx + 1) % len(self.queue)
            self._mutate_round(current, stats)
            next_tick = self._record_timeline(stats, start, next_tick)

        next_tick = self._record_timeline(stats, start, next_tick)
        if stats.coverage_over_time:
            stats.coverage_over_time[-1][0] = self.config.budget_seconds
        else:
            stats.coverage_over_time = [
                [0, len(self.target.known_coverage)],
                [self.config.budget_seconds, len(self.target.known_coverage)],
            ]
        if stats.branch_coverage_over_time:
            stats.branch_coverage_over_time[-1][0] = self.config.budget_seconds
        else:
            stats.branch_coverage_over_time = [
                [0, self.target.branch_coverage_percent()],
                [self.config.budget_seconds, self.target.branch_coverage_percent()],
            ]
        stats.final_coverage = len(self.target.known_coverage)
        stats.final_branch_coverage_pct = self.target.branch_coverage_percent()
        return stats

    def _record_timeline(self, stats: SchedulerStats, start: float, next_tick: int) -> int:
        elapsed = min(int(time.time() - start), self.config.budget_seconds)
        while elapsed >= next_tick and next_tick <= self.config.budget_seconds:
            stats.coverage_over_time.append([next_tick, len(self.target.known_coverage)])
            stats.branch_coverage_over_time.append([next_tick, self.target.branch_coverage_percent()])
            next_tick += 1
        return next_tick

    def _execute_and_maybe_enqueue(self, tree: Tree, stats: SchedulerStats, is_seed: bool = False) -> None:
        result = self.target.run(tree.unparse())
        stats.total_inputs += 1
        if self.config.use_feedback:
            if result.is_new:
                required = result.new_coverage if result.new_coverage else result.coverage_set
                self._new_cov_events += 1
                accepted = tree
                if self._should_minimize():
                    minimized = self.minimizer.minimize(tree, self.target, required)
                    accepted = minimized.tree
                self.queue.append(accepted)
                self.mutator.register_tree(accepted)
        else:
            if is_seed or self.rng.random() < 0.5:
                self.queue.append(tree)
                self.mutator.register_tree(tree)

    def _mutate_round(self, tree: Tree, stats: SchedulerStats) -> None:
        if self.config.use_tree_mutation:
            mutants = []
            for _ in range(self.config.mutation_round):
                mutants.append(self.mutator.random_mutation(tree))
                mutants.append(self.mutator.splicing_mutation(tree))
                mutants.append(self.mutator.random_recursive_mutation(tree))
        else:
            mutants = [self._byte_mutate(tree)]

        for mutant in mutants:
            if time.time() >= self._deadline:
                break
            self._execute_and_maybe_enqueue(mutant, stats)

    def _byte_mutate(self, tree: Tree) -> Tree:
        text = tree.unparse()
        if not text:
            return tree
        chars = list(text.encode("utf-8", errors="ignore"))
        if not chars:
            return tree
        idx = self.rng.randrange(len(chars))
        op = self.rng.choice(["flip_bit", "flip_byte", "arith"])
        if op == "flip_bit":
            chars[idx] ^= 1 << self.rng.randrange(8)
        elif op == "flip_byte":
            chars[idx] = self.rng.randrange(256)
        else:
            chars[idx] = (chars[idx] + self.rng.choice([-1, 1])) % 256
        mutated = bytes(chars).decode("utf-8", errors="ignore")
        # Reuse parser-less path by wrapping mutated string into terminal-only tree.
        from tree import Node

        return Tree(root=Node(symbol="START", is_terminal=False, children=[Node(symbol="TERMINAL", is_terminal=True, value=mutated)]))

    def _should_minimize(self) -> bool:
        if not self.config.enable_minimization:
            return False
        if self._new_cov_events <= self.config.warmup_new_coverage:
            return True
        return self._new_cov_events % max(1, self.config.minimize_every_n_new) == 0


def config_for_group(group_name: str) -> SchedulerConfig:
    if group_name == "random_grammar":
        return SchedulerConfig(
            use_tree_mutation=False,
            use_feedback=False,
            use_byte_mutation=False,
            enable_minimization=False,
            mutation_round=1,
        )
    if group_name == "afl_like":
        return SchedulerConfig(
            use_tree_mutation=False,
            use_feedback=True,
            use_byte_mutation=True,
            enable_minimization=False,
            mutation_round=1,
        )
    if group_name == "nautilus_no_feedback":
        return SchedulerConfig(
            use_tree_mutation=True,
            use_feedback=False,
            enable_minimization=False,
            mutation_round=3,
        )
    if group_name == "nautilus_full":
        return SchedulerConfig(
            use_tree_mutation=True,
            use_feedback=True,
            enable_minimization=True,
            minimize_every_n_new=4,
            warmup_new_coverage=6,
            mutation_round=2,
        )
    raise ValueError(f"unknown group: {group_name}")


def apply_full_minimize_mode(config: SchedulerConfig, mode: str) -> SchedulerConfig:
    if mode not in {"off", "sparse", "full"}:
        raise ValueError(f"unknown full minimize mode: {mode}")
    if mode == "off":
        config.enable_minimization = False
        return config
    if mode == "full":
        config.enable_minimization = True
        config.minimize_every_n_new = 1
        config.warmup_new_coverage = 0
        return config
    # sparse (default tuned mode)
    config.enable_minimization = True
    config.minimize_every_n_new = 4
    config.warmup_new_coverage = 6
    return config
