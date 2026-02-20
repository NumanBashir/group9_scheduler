from __future__ import annotations
import argparse
import os

from src.discover import discover_csvs
from src.io import load_taskset
from src.analysis_dm import analyze_dm
from src.analysis_edf import analyze_edf_pdc
from src.simulator import simulate
from src.reporting import util, write_all_tasksets_csv, aggregate_by_bucket


def choose_horizon(tasks, periods_to_sim=3, cap=500_000):
    # Your periods are large (10k..90k etc) => hyperperiod is impossible.
    # Use a practical horizon: a few max periods.
    maxT = max(t.period for t in tasks)
    return min(periods_to_sim * maxT, cap)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", required=True, help="Root folder containing the taskset directories")
    ap.add_argument("--exec", dest="exec_mode", choices=["wcet", "random"], default="wcet")
    ap.add_argument("--seed", type=int, default=1)
    ap.add_argument("--periods", type=int, default=3, help="Sim horizon = periods * max_period")
    ap.add_argument("--cap", type=int, default=500_000, help="Max sim horizon cap")
    ap.add_argument("--Lmax", type=int, default=200_000, help="EDF PDC check bound (time units)")
    ap.add_argument("--out", default="results", help="Output folder")
    args = ap.parse_args()

    metas = discover_csvs(args.root)
    print(f"Discovered {len(metas)} CSV tasksets under {args.root}")

    rows = []
    for idx, meta in enumerate(metas, 1):
        tasks = load_taskset(meta.path)
        U = util(tasks)

        dm = analyze_dm(tasks)
        edf = analyze_edf_pdc(tasks, L_max=args.Lmax)

        horizon = choose_horizon(tasks, periods_to_sim=args.periods, cap=args.cap)
        sim_dm = simulate(tasks, "DM", horizon=horizon, mode=args.exec_mode, seed=args.seed)
        sim_edf = simulate(tasks, "EDF", horizon=horizon, mode=args.exec_mode, seed=args.seed)

        row = {
            "path": meta.path,
            "distribution": meta.distribution,
            "family": meta.family,
            "util_bucket": meta.util_bucket,
            "n_tasks": len(tasks),
            "U_total": round(U, 6),
            "dm_schedulable": int(dm.schedulable),
            "edf_schedulable": int(edf.schedulable),
            "edf_checked_points": edf.checked_points,
            "edf_worst_violation": edf.worst_violation,
            "sim_horizon": horizon,
            "sim_dm_missed_total": sim_dm.total_missed,
            "sim_edf_missed_total": sim_edf.total_missed,
        }
        rows.append(row)

        if idx % 100 == 0:
            print(f"Processed {idx}/{len(metas)}...")

    all_path = os.path.join(args.out, "all_tasksets.csv")
    write_all_tasksets_csv(rows, all_path)
    print(f"Saved per-taskset summary: {all_path}")

    agg = aggregate_by_bucket(rows)
    agg_path = os.path.join(args.out, "aggregate_by_bucket.csv")
    write_all_tasksets_csv(agg, agg_path)
    print(f"Saved aggregated summary: {agg_path}")


if __name__ == "__main__":
    main()