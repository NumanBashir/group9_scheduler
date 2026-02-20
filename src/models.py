from __future__ import annotations
from dataclasses import dataclass


@dataclass(frozen=True)
class Task:
    name: str
    wcet: int
    period: int
    deadline: int
    bcet: int | None = None

    def __post_init__(self):
        if self.wcet < 0 or self.period <= 0 or self.deadline <= 0:
            raise ValueError(f"Invalid params in {self}")
        if self.deadline > self.period:
            # Mini-project 1 assumes D <= T
            raise ValueError(f"Task {self.name}: D>T (D={self.deadline}, T={self.period})")

    @property
    def bcet_eff(self) -> int:
        if self.bcet is None:
            return self.wcet
        return max(0, int(self.bcet))


@dataclass
class Job:
    task: Task
    job_id: int
    release: int
    abs_deadline: int
    remaining: int
    start_time: int | None = None
    finish_time: int | None = None

    def response_time(self) -> int | None:
        return None if self.finish_time is None else self.finish_time - self.release