# Mini Project 1 - Test Results

Generated: 2026-02-13 12:34:19

## Schedulability by Utilization Level

| Utilization | DM Auto % | EDF Auto % | DM UUni % | EDF UUni % |
|-------------|-----------|------------|-----------|------------|
| 0.10 | 100.0% | 100.0% | 100.0% | 100.0% |
| 0.20 | 100.0% | 100.0% | 100.0% | 100.0% |
| 0.30 | 100.0% | 100.0% | 100.0% | 100.0% |
| 0.40 | 100.0% | 100.0% | 100.0% | 100.0% |
| 0.50 | 100.0% | 100.0% | 100.0% | 100.0% |
| 0.60 | 100.0% | 100.0% | 100.0% | 100.0% |
| 0.70 | 100.0% | 100.0% | 100.0% | 100.0% |
| 0.80 | 60.0% | 60.0% | 100.0% | 100.0% |
| 0.90 | 70.0% | 70.0% | 80.0% | 100.0% |
| 1.00 | 10.0% | 10.0% | 0.0% | 100.0% |

## Key Findings

### DM vs EDF Comparison

- Total task sets tested: 200
- DM schedulable: 172/200 (86.0%)
- EDF schedulable: 184/200 (92.0%)
- EDF advantage: 12 more task sets

### Analysis vs Simulation

(See JSON file for detailed simulation results)

## Methodology

### Response Time Analysis (DM)
- Algorithm: Fixed-point iteration (Buttazzo Eq 4.24)
- Priority: Deadline Monotonic (shorter deadline = higher priority)
- Schedulability: WCRT ≤ Deadline

### EDF Schedulability
- Algorithm: Processor Demand Approach (Buttazzo Section 4.6.1)
- Check: h(t) ≤ t for all critical instants
- Quick test: U ≤ 1.0 necessary but not sufficient

### Simulation
- Duration: 50,000 time units
- Runs: 3 per algorithm (RM and EDF)
- Execution time: Random between BCET and WCET
