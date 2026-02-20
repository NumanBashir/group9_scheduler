from __future__ import annotations
import os
from dataclasses import dataclass


@dataclass(frozen=True)
class TasksetMeta:
    path: str
    distribution: str   # automotive-utilDist / uunifast-utilDist / unknown
    util_bucket: str    # "0.10", "0.20", ... "1.00" or "unknown"
    family: str         # e.g. "uniform-discrete" or "automotive-xxx"


def _infer_meta(path: str) -> TasksetMeta:
    norm = path.replace("\\", "/")
    parts = norm.split("/")

    distribution = "unknown"
    util_bucket = "unknown"
    family = "unknown"

    # distribution
    for p in parts:
        if p.endswith("automotive-utilDist"):
            distribution = "automotive-utilDist"
        if p.endswith("uunifast-utilDist"):
            distribution = "uunifast-utilDist"

    # util bucket folder like "0.10-util"
    for p in parts:
        if p.endswith("-util") and len(p) >= 8 and p[0].isdigit():
            util_bucket = p.split("-util")[0]  # "0.10"

    # family is the folder right after distribution if available
    if distribution in parts:
        idx = parts.index(distribution)
        if idx + 1 < len(parts):
            family = parts[idx + 1]

    return TasksetMeta(path=path, distribution=distribution, util_bucket=util_bucket, family=family)


def discover_csvs(root: str) -> list[TasksetMeta]:
    metas: list[TasksetMeta] = []
    for dirpath, _, filenames in os.walk(root):
        for fn in filenames:
            if fn.lower().endswith(".csv"):
                full = os.path.join(dirpath, fn)
                metas.append(_infer_meta(full))
    metas.sort(key=lambda m: (m.distribution, m.family, m.util_bucket, m.path))
    return metas