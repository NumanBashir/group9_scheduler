import csv
import math

# A simple class to hold task data makes the math easier later
class Task:
    def __init__(self, row):
        self.name = row['Name']
        self.wcet = int(row['WCET'])     # C_i
        self.period = int(row['Period']) # T_i
        self.deadline = int(row['Deadline']) # D_i
        self.id = int(self.name.replace('T', '')) # Turn 'T0' into 0
        
    def __repr__(self):
        return f"Task({self.name}, C={self.wcet}, T={self.period}, D={self.deadline})"

def load_taskset(filepath):
    """Reads a CSV file and returns a list of Task objects."""
    tasks = []
    try:
        with open(filepath, 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                # We interpret the row dictionary into a Task object
                tasks.append(Task(row))
    except FileNotFoundError:
        print(f"Error: Could not find file {filepath}")
        return []
        
    return tasks

def calculate_utilization(tasks):
    """Calculates total utilization U = Sum(C/T)."""
    u = 0.0
    for t in tasks:
        u += t.wcet / t.period
    return u

# --- Main Execution ---
if __name__ == "__main__":
    # Test with the first file you generated
    file_path = "data/taskset-0.csv" 
    
    print(f"--- Loading {file_path} ---")
    task_set = load_taskset(file_path)
    
    if task_set:
        print(f"Loaded {len(task_set)} tasks.")
        
        # 1. Calculate Utilization
        utilization = calculate_utilization(task_set)
        print(f"Total Utilization (U): {utilization:.4f} ({(utilization*100):.2f}%)")
        
        # 2. Check if valid (U <= 1.0)
        if utilization <= 1.0:
            print("System is UNDERLOADED (Theoretically schedulable by EDF)")
        else:
            print("System is OVERLOADED (Not schedulable)")
            
        # Print the first task just to check
        print("\nFirst Task Details:")
        print(task_set[0])