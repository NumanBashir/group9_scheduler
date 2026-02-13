import csv
import math
import random
from typing import List, Dict, Tuple
from collections import deque

# A simple class to hold task data makes the math easier later
class Task:
    def __init__(self, row):
        self.name = row['Name']
        self.wcet = int(row['WCET'])     # C_i
        self.bcet = int(row.get('BCET', row['WCET']))  # Best case
        self.period = int(row['Period']) # T_i
        self.deadline = int(row['Deadline']) # D_i
        self.jitter = int(row.get('Jitter', 0))
        self.id = int(self.name.replace('T', '')) # Turn 'T0' into 0
        
    def __repr__(self):
        return f"Task({self.name}, C={self.wcet}, T={self.period}, D={self.deadline})"
    
    def utilization(self):
        return self.wcet / self.period


class Job:
    """Represents a single job (instance) of a task"""
    def __init__(self, task_id: int, release_time: int, deadline: int, exec_time: int):
        self.task_id = task_id
        self.release_time = release_time
        self.deadline = deadline
        self.exec_time = exec_time
        self.remaining = exec_time
        self.completion_time = None
        
    @property
    def response_time(self):
        if self.completion_time:
            return self.completion_time - self.release_time
        return None
    
    @property
    def missed_deadline(self):
        if self.completion_time:
            return self.completion_time > self.deadline
        return False


