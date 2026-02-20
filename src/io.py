from __future__ import annotations
import csv

from .models import Task


def _get_any(row: dict, keys: list[str]) -> str | None:
    for k in keys:
        if k in row and str(row[k]).strip() != "":
            return str(row[k]).strip()
    return None


def _to_int(x: str) -> int:
    return int(float(x))


def load_taskset(path: str) -> list[Task]:
    with open(path, "r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        if not reader.fieldnames:
            raise ValueError(f"No header found in {path}")

        tasks: list[Task] = []
        for row in reader:
            # Name: either Name, task_name, or TaskID
            name = _get_any(row, ["Name", "name", "task_name", "Task", "task"])
            if name is None:
                tid = _get_any(row, ["TaskID", "taskid", "id", "ID"])
                if tid is None:
                    raise ValueError(f"Cannot find Name/TaskID in row: {row}")
                name = f"T{_to_int(tid)}"

            # Period / Deadline
            period_s = _get_any(row, ["Period", "period", "T"])
            deadline_s = _get_any(row, ["Deadline", "deadline", "D"])
            if period_s is None or deadline_s is None:
                raise ValueError(f"Missing Period/Deadline in {path}. Row={row}")

            # WCET / BCET (uunifast)
            wcet_s = _get_any(row, ["WCET", "wcet", "C"])
            bcet_s = _get_any(row, ["BCET", "bcet"])

            if wcet_s is None:
                raise ValueError(f"Missing WCET in {path}. Row={row}")

            period = _to_int(period_s)
            deadline = _to_int(deadline_s)
            wcet = _to_int(wcet_s)
            bcet = _to_int(bcet_s) if bcet_s is not None else None

            tasks.append(Task(name=name, wcet=wcet, period=period, deadline=deadline, bcet=bcet))

        if not tasks:
            raise ValueError(f"No tasks found in {path}")
        return tasks