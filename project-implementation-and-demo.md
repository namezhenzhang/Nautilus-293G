# Nautilus 课程项目：实现范围与展示方案

## 1. 项目目标

复现 Nautilus 的核心思想（grammar-aware + coverage-guided），而非完整工业实现。  
核心研究问题：在结构化输入场景下，`语法树变异 + 覆盖反馈` 是否优于传统 baseline。

**技术栈**：

- 语言：Python 3.10+（fuzzer 本体）
- Target：Lua 5.4 解释器（C 源码编译）
- Coverage：编译 Lua 时加 `--coverage`，通过 `gcov` 收集 C 源码行覆盖
- Grammar：Lua 语法子集，JSON 格式定义

---

## 2. 任务清单（按依赖顺序）

### Task 1：Grammar + Tree 数据结构

- 定义 JSON grammar 格式
- 实现 `Tree` 类：节点存储 `(non_terminal, children)` 或 `(terminal, value)`
- 每个节点记录自己的 non-terminal 类型，方便 splicing 索引
- 实现 `tree.nodes_by_nonterminal() -> Dict[str, List[NodeID]]`（为 splicing 做准备）

Grammar 使用 Lua 语法子集（~150 条规则，~30 个 non-terminal），参考 Nautilus 开源版本的 `grammars/lua.py`。
覆盖：算术/比较/逻辑/位运算、变量赋值、控制流、函数定义与调用、table/metatable、协程、标准库函数名。

完整 grammar 定义见 `grammar/lua_grammar.json`（独立文件，不在此内联）。

Grammar 设计要点：
- **IDENTIFIER 列表是关键**：需包含 ~70 个 Lua 标准库函数名（`math.sin`, `string.len`, `table.insert`, `pcall`, `setmetatable` 等）和元方法名（`__index`, `__add`, `__call` 等）。每个函数名对应 Lua interpreter 中不同的 C 代码路径。
- **VAR 需包含模块名**：`coroutine`, `debug`, `math`, `io`, `os`, `string`, `table`, `utf8`，使得 `VAR.IDENTIFIER(ARGS)` 能生成合法的标准库调用。
- **运算符需补全**：二元运算符 17 种（`+`, `-`, `*`, `/`, `//`, `^`, `%`, `&`, `~`, `|`, `>>`, `<<`, `..`, `<`, `<=`, `>`, `>=`, `==`, `~=`, `and`, `or`），一元运算符 4 种（`-`, `not`, `#`, `~`）。
- **语法结构**：除基础控制流外，需包含 lambda（`function(...) ... end`）、协程（`coroutine.create/resume/yield`）、repeat/until、goto/label、多变量赋值。

### Task 2：Generation + Unparsing

- **Naive Generation**：从 start symbol 递归随机展开，配置 `max_depth`（默认 10）
  - 接近 max_depth 时强制选最短规则（避免无限递归）
  - 需要预计算每个 non-terminal 的 `min_expansion_depth`
- **Unparsing**：递归拼接叶节点字符串，`tree.unparse() -> str`

### Task 3：Lua Target + Coverage 收集

#### 3a. 编译 Lua

下载 Lua 5.4 源码，修改编译参数加入 coverage 插桩：

```bash
curl -R -O https://www.lua.org/ftp/lua-5.4.7.tar.gz
tar zxf lua-5.4.7.tar.gz
cd lua-5.4.7
make MYCFLAGS="--coverage -O0 -g" MYLDFLAGS="--coverage" macosx
```

编译产物：`src/lua`（带 coverage 插桩的 Lua 二进制）+ `src/*.gcno`（coverage 结构文件）。

为并行实验准备多份独立 build（各自有独立的 `.gcda` 文件）。

#### 3b. Target 接口

```python
class LuaTarget:
    def run(self, input_str) -> (status, coverage_set, is_new):
        # 1. 删除旧 .gcda 文件（重置 coverage）
        # 2. 写入 input_str 到临时 .lua 文件
        # 3. subprocess 执行 ./lua temp.lua（timeout=2s）
        # 4. 解析 .gcda / 运行 gcov 获取覆盖行集合
        # 5. 与全局已知 coverage 做 diff
        # 6. 返回 (status, coverage_set, has_new_coverage)
```

**性能预估**：~100-150ms/input（subprocess + gcov 解析）。10 分钟实验 ≈ 4000-6000 inputs。

**优化**：大部分输入不触发新 coverage。可先对 `.gcda` 文件做快速 hash 比对，仅在 hash 变化时才跑完整 gcov 解析。

### Task 4：Mutation 引擎

按优先级实现（前 3 个必做，后 2 个时间允许再加）：

1. **Random Mutation**（必做）
   - 随机选一个节点，用同 non-terminal 的新生成子树替换

2. **Splicing Mutation**（必做）
   - 从 queue 中另一棵树取同 non-terminal 的子树替换当前树的对应节点
   - 维护全局索引 `Dict[str, List[(tree_id, node_id)]]`，入队时更新

3. **Random Recursive Mutation**（必做）
   - 找到树中的递归结构（某 non-terminal 的子树中包含同类型后代）
   - 重复该递归 2^n 次（n 随机 1-5），增加嵌套深度

4. **Rules Mutation**（可选）
   - 对每个节点，尝试该 non-terminal 的所有其他产生式

5. **AFL-lite Mutation**（可选）
   - 对 unparsed string 做 bit flip / byte flip / ±1 arithmetic

### Task 5：Minimization

