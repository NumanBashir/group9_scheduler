# DM WCRT via RTA

from __future__ import annotations
import math
from dataclasses import dataclass
from .models import Task


@dataclass
class DMResult:
    schedulable: bool
    wcrt: dict[str, int]
    order: list[str]


def dm_order(tasks: list[Task]) -> list[Task]:
    # Deadline Monotonic: smaller D => higher priority
    return sorted(tasks, key=lambda t: (t.deadline, t.period, t.name))


def analyze_dm(tasks: list[Task]) -> DMResult:
    ordered = dm_order(tasks)
    wcrt: dict[str, int] = {}
    sched = True

    for i, ti in enumerate(ordered):
        hp = ordered[:i]
        R = ti.wcet
        while True:
            interference = 0
            for th in hp:
                interference += math.ceil(R / th.period) * th.wcet
            R_next = ti.wcet + interference

            if R_next == R:
                break
            if R_next > ti.deadline:
                # can stop early – already not schedulable
                R = R_next
                break
            R = R_next

        wcrt[ti.name] = R
        if R > ti.deadline:
            sched = False

    return DMResult(schedulable=sched, wcrt=wcrt, order=[t.name for t in ordered])