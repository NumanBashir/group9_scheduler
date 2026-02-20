from __future__ import annotations
import argparse
import os

from src.discover import discover_csvs
from src.io import load_taskset
from src.analysis_dm import analyze_dm
from src.analysis_edf import analyze_edf_pdc
from src.simulator import simulate
from src.reporting import util, write_all_tasksets_csv, aggregate_by_bucket


def choose_horizon(tasks, periods_to_sim: int, cap: int):
    maxT = max(t.period for t in tasks)
    return min(periods_to_sim * maxT, cap)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", required=True, help="Root folder containing the taskset directories")
    ap.add_argument("--exec", dest="exec_mode", choices=["wcet", "random"], default="wcet")
    ap.add_argument("--seed", type=int, default=1)
    # ap.add_argument("--periods", type=int, default=3, help="Sim horizon = periods * max_period")
    # ap.add_argument("--cap", type=int, default=500_000, help="Max sim horizon cap")
    ap.add_argument("--periods", type=int, default=10, help="Sim horizon = periods * max_period")
    ap.add_argument("--cap", type=int, default=2_000_000, help="Max sim horizon cap")
    
    # ap.add_argument("--Lmax", type=int, default=200_000, help="EDF PDC check bound (time units)")
    ap.add_argument("--Lmax", type=int, default=0, help="0 = auto (20*maxT capped)")
    ap.add_argument("--out", default="results", help="Output folder")
    ap.add_argument("--limit", type=int, default=0, help="Process only first N tasksets (0 = no limit)")
    args = ap.parse_args()

    metas = discover_csvs(args.root)
    print(f"Discovered {len(metas)} CSV tasksets under {args.root}")
    if args.limit and args.limit > 0:
        metas = metas[:args.limit]
        print(f"Limiting run to first {len(metas)} tasksets")

    rows = []
    for idx, meta in enumerate(metas, 1):
        tasks = load_taskset(meta.path)
        U = util(tasks)

        overloaded = U > 1.0  # Fix 3: basic feasibility sanity

        dm = analyze_dm(tasks)

        maxT = max(t.period for t in tasks)
        auto_Lmax = min(20 * maxT, 2_000_000)
        Lmax = args.Lmax if args.Lmax and args.Lmax > 0 else auto_Lmax
        edf = analyze_edf_pdc(tasks, L_max=Lmax)

        horizon = choose_horizon(tasks, periods_to_sim=args.periods, cap=args.cap)
        sim_dm = simulate(tasks, "DM", horizon=horizon, mode=args.exec_mode, seed=args.seed)
        sim_edf = simulate(tasks, "EDF", horizon=horizon, mode=args.exec_mode, seed=args.seed)

        dm_sched = int(dm.schedulable and not overloaded)
        edf_sched = int(edf.schedulable and not overloaded)

        row = {
            "path": meta.path,
            "distribution": meta.distribution,
            "family": meta.family,
            "util_bucket": meta.util_bucket,
            "n_tasks": len(tasks),
            "U_total": round(U, 6),
            "overloaded": int(overloaded),
            "dm_schedulable": dm_sched,
            "edf_schedulable": edf_sched,
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