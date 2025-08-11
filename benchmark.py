#!/usr/bin/env python3
import argparse, csv, subprocess, re, statistics, sys
from pathlib import Path
from typing import Optional

BUILD_DIR = Path('build')

# default parameters (can be overridden by CLI)
WIDTH = 160
HEIGHT = 96
PROB = 0.25
REPEATS = 3
STEPS_LIST = [500, 1000, 1500, 2000, 3000, 4000]
OMP_THREADS = None  # e.g., 8 to fix threads; None to use OpenMP default
PLOT_FILE_TOTAL = 'steps_vs_time.png'
CSV_FILE = 'results.csv'

TIME_RE = re.compile(r"time_ms=([0-9.]+)")

# mappings for variants and modes
VARIANT_DIR = {
    'default': 'default',
    'antilife': 'antiLife',
    'inverse': 'inverseLife',
    'wp': 'w&pLife',
    'oils': 'oilsLife',
    'invertamaze': 'invertAmazeLife',
    'neonblobs': 'neonBlobsLife',
    'htree': 'hTreeLife',
    'fuzz': 'fuzzLife',
    'gnarl': 'gnarlLife',
    'custom': 'customLife',
}

MODE_SUFFIX = {
    'seq': 'sequential',
    'parfor': 'openMP_parallel_for',
    'tasks': 'openMP_parallel_tasks',
    'simd': 'openMP_parallel_for_simd',
}

def exe_path(variant_key: str, mode_key: str) -> Path:
    vdir = VARIANT_DIR[variant_key]
    suffix = MODE_SUFFIX[mode_key]
    # default lives under default/, others under their own dir; all executables are in build/
    # Output name equals cpp basename, e.g., default_sequential, antiLife_openMP_parallel_for, w&pLife_sequential, etc.
    base = f"{vdir}_{suffix}"
    return BUILD_DIR / base

def run_once(exe: Path, steps: int, width: int, height: int, prob: float, omp_threads: Optional[int], extra_args=None) -> float:
    cmd = [str(exe), '--no-draw', '--steps', str(steps), '--prob', str(prob), '--width', str(width), '--height', str(height)]
    if extra_args:
        cmd += list(extra_args)
    if ('openMP' in exe.name) and (omp_threads is not None):
        cmd += ['--threads', str(omp_threads)]
    proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if proc.returncode != 0:
        print(proc.stdout)
        print(proc.stderr, file=sys.stderr)
        raise SystemExit(f'Executable run failed: {exe}')
    m = TIME_RE.search(proc.stdout)
    if not m:
        raise SystemExit(f'Unexpected output from {exe}: {proc.stdout.strip()}')
    return float(m.group(1))

def run_series(label: str, exe: Path, steps_list, repeats, width, height, prob, omp_threads, extra_args=None):
    if not exe.exists():
        print(f"Skip missing executable: {exe}")
        return None
    xs, ys, err = [], [], []
    for s in steps_list:
        vals = [run_once(exe, s, width, height, prob, omp_threads, extra_args=extra_args) for _ in range(repeats)]
        xs.append(s)
        ys.append(statistics.mean(vals))
        err.append(statistics.pstdev(vals) if repeats > 1 else 0.0)
        print(f'{label}: steps={s} mean_ms={ys[-1]:.2f} sd={err[-1]:.2f}')
    return {'label': label, 'x': xs, 'y': ys, 'e': err}

def parse_args():
    p = argparse.ArgumentParser(description='Benchmark Life variants and OpenMP modes.')
    p.add_argument('--variants', default='default', help='Comma-separated list of Life rule variants to benchmark. Options: default, antilife, inverse, wp, oils, invertamaze, neonblobs, htree, fuzz, gnarl, custom.')
    p.add_argument('--modes', default='seq,parfor,simd,tasks', help='Comma-separated list of parallelization modes to test. Options: seq (sequential), parfor (OpenMP parallel for), simd (OpenMP parallel for simd), tasks (OpenMP parallel tasks).')
    p.add_argument('--compare', choices=['free','parallel','variants'], default='free',
                   help=("Comparison type: 'free' runs all selected combinations; 'parallel' compares modes within a single variant; "
                         "'variants' compares variants within a single mode."))
    p.add_argument('--blockrows', default='2', help='Comma-separated list of block row sizes for tasks mode (e.g., 2,16,32). Only used for --modes tasks.')
    p.add_argument('--width', type=int, default=WIDTH, help='Grid width for each run (default: 160).')
    p.add_argument('--height', type=int, default=HEIGHT, help='Grid height for each run (default: 96).')
    p.add_argument('--prob', type=float, default=PROB, help='Initial probability for a cell to be alive (default: 0.25).')
    p.add_argument('--repeats', type=int, default=REPEATS, help='Number of times to repeat each benchmark for averaging (default: 3).')
    p.add_argument('--steps', default=','.join(str(x) for x in STEPS_LIST), help='Comma-separated list of step counts to benchmark (default: 500,1000,1500,2000,3000,4000).')
    p.add_argument('--threads', type=int, default=None, help='Number of OpenMP threads to use (default: use OpenMP default).')
    p.add_argument('--build-dir', default=str(BUILD_DIR), help='Path to the build directory containing executables (default: build).')
    p.add_argument('--csv', default=CSV_FILE, help='Path to save benchmark results as CSV (default: results.csv).')
    p.add_argument('--plot', default=PLOT_FILE_TOTAL, help='Path to save the output plot as PNG (default: steps_vs_time.png).')
    p.add_argument('--rule', default=None, help='Rulestring for customLife variant (e.g., B36/S23). If provided, passed to all runs.')
    return p.parse_args()

