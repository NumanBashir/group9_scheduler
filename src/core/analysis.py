"""
Analytical schedulability analysis algorithms.
"""

import math
from typing import List, Dict, Optional, Tuple
from src.core.models import Task, TaskSet, AnalysisResult


class ResponseTimeAnalyzer:
    """Response Time Analysis for fixed-priority scheduling."""
    
    @staticmethod
    def calculate_wcrt(task: Task, higher_priority_tasks: List[Task], 
                      max_iterations: int = 1000) -> float:
        """
        Calculate Worst-Case Response Time using fixed-point iteration.
        
        Implements Equation 4.24 from Buttazzo:
        R_i = C_i + sum_{j in hp(i)} ceil(R_i / T_j) * C_j
        
        Args:
            task: Task to analyze
            higher_priority_tasks: List of higher priority tasks
            max_iterations: Maximum iterations for convergence
            
        Returns:
            WCRT or infinity if unschedulable
        """
        r = task.wcet  # Initial guess
        
        for _ in range(max_iterations):
            # Calculate interference
            interference = sum(
                math.ceil(r / hp_task.period) * hp_task.wcet
                for hp_task in higher_priority_tasks
            )
            
            new_r = task.wcet + interference
            
            # Check convergence
            if abs(new_r - r) < 0.01:
                return r
            
            # Check if exceeds deadline
            if new_r > task.deadline:
                return float('inf')
            
            r = new_r
        
        return float('inf')  # Did not converge
    
    @staticmethod
    def analyze_taskset_dm(taskset: TaskSet) -> List[AnalysisResult]:
        """
        Analyze entire task set under Deadline Monotonic.
        
        Args:
            taskset: Task set to analyze
            
        Returns:
            List of analysis results per task
        """
        # Sort by deadline (DM priority)
        sorted_tasks = taskset.sort_by_deadline()
        results = []
        
        for i, task in enumerate(sorted_tasks):
            wcrt = ResponseTimeAnalyzer.calculate_wcrt(
                task, 
                sorted_tasks[:i]  # Higher priority tasks
            )
            
            results.append(AnalysisResult(
                task_id=task.id,
                task_name=task.name,
                wcrt=wcrt,
                schedulable=wcrt <= task.deadline,
                deadline=task.deadline
            ))
        
        return results
    
    @staticmethod
    def analyze_taskset_rm(taskset: TaskSet) -> List[AnalysisResult]:
        """
        Analyze entire task set under Rate Monotonic.
        
        Args:
            taskset: Task set to analyze
            
        Returns:
            List of analysis results per task
        """
        # Sort by period (RM priority)
        sorted_tasks = taskset.sort_by_period()
        results = []
        
        for i, task in enumerate(sorted_tasks):
            wcrt = ResponseTimeAnalyzer.calculate_wcrt(
                task,
                sorted_tasks[:i]
            )
            
            results.append(AnalysisResult(
                task_id=task.id,
                task_name=task.name,
                wcrt=wcrt,
                schedulable=wcrt <= task.deadline,
                deadline=task.deadline
            ))
        
        return results


class EDFAnalyzer:
    """EDF schedulability analysis using Processor Demand Approach."""
    
    @staticmethod
    def calculate_hyperperiod(taskset: TaskSet) -> int:
        """Calculate LCM of all periods."""
        from math import gcd
        from functools import reduce
        
        periods = [task.period for task in taskset.tasks]
        return reduce(lambda x, y: x * y // gcd(x, y), periods)
    
    @staticmethod
    def processor_demand(t: int, tasks: List[Task]) -> float:
        """
        Calculate processor demand h(t) at time t.
        
        h(t) = sum_{i} max(0, floor((t - D_i) / T_i) + 1) * C_i
        """
        demand = 0.0
        for task in tasks:
            if t >= task.deadline:
                num_jobs = (t - task.deadline) // task.period + 1
                demand += num_jobs * task.wcet
        return demand
    
    @staticmethod
    def analyze_taskset(taskset: TaskSet, check_limit: Optional[int] = None) -> Dict:
        """
        Check EDF schedulability using Processor Demand Approach.
        
        Args:
            taskset: Task set to analyze
            check_limit: Maximum time to check (default: hyperperiod or 1M)
            
        Returns:
            Dictionary with schedulability result
        """
        total_util = taskset.total_utilization
        
        # Quick check: U > 1 is never schedulable
        if total_util > 1.0:
            return {
                'schedulable': False,
                'utilization': total_util,
                'reason': f'Utilization {total_util:.4f} > 1.0',
                'algorithm': 'Processor Demand'
            }
        
        # Calculate check limit
        if check_limit is None:
            hyperperiod = EDFAnalyzer.calculate_hyperperiod(taskset)
            check_limit = min(hyperperiod, 1000000)
        
        # Check processor demand at critical instants (deadlines)
        for task in taskset.tasks:
            t = task.deadline
            while t <= check_limit:
                demand = EDFAnalyzer.processor_demand(t, taskset.tasks)
                if demand > t:
                    return {
                        'schedulable': False,
                        'utilization': total_util,
                        'violation_time': t,
                        'demand': demand,
                        'reason': f'Processor demand {demand:.2f} > {t} at t={t}',
                        'algorithm': 'Processor Demand'
                    }
                t += task.period
        
        return {
            'schedulable': True,
            'utilization': total_util,
            'hyperperiod': EDFAnalyzer.calculate_hyperperiod(taskset),
            'algorithm': 'Processor Demand'
        }
