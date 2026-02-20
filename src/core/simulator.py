"""
Discrete event simulation for scheduling algorithms.
"""

import random
import heapq
from typing import List, Dict, Optional
from dataclasses import dataclass, field
from src.core.models import Task, TaskSet, Job, SimulationResult


@dataclass(order=True)
class Event:
    """Simulation event."""
    time: int
    type: str = field(compare=False)  # 'release', 'completion', 'deadline'
    task_id: int = field(compare=False)
    job: Optional[Job] = field(compare=False, default=None)
    
    def __repr__(self):
        return f"Event({self.type}@t={self.time}, T{self.task_id})"


class SchedulerSimulator:
    """Base class for scheduling simulators."""
    
    def __init__(self, taskset: TaskSet, duration: int = 100000, seed: int = 42):
        self.taskset = taskset
        self.duration = duration
        self.seed = seed
        self.time = 0
        self.event_queue = []
        self.ready_queue = []
        self.results = {}
        self.jobs = {}
        
        random.seed(seed)
        self._init_results()
    
    def _init_results(self):
        """Initialize result tracking."""
        for task in self.taskset.tasks:
            self.results[task.id] = SimulationResult(
                task_id=task.id,
                task_name=task.name
            )
            self.jobs[task.id] = []
    
    def _generate_execution_time(self, task: Task) -> int:
        """Generate random execution time between BCET and WCET."""
        return random.randint(task.bcet, task.wcet)
    
    def _schedule_jobs(self):
        """Schedule jobs - to be implemented by subclasses."""
        raise NotImplementedError
    
    def run(self) -> Dict[int, SimulationResult]:
        """Run simulation."""
        raise NotImplementedError


class RMSimulator(SchedulerSimulator):
    """Rate Monotonic scheduler simulator."""
    
    def __init__(self, taskset: TaskSet, duration: int = 100000, seed: int = 42):
        super().__init__(taskset, duration, seed)
        # Sort tasks by period for RM priority
        self.sorted_tasks = taskset.sort_by_period()
        self.next_releases = {task.id: 0 for task in taskset.tasks}
    
    def _get_priority(self, job: Job):
        """Get RM priority (lower period = higher priority)."""
        task = self.taskset.get_task_by_id(job.task_id)
        return task.period if task else float('inf')
    
    def run(self) -> Dict[int, SimulationResult]:
        """Run RM simulation."""
        current_time = 0
        
        while current_time < self.duration:
            # Release new jobs
            for task in self.sorted_tasks:
                if current_time >= self.next_releases[task.id]:
                    exec_time = self._generate_execution_time(task)
                    job = Job(
                        task_id=task.id,
                        task_name=task.name,
                        release_time=current_time,
                        absolute_deadline=current_time + task.deadline,
                        execution_time=exec_time,
                        remaining_time=exec_time
                    )
                    self.ready_queue.append(job)
                    self.results[task.id].releases += 1
                    self.next_releases[task.id] = current_time + task.period
            
            # Sort by RM priority
            self.ready_queue.sort(key=self._get_priority)
            
            # Execute highest priority job
            if self.ready_queue:
                job = self.ready_queue[0]
                job.remaining_time -= 1
                
                if job.remaining_time <= 0:
                    # Job completed
                    job.completion_time = current_time + 1
                    rt = job.response_time
                    
                    if rt is not None:
                        self.results[job.task_id].response_times.append(rt)
                    
                    if job.completion_time > job.absolute_deadline:
                        job.missed = True
                        self.results[job.task_id].misses += 1
                    
                    self.ready_queue.pop(0)
            
            current_time += 1
        
        return self.results


class EDFSimulator(SchedulerSimulator):
    """EDF scheduler simulator."""
    
    def __init__(self, taskset: TaskSet, duration: int = 100000, seed: int = 42):
        super().__init__(taskset, duration, seed)
        self.next_releases = {task.id: 0 for task in taskset.tasks}
    
    def _get_priority(self, job: Job) -> int:
        """Get EDF priority (earlier deadline = higher priority)."""
        return job.absolute_deadline
    
    def run(self) -> Dict[int, SimulationResult]:
        """Run EDF simulation."""
        current_time = 0
        
        while current_time < self.duration:
            # Release new jobs
            for task in self.taskset.tasks:
                if current_time >= self.next_releases[task.id]:
                    exec_time = self._generate_execution_time(task)
                    job = Job(
                        task_id=task.id,
                        task_name=task.name,
                        release_time=current_time,
                        absolute_deadline=current_time + task.deadline,
                        execution_time=exec_time,
                        remaining_time=exec_time
                    )
                    self.ready_queue.append(job)
                    self.results[task.id].releases += 1
                    self.next_releases[task.id] = current_time + task.period
            
            # Sort by EDF priority (earliest deadline first)
            self.ready_queue.sort(key=self._get_priority)
            
            # Execute job with earliest deadline
            if self.ready_queue:
                job = self.ready_queue[0]
                job.remaining_time -= 1
                
                if job.remaining_time <= 0:
                    # Job completed
                    job.completion_time = current_time + 1
                    rt = job.response_time
                    
                    if rt is not None:
                        self.results[job.task_id].response_times.append(rt)
                    
                    if job.completion_time > job.absolute_deadline:
                        job.missed = True
                        self.results[job.task_id].misses += 1
                    
                    self.ready_queue.pop(0)
            
            current_time += 1
        
        return self.results


class SimulationRunner:
    """Run multiple simulations and aggregate results."""
    
    def __init__(self, taskset: TaskSet, duration: int = 100000, num_runs: int = 5):
        self.taskset = taskset
        self.duration = duration
        self.num_runs = num_runs
    
    def run_rm(self) -> Dict[int, Dict]:
        """Run multiple RM simulations and aggregate."""
        all_runs = []
        
        for seed in range(self.num_runs):
            sim = RMSimulator(self.taskset, self.duration, seed)
            results = sim.run()
            all_runs.append(results)
        
        return self._aggregate_results(all_runs)
    
    def run_edf(self) -> Dict[int, Dict]:
        """Run multiple EDF simulations and aggregate."""
        all_runs = []
        
        for seed in range(self.num_runs):
            sim = EDFSimulator(self.taskset, self.duration, seed)
            results = sim.run()
            all_runs.append(results)
        
        return self._aggregate_results(all_runs)
    
    def _aggregate_results(self, runs: List[Dict[int, SimulationResult]]) -> Dict[int, Dict]:
        """Aggregate results from multiple runs."""
        if not runs:
            return {}
        
        task_ids = list(runs[0].keys())
        aggregated = {}
        
        for task_id in task_ids:
            max_rts = [run[task_id].max_response_time for run in runs]
            avg_rts = [run[task_id].avg_response_time for run in runs]
            total_misses = sum(run[task_id].misses for run in runs)
            total_releases = sum(run[task_id].releases for run in runs)
            
            aggregated[task_id] = {
                'max_rt': max(max_rts),
                'avg_rt': sum(avg_rts) / len(avg_rts),
                'min_rt': min([run[task_id].min_response_time for run in runs]),
                'misses': total_misses,
                'releases': total_releases
            }
        
        return aggregated
