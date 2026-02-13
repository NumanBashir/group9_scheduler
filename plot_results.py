#!/usr/bin/env python3
"""
Generate plots comparing analytical and simulation results.
"""

import json
from pathlib import Path
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('Agg')  # Non-interactive backend


def load_results(results_file="results/all_results.json"):
    """Load results from JSON file"""
    with open(results_file, 'r') as f:
        return json.load(f)


def plot_response_times(results, output_dir="results"):
    """Generate comparison plots for each task set"""
    output_path = Path(output_dir)
    output_path.mkdir(exist_ok=True)
    
    for taskset_name, data in results.items():
        task_ids = list(data['dm_wcrts'].keys())
        dm_wcrts = [data['dm_wcrts'][tid] for tid in task_ids]
        rm_max = [data['rm_sim_max'][tid] for tid in task_ids]
        edf_max = [data['edf_sim_max'][tid] for tid in task_ids]
        
        # Create bar chart
        fig, ax = plt.subplots(figsize=(12, 6))
        x = range(len(task_ids))
        width = 0.25
        
        ax.bar([i - width for i in x], dm_wcrts, width, 
               label='DM WCRT (Analytical)', alpha=0.8, color='#2ecc71')
        ax.bar(x, rm_max, width, 
               label='RM Max (Simulation)', alpha=0.8, color='#3498db')
        ax.bar([i + width for i in x], edf_max, width, 
               label='EDF Max (Simulation)', alpha=0.8, color='#e74c3c')
        
        ax.set_xlabel('Task ID')
        ax.set_ylabel('Response Time')
        ax.set_title(f'Response Time Comparison - {taskset_name}\n'
                    f'Utilization: {data["utilization"]:.4f}')
        ax.set_xticks(x)
        ax.set_xticklabels(task_ids)
        ax.legend()
        ax.grid(True, alpha=0.3, axis='y')
        
        # Save plot
        plot_file = output_path / f"{taskset_name.replace('.csv', '')}_comparison.png"
        plt.tight_layout()
        plt.savefig(plot_file, dpi=150, bbox_inches='tight')
        plt.close()
        
        print(f"  Saved: {plot_file}")


def plot_utilization_analysis(results, output_dir="results"):
    """Generate utilization analysis plot across all task sets"""
    output_path = Path(output_dir)
    
    tasksets = list(results.keys())
    utils = [results[ts]['utilization'] for ts in tasksets]
    dm_sched = [1 if results[ts]['dm_schedulable'] else 0 for ts in tasksets]
    edf_sched = [1 if results[ts]['edf_schedulable'] else 0 for ts in tasksets]
    
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))
    
    # Utilization plot
    x = range(len(tasksets))
    ax1.bar(x, utils, color='#3498db', alpha=0.7)
    ax1.axhline(y=1.0, color='r', linestyle='--', label='U = 1.0 (EDF bound)')
    ax1.set_xlabel('Task Set')
    ax1.set_ylabel('Utilization')
    ax1.set_title('Utilization by Task Set')
    ax1.set_xticks(x)
    ax1.set_xticklabels([ts.replace('.csv', '') for ts in tasksets], rotation=45)
    ax1.legend()
    ax1.grid(True, alpha=0.3, axis='y')
    
    # Schedulability plot
    width = 0.35
    ax2.bar([i - width/2 for i in x], dm_sched, width, 
            label='DM Schedulable', alpha=0.8, color='#2ecc71')
    ax2.bar([i + width/2 for i in x], edf_sched, width, 
            label='EDF Schedulable', alpha=0.8, color='#e74c3c')
    ax2.set_xlabel('Task Set')
    ax2.set_ylabel('Schedulable (1=Yes, 0=No)')
    ax2.set_title('Schedulability Analysis')
    ax2.set_xticks(x)
    ax2.set_xticklabels([ts.replace('.csv', '') for ts in tasksets], rotation=45)
    ax2.legend()
    ax2.set_ylim(-0.1, 1.1)
    ax2.grid(True, alpha=0.3, axis='y')
    
    plt.tight_layout()
    plot_file = output_path / "utilization_analysis.png"
    plt.savefig(plot_file, dpi=150, bbox_inches='tight')
    plt.close()
    
    print(f"  Saved: {plot_file}")


def generate_all_plots():
    """Generate all comparison plots"""
    print("Generating plots...")
    print("="*80)
    
    try:
        results = load_results()
        
        print("\n1. Response time comparisons per task set:")
        plot_response_times(results)
        
        print("\n2. Utilization and schedulability analysis:")
        plot_utilization_analysis(results)
        
        print("\n" + "="*80)
        print("All plots generated successfully!")
        print("Check the 'results/' directory for output files.")
        
    except FileNotFoundError:
        print("Error: results/all_results.json not found.")
        print("Run 'python run_all.py' first to generate results.")
    except Exception as e:
        print(f"Error generating plots: {e}")


if __name__ == "__main__":
    generate_all_plots()
