# Policy
def bring_shelf_to_target(robot, shelf_name, target_position, shelves, assigned_tasks):
    """Policy to bring a shelf to a target position."""
    if robot not in assigned_tasks:
        assigned_tasks[robot] = (shelves[shelf_name], target_position)

def take_shelf_to_original(robot, shelf_name, original_position, shelves, assigned_tasks):
    """Policy to take a shelf back to its original position."""
    if robot not in assigned_tasks:
        assigned_tasks[robot] = (shelves[shelf_name], original_position)