def load_taskset(filepath):
    """Reads a CSV file and returns a list of Task objects."""
    tasks = []
    try:
        with open(filepath, 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                tasks.append(Task(row))
    except FileNotFoundError:
        print(f"Error: Could not find file {filepath}")
        return []
    return tasks


def calculate_utilization(tasks):
    """Calculates total utilization U = Sum(C/T)."""
    return sum(t.wcet / t.period for t in tasks)


# ============================================================================
# RESPONSE TIME ANALYSIS (Deadline Monotonic)
# ============================================================================

def calculate_response_time(task: Task, higher_priority_tasks: List[Task]) -> float:
    """
    Calculate Worst-Case Response Time using fixed-point iteration.
    
    Implements Equation 4.24 from Buttazzo:
    R_i = C_i + sum_{j in hp(i)} ceil(R_i / T_j) * C_j
    """
    # Initial guess: just the task's WCET
    r = task.wcet
    max_iterations = 1000
    
    for _ in range(max_iterations):
        # Calculate interference from higher priority tasks
        interference = sum(
            math.ceil(r / hp_task.period) * hp_task.wcet
            for hp_task in higher_priority_tasks
        )
        
        # New response time
        new_r = task.wcet + interference
        
        # Check for convergence
        if new_r == r:
            return r
        
        # Check if exceeds deadline (unschedulable)
        if new_r > task.deadline:
            return float('inf')
        
        r = new_r
    
    return float('inf')  # Did not converge


def analyze_dm(tasks: List[Task]) -> Dict[int, float]:
    """
    Analyze all tasks under Deadline Monotonic scheduling.
    Sorts by deadline (shortest deadline = highest priority).
    """
    # Sort by deadline for DM priority
    sorted_tasks = sorted(tasks, key=lambda t: t.deadline)
    
    results = {}
    for i, task in enumerate(sorted_tasks):
        # Higher priority tasks are those before current in sorted list
        wcrt = calculate_response_time(task, sorted_tasks[:i])
        results[task.id] = wcrt
    
    return results


# ============================================================================
# EDF SCHEDULABILITY ANALYSIS (Processor Demand)
# ============================================================================

def lcm(a, b):
    """Least Common Multiple"""
    return abs(a * b) // math.gcd(a, b)


def calculate_hyperperiod(tasks: List[Task]) -> int:
    """Calculate LCM of all periods"""
    hp = 1
    for task in tasks:
        hp = lcm(hp, task.period)
    return hp


def processor_demand(t: int, tasks: List[Task]) -> float:
    """
    Calculate processor demand h(t) at time t under EDF.
    h(t) = sum_{i} max(0, floor((t - D_i) / T_i) + 1) * C_i
    """
    demand = 0.0
    for task in tasks:
        if t >= task.deadline:
            num_jobs = (t - task.deadline) // task.period + 1
            demand += num_jobs * task.wcet
    return demand


def analyze_edf(tasks: List[Task]) -> Dict:
    """
    Check EDF schedulability using Processor Demand Approach.
    Returns schedulability result and details.
    """
    total_utilization = calculate_utilization(tasks)
    
    # Quick test: if U > 1, definitely not schedulable
    if total_utilization > 1.0:
        return {
            'schedulable': False,
            'reason': f'Utilization {total_utilization:.4f} > 1.0',
            'utilization': total_utilization
        }
    
    # Check processor demand at critical instants
    # Critical instants are task deadlines
    hyperperiod = calculate_hyperperiod(tasks)
    check_limit = min(hyperperiod, 100000)  # Cap to avoid excessive computation
    
    for task in tasks:
        t = task.deadline
        while t <= check_limit:
            demand = processor_demand(t, tasks)
            if demand > t:
                return {
                    'schedulable': False,
                    'reason': f'Processor demand {demand:.2f} > {t} at t={t}',
                    'violation_time': t,
                    'demand': demand,
                    'utilization': total_utilization
                }
            t += task.period
    
    return {
        'schedulable': True,
        'utilization': total_utilization,
        'hyperperiod': hyperperiod
    }


# ============================================================================
# DISCRETE EVENT SIMULATOR
# ============================================================================

def simulate_rm(tasks: List[Task], duration: int, seed: int = 42) -> Dict:
    """
    Simulate Rate Monotonic scheduling.
    RM: shorter period = higher priority
    """
    random.seed(seed)
    
    # Sort by period for RM priority
    sorted_tasks = sorted(tasks, key=lambda t: t.period)
    
    # Statistics tracking
    stats = {t.id: {'response_times': [], 'misses': 0, 'releases': 0} for t in tasks}
    
    # Job queue and next releases
    ready_queue = []  # Jobs waiting to execute
    next_releases = {t.id: 0 for t in tasks}
    
    current_time = 0
    while current_time < duration:
        # Release new jobs
        for task in sorted_tasks:
            if current_time >= next_releases[task.id]:
                # Generate execution time between BCET and WCET
                exec_time = random.randint(task.bcet, task.wcet)
                job = Job(
                    task_id=task.id,
                    release_time=current_time,
                    deadline=current_time + task.deadline,
                    exec_time=exec_time
                )
                ready_queue.append(job)
                stats[task.id]['releases'] += 1
                next_releases[task.id] = current_time + task.period
        
        # Sort by priority (RM: period, lower = higher priority)
        ready_queue.sort(key=lambda j: sorted_tasks[
            [t.id for t in sorted_tasks].index(j.task_id)].period)
        
        # Execute highest priority job for 1 time unit
        if ready_queue:
            job = ready_queue[0]
            job.remaining -= 1
            
            if job.remaining <= 0:
                # Job completed
                job.completion_time = current_time + 1
                rt = job.response_time
                stats[job.task_id]['response_times'].append(rt)
                
                if job.missed_deadline:
                    stats[job.task_id]['misses'] += 1
                
                ready_queue.pop(0)
        
        current_time += 1
    
    # Calculate final statistics
    results = {}
    for task_id, s in stats.items():
        rts = s['response_times']
        results[task_id] = {
            'avg_rt': sum(rts) / len(rts) if rts else 0,
            'max_rt': max(rts) if rts else 0,
            'misses': s['misses'],
            'releases': s['releases']
        }
    
    return results


def simulate_edf(tasks: List[Task], duration: int, seed: int = 42) -> Dict:
    """
    Simulate Earliest Deadline First scheduling.
    EDF: earlier absolute deadline = higher priority
    """
    random.seed(seed)
    
    # Statistics tracking
    stats = {t.id: {'response_times': [], 'misses': 0, 'releases': 0} for t in tasks}
    
    # Job queue and next releases
    ready_queue = []
    next_releases = {t.id: 0 for t in tasks}
    
    current_time = 0
    while current_time < duration:
        # Release new jobs
        for task in tasks:
            if current_time >= next_releases[task.id]:
                exec_time = random.randint(task.bcet, task.wcet)
                job = Job(
                    task_id=task.id,
                    release_time=current_time,
                    deadline=current_time + task.deadline,
                    exec_time=exec_time
                )
                ready_queue.append(job)
                stats[task.id]['releases'] += 1
                next_releases[task.id] = current_time + task.period
        
        # Sort by deadline (EDF: earlier = higher priority)
        ready_queue.sort(key=lambda j: j.deadline)
        
        # Execute job with earliest deadline
        if ready_queue:
            job = ready_queue[0]
            job.remaining -= 1
            
            if job.remaining <= 0:
                job.completion_time = current_time + 1
                rt = job.response_time
                stats[job.task_id]['response_times'].append(rt)
                
                if job.missed_deadline:
                    stats[job.task_id]['misses'] += 1
                
                ready_queue.pop(0)
        
        current_time += 1
    
    # Calculate final statistics
    results = {}
    for task_id, s in stats.items():
        rts = s['response_times']
        results[task_id] = {
            'avg_rt': sum(rts) / len(rts) if rts else 0,
            'max_rt': max(rts) if rts else 0,
            'misses': s['misses'],
            'releases': s['releases']
        }
    
    return results


# ============================================================================
# COMPARISON AND REPORTING
# ============================================================================

def compare_analysis_simulation(tasks: List[Task], duration: int = 100000) -> Dict:
    """Compare analytical results with simulation results"""
    # Run analysis
    dm_wcrts = analyze_dm(tasks)
    edf_analysis = analyze_edf(tasks)
    
    # Run multiple simulations for better statistics
    num_runs = 5
    rm_sims = [simulate_rm(tasks, duration, seed) for seed in range(num_runs)]
    edf_sims = [simulate_edf(tasks, duration, seed) for seed in range(num_runs)]
    
    # Aggregate simulations (take worst observed)
    rm_agg = aggregate_simulations(rm_sims)
    edf_agg = aggregate_simulations(edf_sims)
    
    return {
        'dm_wcrts': dm_wcrts,
        'edf_analysis': edf_analysis,
        'rm_simulation': rm_agg,
        'edf_simulation': edf_agg
    }


def aggregate_simulations(simulations: List[Dict]) -> Dict:
    """Aggregate multiple simulation runs"""
    if not simulations:
        return {}
    
    task_ids = simulations[0].keys()
    aggregated = {}
    
    for task_id in task_ids:
        max_rts = [sim[task_id]['max_rt'] for sim in simulations]
        avg_rts = [sim[task_id]['avg_rt'] for sim in simulations]
        total_misses = sum(sim[task_id]['misses'] for sim in simulations)
        
        aggregated[task_id] = {
            'max_rt': max(max_rts),  # Worst observed across runs
            'avg_rt': sum(avg_rts) / len(avg_rts),
            'misses': total_misses
        }
    
    return aggregated


def print_comparison_report(tasks: List[Task], results: Dict):
    """Print a formatted comparison report"""
    print("\n" + "="*80)
    print("COMPARISON: ANALYTICAL VS SIMULATION")
    print("="*80)
    
    print("\n| Task | DM WCRT | RM Sim Max | RM Sim Avg | EDF Sim Max | EDF Sim Avg | Deadline |")
    print("|------|---------|------------|------------|-------------|-------------|----------|")
    
    for task in tasks:
        tid = task.id
        dm_wcrt = results['dm_wcrts'].get(tid, float('inf'))
        rm_max = results['rm_simulation'].get(tid, {}).get('max_rt', 0)
        rm_avg = results['rm_simulation'].get(tid, {}).get('avg_rt', 0)
        edf_max = results['edf_simulation'].get(tid, {}).get('max_rt', 0)
        edf_avg = results['edf_simulation'].get(tid, {}).get('avg_rt', 0)
        
        print(f"| {tid:4d} | {dm_wcrt:7.2f} | {rm_max:10.2f} | {rm_avg:10.2f} | "
              f"{edf_max:11.2f} | {edf_avg:11.2f} | {task.deadline:8d} |")
    
    print("\n" + "="*80)
    print("EDF ANALYSIS:")
    edf = results['edf_analysis']
    print(f"  Schedulable: {edf.get('schedulable', 'N/A')}")
    print(f"  Utilization: {edf.get('utilization', 0):.4f}")
    if 'reason' in edf:
        print(f"  Reason: {edf['reason']}")
    
    print("\n" + "="*80)


# ============================================================================
# MAIN EXECUTION
# ============================================================================

if __name__ == "__main__":
    # Test with the first file
    file_path = "data/taskset-0.csv"
    
    print(f"\n{'='*80}")
    print(f"LOADING: {file_path}")
    print(f"{'='*80}")
    
    task_set = load_taskset(file_path)
    
    if not task_set:
        print("Failed to load task set!")
        exit(1)
    
    print(f"Loaded {len(task_set)} tasks.")
    
    # Calculate utilization
    utilization = calculate_utilization(task_set)
    print(f"\nTotal Utilization (U): {utilization:.4f} ({(utilization*100):.2f}%)")
    
    if utilization <= 1.0:
        print("System is UNDERLOADED (Theoretically schedulable by EDF)")
    else:
        print("System is OVERLOADED (Not schedulable)")
    
    # ANALYSIS
    print(f"\n{'='*80}")
    print("ANALYTICAL ANALYSIS")
    print(f"{'='*80}")
    
    # Deadline Monotonic WCRT
    print("\nDeadline Monotonic (DM) - WCRT Analysis:")
    dm_results = analyze_dm(task_set)
    for task_id, wcrt in dm_results.items():
        task = next(t for t in task_set if t.id == task_id)
        status = "✓" if wcrt <= task.deadline else "✗ UNCHEDULABLE"
        print(f"  Task {task_id}: WCRT = {wcrt:.2f} (Deadline: {task.deadline}) {status}")
    
    # EDF Schedulability
    print("\nEarliest Deadline First (EDF) - Processor Demand Analysis:")
    edf_result = analyze_edf(task_set)
    print(f"  Schedulable: {edf_result['schedulable']}")
    print(f"  Utilization: {edf_result['utilization']:.4f}")
    if 'reason' in edf_result:
        print(f"  Reason: {edf_result['reason']}")
    
    # SIMULATION
    SIMULATION_DURATION = 100000
    
    print(f"\n{'='*80}")
    print(f"SIMULATION (Duration: {SIMULATION_DURATION} time units)")
    print(f"{'='*80}")
    
    # RM Simulation
    print("\nRate Monotonic (RM) Simulation:")
    rm_sim = simulate_rm(task_set, SIMULATION_DURATION)
    for task_id, stats in rm_sim.items():
        task = next(t for t in task_set if t.id == task_id)
        status = "✓" if stats['misses'] == 0 else f"✗ {stats['misses']} misses"
        print(f"  Task {task_id}: Avg RT = {stats['avg_rt']:.2f}, "
              f"Max RT = {stats['max_rt']}, Releases = {stats['releases']} {status}")
    
    # EDF Simulation
    print("\nEDF Simulation:")
    edf_sim = simulate_edf(task_set, SIMULATION_DURATION)
    for task_id, stats in edf_sim.items():
        task = next(t for t in task_set if t.id == task_id)
        status = "✓" if stats['misses'] == 0 else f"✗ {stats['misses']} misses"
        print(f"  Task {task_id}: Avg RT = {stats['avg_rt']:.2f}, "
              f"Max RT = {stats['max_rt']}, Releases = {stats['releases']} {status}")
    
    # COMPARISON
    print(f"\n{'='*80}")
    print("COMPARISON: ANALYSIS VS SIMULATION")
    print(f"{'='*80}")
    
    print("\n| Task | DM WCRT | RM Sim Max | EDF Sim Max | Deadline |")
    print("|------|---------|------------|-------------|----------|")
    
    for task in task_set:
        tid = task.id
        dm_wcrt = dm_results.get(tid, float('inf'))
        rm_max = rm_sim.get(tid, {}).get('max_rt', 0)
        edf_max = edf_sim.get(tid, {}).get('max_rt', 0)
        
        print(f"| {tid:4d} | {dm_wcrt:7.2f} | {rm_max:10.2f} | {edf_max:11.2f} | {task.deadline:8d} |")
    
    print(f"\n{'='*80}")
    print("SUMMARY:")
    print(f"  - DM Analysis predicts worst-case response times")
    print(f"  - Simulation shows actual observed max response times")
    print(f"  - EDF should have lower or equal response times than RM")
    print(f"{'='*80}\n")
