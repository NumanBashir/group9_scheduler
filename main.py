import csv
import math
from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class Task:
    name: str
    wcet: int       # C_i
    period: int     # T_i
    deadline: int   # D_i
    jitter: int     # J_i
    bcet: int = 0
    pe: int = 0     # Processor/core assignment

    def utilization(self) -> float:
        return self.wcet / self.period

    def __repr__(self):
        return (f"Task({self.name}, C={self.wcet}, T={self.period}, "
                f"D={self.deadline}, J={self.jitter}, PE={self.pe})")


def load_taskset(filepath: str) -> List[Task]:
    tasks = []
    try:
        with open(filepath, newline='') as f:
            reader = csv.DictReader(f)
            for row in reader:
                name = row.get('Name') or row.get('TaskID') or '?'
                period = int(row['Period'])
                tasks.append(Task(
                    name=str(name),
                    wcet=int(row.get('WCET') or row.get('C') or 0),
                    bcet=int(row.get('BCET') or 0),
                    period=period,
                    deadline=int(row.get('Deadline') or period),
                    jitter=int(row.get('Jitter') or 0),
                    pe=int(row.get('PE') or 0),
                ))
    except FileNotFoundError:
        print(f"Error: File not found: {filepath}")
    return tasks


def calculate_utilization(tasks: List[Task]) -> float:
    return sum(t.utilization() for t in tasks)


# ---------------------------------------------------------------------------
# EDF Analysis
# ---------------------------------------------------------------------------

def _edf_wcrt(task: Task, all_tasks: List[Task], max_iter: int = 1000) -> int:
    """
    EDF WCRT via busy-period analysis with jitter.
    Interference from task j on task i:
        ceil((R + J_j) / T_j) * C_j
    """
    R = task.wcet
    for _ in range(max_iter):
        interference = sum(
            math.ceil((R + t.jitter) / t.period) * t.wcet
            for t in all_tasks if t is not task
        )
        R_next = task.wcet + interference
        if R_next == R:
            return R
        if R_next > task.deadline:
            return R_next  # Infeasible — caller checks > deadline
        R = R_next
    return R  # Did not converge


def edf_analysis(tasks: List[Task]) -> tuple[bool, List[int]]:
    u = calculate_utilization(tasks)
    print("\n--- EDF Analysis ---")
    print(f"Utilization U = {u:.4f} ({u * 100:.2f}%)")

    if u > 1.0:
        print("NOT schedulable: U > 1.0 (necessary condition failed)")
        return False, []

    wcrts = [_edf_wcrt(t, tasks) for t in tasks]
    results = [(wcrt + t.jitter <= t.deadline, wcrt, t) for wcrt, t in zip(wcrts, tasks)]
    schedulable = all(ok for ok, _, _ in results)

    print(f"Schedulable (all WCRT + J <= D): {'YES' if schedulable else 'NO'}")
    print(f"{'Task':<8} {'WCRT':>8} {'Jitter':>8} {'WCRT+J':>8} {'Deadline':>10} {'OK':>4}")
    for ok, wcrt, t in results:
        total = wcrt + t.jitter
        print(f"  {t.name:<6} {wcrt:>8} {t.jitter:>8} {total:>8} {t.deadline:>10} {'✓' if ok else '✗':>4}")

    return schedulable, wcrts


# ---------------------------------------------------------------------------
# Deadline Monotonic (DM) Analysis
# ---------------------------------------------------------------------------

def _dm_wcrt(task: Task, hp_tasks: List[Task], max_iter: int = 1000) -> int:
    """
    DM WCRT with jitter for higher-priority tasks:
        ceil((R + J_hp) / T_hp) * C_hp
    """
    R = task.wcet
    for _ in range(max_iter):
        interference = sum(
            math.ceil((R + hp.jitter) / hp.period) * hp.wcet
            for hp in hp_tasks
        )
        R_next = task.wcet + interference
        if R_next == R:
            return R
        if R_next > task.deadline:
            return R_next  # Infeasible
        R = R_next
    return R


def dm_analysis(tasks: List[Task]) -> tuple[bool, List[int]]:
    sorted_tasks = sorted(tasks, key=lambda t: t.deadline)
    u = calculate_utilization(sorted_tasks)

    print("\n--- Deadline Monotonic (DM) Analysis ---")
    print(f"Utilization U = {u:.4f} ({u * 100:.2f}%)")

    wcrts = []
    for i, task in enumerate(sorted_tasks):
        hp = sorted_tasks[:i]
        wcrts.append(_dm_wcrt(task, hp))

    results = [(wcrt + t.jitter <= t.deadline, wcrt, t) for wcrt, t in zip(wcrts, sorted_tasks)]
    schedulable = all(ok for ok, _, _ in results)

    print(f"Schedulable (all WCRT + J <= D): {'YES' if schedulable else 'NO'}")
    print(f"{'Task':<8} {'Priority':>8} {'WCRT':>8} {'Jitter':>8} {'WCRT+J':>8} {'Deadline':>10} {'OK':>4}")
    for prio, (ok, wcrt, t) in enumerate(results, start=1):
        total = wcrt + t.jitter
        print(f"  {t.name:<6} {prio:>8} {wcrt:>8} {t.jitter:>8} {total:>8} {t.deadline:>10} {'✓' if ok else '✗':>4}")

    return schedulable, wcrts


# ---------------------------------------------------------------------------
# Multi-core: group tasks by PE and analyse each core separately
# ---------------------------------------------------------------------------

def analyse_by_pe(tasks: List[Task]):
    pes: dict[int, List[Task]] = {}
    for t in tasks:
        pes.setdefault(t.pe, []).append(t)

    if len(pes) == 1:
        return  # Single core, already handled by caller

    print("\n=== Per-PE Analysis ===")
    for pe_id, pe_tasks in sorted(pes.items()):
        print(f"\n== PE {pe_id} ({len(pe_tasks)} tasks) ==")
        edf_analysis(pe_tasks)
        dm_analysis(pe_tasks)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import sys
    files = sys.argv[1:] or ["data/taskset-0.csv"]

    for filepath in files:
        print(f"\n{'='*60}")
        print(f"Loading: {filepath}")
        tasks = load_taskset(filepath)
        if not tasks:
            continue
        print(f"Loaded {len(tasks)} tasks.")

        edf_analysis(tasks)
        dm_analysis(tasks)
        analyse_by_pe(tasks)