**Subtree Minimization**（必做）：
- 预计算每个 non-terminal 的最小子树
- 从根到叶遍历，尝试用最小子树替换每个节点
- 替换后执行，若仍触发相同新 coverage 则保留替换，否则回滚

**Recursive Minimization**（可选）：
- 找递归节点（EXPR -> ... -> EXPR），用内层替换外层，减少嵌套

### Task 6：Scheduler + 主循环

```
1. 用 generation 生成 N=200 个初始输入
2. 逐个执行，触发新 coverage 的加入 queue
3. 主循环（直到时间预算耗尽）：
   a. 从 queue 取下一个输入
   b. 如果是新入队（init 状态）→ 先 minimize，再进入 mutation
   c. 对该输入执行一轮 mutation（random + splicing + recursive 各若干次）
   d. 每个 mutant 执行 → 触发新 coverage 则入队
   e. 移到 queue 中下一个
   f. queue 遍历完一轮后，可穿插 generate 新输入
```

### Task 7：Baseline 实现

共 4 组对照（含 Nautilus Full）：

| # | 名称 | Grammar | Tree Mutation | Coverage Feedback |
|---|------|---------|---------------|-------------------|
| 1 | Random Grammar | Yes | No | No |
| 2 | AFL-like Byte Mutation | No | No | Yes |
| 3 | Nautilus No Feedback | Yes | Yes | No |
| 4 | **Nautilus Full** | Yes | Yes | Yes |

- **Random Grammar**：持续随机生成 grammar 输入，执行并记录 coverage，但不做 mutation 也不做 feedback 选择
- **AFL-like**：以 generation 的 seed 为起点，对 unparsed string 做字节级变异（bit flip, byte flip, arithmetic），有 coverage feedback
- **Nautilus No Feedback**：有 tree mutation，但不按 coverage 筛选，随机保留输入继续变异

这 3 个 baseline 都复用已有模块，只需在主循环中开关对应功能即可。

### Task 8：实验运行脚本

- 每组运行 **10 分钟**（Lua target 每次执行较慢，需要更长窗口）
- 每组重复 **5 次**（固定 seed 0-4）
- 每秒记录一次当前 cumulative coverage
- 每组使用独立的 Lua build 目录（隔离 `.gcda` 文件），支持并行跑不同组
- 输出格式：`results/{group_name}/run_{seed}.json`
  ```json
  {"coverage_over_time": [[0, 5], [1, 8], [2, 12], ...], "final_coverage": 420, "total_inputs": 5000}
  ```

### Task 9：画图 + 结果分析

用 `matplotlib` 生成：

1. **Coverage-Time 曲线**（4 组同图，带 std shading）
2. **最终覆盖率柱状图**（4 组，带 error bar）
3. **（可选）Ablation 表格**：Full vs 去掉 Splicing vs 去掉 Recursive vs 仅 Random

---

## 3. 明确不做（Out of Scope）

- Uniform generation（组合计数法）
- 脚本化 grammar / 非 CFG 语义约束
- 完整 AFL deterministic/havoc 全流程
- 高性能 forkserver / 编译器级插桩优化
- 完整 Lua 语法（只用子集）
- ANTLR grammar 解析
- Mann-Whitney U test（图表够说明问题即可）

---

## 4. 展示方案

### 4.1 系统展示

1. **架构图（1 张）**：Grammar → Generation → Mutation → Unparse → Execute Lua → Coverage Feedback → Queue
2. **模块 demo（各 1 例）**：
   - Generation：展示一棵生成的 AST 和对应 Lua 代码
   - Mutation：展示 splicing 前后的两棵 AST
   - Minimization：展示缩减前后长度，coverage 不变
3. **关键伪代码（2-3 段）**：主循环、splicing、minimization

### 4.2 实验结果

1. **图 1：Coverage-Time 曲线**（4 组对比，核心图）
2. **图 2：最终覆盖率柱状图**（均值 + std error bar）
3. **（可选）图 3：有效输入率** — grammar-aware 组 vs AFL-like 组
4. **（可选）表 1：Ablation** — 各 mutation 的贡献

---

## 5. 交付物

1. 代码仓库（可运行）
2. README（运行方法、依赖、Lua 编译步骤）
3. 实验脚本（`run_experiments.py`，一键跑全部）
4. 结果数据（JSON）
5. 图表（PNG）
6. 演示 slides

---

## 6. 报告结构

1. Introduction（问题与动机）
2. Method（系统设计与算法）
3. Implementation（工程实现细节：Python fuzzer + Lua target + gcov coverage）
4. Evaluation（实验设计与结果）
5. Ablation Study（如果做了）
6. Limitations（与论文差距：子集 grammar、无 uniform generation、无 forkserver、执行速度较慢等）
7. Conclusion

---

## 7. 项目范围声明

This project re-implements the core ideas of Nautilus rather than all engineering details of the original system.  
Our implementation includes grammar-based tree generation, tree-aware mutations (random, splicing, random recursive), lightweight subtree minimization, and coverage-guided scheduling.  
The fuzzer is implemented in Python, targeting the Lua 5.4 interpreter compiled with `gcc --coverage` for line-level C source coverage collection via `gcov`.  
We use a simplified subset of Lua grammar (~20 production rules) that covers arithmetic, variables, control flow, functions, and tables.  
Advanced features such as uniform generation, full AFL mutation stack, ANTLR compatibility, forkserver, and high-performance instrumentation are outside the project scope.
