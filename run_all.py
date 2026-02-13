#!/usr/bin/env python3
"""
Batch runner for all task sets.
Generates comprehensive comparison report.
"""

import sys
import json
from pathlib import Path

# Import from main.py
from main import load_taskset, analyze_dm, analyze_edf, simulate_rm, simulate_edf, calculate_utilization


def run_all_tasksets(data_dir="data", duration=100000):
    """Run analysis on all task sets in the data directory"""
    data_path = Path(data_dir)
    
    if not data_path.exists():
        print(f"Error: Directory {data_dir} not found")
        return
    
    # Find all CSV files
    taskset_files = sorted(data_path.glob("taskset-*.csv"))
    
    if not taskset_files:
        print(f"No taskset files found in {data_dir}")
        return
    
    print(f"Found {len(taskset_files)} task sets")
    print("="*80)
    
    all_results = {}
    
    for taskset_file in taskset_files:
        print(f"\nProcessing: {taskset_file.name}")
        print("-"*80)
        
        # Load task set
        tasks = load_taskset(str(taskset_file))
        if not tasks:
            print(f"  Failed to load {taskset_file.name}")
            continue
        
        # Calculate utilization
        util = calculate_utilization(tasks)
        print(f"  Tasks: {len(tasks)}, Utilization: {util:.4f}")
        
        # Run analysis
        dm_results = analyze_dm(tasks)
        edf_result = analyze_edf(tasks)
        
        # Check DM schedulability
        dm_schedulable = all(
            wcrt <= task.deadline 
            for task, wcrt in zip(tasks, dm_results.values())
        )
        
        print(f"  DM Schedulable: {dm_schedulable}")
        print(f"  EDF Schedulable: {edf_result['schedulable']}")
        
        # Run simulation
        rm_sim = simulate_rm(tasks, duration)
        edf_sim = simulate_edf(tasks, duration)
        
        # Check for misses
        rm_misses = sum(s['misses'] for s in rm_sim.values())
        edf_misses = sum(s['misses'] for s in edf_sim.values())
        
        print(f"  RM Simulation Misses: {rm_misses}")
        print(f"  EDF Simulation Misses: {edf_misses}")
        
        # Store results
        all_results[taskset_file.name] = {
            'utilization': util,
            'num_tasks': len(tasks),
            'dm_schedulable': dm_schedulable,
            'edf_schedulable': edf_result['schedulable'],
            'dm_wcrts': dm_results,
            'rm_sim_max': {tid: s['max_rt'] for tid, s in rm_sim.items()},
            'edf_sim_max': {tid: s['max_rt'] for tid, s in edf_sim.items()},
            'rm_misses': rm_misses,
            'edf_misses': edf_misses
        }
    
    # Save results to JSON
    results_file = Path("results/all_results.json")
    results_file.parent.mkdir(exist_ok=True)
    
    with open(results_file, 'w') as f:
        json.dump(all_results, f, indent=2)
    
    print(f"\n{'='*80}")
    print(f"Results saved to {results_file}")
    
    # Generate summary report
    generate_summary_report(all_results)
    
    return all_results


def generate_summary_report(results):
    """Generate a markdown summary report"""
    report_lines = [
        "# Mini Project 1 - Scheduling Analysis Report",
        "",
        "## Overview",
        f"- Number of task sets analyzed: {len(results)}",
        "",
        "## Summary by Task Set",
        "",
        "| Task Set | Utilization | DM Schedulable | EDF Schedulable | RM Misses | EDF Misses |",
        "|----------|-------------|----------------|-----------------|-----------|------------|"
    ]
    
    for taskset_name, data in results.items():
        report_lines.append(
            f"| {taskset_name} | {data['utilization']:.4f} | "
            f"{data['dm_schedulable']} | {data['edf_schedulable']} | "
            f"{data['rm_misses']} | {data['edf_misses']} |"
        )
    
    report_lines.extend([
        "",
        "## Key Findings",
        "",
        "### Deadline Monotonic (DM) Analysis",
        "- WCRT calculated using Response Time Analysis (RTA)",
        "- Task schedulable if WCRT ≤ Deadline",
        "",
        "### EDF Analysis", 
        "- Schedulability checked using Processor Demand Approach",
        "- If U ≤ 1.0 and no demand violations, system is schedulable",
        "",
        "### Simulation",
        "- Discrete event simulation for 100,000 time units",
        "- Execution times randomly generated between BCET and WCET",
        "- Multiple runs to capture statistical variance",
        "",
        "## Comparison",
        "- Analytical WCRT provides upper bound on response times",
        "- Simulation shows actual observed maximum response times",
        "- EDF typically achieves better response times than RM for low-priority tasks"
    ])
    
    # Save report
    report_file = Path("results/report.md")
    with open(report_file, 'w') as f:
        f.write('\n'.join(report_lines))
    
    print(f"Summary report saved to {report_file}")


if __name__ == "__main__":
    duration = int(sys.argv[1]) if len(sys.argv) > 1 else 100000
    run_all_tasksets(duration=duration)
