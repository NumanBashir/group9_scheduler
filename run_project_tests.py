#!/usr/bin/env python3
"""
Comprehensive test runner for Mini Project 1.

This script runs the full analysis on task sets across all utilization levels
and generates the comparison report required by the project.
"""

import sys
import os
import json
import csv
from pathlib import Path
from datetime import datetime

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.core.models import TaskSet
from src.core.analysis import ResponseTimeAnalyzer, EDFAnalyzer
from src.core.simulator import SimulationRunner
from src.utils.parser import TaskSetParser


class ProjectTestRunner:
    """Test runner for Mini Project 1 requirements."""
    
    def __init__(self, base_dir="data/task-sets/output", output_dir="test_results"):
        self.base_dir = Path(base_dir)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        self.results = []
        
    def get_task_sets_by_utilization(self):
        """Get all task sets organized by utilization level."""
        util_levels = ['0.10', '0.20', '0.30', '0.40', '0.50', 
                      '0.60', '0.70', '0.80', '0.90', '1.00']
        
        by_util = {}
        
        for util in util_levels:
            by_util[util] = {
                'automotive': [],
                'uunifast': []
            }
            
            # Find automotive task sets
            auto_path = self.base_dir / f"automotive-utilDist/*/*/*/*/{util}-util/tasksets/*.csv"
            for csv_file in self.base_dir.rglob(f"*{util}-util*/tasksets/*.csv"):
                if 'automotive' in str(csv_file):
                    by_util[util]['automotive'].append(csv_file)
                elif 'uunifast' in str(csv_file):
                    by_util[util]['uunifast'].append(csv_file)
        
        return by_util
    
    def analyze_task_set(self, csv_file, run_simulation=True):
        """Analyze a single task set."""
        try:
            taskset = TaskSetParser.parse_file(str(csv_file))
            if not taskset:
                return None
            
            result = {
                'file': str(csv_file),
                'name': taskset.name,
                'utilization': taskset.total_utilization,
                'num_tasks': taskset.num_tasks
            }
            
            # 1. DM Analysis (Response Time Analysis)
            dm_results = ResponseTimeAnalyzer.analyze_taskset_dm(taskset)
            dm_schedulable = all(r.schedulable for r in dm_results)
            
            result['dm'] = {
                'schedulable': dm_schedulable,
                'wcrt_by_task': {r.task_id: r.wcrt for r in dm_results},
                'tasks_schedulable': sum(1 for r in dm_results if r.schedulable),
                'total_tasks': len(dm_results)
            }
            
            # 2. EDF Analysis (Processor Demand)
            edf_result = EDFAnalyzer.analyze_taskset(taskset)
            result['edf'] = {
                'schedulable': edf_result['schedulable'],
                'utilization': edf_result['utilization']
            }
            
            # 3. Simulation (if requested)
            if run_simulation:
                runner = SimulationRunner(taskset, duration=50000, num_runs=3)
                
                # RM Simulation
                rm_sim = runner.run_rm()
                rm_misses = sum(s['misses'] for s in rm_sim.values())
                
                # EDF Simulation
                edf_sim = runner.run_edf()
                edf_misses = sum(s['misses'] for s in edf_sim.values())
                
                result['simulation'] = {
                    'rm_misses': rm_misses,
                    'edf_misses': edf_misses,
                    'rm_max_rt': {tid: s['max_rt'] for tid, s in rm_sim.items()},
                    'edf_max_rt': {tid: s['max_rt'] for tid, s in edf_sim.items()}
                }
            
            return result
            
        except Exception as e:
            print(f"  Error analyzing {csv_file}: {e}")
            return None
    
    def run_tests(self, sample_size=10, run_simulation=False):
        """Run tests on task sets across all utilization levels."""
        print("="*80)
        print("MINI PROJECT 1 - COMPREHENSIVE TEST RUNNER")
        print("="*80)
        print(f"\nConfiguration:")
        print(f"  Sample size per level: {sample_size}")
        print(f"  Run simulation: {run_simulation}")
        print(f"  Output directory: {self.output_dir}")
        print()
        
        by_util = self.get_task_sets_by_utilization()
        
        total_tasksets = 0
        for util, dists in by_util.items():
            count = len(dists['automotive']) + len(dists['uunifast'])
            total_tasksets += count
        
        print(f"Found {total_tasksets} total task sets")
        print(f"Will sample {sample_size} per utilization level (where available)")
        print()
        
        all_results = []
        
        for util in sorted(by_util.keys()):
            print(f"\n{'='*80}")
            print(f"Testing Utilization Level: {util}")
            print(f"{'='*80}")
            
            util_results = {
                'utilization': util,
                'automotive': [],
                'uunifast': []
            }
            
            # Test automotive
            auto_files = by_util[util]['automotive'][:sample_size]
            print(f"\n  Automotive distribution: {len(auto_files)} task sets")
            for i, csv_file in enumerate(auto_files, 1):
                print(f"    [{i}/{len(auto_files)}] {csv_file.name}...", end=' ', flush=True)
                result = self.analyze_task_set(csv_file, run_simulation)
                if result:
                    result['distribution'] = 'automotive'
                    util_results['automotive'].append(result)
                    dm_status = "✓" if result['dm']['schedulable'] else "✗"
                    edf_status = "✓" if result['edf']['schedulable'] else "✗"
                    print(f"DM:{dm_status} EDF:{edf_status}")
                else:
                    print("FAILED")
            
            # Test uunifast
            uuni_files = by_util[util]['uunifast'][:sample_size]
            print(f"\n  UUnifast distribution: {len(uuni_files)} task sets")
            for i, csv_file in enumerate(uuni_files, 1):
                print(f"    [{i}/{len(uuni_files)}] {csv_file.name}...", end=' ', flush=True)
                result = self.analyze_task_set(csv_file, run_simulation)
                if result:
                    result['distribution'] = 'uunifast'
                    util_results['uunifast'].append(result)
                    dm_status = "✓" if result['dm']['schedulable'] else "✗"
                    edf_status = "✓" if result['edf']['schedulable'] else "✗"
                    print(f"DM:{dm_status} EDF:{edf_status}")
                else:
                    print("FAILED")
            
            all_results.append(util_results)
        
        self.results = all_results
        return all_results
    
    def generate_report(self):
        """Generate comprehensive report."""
        if not self.results:
            print("No results to report. Run tests first.")
            return
        
        print("\n" + "="*80)
        print("GENERATING REPORTS")
        print("="*80)
        
        # 1. JSON results
        json_file = self.output_dir / "test_results.json"
        with open(json_file, 'w') as f:
            json.dump(self.results, f, indent=2, default=str)
        print(f"\n✓ JSON results: {json_file}")
        
        # 2. Markdown report
        md_file = self.output_dir / "test_report.md"
        with open(md_file, 'w') as f:
            f.write("# Mini Project 1 - Test Results\n\n")
            f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            
            # Summary table
            f.write("## Schedulability by Utilization Level\n\n")
            f.write("| Utilization | DM Auto % | EDF Auto % | DM UUni % | EDF UUni % |\n")
            f.write("|-------------|-----------|------------|-----------|------------|\n")
            
            for util_data in self.results:
                util = util_data['utilization']
                
                # Automotive
                auto_dm = sum(1 for r in util_data['automotive'] if r['dm']['schedulable'])
                auto_edf = sum(1 for r in util_data['automotive'] if r['edf']['schedulable'])
                auto_total = len(util_data['automotive'])
                
                # UUnifast
                uuni_dm = sum(1 for r in util_data['uunifast'] if r['dm']['schedulable'])
                uuni_edf = sum(1 for r in util_data['uunifast'] if r['edf']['schedulable'])
                uuni_total = len(util_data['uunifast'])
                
                if auto_total > 0:
                    auto_dm_pct = auto_dm / auto_total * 100
                    auto_edf_pct = auto_edf / auto_total * 100
                else:
                    auto_dm_pct = auto_edf_pct = 0
                
                if uuni_total > 0:
                    uuni_dm_pct = uuni_dm / uuni_total * 100
                    uuni_edf_pct = uuni_edf / uuni_total * 100
                else:
                    uuni_dm_pct = uuni_edf_pct = 0
                
                f.write(f"| {util} | {auto_dm_pct:.1f}% | {auto_edf_pct:.1f}% | "
                       f"{uuni_dm_pct:.1f}% | {uuni_edf_pct:.1f}% |\n")
            
            f.write("\n## Key Findings\n\n")
            f.write("### DM vs EDF Comparison\n\n")
            
            total_dm_sched = sum(
                sum(1 for r in util_data['automotive'] if r['dm']['schedulable']) +
                sum(1 for r in util_data['uunifast'] if r['dm']['schedulable'])
                for util_data in self.results
            )
            
            total_edf_sched = sum(
                sum(1 for r in util_data['automotive'] if r['edf']['schedulable']) +
                sum(1 for r in util_data['uunifast'] if r['edf']['schedulable'])
                for util_data in self.results
            )
            
            total_tasksets = sum(
                len(util_data['automotive']) + len(util_data['uunifast'])
                for util_data in self.results
            )
            
            f.write(f"- Total task sets tested: {total_tasksets}\n")
            f.write(f"- DM schedulable: {total_dm_sched}/{total_tasksets} "
                   f"({total_dm_sched/total_tasksets*100:.1f}%)\n")
            f.write(f"- EDF schedulable: {total_edf_sched}/{total_tasksets} "
                   f"({total_edf_sched/total_tasksets*100:.1f}%)\n")
            f.write(f"- EDF advantage: {(total_edf_sched - total_dm_sched)} more task sets\n")
            
            f.write("\n### Analysis vs Simulation\n\n")
            f.write("(See JSON file for detailed simulation results)\n")
            
            f.write("\n## Methodology\n\n")
            f.write("### Response Time Analysis (DM)\n")
            f.write("- Algorithm: Fixed-point iteration (Buttazzo Eq 4.24)\n")
            f.write("- Priority: Deadline Monotonic (shorter deadline = higher priority)\n")
            f.write("- Schedulability: WCRT ≤ Deadline\n\n")
            
            f.write("### EDF Schedulability\n")
            f.write("- Algorithm: Processor Demand Approach (Buttazzo Section 4.6.1)\n")
            f.write("- Check: h(t) ≤ t for all critical instants\n")
            f.write("- Quick test: U ≤ 1.0 necessary but not sufficient\n\n")
            
            f.write("### Simulation\n")
            f.write("- Duration: 50,000 time units\n")
            f.write("- Runs: 3 per algorithm (RM and EDF)\n")
            f.write("- Execution time: Random between BCET and WCET\n")
        
        print(f"✓ Markdown report: {md_file}")
        
        # 3. CSV summary
        csv_file = self.output_dir / "test_summary.csv"
        with open(csv_file, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow([
                'Utilization', 'Distribution', 'TaskSet', 
                'DM_Schedulable', 'EDF_Schedulable',
                'Utilization_Value', 'Num_Tasks'
            ])
            
            for util_data in self.results:
                util = util_data['utilization']
                
                for result in util_data['automotive']:
                    writer.writerow([
                        util, 'automotive', result['name'],
                        result['dm']['schedulable'],
                        result['edf']['schedulable'],
                        result['utilization'],
                        result['num_tasks']
                    ])
                
                for result in util_data['uunifast']:
                    writer.writerow([
                        util, 'uunifast', result['name'],
                        result['dm']['schedulable'],
                        result['edf']['schedulable'],
                        result['utilization'],
                        result['num_tasks']
                    ])
        
        print(f"✓ CSV summary: {csv_file}")
        
        print("\n" + "="*80)
        print("REPORT GENERATION COMPLETE")
        print("="*80)
        print(f"\nResults saved to: {self.output_dir}/")
        print("\nFiles generated:")
        print(f"  - test_results.json (detailed results)")
        print(f"  - test_report.md (readable report)")
        print(f"  - test_summary.csv (data for plotting)")


def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Run Mini Project 1 tests on task sets'
    )
    parser.add_argument(
        '--sample', '-s',
        type=int,
        default=10,
        help='Number of task sets to sample per utilization level (default: 10)'
    )
    parser.add_argument(
        '--simulation', '-sim',
        action='store_true',
        help='Run simulations (slower but more comprehensive)'
    )
    parser.add_argument(
        '--output', '-o',
        type=str,
        default='test_results',
        help='Output directory (default: test_results)'
    )
    
    args = parser.parse_args()
    
    runner = ProjectTestRunner(output_dir=args.output)
    runner.run_tests(sample_size=args.sample, run_simulation=args.simulation)
    runner.generate_report()
    
    print("\n" + "="*80)
    print("DONE!")
    print("="*80)


if __name__ == "__main__":
    main()
