# DM + EDF simulation

from __future__ import annotations
import heapq
import random
from dataclasses import dataclass

from .models import Task, Job


@dataclass
class TaskStats:
    jobs: int = 0
    missed: int = 0
    sum_rt: int = 0
    max_rt: int = 0

    def add(self, rt: int, missed: bool):
        self.jobs += 1
        self.sum_rt += rt
        self.max_rt = max(self.max_rt, rt)
        if missed:
            self.missed += 1

    def avg(self) -> float:
        return self.sum_rt / self.jobs if self.jobs else 0.0


@dataclass
class SimResult:
    policy: str
    horizon: int
    per_task: dict[str, TaskStats]
    total_missed: int


def _exec_time(task: Task, mode: str, rng: random.Random) -> int:
    if mode == "wcet":
        return task.wcet
    if mode == "random":
        lo = task.bcet_eff
        hi = task.wcet
        if lo > hi:
            lo = hi
        return rng.randint(lo, hi)
    raise ValueError(mode)


def _prio(job: Job, policy: str) -> tuple:
    if policy == "DM":
        t = job.task
        return (t.deadline, t.period, t.name, job.job_id)
    if policy == "EDF":
        t = job.task
        return (job.abs_deadline, t.deadline, t.name, job.job_id)
    raise ValueError(policy)


def simulate(tasks: list[Task], policy: str, horizon: int, mode: str = "wcet", seed: int = 1) -> SimResult:
    rng = random.Random(seed)
    stats = {t.name: TaskStats() for t in tasks}

    next_rel = {t.name: 0 for t in tasks}
    jid = {t.name: 0 for t in tasks}

    ready: list[tuple[tuple, int, Job]] = []
    current: Job | None = None
    now = 0

    def release(at: int):
        for t in tasks:
            if next_rel[t.name] == at:
                jid[t.name] += 1
                j = Job(
                    task=t,
                    job_id=jid[t.name],
                    release=at,
                    abs_deadline=at + t.deadline,
                    remaining=_exec_time(t, mode, rng),
                )
                heapq.heappush(ready, (_prio(j, policy), id(j), j))
                next_rel[t.name] += t.period

    def pick():
        nonlocal current
        if not ready:
            current = None
            return
        _, _, j = heapq.heappop(ready)
        current = j
        if current.start_time is None:
            current.start_time = now

    while now < horizon:
        release(now)

        if current is None:
            pick()
            if current is None:
                nxt = min(next_rel.values())
                if nxt >= horizon:
                    break
                now = nxt
                continue

        # preemption check
        if ready:
            best_pr, _, best_job = ready[0]
            cur_pr = _prio(current, policy)
            if best_pr < cur_pr:
                heapq.heappush(ready, (cur_pr, id(current), current))
                pick()

        # advance to next event (completion or next release)
        t_finish = now + current.remaining
        t_next_release = min(next_rel.values())
        nxt = min(t_finish, t_next_release, horizon)

        ran = nxt - now
        current.remaining -= ran
        now = nxt

        if current.remaining == 0:
            current.finish_time = now
            rt = current.finish_time - current.release
            missed = current.finish_time > current.abs_deadline
            stats[current.task.name].add(rt, missed)
            current = None

    total_missed = sum(s.missed for s in stats.values())
    return SimResult(policy, horizon, stats, total_missed)