# Real-Time Scheduling Analysis Tool

This tool analyzes and compares Rate Monotonic (RM), Deadline Monotonic (DM), and Earliest Deadline First (EDF) scheduling algorithms.

## Features

- **Response Time Analysis**: Calculate Worst-Case Response Times (WCRT) for Deadline Monotonic scheduling
- **EDF Schedulability Analysis**: Check schedulability using Processor Demand Approach
- **Discrete Event Simulation**: Simulate RM and EDF scheduling with random execution times
- **Comparison**: Compare analytical results with simulation results
- **Visualization**: Generate comparison plots and reports

## Project Structure

```
group9_scheduler/
├── main.py              # Main analysis and simulation script
├── run_all.py           # Batch runner for all task sets
├── plot_results.py      # Generate comparison plots
├── data/                # Task set CSV files
│   ├── taskset-0.csv
│   ├── taskset-1.csv
│   ├── taskset-2.csv
│   ├── taskset-3.csv
│   └── taskset-4.csv
└── results/             # Output directory
    ├── all_results.json
    ├── report.md
    └── *.png            # Comparison plots
```

## Usage

### 1. Analyze a Single Task Set

```bash
python main.py
```

This will analyze `data/taskset-0.csv` and print:
- Utilization calculation
- DM WCRT analysis
- EDF schedulability check
- RM and EDF simulation results
- Comparison table

### 2. Analyze All Task Sets

```bash
python run_all.py
```

This processes all task sets in the `data/` directory and generates:
- `results/all_results.json` - Detailed results in JSON format
- `results/report.md` - Summary markdown report

### 3. Generate Plots

```bash
python plot_results.py
```

This generates comparison plots in `results/`:
- Individual plots for each task set showing DM WCRT vs simulation max
- Utilization analysis across all task sets

## Algorithms Implemented

### Response Time Analysis (DM)

Implements Equation 4.24 from Buttazzo (Section 4.5.2):

```
R_i = C_i + sum_{j in hp(i)} ceil(R_i / T_j) * C_j
```

Where:
- R_i = Response time of task i
- C_i = Worst-case execution time of task i
- T_j = Period of higher priority task j

### EDF Schedulability (Processor Demand)

Implements Processor Demand Approach from Buttazzo (Section 4.6.1):

```
h(t) = sum_{i} max(0, floor((t - D_i) / T_i) + 1) * C_i
```

System is schedulable if h(t) ≤ t for all critical instants.

### Simulation

Discrete event simulation:
- Jobs released periodically based on task periods
- Execution times randomly generated between BCET and WCET
- Priority-based scheduling (RM: period-based, EDF: deadline-based)
- Response times tracked for each job

## CSV Format

Task sets should be in CSV format with these columns:
- `Name`: Task identifier (e.g., "T0")
- `Jitter`: Release jitter (usually 0)
- `BCET`: Best-case execution time
- `WCET`: Worst-case execution time
- `Period`: Task period
- `Deadline`: Relative deadline
- `PE`: Processing element (ignored)

## Dependencies

```bash
pip install matplotlib
```

Only `matplotlib` is required for plotting. All other functionality uses standard library.

## Generating Task Sets

To generate new task sets, use the task generator:

```bash
cd real-time-task_generators
./task_generator.py --nset=5 --ntask=10 --utilization=60
```

This creates 5 task sets with 10 tasks each at 60% utilization.

## Output Examples

### Console Output (main.py)

```
================================================================================
ANALYTICAL ANALYSIS
================================================================================

Deadline Monotonic (DM) - WCRT Analysis:
  Task 0: WCRT = 13.00 (Deadline: 157) ✓
  Task 1: WCRT = 32.00 (Deadline: 246) ✓
  ...

Earliest Deadline First (EDF) - Processor Demand Analysis:
  Schedulable: True
  Utilization: 0.6001
```

### Comparison Table

| Task | DM WCRT | RM Sim Max | EDF Sim Max | Deadline |
|------|---------|------------|-------------|----------|
| 0    | 13.00   | 13.00      | 13.00       | 157      |
| 1    | 32.00   | 31.00      | 31.00       | 246      |

## Notes

- DM WCRT provides an upper bound on response times
- Simulation shows actual observed maximum response times
- EDF typically achieves better response times for low-priority tasks
- All task sets should be schedulable at 60% utilization

## References

- Giorgio Buttazzo, "Hard Real-Time Computing Systems", Chapter 4
- Course materials: 02225 Distributed Real-Time Systems
