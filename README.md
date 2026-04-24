# group9_scheduler

Tool for Mini-project 1 in `02225 Distributed Real-Time Systems`.

This program analyzes and simulates constrained-deadline periodic real-time task sets on a single core using:

- Deadline Monotonic (DM) analytical response-time analysis
- Earliest Deadline First (EDF) analytical processor-demand feasibility analysis
- Preemptive single-core simulation in `wcet` and `random` execution-time modes

The code matches the following model assumptions:

- single-core execution
- independent periodic tasks
- constrained deadlines (`D <= T`)
- fully preemptive scheduling
- zero release jitter

## Requirements

- Python 3.10+ recommended
- No external Python packages are required

## How To Run

Change into the project folder:

```bash
cd group9_scheduler
```

Run the tool on the provided benchmark archive:

```bash
python3 main.py --root data/output --exec wcet
```

This performs:

- DM analytical analysis
- EDF demand-bound schedulability analysis
- Simulation where every job executes for its WCET
- CSV export of per-taskset, per-task, and aggregated results

Run the random execution-time simulation:

```bash
python3 main.py --root data/output --exec random --seed 123
```

This uses the same task sets, but each job execution time is sampled uniformly between BCET and WCET.

## Useful Options

Main entry point:

```bash
python3 main.py --root <taskset_root> [options]
```

Important options:

- `--root`: root directory containing the task-set CSV files
- `--exec {wcet,random}`: execution-time mode
- `--seed`: random seed used in `random` mode
- `--periods`: simulation horizon multiplier, default `10`
- `--cap`: upper bound on simulation horizon, default `2000000`
- `--Lmax`: EDF processor-demand check bound, default `0` meaning auto
- `--out`: output directory, default `results`
- `--limit`: process only the first `N` task sets, useful for quick tests

Example quick test:

```bash
python3 main.py --root data/output --exec wcet --limit 10 --out tmp_results
```

To reproduce the report-style outputs in separate folders:

```bash
python3 main.py --root data/output --exec wcet --out results_wcet
python3 main.py --root data/output --exec random --seed 123 --out results_random
```

## Input Format

The tool expects CSV task sets. It accepts common column names used in the provided archive, including:

- task identifier: `TaskID` or `Name`
- period: `Period`
- deadline: `Deadline`
- worst-case execution time: `WCET`
- optional best-case execution time: `BCET`

## Output Files

Each run writes three CSV files in the selected output folder:

- `all_tasksets.csv`: one row per task set
- `per_task_response_times.csv`: one row per task with DM analytical WCRT and simulated response-time statistics
- `aggregate_by_bucket.csv`: results aggregated by distribution, family, and utilization bucket

Main output columns include:

- total utilization
- DM schedulability result
- EDF schedulability result
- EDF checked points / worst violation
- simulation horizon
- maximum DM analytical WCRT per task set
- maximum simulated response time per task set for DM and EDF
- number of tasks whose simulated DM maximum response time exceeded the DM analytical WCRT
- total missed deadlines in DM simulation
- total missed deadlines in EDF simulation

`per_task_response_times.csv` is the main validation file for comparing:

- DM analytical WCRT vs. maximum response time observed in DM simulation
- per-task response-time statistics across DM and EDF
- missed deadlines per task under both schedulers

## Contents Of The Archive

This folder contains:

- `main.py`: command-line entry point
- `src/`: implementation code
- `data/`: sample task sets and the provided benchmark archive
- `results_wcet/`: saved WCET-mode results used in the report
- `results_random/`: saved random-mode results used in the report
- `results/`: default result folder from a previous run
- `commands.txt`: short command notes used during development

Important source files in `src/`:

- `analysis_dm.py`: DM response-time analysis
- `analysis_edf.py`: EDF processor-demand schedulability analysis
- `simulator.py`: preemptive discrete-event simulator
- `io.py`: CSV loading
- `discover.py`: recursive task-set discovery and metadata extraction
- `reporting.py`: CSV result export and aggregation
- `models.py`: task and job data models

## Notes

- The EDF implementation checks feasibility with a demand-bound function test. It does not compute per-task EDF analytical WCRTs.
- If the report describes EDF WCRT construction from a synchronous hyperperiod schedule, that text should be updated to match the code, or the code should be extended accordingly.
- `results_wcet/` and `results_random/` are included so the report results can be reproduced or inspected directly.
- For large task sets, simulating a full hyperperiod may be impractical, so the simulator uses a bounded horizon controlled by `--periods` and `--cap`.
- If you rerun the tool with the default `--out results`, existing files in that folder will be overwritten.

## Final Hand-In Checklist

For the final submission archive, this folder already contains the expected categories:

- code: `main.py` and `src/`
- input data: `data/`
- results: `results_wcet/`, `results_random/`, and `results/`
- README: this file

Recommended final ZIP contents:

- this `group9_scheduler/` folder
- the exact PDF report submitted separately in DTU Learn, if your group wants the archive to be fully self-contained
