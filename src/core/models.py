"""
Core data models for real-time scheduling.
"""

from dataclasses import dataclass, field
from typing import Optional, List, Dict
import math


@dataclass
class Task:
    """Represents a periodic real-time task."""
    id: int
    name: str
    wcet: int  # Worst-case execution time (C_i)
    bcet: int  # Best-case execution time
    period: int  # Period (T_i)
    deadline: int  # Relative deadline (D_i)
    jitter: int = 0  # Release jitter
    priority: Optional[int] = None  # For fixed-priority scheduling
    
    def __post_init__(self):
        if self.priority is None:
            # Default to deadline for DM
            self.priority = self.deadline
    
    @property
    def utilization(self) -> float:
        """Task utilization U_i = C_i / T_i"""
        return self.wcet / self.period
    
    @property
    def density(self) -> float:
        """Task density = C_i / D_i"""
        return self.wcet / self.deadline
    
    def __repr__(self) -> str:
        return f"Task({self.name}, C={self.wcet}, T={self.period}, D={self.deadline})"
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for serialization."""
        return {
            'id': self.id,
            'name': self.name,
            'wcet': self.wcet,
            'bcet': self.bcet,
            'period': self.period,
            'deadline': self.deadline,
            'jitter': self.jitter,
            'utilization': self.utilization
        }


@dataclass
class Job:
    """Represents a single job (instance) of a task."""
    task_id: int
    task_name: str
    release_time: int
    absolute_deadline: int
    execution_time: int
    remaining_time: int
    completed: bool = False
    completion_time: Optional[int] = None
    missed: bool = False
    
    @property
    def response_time(self) -> Optional[int]:
        """Calculate response time if job completed."""
        if self.completion_time is not None:
            return self.completion_time - self.release_time
        return None
    
    @property
    def lateness(self) -> Optional[int]:
        """Calculate lateness (completion_time - deadline)."""
        if self.completion_time is not None:
            return self.completion_time - self.absolute_deadline
        return None
    
    def __repr__(self) -> str:
        status = "✓" if self.completed else "⋯"
        if self.missed:
            status = "✗"
        return f"Job(T{self.task_id}, released@{self.release_time}, {status})"


@dataclass
class TaskSet:
    """Collection of tasks."""
    tasks: List[Task]
    name: str = "unnamed"
    
    @property
    def total_utilization(self) -> float:
        """Total system utilization."""
        return sum(task.utilization for task in self.tasks)
    
    @property
    def hyperperiod(self) -> int:
        """Calculate LCM of all periods."""
        from math import gcd
        from functools import reduce
        
        periods = [task.period for task in self.tasks]
        return reduce(lambda x, y: x * y // gcd(x, y), periods)
    
    @property
    def num_tasks(self) -> int:
        return len(self.tasks)
    
    def get_task_by_id(self, task_id: int) -> Optional[Task]:
        """Find task by ID."""
        for task in self.tasks:
            if task.id == task_id:
                return task
        return None
    
    def sort_by_deadline(self) -> List[Task]:
        """Sort tasks by deadline (for DM)."""
        return sorted(self.tasks, key=lambda t: t.deadline)
    
    def sort_by_period(self) -> List[Task]:
        """Sort tasks by period (for RM)."""
        return sorted(self.tasks, key=lambda t: t.period)
    
    def __repr__(self) -> str:
        return f"TaskSet({self.name}, {self.num_tasks} tasks, U={self.total_utilization:.4f})"


@dataclass
class SimulationResult:
    """Results from a simulation run."""
    task_id: int
    task_name: str
    response_times: List[int] = field(default_factory=list)
    misses: int = 0
    releases: int = 0
    executed_units: int = 0
    on_time_units: int = 0
    late_units: int = 0
    unfinished_units: int = 0
    
    @property
    def avg_response_time(self) -> float:
        if self.response_times:
            return sum(self.response_times) / len(self.response_times)
        return 0.0
    
    @property
    def max_response_time(self) -> int:
        if self.response_times:
            return max(self.response_times)
        return 0
    
    @property
    def min_response_time(self) -> int:
        if self.response_times:
            return min(self.response_times)
        return 0


@dataclass
class AnalysisResult:
    """Results from analytical analysis."""
    task_id: int
    task_name: str
    wcrt: float  # Worst-case response time
    schedulable: bool
    deadline: int
    
    @property
    def slack(self) -> float:
        """Time slack before deadline."""
        return self.deadline - self.wcrt
