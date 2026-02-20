"""
CSV parsing utilities.
"""

import csv
from pathlib import Path
from typing import List, Optional
from src.core.models import Task, TaskSet


class TaskSetParser:
    """Parser for task set CSV files."""
    
    @staticmethod
    def parse_file(filepath: str) -> Optional[TaskSet]:
        """
        Parse a task set from a CSV file.
        
        Args:
            filepath: Path to CSV file
            
        Returns:
            TaskSet or None if parsing failed
        """
        path = Path(filepath)
        
        if not path.exists():
            raise FileNotFoundError(f"File not found: {filepath}")
        
        tasks = []
        
        with open(path, 'r') as f:
            reader = csv.DictReader(f)
            
            for row in reader:
                task = Task(
                    id=int(row.get('TaskID', row.get('id', 0))),
                    name=row.get('Name', f"T{len(tasks)}"),
                    wcet=int(row['WCET']),
                    bcet=int(row.get('BCET', row['WCET'])),
                    period=int(row['Period']),
                    deadline=int(row['Deadline']),
                    jitter=int(row.get('Jitter', 0))
                )
                tasks.append(task)
        
        return TaskSet(
            tasks=tasks,
            name=path.stem
        )
    
    @staticmethod
    def parse_directory(directory: str, pattern: str = "*.csv") -> List[TaskSet]:
        """
        Parse all task sets in a directory.
        
        Args:
            directory: Directory path
            pattern: File pattern to match
            
        Returns:
            List of TaskSets
        """
        path = Path(directory)
        tasksets = []
        
        if not path.exists():
            raise FileNotFoundError(f"Directory not found: {directory}")
        
        for csv_file in path.rglob(pattern):
            try:
                taskset = TaskSetParser.parse_file(str(csv_file))
                if taskset:
                    tasksets.append(taskset)
            except Exception as e:
                print(f"Warning: Failed to parse {csv_file}: {e}")
        
        return tasksets
    
    @staticmethod
    def get_task_sets_by_utilization(base_dir: str) -> dict:
        """
        Organize task sets by utilization level.
        
        Returns dict like:
        {
            '0.10': [TaskSet, TaskSet, ...],
            '0.20': [TaskSet, TaskSet, ...],
            ...
        }
        """
        from pathlib import Path
        
        path = Path(base_dir)
        by_utilization = {}
        
        # Find all CSV files
        for csv_file in path.rglob("*.csv"):
            # Extract utilization from path (e.g., "0.10-util")
            parts = csv_file.parts
            for part in parts:
                if 'util' in part.lower():
                    # Extract number (e.g., "0.10-util" -> "0.10")
                    util = part.split('-')[0]
                    if util not in by_utilization:
                        by_utilization[util] = []
                    
                    try:
                        taskset = TaskSetParser.parse_file(str(csv_file))
                        if taskset:
                            by_utilization[util].append(taskset)
                    except Exception as e:
                        pass
        
        return by_utilization
