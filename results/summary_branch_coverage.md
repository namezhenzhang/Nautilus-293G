# Result Summary (Branch Coverage Primary)

| Group | Runs | Final Branch Coverage % (mean ± std) | Delta vs Random (pp) | Final Line Coverage (mean ± std) | Total Inputs (mean ± std) |
|---|---:|---:|---:|---:|---:|
| random_grammar | 5 | 29.122 ± 0.488 | 0.000 | 4762.400 ± 30.312 | 19629.200 ± 222.887 |
| afl_like | 5 | 32.372 ± 0.833 | 3.251 | 4963.000 ± 53.207 | 19525.200 ± 273.963 |
| nautilus_no_feedback | 5 | 36.749 ± 0.668 | 7.628 | 5374.000 ± 101.973 | 15708.200 ± 1513.822 |
| nautilus_full | 5 | 40.912 ± 0.978 | 11.791 | 5622.800 ± 103.406 | 17959.200 ± 425.782 |

Notes:
- Primary metric follows Nautilus paper style: branch coverage percentage.
- Delta is in percentage points (pp) against `random_grammar`.