def main():
    args = parse_args()
    build_dir = Path(args.build_dir)
    if not build_dir.exists():
        raise SystemExit(f'Missing build dir: {build_dir}. Build first.')

    # Normalize selections
    variants = [v.strip().lower() for v in args.variants.split(',') if v.strip()]
    modes = [m.strip().lower() for m in args.modes.split(',') if m.strip()]
    steps_list = [int(x) for x in args.steps.split(',') if x.strip()]
    blockrows_list = [int(x) for x in args.blockrows.split(',') if x.strip()]

    # Determine compare type and auto-expand variants for 'variants' comparison when not explicitly provided
    compare_type = args.compare
    if compare_type == 'variants' and args.variants == 'default':
        # Auto-compare all variants under the selected mode; include 'custom' only if a rule is provided
        if args.rule:
            variants = list(VARIANT_DIR.keys())
        else:
            variants = [k for k in VARIANT_DIR.keys() if k != 'custom']

    # Validate keys
    for v in variants:
        if v not in VARIANT_DIR:
            raise SystemExit(f'Unknown variant: {v}. Choose from: {", ".join(VARIANT_DIR.keys())}')
    for m in modes:
        if m not in MODE_SUFFIX:
            raise SystemExit(f'Unknown mode: {m}. Choose from: {", ".join(MODE_SUFFIX.keys())}')

    # Validate compare type constraints
    if compare_type == 'parallel' and len(variants) != 1:
        raise SystemExit("'compare=parallel' requires exactly one variant (use --variants <one>)")
    if compare_type == 'variants' and len(modes) != 1:
        raise SystemExit("'compare=variants' requires exactly one mode (use --modes <one>)")

    series = []
    csv_rows = [] 

    print(f'Benchmark: {args.width}x{args.height}, prob={args.prob}, repeats={args.repeats}, threads={args.threads}, compare={compare_type}')

    for v in variants:
        for m in modes:
            if m == 'tasks':
                for br in blockrows_list:
                    exe = exe_path(v, m).with_suffix('')
                    if compare_type == 'parallel':
                        label = f'{MODE_SUFFIX[m]} (blockrows={br})'
                    elif compare_type == 'variants':
                        label = f'{VARIANT_DIR[v]} (blockrows={br})'
                    else:
                        label = f'{VARIANT_DIR[v]} {MODE_SUFFIX[m]} (blockrows={br})'
                    extra = ['--blockrows', str(br)]
                    if args.rule:
                        extra += ['--rule', args.rule]
                    result = run_series(label, exe, steps_list, args.repeats, args.width, args.height, args.prob, args.threads, extra_args=extra)
                    if result:
                        series.append(result)
                        for x, y, e in zip(result['x'], result['y'], result['e']):
                            csv_rows.append([VARIANT_DIR[v], MODE_SUFFIX[m], br, x, y, e, exe.name])
            else:
                exe = exe_path(v, m).with_suffix('')
                if compare_type == 'parallel':
                    label = f'{MODE_SUFFIX[m]}'
                elif compare_type == 'variants':
                    label = f'{VARIANT_DIR[v]}'
                else:
                    label = f'{VARIANT_DIR[v]} {MODE_SUFFIX[m]}'
                extra = []
                if args.rule:
                    extra += ['--rule', args.rule]
                result = run_series(label, exe, steps_list, args.repeats, args.width, args.height, args.prob, args.threads, extra_args=extra)
                if result:
                    series.append(result)
                    for x, y, e in zip(result['x'], result['y'], result['e']):
                        csv_rows.append([VARIANT_DIR[v], MODE_SUFFIX[m], '', x, y, e, exe.name])

    # Save CSV
    if csv_rows:
        with open(args.csv, 'w', newline='') as f:
            w = csv.writer(f)
            w.writerow(['variant', 'mode', 'blockrows', 'steps', 'mean_ms', 'sd_ms', 'exe'])
            w.writerows(csv_rows)
        print(f'Saved CSV -> {args.csv}')
    else:
        print('No data collected; CSV not written.')

    # Plot
    try:
        import matplotlib.pyplot as plt
    except ImportError:
        print('matplotlib not installed; skipping plot.')
        return

    if not series:
        print('No series to plot.')
        return

    import itertools
    plt.figure(figsize=(7,4.5))
    styles = ['o-', 's--', '^-.', 'v:', 'd-', 'x--', 'p-.', 'h:']
    color_cycle = itertools.cycle(['C0','C1','C2','C3','C4','C5','C6','C7','C8','C9'])
    for i, s in enumerate(series):
        fmt = styles[i % len(styles)]
        color = next(color_cycle)
        plt.errorbar(s['x'], s['y'], yerr=s['e'], fmt=fmt, color=color, capsize=4, label=s['label'])

    plt.xlabel('Steps')
    plt.ylabel('Total time (ms)')
    title = f'Total time vs Steps ({args.width}x{args.height}, prob={args.prob})'
    if compare_type == 'parallel':
        title += f' [parallel: {VARIANT_DIR[variants[0]]}]'
    elif compare_type == 'variants':
        title += f' [variants: {MODE_SUFFIX[modes[0]]}]'
    if args.threads:
        title += f' [threads={args.threads}]'
    plt.title(title)
    plt.grid(True, alpha=0.3)
    plt.legend(fontsize='small', ncol=2)
    plt.tight_layout()
    plt.savefig(args.plot, dpi=140)
    print(f'Saved plot -> {args.plot}')

if __name__ == '__main__':
    main()
