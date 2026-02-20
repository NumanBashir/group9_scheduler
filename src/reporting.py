from __future__ import annotations
import csv
import os
from dataclasses import dataclass
from collections import defaultdict

from .models import Task
from .analysis_dm import DMResult
from .analysis_edf import EDFResult
from .simulator import SimResult


def util(tasks: list[Task]) -> float:
    return sum(t.wcet / t.period for t in tasks)


def ensure_dir(p: str):
    os.makedirs(p, exist_ok=True)


def write_all_tasksets_csv(rows: list[dict], out_path: str):
    ensure_dir(os.path.dirname(out_path))
    if not rows:
        return
    fieldnames = list(rows[0].keys())
    with open(out_path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        w.writerows(rows)


def aggregate_by_bucket(rows: list[dict]) -> list[dict]:
    # group by distribution + family + util_bucket
    groups = defaultdict(list)
    for r in rows:
        key = (r["distribution"], r["family"], r["util_bucket"])
        groups[key].append(r)

    out = []
    for (dist, fam, ub), items in sorted(groups.items()):
        def avg(field):
            return sum(float(x[field]) for x in items) / len(items)

        out.append({
            "distribution": dist,
            "family": fam,
            "util_bucket": ub,
            "n_tasksets": len(items),
            "avg_U": round(avg("U_total"), 6),
            "pct_dm_sched": round(100 * avg("dm_schedulable"), 2),
            "pct_edf_sched": round(100 * avg("edf_schedulable"), 2),
            "avg_sim_dm_missed": round(avg("sim_dm_missed_total"), 3),
            "avg_sim_edf_missed": round(avg("sim_edf_missed_total"), 3),
        })
    return out