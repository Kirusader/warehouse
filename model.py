# Model
def assign_task(shelf_name, target_position, shelves, robots, assigned_tasks, assigned_robots):
    """Assign a robot to move a shelf."""
    shelf_position = shelves.get(shelf_name)
    if shelf_position is None:
        print(f"Shelf {shelf_name} not found.")
        return None

    # Find the first available robot
    available_robots = [r for r in robots if r not in assigned_robots.values()]
    if not available_robots:
        print("No available robots to assign.")
        return None

    robot = available_robots[0]  # Assign the first available robot
    assigned_robots[robot] = shelf_name
    assigned_tasks[robot] = (shelf_position, target_position)
    return robot

def release_robot(robot, assigned_robots, assigned_tasks):
    """Release a robot after completing its task."""
    if robot in assigned_robots:
        del assigned_robots[robot]
    if robot in assigned_tasks:
        del assigned_tasks[robot]
