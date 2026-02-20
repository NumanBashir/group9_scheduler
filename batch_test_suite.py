
import os
import sys
import csv
from glob import glob
# Ensure parent directory is in sys.path for imports
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))
from main import load_taskset, edf_analysis, dm_analysis

# Directory containing all task set CSVs (update as needed)
BASE_DIR = r'c:/Users/Nicol/Downloads/task-sets (1)/output/automotive-utilDist/automotive-perDist/1-core/25-task/0-jitter/0.10-util/tasksets'

results = []
csv_files = glob(os.path.join(BASE_DIR, '*.csv'))

for csv_file in csv_files:
    tasks = load_taskset(csv_file)
    if not tasks:
        continue
    edf_sched, edf_wcrts = edf_analysis(tasks)
    dm_sched, dm_wcrts = dm_analysis(tasks)
    results.append({
        'file': os.path.basename(csv_file),
        'edf_schedulable': edf_sched,
        'dm_schedulable': dm_sched,
        'edf_wcrt': edf_wcrts,
        'dm_wcrt': dm_wcrts
    })

# Output summary

# Output summary
print("\n--- Batch Test Results ---")
for r in results:
    print(f"{r['file']}: EDF: {'YES' if r['edf_schedulable'] else 'NO'}, DM: {'YES' if r['dm_schedulable'] else 'NO'}")

# Draw logical conclusions
total = len(results)
edf_only = sum(1 for r in results if r['edf_schedulable'] and not r['dm_schedulable'])
dm_only = sum(1 for r in results if not r['edf_schedulable'] and r['dm_schedulable'])
both = sum(1 for r in results if r['edf_schedulable'] and r['dm_schedulable'])
neither = sum(1 for r in results if not r['edf_schedulable'] and not r['dm_schedulable'])

print("\n--- Batch Summary ---")
print(f"Total task sets analyzed: {total}")
print(f"Schedulable by BOTH EDF and DM: {both}")
print(f"Schedulable by ONLY EDF: {edf_only}")
print(f"Schedulable by ONLY DM: {dm_only}")
print(f"Schedulable by NEITHER: {neither}")

if edf_only > 0:
    print("\nConclusion: There are task sets schedulable by EDF but not by DM. This is expected, as EDF is optimal for uniprocessor scheduling with deadlines ≤ periods.")
if dm_only > 0:
    print("\nConclusion: There are task sets schedulable by DM but not by EDF. This is rare and may indicate a bug or special case.")
if both == total:
    print("\nConclusion: All task sets are schedulable by both algorithms. The system is lightly loaded or the task sets are easy.")
if neither == total:
    print("\nConclusion: No task sets are schedulable by either algorithm. The system is overloaded or the task sets are too demanding.")
