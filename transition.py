import math
import threading
import time
from collections import deque

# Counter to track active robot threads
active_robots = 0
lock = threading.Lock()

def get_neighbors(node, markers):
    """Get neighboring positions on the grid."""
    x, y = node
    neighbors = []
    for dx, dy in [(-80, 0), (80, 0), (0, -100), (0, 100)]:
        neighbor = (x + dx, y + dy)
        if neighbor in markers:
            neighbors.append(neighbor)
    return neighbors

def bfs(start, goal, markers):
    """Find the shortest path between two points using Breadth-First Search."""
    queue = deque([start])
    came_from = {start: None}
    while queue:
        current = queue.popleft()
        if current == goal:
            break
        for neighbor in get_neighbors(current, markers):
            if neighbor not in came_from:
                queue.append(neighbor)
                came_from[neighbor] = current

    path = []
    while goal:
        path.append(goal)
        goal = came_from[goal]
    return path[::-1]

def move_robot(robot, path, occupied_positions, target_position, marker_positions):
    """Move the robot along the path with improved collision handling."""
    goal_marker = min(marker_positions, key=lambda pos: math.hypot(pos[0] - target_position[0], pos[1] - target_position[1]))
    current_position = (round(robot.position()[0]), round(robot.position()[1]))
    start_marker = min(marker_positions, key=lambda pos: math.hypot(pos[0] - current_position[0], pos[1] - current_position[1]))

    robot.goto(start_marker)

    while path:
        step = path.pop(0)

        # Clear the robot's previous position from occupied_positions
        if current_position in occupied_positions:
            occupied_positions.remove(current_position)

        # Check for collisions at the next step
        if step in occupied_positions:
            print(f"Collision detected at {step}. Recalculating path...")
            neighbors = get_neighbors(current_position, marker_positions)

            # Attempt alternate paths dynamically
            alternate_path = None
            for neighbor in neighbors:
                if neighbor not in occupied_positions:
                    alternate_path = bfs(neighbor, goal_marker, marker_positions)
                    if alternate_path:
                        print(f"Recalculated path via neighbor {neighbor}: {alternate_path}")
                        path = alternate_path
                        break

            # If no alternate path found, retry from current position
            if not alternate_path:
                print("No alternate path available. Retrying...")
                time.sleep(1)
                path = bfs(current_position, goal_marker, marker_positions)
                continue

        # Move the robot to the next step
        robot.pencolor("blue")
        robot.pendown()
        robot.goto(step)
        robot.getscreen().update()
        time.sleep(0.5)
        occupied_positions.add(step)
        current_position = step

        # If the robot reaches the goal marker, move directly to the target position
        if step == goal_marker:
            robot.pencolor("green")
            robot.goto(target_position)
            robot.getscreen().update()
            time.sleep(0.5)
            break

    # Clear the robot's position from occupied_positions when task is done
    if current_position in occupied_positions:
        occupied_positions.remove(current_position)

    return robot.position()
