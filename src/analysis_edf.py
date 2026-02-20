# EDF PDC

from __future__ import annotations
from dataclasses import dataclass

from .models import Task


@dataclass
class EDFResult:
    schedulable: bool
    checked_points: int
    worst_violation: int
    worst_L: int | None


def dbf(task: Task, L: int) -> int:
    # Demand Bound Function for constrained deadlines
    # jobs with deadlines <= L
    if L < task.deadline:
        return 0
    n = (L - task.deadline) // task.period + 1
    return int(n) * task.wcet


def analyze_edf_pdc(tasks: list[Task], L_max: int = 200_000) -> EDFResult:
    # Candidate L values: all deadlines k*T + D up to L_max
    candidates: set[int] = set()
    for t in tasks:
        k = 0
        while True:
            L = k * t.period + t.deadline
            if L > L_max:
                break
            candidates.add(L)
            k += 1

    worst_violation = -10**18
    worst_L = None

    for L in sorted(candidates):
        demand = sum(dbf(t, L) for t in tasks)
        viol = demand - L
        if viol > worst_violation:
            worst_violation = viol
            worst_L = L
        if demand > L:
            return EDFResult(False, len(candidates), viol, L)

    return EDFResult(True, len(candidates), worst_violation, worst_L)