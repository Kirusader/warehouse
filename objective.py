# Objective Function
def evaluate_efficiency(tasks_completed, total_distance):
    """Calculate efficiency based on tasks completed and distance traveled."""
    return (tasks_completed / total_distance )  if total_distance > 0 else 0

def evaluate_task_completion(assigned_tasks, completed_tasks):
    """Measure task completion ratio."""
    return len(completed_tasks) / len(assigned_tasks) if assigned_tasks else 0
