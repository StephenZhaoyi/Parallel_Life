# Parallel_Life

This is a educational course project for *Parallel Computing(CITHN2003)* with the following discriptions:

University Name: Technical University of Munich

Course Name: Parallel Computing(CITHN2003)

Create parallelled version(with openMP) of Conway's game of life and do benchmarking.

# Requirement

***If you are currently enrolled in Parallel Computing(CITHN2003):***

Please first install Docker at [https://www.docker.com/]()

Docker Container: compassionate_euler at [https://hub.docker.com/r/pratikvn/2025-parco]()

And fetch the docker

`docker pull pratikvn/2025-parco `

You can easily run this project in this docker environment, all requirements should already meet.

***If you are an external user:***

Prerequisites (Linux/macOS/WSL recommended):

- A C++20 compiler (GCC 11+/Clang 14+)
- CMake 3.15+
- OpenMP (usually comes with your compiler; CMake will detect it)
- Python 3.12+ for benchmarking (matplotlib optional for plots)

# Build

From the repo root:

1) Configure and build

```
cmake -S . -B build
cmake --build build -j
```

2) Artifacts will be created under `build/` with executable names matching their source file basenames (see below).

# Predifined Life-like Rules

Life-like rules implemented in this final project:

| Rule Name                       | Rulestring         |
| :------------------------------ | ------------------ |
| default                         | B3/S23             |
| AntiLife                        | B0123478/S01234678 |
| InverseLife                     | B0123478/S34678    |
| Wickstretcher And The Parasites | B01356/S012345     |
| Oils                            | B014/S2            |
| Invertamaze                     | B028/S0124         |
| Neon Blobs                      | B08/S4             |
| H-trees                         | B1/S012345678      |
| Fuzz                            | B1/S014567         |
| Gnarl                           | B1/S1              |

You can look up for the cpp source codes and executables in this project for these predefined rulesets.

For more life-like rules, please see [https://conwaylife.com/wiki/List_of_Life-like_rules]()

# **Usage: C++ Life Variants**

All C++ executables are located in `build/` and named as `<variant>_<mode>`, e.g., `default_sequential`, `antiLife_openMP_parallel_for`, etc.

***C++ Executable CLI Flags***

- `--steps <N>` : Number of simulation steps to run
- `--no-draw` : Disable terminal animation **and** print timing summary only, **must** be used **together with** `--steps <N>`
- `--prob <P>` : Initial alive probability in [0,1] (Bernoulli distribution for each cell)
- `--width <W>` : Grid width
- `--height <H>` : Grid height
- `--threads <T>` : OpenMP threads (only for OpenMP targets)
- `--blockrows <B>` : Rows per task block (**only** for `*_openMP_parallel_tasks`)
- `--rule <RULE>` : (customLife **only**) Custom rulestring, e.g., B36/S23

***Example commands:***

***Default Life (Show drawing output)***

```
./build/default_sequential
```

***Default Life (Show summary only, steps and threads defined)***

`./build/default_openMP_parallel_for --no-draw --steps 2000 --threads 8`

***Fuzz Life***

```
./build/fuzzLife_sequential --no-draw --steps 2000
```

***Custom Life (user-defined rules)***

```
./build/customLife_sequential --no-draw --steps 2000 --rule B36/S23
```

***Timing output (when `--no-draw` is used) looks like:***

```
steps=2000 width=80 height=24 threads=8 time_ms=36.9808 per_step_ms=0.0184904 per_cell_us=0.00963042
```

# Benchmarking with Python

The repo includes a Python script `benchmark.py` for automated benchmarking and comparison of all Life variants and parallelization modes.

***Python Benchmark CLI Flags***

- `--variants` : Comma-separated list of Life rule variants to benchmark (e.g., default,antilife,custom)
- `--modes` : Comma-separated list of parallelization modes (e.g., seq,parfor,simd,tasks)
- `--compare` : Comparison type: free (all combinations), parallel (compare modes within one variant), variants (compare variants within one mode). Legacy aliases intra/inter still accepted.
- `--blockrows` : Comma-separated block row sizes for tasks mode
- `--width` / `--height` : Grid size
- `--prob` : Initial alive probability
- `--repeats` : Number of repeats per measurement
- `--steps` : Comma-separated step counts
- `--threads` : OpenMP threads (for OpenMP targets)
- `--build-dir` : Path to build directory
- `--csv` : Output CSV path
- `--plot` : Output plot path
- `--rule` : Rulestring for customLife (e.g., B36/S23)

***Allowed Values***

- Variants (`--variants`, comma-separated):

  - `default`
  - `antilife`
  - `inverse`
  - `wp`
  - `oils`
  - `invertamaze`
  - `neonblobs`
  - `htree`
  - `fuzz`
  - `gnarl`
  - `custom` (custom rule; use with --rule)
- Modes (`--modes`, comma-separated):

  - `seq` (single-thread sequential)
  - `parfor` (OpenMP parallel for)
  - `simd` (OpenMP parallel for with SIMD vectorization hint)
  - `tasks` (OpenMP tasks; combine with `--blockrows`)
- Compare types (`--compare`, can only choose one):

  - `free`: run all selected variant/mode Cartesian combinations
  - `parallel`: compare all parallel modes within a single variant (requires exactly one variant)
  - `variants`: compare variants within a single parallel mode (requires exactly one mode)

***Example commands***

- Compare all modes for a single variant (parallel comparison):
  ```
  python3 benchmark.py --variants default --compare parallel
  ```
- Compare multiple variants for a single mode (variants comparison):
  ```
  python3 benchmark.py --variants default,antilife,inverse --modes parfor --compare variants
  ```
- Benchmark with custom grid size and repeats:
  ```
  python3 benchmark.py --variants fuzz --modes tasks --blockrows 2,4,8 --width 256 --height 256 --steps 1000,2000 --repeats 5
  ```
- Benchmark a custom rule (customLife):
  ```
  python3 benchmark.py --variants custom --modes seq,parfor --rule B36/S23
  ```

## Output

- Results are saved to `results.csv` by default (can be changed with `--csv`).
- A plot is saved as `steps_vs_time.png` (can be changed with `--plot`).
- All CLI options are documented with `python3 benchmark.py --help`.

# License

Educational project; see repository history for attribution. If you intend to reuse code, please add an explicit license file.
