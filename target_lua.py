from __future__ import annotations

import glob
import hashlib
import os
import re
import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Set, Tuple


@dataclass
class RunResult:
    status: str
    coverage_set: Set[str]
    new_coverage: Set[str]
    is_new: bool
    branch_coverage_pct: float


class LuaTarget:
    def __init__(
        self,
        lua_bin: str,
        build_dir: str,
        timeout_sec: float = 2.0,
        coverage_sample_interval: int = 5,
        gcov_timeout_sec: Optional[float] = None,
    ):
        self.lua_bin = lua_bin
        self.build_dir = build_dir
        self.timeout_sec = timeout_sec
        self.coverage_sample_interval = max(1, coverage_sample_interval)
        self.gcov_timeout_sec = gcov_timeout_sec
        self.known_coverage: Set[str] = set()
        self._known_branch_coverage: Set[str] = set()
        self._total_branch_count = self._estimate_total_branch_count()
        self._last_gcda_hash = ""
        self._run_count = 0

    def run(self, input_str: str) -> RunResult:
        self._run_count += 1
        self._reset_gcda()
        with tempfile.NamedTemporaryFile("w", suffix=".lua", delete=False, encoding="utf-8") as f:
            f.write(input_str)
            lua_file = f.name

        status = "ok"
        try:
            proc = subprocess.run(
                [self.lua_bin, lua_file],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=self.timeout_sec,
                check=False,
            )
            if proc.returncode != 0:
                status = "crash"
        except subprocess.TimeoutExpired:
            status = "timeout"
        finally:
            try:
                os.unlink(lua_file)
            except OSError:
                pass

        coverage_set, branch_hits = self._collect_coverage()
        new_bits = coverage_set - self.known_coverage
        is_new = bool(new_bits)
        if is_new:
            self.known_coverage.update(new_bits)
        if branch_hits:
            self._known_branch_coverage.update(branch_hits)
        return RunResult(
            status=status,
            coverage_set=coverage_set,
            new_coverage=new_bits,
            is_new=is_new,
            branch_coverage_pct=self.branch_coverage_percent(),
        )

    def _reset_gcda(self) -> None:
        for gcda in glob.glob(os.path.join(self.build_dir, "**", "*.gcda"), recursive=True):
            try:
                os.remove(gcda)
            except OSError:
                continue

    def _collect_coverage(self) -> Tuple[Set[str], Set[str]]:
        # Heavy gcov parsing is sampled to avoid apparent "hangs" on long runs.
        if self._run_count % self.coverage_sample_interval != 0:
            return set(), set()

        quick_hash = self._hash_gcda()
        if quick_hash == self._last_gcda_hash:
            return set(), set()
        self._last_gcda_hash = quick_hash

        src_files = self._source_files_with_gcda()
        if not src_files:
            return set(), set()

        self._cleanup_old_gcov_files()
        for src in src_files:
            try:
                src_path = Path(src)
                kwargs = {
                    "cwd": str(src_path.parent),
                    "stdout": subprocess.DEVNULL,
                    "stderr": subprocess.DEVNULL,
                    "check": False,
                }
                if self.gcov_timeout_sec is not None and self.gcov_timeout_sec > 0:
                    kwargs["timeout"] = self.gcov_timeout_sec
                subprocess.run(["gcov", "-b", "-o", str(src_path.parent), src_path.name], **kwargs)
            except subprocess.TimeoutExpired:
                continue

        coverage: Set[str] = set()
        branch_hits: Set[str] = set()
        for gcov_path in glob.glob(os.path.join(self.build_dir, "**", "*.gcov"), recursive=True):
            if not os.path.exists(gcov_path):
                continue
            lines, branches = self._parse_gcov_file(gcov_path)
            coverage.update(lines)
            branch_hits.update(branches)
        return coverage, branch_hits

    def _source_files_with_gcda(self) -> Set[Path]:
        src_files: Set[Path] = set()
        for gcda in glob.glob(os.path.join(self.build_dir, "**", "*.gcda"), recursive=True):
            stem = Path(gcda).stem
            if not stem:
                continue
            candidate = Path(gcda).with_name(stem + ".c")
            if candidate.exists():
                src_files.add(candidate)
        return src_files

    def _cleanup_old_gcov_files(self) -> None:
        for gcov_path in glob.glob(os.path.join(self.build_dir, "**", "*.gcov"), recursive=True):
            try:
                os.remove(gcov_path)
            except OSError:
                continue

    def _parse_gcov_file(self, gcov_path: str) -> Tuple[Set[str], Set[str]]:
        line_hits: Set[str] = set()
        branch_hits: Set[str] = set()
        current_line = -1
        file_name = Path(gcov_path).name
        try:
            with open(gcov_path, "r", encoding="utf-8", errors="ignore") as f:
                for line in f:
                    # format: "    12:  34: code"
                    m = re.match(r"^\s*([0-9]+):\s*([0-9]+):", line)
                    if m:
                        hits = int(m.group(1))
                        line_no = int(m.group(2))
                        current_line = line_no
                        if hits > 0:
                            line_hits.add(f"{file_name}:{line_no}")
                        continue
                    bm = re.match(r"^\s*branch\s+(\d+)\s+taken\s+([0-9]+|[0-9]+%)", line)
                    if bm and current_line >= 0:
                        branch_id = bm.group(1)
                        taken = bm.group(2)
                        if taken.endswith("%"):
                            hit = int(taken[:-1]) > 0
                        else:
                            hit = int(taken) > 0
                        if hit:
                            branch_hits.add(f"{file_name}:{current_line}:{branch_id}")
        except FileNotFoundError:
            # gcov files may disappear between scan and open on some runs.
            return line_hits, branch_hits
        return line_hits, branch_hits

    def _hash_gcda(self) -> str:
        digest = hashlib.sha256()
        paths = sorted(glob.glob(os.path.join(self.build_dir, "**", "*.gcda"), recursive=True))
        for p in paths:
            try:
                st = os.stat(p)
                digest.update(p.encode("utf-8"))
                digest.update(str(st.st_size).encode("utf-8"))
                digest.update(str(st.st_mtime_ns).encode("utf-8"))
            except OSError:
                continue
        return digest.hexdigest()

    def _estimate_total_branch_count(self) -> int:
        count = 0
        for gcno in glob.glob(os.path.join(self.build_dir, "**", "*.gcno"), recursive=True):
            src_path = Path(gcno).with_suffix(".c")
            if not src_path.exists():
                continue
            try:
                proc = subprocess.run(
                    ["gcov", "-b", "-n", "-o", str(src_path.parent), src_path.name],
                    cwd=str(src_path.parent),
                    stdout=subprocess.PIPE,
                    stderr=subprocess.DEVNULL,
                    check=False,
                    text=True,
                )
                for line in proc.stdout.splitlines():
                    m = re.search(r"Branches executed:.*of\s+([0-9]+)", line)
                    if m:
                        count += int(m.group(1))
            except Exception:
                continue
        return max(1, count)

    def branch_coverage_percent(self) -> float:
        return 100.0 * len(self._known_branch_coverage) / float(self._total_branch_count)
