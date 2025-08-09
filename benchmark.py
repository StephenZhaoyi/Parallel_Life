#!/usr/bin/env python3
"""Simple benchmark: total time vs steps for a fixed size.

Runs sequential, OpenMP (if present), and tasks(blockrows=16/32 if present),
and saves a single plot steps_vs_time.png. Keep it minimal and robust.
"""
import subprocess, re, statistics, sys
from pathlib import Path

BUILD_DIR = Path('build')
EXEC_SEQ = BUILD_DIR / 'default_sequential'
EXEC_OMP_P = BUILD_DIR / 'default_openMP_parallel_for'
EXEC_OMP_TASKS = BUILD_DIR / 'default_openMP_parallel_tasks'
WIDTH = 160
HEIGHT = 96
PROB = 0.25
REPEATS = 3
STEPS_LIST = [500, 1000, 2000, 4000]
OMP_THREADS = None  # e.g., 8 to fix threads; None to use OpenMP default
PLOT_FILE_TOTAL = 'steps_vs_time.png'

TIME_RE = re.compile(r"time_ms=([0-9.]+)")

def run_once(exe: Path, steps: int, extra_args=None) -> float:
    cmd = [str(exe), '--no-draw', '--steps', str(steps), '--prob', str(PROB), '--width', str(WIDTH), '--height', str(HEIGHT)]
    if extra_args:
        cmd += list(extra_args)
    if exe.name in ('default_openMP_parallel_for', 'default_openMP_parallel_tasks') and OMP_THREADS is not None:
        cmd += ['--threads', str(OMP_THREADS)]
    proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if proc.returncode != 0:
        print(proc.stdout)
        print(proc.stderr, file=sys.stderr)
        raise SystemExit(f'Executable run failed: {exe}')
    m = TIME_RE.search(proc.stdout)
    if not m:
        raise SystemExit(f'Unexpected output from {exe}: {proc.stdout.strip()}')
    return float(m.group(1))

def run_series(label: str, exe: Path, extra_args=None):
    if not exe.exists():
        return None
    xs, ys, err = [], [], []
    for s in STEPS_LIST:
        vals = [run_once(exe, s, extra_args=extra_args) for _ in range(REPEATS)]
        xs.append(s)
        ys.append(statistics.mean(vals))
        err.append(statistics.pstdev(vals) if REPEATS > 1 else 0.0)
        print(f'{label}: steps={s} mean_ms={ys[-1]:.2f} sd={err[-1]:.2f}')
    return {'label': label, 'x': xs, 'y': ys, 'e': err}

def main():
    if not EXEC_SEQ.exists():
        raise SystemExit(f'Missing executable: {EXEC_SEQ}. Build first.')

    print(f'Benchmark: {WIDTH}x{HEIGHT}, prob={PROB}, repeats={REPEATS}')
    series = []
    s1 = run_series('sequential', EXEC_SEQ)
    if s1: series.append(s1)

    s2 = run_series('OpenMP-parallel_for', EXEC_OMP_P)
    if s2: series.append(s2)
    s3 = run_series('OpenMP-tasks (blockrows=2)', EXEC_OMP_TASKS, extra_args=['--blockrows','2'])
    if s3: series.append(s3)

    s4 = run_series('OpenMP-tasks (blockrows=4)', EXEC_OMP_TASKS, extra_args=['--blockrows','4'])
    if s4: series.append(s4)

    s5 = run_series('OpenMP-tasks (blockrows=8)', EXEC_OMP_TASKS, extra_args=['--blockrows','8'])
    if s5: series.append(s5)

    s6 = run_series('OpenMP-tasks (blockrows=16)', EXEC_OMP_TASKS, extra_args=['--blockrows','16'])
    if s6: series.append(s6)

    s7 = run_series('OpenMP-tasks (blockrows=32)', EXEC_OMP_TASKS, extra_args=['--blockrows','32'])
    if s7: series.append(s7)

    s8 = run_series('OpenMP-tasks (blockrows=64)', EXEC_OMP_TASKS, extra_args=['--blockrows','64'])
    if s8: series.append(s8)

    try:
        import matplotlib.pyplot as plt
    except ImportError:
        print('matplotlib not installed; skipping plot.')
        return

    plt.figure(figsize=(6,4))
    styles = ['o-', 's--', '^-.', 'v:']
    for i, s in enumerate(series):
        fmt = styles[i % len(styles)]
        plt.errorbar(s['x'], s['y'], yerr=s['e'], fmt=fmt, capsize=4, label=s['label'])

    plt.xlabel('Steps')
    plt.ylabel('Total time (ms)')
    title = f'Total time vs Steps ({WIDTH}x{HEIGHT})'
    if OMP_THREADS:
        title += f' [threads={OMP_THREADS}]'
    plt.title(title)
    plt.grid(True, alpha=0.3)
    plt.legend()
    plt.tight_layout()
    plt.savefig(PLOT_FILE_TOTAL, dpi=140)
    print(f'Saved plot -> {PLOT_FILE_TOTAL}')

if __name__ == '__main__':
    main()
