#!/usr/bin/env python3
import subprocess, re, statistics, sys
from pathlib import Path

BUILD_DIR = Path('build')
EXEC_SEQ = BUILD_DIR / 'default_sequential'
EXEC_OMP_P = BUILD_DIR / 'default_openMP_parallel_for'
EXEC_OMP_P_SIMD = BUILD_DIR / 'default_openMP_parallel_for_simd'
EXEC_OMP_TASKS = BUILD_DIR / 'default_openMP_parallel_tasks'
EXEC_ANTI_LIFE_SEQ = BUILD_DIR / 'antiLife_sequential'
EXEC_ANTI_LIFE_P = BUILD_DIR / 'antiLife_parallel'

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
    d_seq = run_series('sequential', EXEC_SEQ)
    if d_seq: series.append(d_seq)

    d_parfor = run_series('OpenMP-parallel_for', EXEC_OMP_P)
    if d_parfor: series.append(d_parfor)
    d_parfor_simd = run_series('OpenMP-parallel_for_simd', EXEC_OMP_P_SIMD)
    if d_parfor_simd: series.append(d_parfor_simd)
    d_tasks_2 = run_series('OpenMP-tasks (blockrows=2)', EXEC_OMP_TASKS, extra_args=['--blockrows','2'])
    if d_tasks_2: series.append(d_tasks_2)
    
    antiLife_seq = run_series('Anti-Life sequential', EXEC_ANTI_LIFE_SEQ)
    if antiLife_seq: series.append(antiLife_seq)

    antiLife_parfor = run_series('Anti-Life OpenMP-parallel_for', EXEC_ANTI_LIFE_P)
    if antiLife_parfor: series.append(antiLife_parfor)

    # d_tasks_4 = run_series('OpenMP-tasks (blockrows=4)', EXEC_OMP_TASKS, extra_args=['--blockrows','4'])
    # if d_tasks_4: series.append(d_tasks_4)

    # d_tasks_8 = run_series('OpenMP-tasks (blockrows=8)', EXEC_OMP_TASKS, extra_args=['--blockrows','8'])
    # if d_tasks_8: series.append(d_tasks_8)

    # d_tasks_16 = run_series('OpenMP-tasks (blockrows=16)', EXEC_OMP_TASKS, extra_args=['--blockrows','16'])
    # if d_tasks_16: series.append(d_tasks_16)

    # d_tasks_32 = run_series('OpenMP-tasks (blockrows=32)', EXEC_OMP_TASKS, extra_args=['--blockrows','32'])
    # if d_tasks_32: series.append(d_tasks_32)

    # d_tasks_64 = run_series('OpenMP-tasks (blockrows=64)', EXEC_OMP_TASKS, extra_args=['--blockrows','64'])
    # if d_tasks_64: series.append(d_tasks_64)

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
