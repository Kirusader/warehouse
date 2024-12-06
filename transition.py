import math
import threading
import random
import time

# Q-learning parameters
ALPHA = 0.1  # Learning rate
GAMMA = 0.95  # Discount factor
EPSILON = 1.0  # Exploration rate
EPSILON_DECAY = 0.99
MIN_EPSILON = 0.01
Q_TABLE = {}
lock = threading.Lock()  # Thread safety for Q-table access

def get_neighbors(node, markers):
    """Get neighbors of a given node."""
    x, y = node
    neighbors = [(x + dx, y + dy) for dx, dy in [(-80, 0), (80, 0), (0, -100), (0, 100)]]
    valid_neighbors = [neighbor for neighbor in neighbors if neighbor in markers]
    return valid_neighbors

def initialize_q_table(markers):
    """Initialize Q-table for all markers."""
    global Q_TABLE
    with lock:  # Protect Q-table initialization
        Q_TABLE = {}
        for marker in markers:
            neighbors = get_neighbors(marker, markers)
            if neighbors:
                Q_TABLE[marker] = {neighbor: 0.0 for neighbor in neighbors}
            else:
                Q_TABLE[marker] = {}
                print(f"Warning: Marker {marker} has no neighbors.")
        print(f"Final Q-Table Keys: {list(Q_TABLE.keys())}")

def choose_action(state):
    """Epsilon-greedy action selection."""
    with lock:  # Thread-safe access
        if state not in Q_TABLE or not Q_TABLE[state]:
            print(f"Warning: State {state} is missing or has no valid actions.")
            fallback_state = random.choice(list(Q_TABLE.keys()))
            return random.choice(list(Q_TABLE[fallback_state].keys()))
        if random.uniform(0, 1) < EPSILON:
            return random.choice(list(Q_TABLE[state].keys()))  # Explore
        else:
            return max(Q_TABLE[state], key=Q_TABLE[state].get)  # Exploit

def update_q_table(state, action, reward, next_state):
    """Update Q-table using Q-learning formula."""
    with lock:  # Thread-safe access
        max_future_q = max(Q_TABLE[next_state].values(), default=0)
        current_q = Q_TABLE[state][action]
        Q_TABLE[state][action] = (1 - ALPHA) * current_q + ALPHA * (reward + GAMMA * max_future_q)

def q_learning_path(start, goal, markers, verbose=False):
    """Train Q-learning to find the shortest path."""
    global EPSILON
    if start not in Q_TABLE or goal not in Q_TABLE:
        raise ValueError(f"Invalid start or goal state: {start}, {goal}")
    for episode in range(1000):
        state = start
        while state != goal:
            action = choose_action(state)
            reward = 10 if action == goal else -1
            update_q_table(state, action, reward, action)
            state = action
        EPSILON = max(MIN_EPSILON, EPSILON * EPSILON_DECAY)

    path = [start]
    state = start
    while state != goal:
        state = max(Q_TABLE[state], key=Q_TABLE[state].get)
        path.append(state)
    return path

def move_robot_with_q_learning(robot, path, occupied_positions, target_position, markers):
    """Move robot along Q-learning path."""
    """Move the robot along the path with improved collision handling."""
    goal_marker = min(markers,
                      key=lambda pos: math.hypot(pos[0] - target_position[0], pos[1] - target_position[1]))
    current_position = (round(robot.position()[0]), round(robot.position()[1]))
    start_marker = min(markers,
                       key=lambda pos: math.hypot(pos[0] - current_position[0], pos[1] - current_position[1]))
    robot.goto(start_marker)
    while path:
        step = path.pop(0)
        # Clear the robot's previous position from occupied_positions
        if current_position in occupied_positions:
            occupied_positions.remove(current_position)
        if step in occupied_positions:
            ###
            print(f"Collision detected at {step}. Recalculating...")
            neighbors = get_neighbors(current_position, markers)

            # Attempt alternate paths dynamically
            alternate_path = None
            for neighbor in neighbors:
                if neighbor not in occupied_positions:
                    alternate_path = q_learning_path(current_position, goal_marker, markers)
                    if alternate_path:
                        print(f"Recalculated path via neighbor {neighbor}: {alternate_path}")
                        path = alternate_path
                        break

            # If no alternate path found, retry from current position
            if not alternate_path:
                print("No alternate path available. Retrying...")
                time.sleep(1)
                path = q_learning_path(current_position,  goal_marker, markers)
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
